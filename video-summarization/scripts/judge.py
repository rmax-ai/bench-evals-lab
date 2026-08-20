#!/usr/bin/env python3
"""Score one video-summarization candidate output with an LLM judge.

The judge reads the fact sheet (ground truth, extracted once per video) and the
candidate's SummarySchema data dict, then scores five fidelity dimensions on a
1-5 scale: structure, faithfulness, coverage, precision, compression. It also
lists hallucinations verbatim (candidate-JSON strings not supported by the
fact sheet, whitespace-normalized). The judge NEVER sees the video, only the
fact sheet.

- gemini-3.1-pro-preview judgments go through the native generateContent
  endpoint with a pure-text prompt (no file_data).
- deepseek-v4-pro judgments go through the DeepSeek OpenAI-compatible chat
  endpoint with ``response_format {"type": "json_object"}``.

The judge's own JSON is validated against a local schema once; on failure it
retries once, and on a second failure writes ``{"error": ...}`` and exits 1.
Output contract matches the other evals' judge.py: ``{"judged_candidate",
"judge_model", "scores", "total", "rationale", "hallucinations",
"elapsed_seconds", "cost_usd"}``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from summarize_video import (
    JUDGE_TIMEOUT,
    estimate_cost,
    native_generate,
    native_response_text,
    native_usage,
    parse_json_response,
    write_json,
)

DIMENSIONS = ["structure", "faithfulness", "coverage", "precision", "compression"]
JUDGE_MODELS = ["gemini-3.1-pro-preview", "deepseek-v4-pro"]

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

JUDGE_INSTRUCTIONS = (
    "You are an evaluation judge for a fidelity eval. You will receive a fact "
    "sheet extracted from a YouTube video (the reference ground truth, covering "
    "both spoken audio and slides) and a candidate's structured JSON summary of "
    "the video. You never see the video itself; score only against the fact "
    "sheet. Score the candidate JSON strictly on these five dimensions from 1 "
    "(severe failure) to 5 (near-perfect). Be strict: use the full 1-5 range; "
    "most outputs should land 2-4; do not cluster at 3. Each score MUST be an "
    "integer between 1 and 5 inclusive; never use a 10-point or 100-point "
    "scale.\n\n"
    "- structure: all schema fields sensibly populated and organized.\n"
    "- faithfulness: EVERY string in the candidate JSON is supported by the "
    "fact sheet. Penalize invented claims, numbers, and quotes.\n"
    "- coverage: material content of the fact sheet (topics, claims, examples, "
    "terminology, frameworks, takeaways, quotes) is present in the JSON.\n"
    "- precision: quotes verbatim, names and numbers exact.\n"
    "- compression: no redundant restatement, high density.\n\n"
    "Hallucinations are candidate-JSON strings that cannot be found in the "
    "fact sheet (compare whitespace-normalized). List them verbatim in the "
    "hallucinations array.\n\n"
    "Respond with a single JSON object (never an array, never a copy of the "
    "fact sheet) with exactly three keys: \"scores\" "
    "(an object with integer values for structure, faithfulness, coverage, "
    "precision, compression), \"rationale\" (a string, at most 150 words, "
    "citing concrete evidence for each sub-4 score), and \"hallucinations\" "
    "(an array of strings). Output ONLY valid JSON, no markdown fences, no "
    "commentary."
)

JUDGE_RETRY_NUDGE = (
    "Your previous response was not valid. Respond with ONLY a single JSON "
    "object (never an array, no markdown fences) with exactly three keys: "
    '{"scores": {"structure": 1-5, "faithfulness": 1-5, "coverage": 1-5, '
    '"precision": 1-5, "compression": 1-5}, "rationale": "string", '
    '"hallucinations": ["string", ...]}. Each score MUST be an integer from 1 '
    "to 5 inclusive."
)


def validate_verdict(obj: Any) -> dict:
    """Validate a parsed judge response against the local output schema."""
    if not isinstance(obj, dict):
        raise ValueError("judge response is not a JSON object")
    if not isinstance(obj.get("scores"), dict):
        raise ValueError("judge response is missing the scores object")
    scores: dict[str, int] = {}
    for dim in DIMENSIONS:
        if dim not in obj["scores"]:
            raise ValueError(f"judge response is missing the {dim} score")
        try:
            value = int(obj["scores"][dim])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{dim} score is not an integer") from error
        if not 1 <= value <= 5:
            raise ValueError(f"judge returned out-of-range score {value} for {dim}")
        scores[dim] = value
    rationale = obj.get("rationale")
    if not isinstance(rationale, str):
        raise ValueError("judge response has a non-string rationale")
    hallucinations = obj.get("hallucinations")
    if not isinstance(hallucinations, list) or not all(
        isinstance(h, str) for h in hallucinations
    ):
        raise ValueError("judge response hallucinations must be an array of strings")
    return {"scores": scores, "rationale": rationale, "hallucinations": hallucinations}


def build_user_prompt(fact_sheet: dict, candidate_data: dict) -> str:
    """Build the judge prompt text: fact sheet ground truth + candidate JSON."""
    fact_content = {key: value for key, value in fact_sheet.items() if key != "metadata"}
    facts_pretty = json.dumps(fact_content, indent=2, ensure_ascii=False)
    candidate_pretty = json.dumps(candidate_data, indent=2, ensure_ascii=False)
    return (
        "# FACT SHEET (video ground truth: audio + slides)\n\n"
        f"{facts_pretty}\n\n"
        "# CANDIDATE JSON\n\n"
        f"{candidate_pretty}"
    )


def _call_gemini_text(judge_model: str, content: str) -> tuple[str, int, int, float]:
    """Native generateContent call with a pure-text prompt (no file_data)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required; set it in the environment before running."
        )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": content}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 8192,
        },
    }
    response = native_generate(judge_model, api_key, payload, timeout=JUDGE_TIMEOUT)
    pt, ct, _ = native_usage(response)
    text = native_response_text(response)
    return text, pt, ct, estimate_cost(judge_model, pt, ct)


def _call_deepseek(judge_model: str, content: str) -> tuple[str, int, int, float]:
    """DeepSeek OpenAI-compatible chat call with json_object mode."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is required; set it in the environment before running."
        )
    body = {
        "model": judge_model,
        "messages": [
            {"role": "system", "content": JUDGE_INSTRUCTIONS},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 16000,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = httpx.post(
            DEEPSEEK_URL, json=body, headers=headers, timeout=JUDGE_TIMEOUT
        )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"DeepSeek judge request failed: {exc}") from exc
    if response.status_code != 200:
        snippet = response.text[:300]
        raise RuntimeError(
            f"DeepSeek judge returned {response.status_code} "
            f"for {judge_model}: {snippet}"
        )
    payload = response.json()
    text = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    return text, pt, ct, estimate_cost(judge_model, pt, ct)


def call_judge(
    judge_model: str, user_prompt: str, nudge: bool = False
) -> tuple[str, int, int, float]:
    """One judge LLM call; returns (text, prompt_tokens, completion_tokens, cost_usd)."""
    content = user_prompt if not nudge else f"{user_prompt}\n\n{JUDGE_RETRY_NUDGE}"
    if judge_model == "gemini-3.1-pro-preview":
        return _call_gemini_text(judge_model, content)
    if judge_model == "deepseek-v4-pro":
        return _call_deepseek(judge_model, content)
    raise ValueError(f"unknown judge model {judge_model!r}")


def run_judgment(
    *, judge_model: str, fact_sheet_file: Path, candidate_json_file: Path,
    output_file: Path,
) -> dict:
    """Score one candidate result; write and return the verdict dict."""
    if judge_model not in JUDGE_MODELS:
        raise ValueError(f"unknown judge model {judge_model!r}")
    fact_sheet = json.loads(fact_sheet_file.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_json_file.read_text(encoding="utf-8"))
    judged_candidate = candidate.get("candidate") or candidate_json_file.stem
    data = candidate.get("data")
    started = time.perf_counter()

    if data is None:
        error_note = "candidate produced no data (summarization failed); nothing to judge"
        write_json(output_file, {"error": error_note})
        return {
            "judged_candidate": judged_candidate,
            "judge_model": judge_model,
            "error": error_note,
        }

    user_prompt = build_user_prompt(fact_sheet, data)
    scores: dict[str, int] | None = None
    rationale = ""
    hallucinations: list[str] = []
    prompt_tokens = completion_tokens = 0
    cost_usd = 0.0
    error_note = ""
    try:
        for attempt in (0, 1):
            try:
                text, prompt_tokens, completion_tokens, cost_usd = call_judge(
                    judge_model, user_prompt, nudge=bool(attempt))
                obj = parse_json_response(text)
                verdict = validate_verdict(obj)
                scores = verdict["scores"]
                rationale = verdict["rationale"]
                hallucinations = verdict["hallucinations"]
                break
            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as parse_error:
                error_note = f"{type(parse_error).__name__}: {str(parse_error)[:300]}"
                if os.environ.get("JUDGE_DEBUG"):
                    print(f"judge debug attempt {attempt} raw: {text[:400]!r}",
                          file=sys.stderr)
    except (httpx.HTTPError, RuntimeError, OSError) as transport_error:
        error_note = f"{type(transport_error).__name__}: {transport_error}"

    elapsed = time.perf_counter() - started
    if scores is None:
        result = {"error": error_note or "judge call failed"}
        write_json(output_file, result)
        return {
            "judged_candidate": judged_candidate,
            "judge_model": judge_model,
            "error": result["error"],
        }

    total = round(sum(scores.values()) / len(scores), 2)
    result = {
        "judged_candidate": judged_candidate,
        "judge_model": judge_model,
        "scores": scores,
        "total": total,
        "rationale": rationale,
        "hallucinations": hallucinations,
        "elapsed_seconds": round(elapsed, 4),
        "cost_usd": round(cost_usd, 6),
    }
    write_json(output_file, result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-judgment command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", required=True, choices=JUDGE_MODELS,
                        help="Judge model identifier")
    parser.add_argument("--fact-sheet", type=Path, required=True,
                        help="Path to the fact-sheet ground truth JSON")
    parser.add_argument("--candidate-json", type=Path, required=True,
                        help="Path to the candidate result JSON")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the judge JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected failures into concise errors."""
    args = parse_args(argv)
    try:
        result = run_judgment(
            judge_model=args.judge, fact_sheet_file=args.fact_sheet,
            candidate_json_file=args.candidate_json, output_file=args.output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if "error" in result:
        print(f"error: {result['error']}", file=sys.stderr)
        return 1
    dims = ", ".join(f"{k}={v}" for k, v in result["scores"].items())
    print(f"wrote {args.output}: total {result['total']:.2f}/5 ({dims}), "
          f"{result['elapsed_seconds']:.1f}s, ${result['cost_usd']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
