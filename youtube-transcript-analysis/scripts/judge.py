#!/usr/bin/env python3
"""Score one analysis artifact against its source video with an LLM judge.

Two providers are supported:

- `gemini` (default): the judge ingests the video URI itself (slides + audio)
  plus the verbatim transcript. Highest ground-truth fidelity; same-vendor.
- `deepseek` (OpenAI-compatible): the judge scores the analysis against a
  text fact sheet (extracted once from the video by `ground_truth.py`) plus
  the transcript. Cross-vendor independence; no video ingestion.

Both return per-dimension scores, a rationale, and a list of hallucinated or
unsupported statements quoted verbatim from the analysis. Disagreements
between judges are the interesting signal, not noise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from analyze import estimate_cost

DIMENSIONS = ["structure", "faithfulness", "coverage", "precision", "compression"]

RUBRIC = """Score the candidate analysis on each dimension from 1 (severe
failure) to 5 (near-perfect). Be strict: most outputs should land 2-4. Use the
full range; do not cluster at 3.

- structure: all 9 required sections present (overview, topic map, key points,
  frameworks, examples, takeaways, claims to verify, quotes, summary), clear
  headings, coherent markdown.
- faithfulness: every claim, number, and quote in the analysis is supported by
  the source material you are given. Penalize invented statistics, fabricated
  quotes, and statements the source neither supports nor contains.
  Transcription errors are not the candidate's fault.
- coverage: the analysis captures the source's key topics, claims, examples,
  frameworks, and terminology without material omissions.
- precision: concrete terminology, numbers, names, and details from the
  source rather than generic filler. Penalize vague rewording.
- compression: high information density; no repetition, boilerplate, or empty
  connective prose. Longer is not better; density is.

Also list every statement in the analysis that is NOT supported by the source
material (hallucinations), quoting the analysis verbatim. If none, use an
empty list."""

JUDGE_INSTRUCTIONS_GEMINI = (
    "You are an evaluation judge. You will receive the source video (audio and "
    "slides), its transcript, and a candidate analysis of that video. Score the "
    "analysis strictly against the rubric.\n\n"
    f"{RUBRIC}\n\n"
    "Scores are integers 1-5 per dimension. Rationale: at most 150 words, "
    "mentioning concrete evidence for each sub-4 score. Do not be lenient."
)

JUDGE_INSTRUCTIONS_FACTS = (
    "You are an evaluation judge. You will receive a fact sheet extracted from "
    "the source video (covering both spoken audio and slides), the verbatim "
    "transcript, and a candidate analysis of that video. Score the analysis "
    "strictly against the rubric.\n\n"
    f"{RUBRIC}\n\n"
    "Scores are integers 1-5 per dimension. Rationale: at most 150 words, "
    "mentioning concrete evidence for each sub-4 score. Do not be lenient."
)


@dataclass
class Judgment:
    """One judge verdict over one analysis artifact."""

    judged_model: str
    judge_model: str
    judge_model_version: str | None
    provider: str = "gemini"
    scores: dict = None  # type: ignore[assignment]
    total: float = 0.0
    rationale: str = ""
    hallucinations: list = None  # type: ignore[assignment]
    elapsed_seconds: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float = 0.0
    output_file: str = ""

    def __post_init__(self):
        if self.scores is None:
            self.scores = {}
        if self.hallucinations is None:
            self.hallucinations = []


def _judge_schema():
    """Build the JSON response schema for structured Gemini judge output."""
    from google import genai

    def integer_property(description: str):
        return genai.types.Schema(type=genai.types.Type.INTEGER, description=description)

    scores_schema = genai.types.Schema(
        type=genai.types.Type.OBJECT,
        properties={dim: integer_property(f"1-5 score for {dim}") for dim in DIMENSIONS},
        required=list(DIMENSIONS),
    )
    return genai.types.Schema(
        type=genai.types.Type.OBJECT,
        properties={
            "scores": scores_schema,
            "rationale": genai.types.Schema(type=genai.types.Type.STRING),
            "hallucinations": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                items=genai.types.Schema(type=genai.types.Type.STRING),
            ),
        },
        required=["scores", "rationale", "hallucinations"],
    )


def _validate_verdict(verdict: dict) -> dict[str, int]:
    """Range-check judge scores and return them keyed by dimension."""
    scores = {dim: int(verdict["scores"][dim]) for dim in DIMENSIONS}
    for dim, value in scores.items():
        if not 1 <= value <= 5:
            raise ValueError(f"judge returned out-of-range score {value} for {dim}")
    return scores


def _parse_verdict(text: str) -> dict:
    """Parse judge JSON output tolerantly.

    json_object mode only guarantees valid JSON, not the requested shape.
    Handle markdown fences and flat (unwrapped) score objects.
    """
    import re

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        verdict = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        verdict = json.loads(match.group(0))
    if not isinstance(verdict, dict):
        raise json.JSONDecodeError("verdict is not an object", text, 0)
    if "scores" not in verdict:
        flat = {dim: verdict[dim] for dim in DIMENSIONS if dim in verdict}
        if len(flat) == len(DIMENSIONS):
            verdict = {**verdict, "scores": flat}
        else:
            raise KeyError("scores")
    return verdict


def _run_deepseek_judge(
    *, judge_model: str, user_prompt: str, nudge: str | None = None
) -> tuple[str, int | None, int | None, str | None, float]:
    """Call the DeepSeek OpenAI-compatible endpoint.

    Returns (json_text, input_tokens, output_tokens, model_version, cost_usd).
    Cost uses cache-hit accounting when the API reports it.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required for the deepseek judge provider.")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    content = user_prompt if not nudge else f"{user_prompt}\n\n{nudge}"
    body = {
        "model": judge_model,
        "messages": [
            {"role": "system", "content": JUDGE_INSTRUCTIONS_FACTS},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 16000,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = json.loads(response.read().decode("utf-8"))
    text = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    cost = estimate_cost(judge_model, prompt_tokens, completion_tokens, None)
    cache_hit = usage.get("prompt_cache_hit_tokens") or 0
    cache_miss = usage.get("prompt_cache_miss_tokens")
    if cache_hit and cache_miss is not None:
        # Flat rates: $0.435/M miss, $0.003625/M hit, $0.87/M output.
        cost = (cache_miss * 0.435 + cache_hit * 0.003625) / 1_000_000
        cost += (completion_tokens or 0) * 0.87 / 1_000_000
    return text, prompt_tokens, completion_tokens, payload.get("model"), cost


NUDGE = (
    "The previous response failed schema validation. Respond with valid JSON "
    "ONLY, containing exactly three keys: \"scores\" (an object with integer "
    "values for structure, faithfulness, coverage, precision, compression), "
    "\"rationale\" (a string), and \"hallucinations\" (an array of strings)."
)


def run_judgment(
    *,
    transcript_file: Path,
    analysis_file: Path,
    judge_model: str,
    output_dir: Path,
    judged_model: str,
    provider: str = "gemini",
    video_url: str | None = None,
    ground_truth_file: Path | None = None,
) -> Judgment:
    """Score one analysis, write its judgment JSON, and return the verdict.

    gemini provider: judge ingests the video (slides + audio) plus transcript.
    deepseek provider: judge scores against the fact sheet plus transcript.
    """
    transcript = transcript_file.read_text(encoding="utf-8")
    analysis = analysis_file.read_text(encoding="utf-8")

    if provider == "deepseek":
        if ground_truth_file is None or not ground_truth_file.exists():
            raise RuntimeError("deepseek judge requires a ground-truth fact sheet "
                               "(run scripts/ground_truth.py first)")
        facts = ground_truth_file.read_text(encoding="utf-8")
        user_prompt = (
            "# FACT SHEET (video ground truth: audio + slides)\n\n"
            f"{facts}\n\n"
            "# TRANSCRIPT (verbatim audio reference)\n\n"
            f"{transcript}\n\n"
            "# CANDIDATE ANALYSIS\n\n"
            f"{analysis}"
        )
        started = time.perf_counter()
        text = ""
        prompt_tokens = completion_tokens = None
        model_version = None
        cost_usd = 0.0
        for attempt in (0, 1):
            try:
                text, prompt_tokens, completion_tokens, model_version, cost_usd = (
                    _run_deepseek_judge(
                        judge_model=judge_model,
                        user_prompt=user_prompt,
                        nudge=NUDGE if attempt else None,
                    )
                )
                verdict = _parse_verdict(text)
                break
            except (urllib.error.URLError, urllib.error.HTTPError,
                    json.JSONDecodeError, KeyError) as error:
                if attempt:
                    raise RuntimeError(f"deepseek judge call failed: {error}") from error
        elapsed_seconds = time.perf_counter() - started
    elif provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
        from google import genai

        user_prompt = (
            "# TRANSCRIPT (verbatim audio reference)\n\n"
            f"{transcript}\n\n"
            "# CANDIDATE ANALYSIS\n\n"
            f"{analysis}"
        )
        client = genai.Client(api_key=api_key)
        contents: list[Any] = [JUDGE_INSTRUCTIONS_GEMINI, user_prompt]
        if video_url:
            from analyze import canonical_video_url

            video_part = genai.types.Part.from_uri(
                file_uri=canonical_video_url(video_url), mime_type="video/mp4"
            )
            contents.insert(0, video_part)
        started = time.perf_counter()
        response = client.models.generate_content(
            model=judge_model,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_judge_schema(),
                temperature=0.0,
            ),
        )
        elapsed_seconds = time.perf_counter() - started
        text = response.text
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        completion_tokens = getattr(usage, "candidates_token_count", None)
        model_version = getattr(response, "model_version", None)
    else:
        raise ValueError(f"unknown judge provider {provider!r}")

    if provider == "gemini":
        verdict = json.loads(text)
    # deepseek branch already parsed verdict via _parse_verdict (tolerant).
    scores = _validate_verdict(verdict)
    total = round(sum(scores.values()) / len(scores), 2)
    if provider == "deepseek":
        final_cost = cost_usd
    else:
        final_cost = estimate_cost(judge_model, prompt_tokens, completion_tokens, model_version)
    judgment = Judgment(
        judged_model=judged_model,
        judge_model=judge_model,
        judge_model_version=model_version,
        provider=provider,
        scores=scores,
        total=total,
        rationale=verdict.get("rationale", ""),
        hallucinations=verdict.get("hallucinations", []),
        elapsed_seconds=elapsed_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=final_cost,
        output_file="",
    )
    output_path = output_dir / f"{analysis_file.stem}.{safe_model_name(judge_model)}.judge.json"
    judgment.output_file = output_path.name
    output_path.write_text(json.dumps(asdict(judgment), indent=2) + "\n", encoding="utf-8")
    return judgment


def safe_model_name(name: str) -> str:
    """Convert a model identifier into a portable filename component."""
    import re

    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-judgment command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_file", type=Path, help="Analysis markdown artifact to judge")
    parser.add_argument("--transcript-file", type=Path, required=True)
    parser.add_argument("--judge-model", default="gemini-2.5-pro")
    parser.add_argument("--provider", choices=["gemini", "deepseek"], default="gemini")
    parser.add_argument("--judged-model", default=None, help="Model name recorded in the verdict")
    parser.add_argument("--video-url", default=None,
                        help="YouTube URL/ID the judge ingests (slides + audio); gemini provider")
    parser.add_argument("--ground-truth-file", type=Path, default=None,
                        help="Fact sheet path; required for the deepseek provider")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Where to write the judgment JSON (defaults to analysis dir)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected input failures into concise errors."""
    args = parse_args(argv)
    try:
        output_dir = args.output_dir or args.analysis_file.parent
        judgment = run_judgment(
            transcript_file=args.transcript_file,
            analysis_file=args.analysis_file,
            judge_model=args.judge_model,
            output_dir=output_dir,
            judged_model=args.judged_model or args.analysis_file.stem,
            provider=args.provider,
            video_url=args.video_url,
            ground_truth_file=args.ground_truth_file,
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"wrote {judgment.output_file}: total {judgment.total:.2f}/5 "
        f"({', '.join(f'{k}={v}' for k, v in judgment.scores.items())}), "
        f"{judgment.elapsed_seconds:.1f}s, ${judgment.cost_usd:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
