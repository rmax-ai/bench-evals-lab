#!/usr/bin/env python3
"""Summarize one YouTube video with a Gemini candidate via the native endpoint.

Mirrors the production yt-insights ``summarize_video()`` call
(``src/yt_insights/llm.py``) exactly: the native generateContent endpoint,
YouTube ingestion through ``parts[].file_data.file_uri``, JSON output mode
(``responseMimeType`` only; no ``response_schema`` is sent, so no
additionalProperties stripping is needed), a 65536-token output cap, and token
accounting from each response's ``usageMetadata``. The prompt comes from
``prompts/summary.md`` with the video title and id filled in.

On JSON parse or SummarySchema validation failure the request is retried once
with a corrective nudge appended; a second failure writes ``{"error": ...}``
and exits 1. The OpenAI-compatible endpoint does NOT accept YouTube URLs, so
this script only ever targets the native ``:generateContent`` endpoint.
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

GEMINI_NATIVE_BASE = "https://generativelanguage.googleapis.com/v1beta"

CANDIDATES = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
]

# Flat-rate USD per 1M tokens (input, output); copied from the existing evals'
# PRICING dicts (already committed there) and yt-insights costs.py.
PRICING_PER_MILLION: dict[str, tuple[float, float]] = {
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "deepseek-v4-pro": (0.435, 0.87),
}

NATIVE_TIMEOUT = 1800  # video ingestion can take minutes
JUDGE_TIMEOUT = 600
MAX_OUTPUT_TOKENS = 65536  # documented ceiling for gemini-2.5-flash

RETRY_NUDGE = "Respond with ONLY the corrected JSON object."

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "summary.md"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "corpus" / "manifest.json"


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


def _strip_code_fences(text: str) -> str:
    """Strip one surrounding pair of markdown code fences."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json_object(text: str) -> str:
    """Return the first balanced ``{...}`` object found in ``text``.

    Tracks brace nesting depth and ignores braces inside JSON strings,
    honoring backslash escapes. Returns ``text`` unchanged when no balanced
    object is found. Same mechanism as yt-insights llm.py.
    """
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    i = start
    while i < len(text):
        char = text[i]
        if in_string:
            if char == "\\":
                i += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text


def parse_json_response(text: str) -> dict:
    """Parse model text as a single JSON object, tolerating fences and prose."""
    stripped = _strip_code_fences(text)
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        obj = json.loads(_extract_json_object(stripped))
    if not isinstance(obj, dict):
        raise json.JSONDecodeError("response is not a JSON object", text, 0)
    return obj


def load_prompt() -> str:
    """Read the production summary prompt verbatim from prompts/summary.md."""
    return PROMPT_PATH.read_text(encoding="utf-8")


def resolve_title(video_id: str) -> str:
    """Look up the video title from corpus/manifest.json; '' when unknown."""
    try:
        document = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    for item in document.get("items") or []:
        if item.get("video_id") == video_id:
            return item.get("title") or ""
    return ""


def build_prompt(title: str, video_id: str, channel: str = "") -> str:
    """Fill the summary.md template with the video title, id, and channel."""
    prompt = load_prompt().replace("{title}", title).replace("{channel}", channel or "")
    if video_id:
        channel_line = f"Channel: {channel or ''}"
        prompt = prompt.replace(
            channel_line, f"Video ID: {video_id}\n{channel_line}", 1
        )
    return prompt


def native_url(model: str) -> str:
    """Native generateContent endpoint URL for ``model``."""
    return f"{GEMINI_NATIVE_BASE}/models/{model}:generateContent"


def native_generate(
    model: str,
    api_key: str,
    payload: dict,
    timeout: int = NATIVE_TIMEOUT,
) -> httpx.Response:
    """POST to the native generateContent endpoint; raise on non-200."""
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    try:
        response = httpx.post(
            native_url(model), json=payload, headers=headers, timeout=timeout
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Gemini video analysis request failed: {exc}"
        ) from exc
    if response.status_code != 200:
        snippet = response.text[:300]
        raise RuntimeError(
            f"Gemini video analysis returned {response.status_code} "
            f"for {model}: {snippet}"
        )
    return response


def native_usage(response: httpx.Response) -> tuple[int, int, int]:
    """(prompt_tokens, completion_tokens, cached_tokens) from usageMetadata."""
    try:
        metadata = response.json().get("usageMetadata") or {}
    except ValueError:
        metadata = {}
    return (
        int(metadata.get("promptTokenCount") or 0),
        int(metadata.get("candidatesTokenCount") or 0),
        int(metadata.get("cachedContentTokenCount") or 0),
    )


def native_response_text(response: httpx.Response) -> str:
    """Concatenate the text parts of a native generateContent response."""
    try:
        result = response.json()
    except ValueError:
        return ""
    try:
        candidates = result.get("candidates") or []
        parts = candidates[0]["content"]["parts"] if candidates else []
    except (KeyError, TypeError, IndexError):
        return ""
    return "\n".join(
        part["text"] for part in parts if isinstance(part, dict) and "text" in part
    )


def parse_native_response(response: httpx.Response) -> tuple[dict | None, str]:
    """Return ``(parsed, raw_text)``; raw text feeds error snippets.

    Mirrors the production yt-insights parse path: fence-strip, then direct
    JSON parse, then balanced-object extraction.
    """
    text = native_response_text(response)
    stripped = _strip_code_fences(text)
    try:
        return json.loads(stripped), text
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_extract_json_object(stripped)), text
    except json.JSONDecodeError:
        return None, text


def build_payload(prompt: str, video_url: str, extra_text: str | None = None) -> dict:
    """Build the native generateContent payload for one video summary call."""
    parts: list[dict[str, Any]] = [
        {"file_data": {"mime_type": "video/mp4", "file_uri": video_url}},
        {"text": prompt},
    ]
    if extra_text:
        parts.append({"text": extra_text})
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }


def run_summarize(
    *, candidate: str, video_url: str, video_id: str, output: Path
) -> dict:
    """Summarize one video with one candidate; write and return the result dict."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required; set it in the environment before running."
        )
    if candidate not in CANDIDATES:
        raise ValueError(f"unknown candidate {candidate!r}")

    prompt = build_prompt(resolve_title(video_id), video_id)
    started = time.perf_counter()
    retries = 0
    error_note = ""
    prompt_tokens = completion_tokens = 0
    cost_usd = 0.0
    data: dict | None = None

    for attempt in (0, 1):
        payload = build_payload(
            prompt, video_url, extra_text=RETRY_NUDGE if attempt else None
        )
        try:
            response = native_generate(candidate, api_key, payload)
        except (httpx.HTTPError, RuntimeError) as transport_error:
            error_note = f"{type(transport_error).__name__}: {transport_error}"
            break
        pt, ct, _ = native_usage(response)
        prompt_tokens += pt
        completion_tokens += ct
        cost_usd = estimate_cost(candidate, prompt_tokens, completion_tokens)
        parsed, raw = parse_native_response(response)
        try:
            if parsed is None:
                raise json.JSONDecodeError("response text is not JSON", raw, 0)
            data = SummarySchema.model_validate(parsed).model_dump(mode="json")
            break
        except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as parse_error:
            retries = attempt + 1
            error_note = f"{type(parse_error).__name__}: {str(parse_error)[:300]}"

    elapsed = time.perf_counter() - started
    if data is None:
        result = {
            "candidate": candidate,
            "video_id": video_id,
            "data": None,
            "validation_passed": False,
            "retries": retries,
            "elapsed_seconds": round(elapsed, 4),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": round(cost_usd, 6),
            "error": error_note or "unknown error",
        }
        write_json(output, result)
        return result

    result = {
        "candidate": candidate,
        "video_id": video_id,
        "data": data,
        "validation_passed": True,
        "retries": retries,
        "elapsed_seconds": round(elapsed, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost_usd, 6),
    }
    write_json(output, result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-summarization command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES,
                        help="Gemini candidate model")
    parser.add_argument("--video-url", required=True,
                        help="YouTube watch URL the native endpoint ingests")
    parser.add_argument("--video-id", required=True,
                        help="YouTube video ID (used for prompt fill and artifacts)")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the result JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected failures into concise errors."""
    args = parse_args(argv)
    try:
        result = run_summarize(
            candidate=args.candidate, video_url=args.video_url,
            video_id=args.video_id, output=args.output)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not result.get("validation_passed"):
        print(f"error: {result.get('error', 'summarization failed')}", file=sys.stderr)
        return 1
    print(f"wrote {args.output}: {result['elapsed_seconds']:.1f}s, "
          f"${result['cost_usd']:.6f}, retries={result['retries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
