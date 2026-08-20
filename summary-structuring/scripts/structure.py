#!/usr/bin/env python3
"""Convert a markdown video summary into a SummarySchema JSON object.

Two modes:

- ``parser``: deterministic template parser, no LLM call. It strips the YAML
  frontmatter, splits the body on ``## `` sections, and maps each section to
  SummarySchema fields following the corpus template. Unrecognized sections
  are skipped; absent sections produce empty lists.
- LLM candidates (deepseek-v4-pro, gemini-3.5-flash-lite, gemini-2.5-flash):
  the markdown plus a schema description are sent to the model; the response
  is parsed and validated against SummarySchema, with one retry on parse or
  validation failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

# Make the eval root importable regardless of the invocation cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema import SummarySchema

# Pricing table copied from youtube-transcript-analysis/scripts/analyze.py
# (already committed there); flat-rate estimates as of 2026-08-16.
PRICING_PER_MILLION: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
    # "gemini-flash-lite-latest" deliberately omitted: the alias resolves to
    # gemini-3.5-flash-lite, so pricing must come from model_version, not a
    # stale alias entry.
    "gemini-2.5-flash-lite": (0.10, 0.40),  # Deprecated; retained for old runs.
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.7-flash": (0.75, 3.75),  # scheduled: 1.50/7.50 from 2027-01-01
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    # DeepSeek (flat rates as of 2026-08-16; peak/off-peak billing starts
    # 16:00 UTC 2026-08-16 -- treat these as estimates).
    "deepseek-v4-flash": (0.14, 0.28),
    "deepseek-v4-pro": (0.435, 0.87),
}

CANDIDATES = ["parser", "deepseek-v4-pro", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
LLM_CANDIDATES = set(CANDIDATES) - {"parser"}

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

STRUCTURING_PROMPT = (
    "You are given a markdown summary of a YouTube video. Convert it into the "
    "single JSON object matching the schema below. Output ONLY valid JSON, no "
    "markdown fences, no commentary. The JSON must contain nothing that is not "
    "in the markdown. Do not drop material content: keep all topics, key "
    "claims, examples, terminology, frameworks, takeaways, claims to verify, "
    "and quotes. Preserve quotes verbatim. Empty lists are allowed only where "
    "the markdown has no such content."
)

RETRY_NUDGE = (
    "Your previous response was not valid JSON matching the schema. Respond "
    "with ONLY the corrected JSON object."
)

SCHEMA_DESCRIPTION = """SCHEMA (a single JSON object with these fields):
- overview: object with title (string; the video title), speaker (string), channel (string), main_topic (string), executive_summary (string; the opening paragraph), purpose (string)
- topic_map: array of topic sections; each is an object with topic (string; section heading), timestamp_range (string like "104-149" when the markdown gives one, else null), explanation (string), key_claims (array of strings), examples (array of strings), terminology (array of strings), why_it_matters (string)
- key_points: array of objects with point (string; heading), explanation (string), evidence (string), practical_implication (string)
- frameworks: array of objects with name (string; heading), how_it_works (string), components (array of strings), when_to_use (string)
- examples: array of objects with what_happened (string; heading), illustrates (string), lesson (string)
- takeaways: object with immediate (array of strings), strategic (array of strings), questions_to_investigate (array of strings)
- claims_to_verify: array of objects with claim (string) and claim_type (string; the parenthetical type when present, else "")
- quotes: array of objects with text (string; the verbatim quote, without surrounding quotation marks) and timestamp (integer seconds when the markdown gives "(at M:SS)", else null)
- compressed: object with bullets (array of strings), keywords (array of strings), core_insight (string)"""

# --- markdown parsing -------------------------------------------------------

SECTION_HEADER_RE = re.compile(r"^##\s+(.+)$")
SUB_HEADER_RE = re.compile(r"^###\s+(.+)$")
BOLD_LABEL_RE = re.compile(r"^-\s+\*\*(.+?)\*\*:\s*(.*)$")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
RANGE_RE = re.compile(r"^(.*?)\s*\((\d+-\d+)\)\s*$")
CLAIM_RE = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")
QUOTE_LINE_RE = re.compile(r"^>\s?(.*)$")
QUOTE_PARTS_RE = re.compile(r'^(?:"(.*)"|(.+?))\s*(?:\(at\s+(\d+):(\d+)\))?\s*$')


def write_json(path: Path, obj: dict) -> None:
    """Write a JSON object to path, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def estimate_cost(model: str, prompt_tokens: int | None,
                  completion_tokens: int | None) -> float:
    """Estimate request cost in USD from the flat pricing table."""
    prices = PRICING_PER_MILLION.get(model)
    if prices is None:
        print(f"warning: no price configured for {model}; reporting cost as $0",
              file=sys.stderr)
        return 0.0
    return ((prompt_tokens or 0) * prices[0] + (completion_tokens or 0) * prices[1]) / 1_000_000


def strip_quotes(value: str) -> str:
    """Strip one surrounding pair of single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    """Parse simple ``key: value`` YAML frontmatter; returns lowercase keys."""
    metadata: dict[str, str] = {}
    current_key: str | None = None
    for line in lines:
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if match:
            current_key = match.group(1).lower()
            metadata[current_key] = match.group(2).strip()
        elif current_key and line.strip() and line.startswith((" ", "\t")):
            metadata[current_key] += " " + line.strip()
    if "title" in metadata:
        metadata["title"] = strip_quotes(metadata["title"])
    return metadata


def strip_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    """Remove the leading ``---`` YAML block; return (body, frontmatter)."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                frontmatter = parse_frontmatter(lines[1:i])
                body = "\n".join(lines[i + 1:])
                return body.strip(), frontmatter
    return text.strip(), {}


def split_sections(body: str) -> dict[str, list[str]]:
    """Split the body into sections keyed by their ``## `` header (lowercased)."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def split_range(header: str) -> tuple[str, str | None]:
    """Split ``Topic (104-149)`` into (topic, timestamp_range)."""
    match = RANGE_RE.match(header)
    if match:
        return match.group(1).strip(), match.group(2)
    return header.strip(), None


def parse_labeled_blocks(lines: list[str],
                         field_spec: dict[str, tuple[str, str]]) -> list[dict]:
    """Parse ``### `` sub-blocks of ``- **Label**: value`` lines.

    field_spec maps a lowercased label to (field_name, kind) where kind is
    "text" (inline value plus continuation lines) or "list" (following
    bullets). Each returned dict includes a "_header" key with the heading.
    """
    blocks: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] | None = None
    for line in lines:
        match = SUB_HEADER_RE.match(line)
        if match:
            header = match.group(1).strip()
            if not header:
                continue
            if current is not None:
                blocks.append(current)
            current = {"_header": header, "_lines": []}
        elif current is not None:
            current["_lines"].append(line)
    if current is not None:
        blocks.append(current)

    result: list[dict] = []
    for block in blocks:
        item: dict[str, Any] = {"_header": block["_header"]}
        for _label, (field, kind) in field_spec.items():
            item[field] = [] if kind == "list" else ""
        list_mode: str | None = None
        text_mode: str | None = None
        for line in block["_lines"]:
            bold = BOLD_LABEL_RE.match(line)
            if bold:
                label = bold.group(1).lower()
                value = bold.group(2)
                spec = field_spec.get(label)
                if spec is None:
                    list_mode, text_mode = None, None
                    continue
                field, kind = spec
                if kind == "list":
                    item[field] = []
                    list_mode, text_mode = field, None
                else:
                    item[field] = value
                    list_mode, text_mode = None, field
                continue
            if list_mode:
                bullet = BULLET_RE.match(line)
                if bullet:
                    item[list_mode].append(bullet.group(1).strip())
                continue
            if text_mode:
                stripped = line.strip()
                if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                    item[text_mode] = (item[text_mode] + " " + stripped).strip()
        result.append(item)
    return result


def parse_overview(lines: list[str], frontmatter: dict[str, str]) -> dict[str, str]:
    """Parse the Overview section: labeled fields plus the opening paragraph."""
    label_map = {
        "speaker": "speaker",
        "channel": "channel",
        "main topic": "main_topic",
        "purpose": "purpose",
    }
    overview = {
        "title": frontmatter.get("title", ""),
        "speaker": "",
        "channel": "",
        "main_topic": "",
        "executive_summary": "",
        "purpose": "",
    }
    exec_parts: list[str] = []
    for line in lines:
        bold = BOLD_LABEL_RE.match(line)
        if bold:
            label = bold.group(1).lower()
            if label in label_map:
                overview[label_map[label]] = bold.group(2)
            continue
        stripped = line.strip()
        if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            exec_parts.append(stripped)
    overview["executive_summary"] = " ".join(exec_parts)
    return overview


def parse_takeaways(lines: list[str]) -> dict[str, list[str]]:
    """Parse the Actionable Takeaways section into its three lists."""
    label_map = {
        "immediate": "immediate",
        "strategic": "strategic",
        "questions to investigate": "questions_to_investigate",
    }
    takeaways: dict[str, list[str]] = {
        "immediate": [], "strategic": [], "questions_to_investigate": [],
    }
    mode: str | None = None
    for line in lines:
        bold = BOLD_LABEL_RE.match(line)
        if bold:
            mode = label_map.get(bold.group(1).lower())
            continue
        if mode:
            bullet = BULLET_RE.match(line)
            if bullet:
                takeaways[mode].append(bullet.group(1).strip())
    return takeaways


def parse_claims(lines: list[str]) -> list[dict[str, str]]:
    """Parse the Claims Worth Verifying bullets (claim, optional parenthetical type)."""
    claims: list[dict[str, str]] = []
    for line in lines:
        bullet = BULLET_RE.match(line)
        if not bullet:
            continue
        content = bullet.group(1).strip()
        match = CLAIM_RE.match(content)
        if match:
            claims.append({"claim": match.group(1).strip(),
                           "claim_type": match.group(2).strip()})
        else:
            claims.append({"claim": content, "claim_type": ""})
    return claims


def parse_quotes(lines: list[str]) -> list[dict[str, Any]]:
    """Parse Notable Quotes blockquotes; timestamps are converted to seconds."""
    quotes: list[dict[str, Any]] = []
    for line in lines:
        quote_line = QUOTE_LINE_RE.match(line)
        if not quote_line:
            continue
        content = quote_line.group(1).strip()
        parts = QUOTE_PARTS_RE.match(content)
        if not parts:
            continue
        text = (parts.group(1) if parts.group(1) is not None else parts.group(2) or "").strip()
        timestamp = None
        if parts.group(3) is not None and parts.group(4) is not None:
            timestamp = int(parts.group(3)) * 60 + int(parts.group(4))
        quotes.append({"text": text, "timestamp": timestamp})
    return quotes


def parse_compressed(lines: list[str]) -> dict[str, Any]:
    """Parse the Compressed Summary: bullets, keywords, and core insight."""
    compressed: dict[str, Any] = {"bullets": [], "keywords": [], "core_insight": ""}
    for line in lines:
        bullet = BULLET_RE.match(line)
        if not bullet:
            continue
        content = bullet.group(1).strip()
        if content.startswith("**Keywords**:"):
            keywords = content[len("**Keywords**:"):].strip()
            compressed["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
        elif content.startswith("**Core insight**:"):
            compressed["core_insight"] = content[len("**Core insight**:"):].strip()
        else:
            compressed["bullets"].append(content)
    return compressed


TOPIC_SPEC = {
    "explanation": ("explanation", "text"),
    "key claims": ("key_claims", "list"),
    "examples": ("examples", "list"),
    "terminology": ("terminology", "list"),
    "why it matters": ("why_it_matters", "text"),
}
KEY_POINT_SPEC = {
    "explanation": ("explanation", "text"),
    "evidence": ("evidence", "text"),
    "practical implication": ("practical_implication", "text"),
}
FRAMEWORK_SPEC = {
    "how it works": ("how_it_works", "text"),
    "components": ("components", "list"),
    "when to use": ("when_to_use", "text"),
}
EXAMPLE_SPEC = {
    "illustrates": ("illustrates", "text"),
    "lesson": ("lesson", "text"),
}

SECTION_MAPPING = {
    "overview": "overview",
    "topic map": "topic_map",
    "key points": "key_points",
    "frameworks, models & processes": "frameworks",
    "examples & case studies": "examples",
    "actionable takeaways": "takeaways",
    "claims worth verifying": "claims_to_verify",
    "notable quotes": "quotes",
    "compressed summary": "compressed",
}


def parse_markdown(markdown: str) -> dict:
    """Parse a corpus-style markdown summary into a validated SummarySchema dict."""
    body, frontmatter = strip_frontmatter(markdown)
    sections = split_sections(body)

    topic_map = parse_labeled_blocks(sections.get("topic map", []), TOPIC_SPEC)
    for item in topic_map:
        item["topic"], item["timestamp_range"] = split_range(item.pop("_header"))

    key_points = parse_labeled_blocks(sections.get("key points", []), KEY_POINT_SPEC)
    for item in key_points:
        item["point"] = item.pop("_header")

    frameworks = parse_labeled_blocks(sections.get("frameworks, models & processes", []), FRAMEWORK_SPEC)
    for item in frameworks:
        item["name"] = item.pop("_header")

    examples = parse_labeled_blocks(sections.get("examples & case studies", []), EXAMPLE_SPEC)
    for item in examples:
        item["what_happened"] = item.pop("_header")

    data = {
        "overview": parse_overview(sections.get("overview", []), frontmatter),
        "topic_map": topic_map,
        "key_points": key_points,
        "frameworks": frameworks,
        "examples": examples,
        "takeaways": parse_takeaways(sections.get("actionable takeaways", [])),
        "claims_to_verify": parse_claims(sections.get("claims worth verifying", [])),
        "quotes": parse_quotes(sections.get("notable quotes", [])),
        "compressed": parse_compressed(sections.get("compressed summary", [])),
    }
    return SummarySchema.model_validate(data).model_dump(mode="json")


# --- LLM calls --------------------------------------------------------------

def parse_json_response(text: str) -> dict:
    """Parse a model response as a JSON object, tolerating markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        obj = json.loads(match.group(0))
    if not isinstance(obj, dict):
        raise json.JSONDecodeError("response is not a JSON object", text, 0)
    return obj


def call_llm(model: str, messages: list[dict[str, str]]) -> tuple[str, int, int, float]:
    """POST one chat completion; returns (text, prompt_tokens, completion_tokens, cost_usd).

    Keys are read from the environment only; run_with_key.py is the sole
    resolver of credentials from the Hermes pass store.
    """
    if model == "deepseek-v4-pro":
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required; set it in the environment before running.")
        url = DEEPSEEK_URL
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "max_tokens": 16000,
        }
    elif model in {"gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"}:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
        url = GEMINI_URL
        body = {"model": model, "messages": messages, "max_completion_tokens": 16000}
    else:
        raise ValueError(f"no endpoint configured for model {model!r}")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=600) as client:
        response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        payload = response.json()
    text = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    return text, prompt_tokens, completion_tokens, estimate_cost(model, prompt_tokens, completion_tokens)


def build_messages(markdown: str, nudge: bool = False) -> list[dict[str, str]]:
    """Build the messages array for one structuring request."""
    user = f"{STRUCTURING_PROMPT}\n\n{SCHEMA_DESCRIPTION}\n\n# MARKDOWN\n\n{markdown}"
    messages = [{"role": "user", "content": user}]
    if nudge:
        messages.append({"role": "user", "content": RETRY_NUDGE})
    return messages


def _error_result(candidate: str, *, retries: int, elapsed: float,
                  prompt_tokens: int, completion_tokens: int, cost_usd: float,
                  error_note: str) -> dict:
    return {
        "candidate": candidate,
        "model": candidate,
        "data": None,
        "validation_passed": False,
        "retries": retries,
        "elapsed_seconds": round(elapsed, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost_usd, 6),
        "error": error_note or "unknown error",
    }


def run_structure(*, candidate: str, input_path: Path, output_path: Path) -> dict:
    """Run one candidate on one markdown file; write and return the result dict."""
    markdown = input_path.read_text(encoding="utf-8")
    started = time.perf_counter()

    if candidate == "parser":
        data = parse_markdown(markdown)
        result = {
            "candidate": "parser",
            "model": "parser",
            "data": data,
            "validation_passed": True,
            "retries": 0,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": 0.0,
        }
        write_json(output_path, result)
        return result

    if candidate not in LLM_CANDIDATES:
        raise ValueError(f"unknown candidate {candidate!r}")

    retries = 0
    error_note = ""
    prompt_tokens = completion_tokens = 0
    cost_usd = 0.0
    data = None
    try:
        for attempt in (0, 1):
            try:
                messages = build_messages(markdown, nudge=bool(attempt))
                text, prompt_tokens, completion_tokens, cost_usd = call_llm(candidate, messages)
                obj = parse_json_response(text)
                data = SummarySchema.model_validate(obj).model_dump(mode="json")
                break
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as parse_error:
                retries = attempt + 1
                error_note = f"{type(parse_error).__name__}: {str(parse_error)[:300]}"
    except (httpx.HTTPError, RuntimeError, OSError) as transport_error:
        error_note = f"{type(transport_error).__name__}: {transport_error}"
        retries = 0

    elapsed = time.perf_counter() - started
    if data is None:
        result = _error_result(
            candidate, retries=retries, elapsed=elapsed,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            cost_usd=cost_usd, error_note=error_note,
        )
        write_json(output_path, result)
        return result

    result = {
        "candidate": candidate,
        "model": candidate,
        "data": data,
        "validation_passed": True,
        "retries": retries,
        "elapsed_seconds": round(elapsed, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost_usd, 6),
    }
    write_json(output_path, result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-run command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES,
                        help="parser or one of the LLM candidates")
    parser.add_argument("--input", type=Path, required=True,
                        help="Path to the markdown summary")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the result JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected failures into concise errors."""
    args = parse_args(argv)
    try:
        result = run_structure(candidate=args.candidate, input_path=args.input,
                               output_path=args.output)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not result.get("validation_passed"):
        print(f"error: {result.get('error', 'structuring failed')}", file=sys.stderr)
        return 1
    print(f"wrote {args.output}: {result['elapsed_seconds']:.1f}s, "
          f"${result['cost_usd']:.6f}, retries={result['retries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
