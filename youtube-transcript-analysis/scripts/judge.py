#!/usr/bin/env python3
"""Score one analysis artifact against its source transcript with an LLM judge.

The judge receives the verbatim transcript (ground truth) plus one model's
analysis markdown and returns per-dimension scores, a rationale, and a list
of hallucinated or unsupported statements quoted verbatim from the analysis.

Bias caveat: the judge is a Gemini model judging Gemini outputs. Same-vendor
judging can inherit vendor quirks; treat small score deltas (<0.5) as noise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
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
  the video (spoken content or slides) or the transcript. Penalize invented
  statistics, fabricated quotes, and statements neither source contradicts or
  supports. Transcription errors are not the candidate's fault.
- coverage: the analysis captures the video's key topics, claims, examples,
  frameworks, and terminology without material omissions.
- precision: concrete terminology, numbers, names, and details from the
  transcript rather than generic filler. Penalize vague rewording.
- compression: high information density; no repetition, boilerplate, or empty
  connective prose. Longer is not better; density is.

Also list every statement in the analysis that is NOT supported by the video
(spoken content or slides) or the transcript (hallucinations), quoting the
analysis verbatim. If none, use an empty list."""

JUDGE_INSTRUCTIONS = (
    "You are an evaluation judge. You will receive the source video (audio and "
    "slides), its transcript, and a candidate analysis of that video. Score the "
    "analysis strictly against the rubric.\n\n"
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
    scores: dict[str, int]
    total: float
    rationale: str
    hallucinations: list[str]
    elapsed_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float
    output_file: str


def _judge_schema():
    """Build the JSON response schema for structured judge output."""
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


def run_judgment(
    *,
    transcript_file: Path,
    analysis_file: Path,
    judge_model: str,
    output_dir: Path,
    judged_model: str,
    video_url: str | None = None,
) -> Judgment:
    """Score one analysis, write its judgment JSON, and return the verdict.

    When `video_url` is given, the judge ingests the video itself (slides and
    audio), matching the source material the analyzed models saw. The
    transcript is still supplied as a compact verbatim reference for the
    audio channel.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
    from google import genai

    transcript = transcript_file.read_text(encoding="utf-8")
    analysis = analysis_file.read_text(encoding="utf-8")
    user_prompt = (
        "# TRANSCRIPT (verbatim audio reference)\n\n"
        f"{transcript}\n\n"
        "# CANDIDATE ANALYSIS\n\n"
        f"{analysis}"
    )

    client = genai.Client(api_key=api_key)
    contents: list[Any] = [JUDGE_INSTRUCTIONS, user_prompt]
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
    verdict = json.loads(response.text)
    scores = {dim: int(verdict["scores"][dim]) for dim in DIMENSIONS}
    for dim, value in scores.items():
        if not 1 <= value <= 5:
            raise ValueError(f"judge returned out-of-range score {value} for {dim}")
    total = round(sum(scores.values()) / len(scores), 2)

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", None)
    completion_tokens = getattr(usage, "candidates_token_count", None)
    model_version = getattr(response, "model_version", None)
    judgment = Judgment(
        judged_model=judged_model,
        judge_model=judge_model,
        judge_model_version=model_version,
        scores=scores,
        total=total,
        rationale=verdict.get("rationale", ""),
        hallucinations=verdict.get("hallucinations", []),
        elapsed_seconds=elapsed_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=estimate_cost(judge_model, prompt_tokens, completion_tokens, model_version),
        output_file="",
    )
    output_path = output_dir / f"{analysis_file.stem}.judge.json"
    judgment.output_file = output_path.name
    output_path.write_text(json.dumps(asdict(judgment), indent=2) + "\n", encoding="utf-8")
    return judgment


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-judgment command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_file", type=Path, help="Analysis markdown artifact to judge")
    parser.add_argument("--transcript-file", type=Path, required=True)
    parser.add_argument("--judge-model", default="gemini-2.5-pro")
    parser.add_argument("--judged-model", default=None, help="Model name recorded in the verdict")
    parser.add_argument("--video-url", default=None,
                        help="YouTube URL/ID the judge ingests (slides + audio)")
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
            video_url=args.video_url,
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
