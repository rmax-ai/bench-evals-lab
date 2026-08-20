#!/usr/bin/env python3
"""Score one structuring candidate output with an LLM judge (fidelity eval).

The judge reads the markdown summary (reference ground truth) and the
candidate's data dict, then scores five fidelity dimensions on a 1-5 scale:
structure, faithfulness, coverage, precision, compression. It also lists
hallucinations verbatim. The judge's own JSON is validated against a local
schema once; on failure it retries once, and on a second failure writes
{"error": "..."} and exits 1.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

import structure

DIMENSIONS = ["structure", "faithfulness", "coverage", "precision", "compression"]
JUDGE_MODELS = ["gemini-2.5-pro", "deepseek-v4-pro"]

JUDGE_INSTRUCTIONS = (
    "You are an evaluation judge for a fidelity eval. You will receive a "
    "markdown summary of a YouTube video (the reference ground truth) and a "
    "candidate's structured JSON extraction of it. Score the candidate JSON "
    "strictly on these five dimensions from 1 (severe failure) to 5 "
    "(near-perfect). Be strict: use the full 1-5 range; most outputs should "
    "land 2-4; do not cluster at 3.\n\n"
    "- structure: all schema fields sensibly populated and organized.\n"
    "- faithfulness: EVERY string in the candidate JSON is supported by the "
    "markdown. Penalize invented claims, numbers, and quotes.\n"
    "- coverage: material content of the markdown (topics, claims, examples, "
    "terminology, frameworks, takeaways, quotes) is present in the JSON.\n"
    "- precision: quotes verbatim, names and numbers exact.\n"
    "- compression: no redundant restatement, high density.\n\n"
    "Hallucinations are candidate-JSON strings that cannot be found in the "
    "markdown (compare whitespace-normalized). List them verbatim in the "
    "hallucinations array.\n\n"
    "Respond with a single JSON object with exactly three keys: \"scores\" "
    "(an object with integer values for structure, faithfulness, coverage, "
    "precision, compression), \"rationale\" (a string, at most 150 words, "
    "citing concrete evidence for each sub-4 score), and \"hallucinations\" "
    "(an array of strings). Output ONLY valid JSON, no markdown fences, no "
    "commentary."
)

JUDGE_RETRY_NUDGE = (
    "Your previous response was not valid. Respond with ONLY the JSON object "
    '{"scores": {"structure": int, "faithfulness": int, "coverage": int, '
    '"precision": int, "compression": int}, "rationale": "string", '
    '"hallucinations": ["string", ...]}.'
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


def build_messages(markdown: str, candidate_data: dict, nudge: bool = False) -> list[dict[str, str]]:
    """Build the messages array for one judge request."""
    pretty = json.dumps(candidate_data, indent=2, ensure_ascii=False)
    user = (
        "# MARKDOWN (reference ground truth)\n\n"
        f"{markdown}\n\n"
        "# CANDIDATE JSON\n\n"
        f"{pretty}"
    )
    messages = [
        {"role": "system", "content": JUDGE_INSTRUCTIONS},
        {"role": "user", "content": user},
    ]
    if nudge:
        messages.append({"role": "user", "content": JUDGE_RETRY_NUDGE})
    return messages


def run_judgment(*, judge_model: str, markdown_file: Path,
                 candidate_json_file: Path, output_file: Path) -> dict:
    """Score one candidate result; write and return the verdict dict."""
    if judge_model not in JUDGE_MODELS:
        raise ValueError(f"unknown judge model {judge_model!r}")
    markdown = markdown_file.read_text(encoding="utf-8")
    candidate = json.loads(candidate_json_file.read_text(encoding="utf-8"))
    judged_candidate = candidate.get("candidate") or candidate_json_file.stem
    data = candidate.get("data")
    started = time.perf_counter()

    if data is None:
        error_note = "candidate produced no data (structuring failed); nothing to judge"
        structure.write_json(output_file, {"error": error_note})
        return {
            "judged_candidate": judged_candidate,
            "judge_model": judge_model,
            "error": error_note,
        }

    scores: dict[str, int] | None = None
    rationale = ""
    hallucinations: list[str] = []
    prompt_tokens = completion_tokens = 0
    cost_usd = 0.0
    error_note = ""
    try:
        for attempt in (0, 1):
            try:
                messages = build_messages(markdown, data, nudge=bool(attempt))
                text, prompt_tokens, completion_tokens, cost_usd = structure.call_llm(judge_model, messages)
                obj = structure.parse_json_response(text)
                verdict = validate_verdict(obj)
                scores = verdict["scores"]
                rationale = verdict["rationale"]
                hallucinations = verdict["hallucinations"]
                break
            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as parse_error:
                error_note = f"{type(parse_error).__name__}: {str(parse_error)[:300]}"
    except (httpx.HTTPError, RuntimeError, OSError) as transport_error:
        error_note = f"{type(transport_error).__name__}: {transport_error}"

    elapsed = time.perf_counter() - started
    if scores is None:
        result = {"error": error_note or "judge call failed"}
        structure.write_json(output_file, result)
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
    structure.write_json(output_file, result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-judgment command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", required=True, choices=JUDGE_MODELS,
                        help="Judge model identifier")
    parser.add_argument("--markdown", type=Path, required=True,
                        help="Path to the reference markdown summary")
    parser.add_argument("--candidate-json", type=Path, required=True,
                        help="Path to the candidate result JSON")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the judge JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected failures into concise errors."""
    args = parse_args(argv)
    try:
        result = run_judgment(judge_model=args.judge, markdown_file=args.markdown,
                              candidate_json_file=args.candidate_json,
                              output_file=args.output)
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
