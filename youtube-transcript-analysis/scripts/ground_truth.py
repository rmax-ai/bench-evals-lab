#!/usr/bin/env python3
"""Extract a text fact sheet from one YouTube video (audio + slides) via Gemini.

The fact sheet is the ground-truth document text-only judges (e.g. DeepSeek)
score analyses against: every factual claim visible in the video — spoken
numbers, slide statistics, names, provider lists, verbatim quotes — distilled
into inspectable text. It is a committed artifact and can be amended by hand.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze import canonical_video_url, estimate_cost

FACTS_PROMPT = """Extract ALL factual claims from this video, from BOTH the
spoken audio AND any text visible on slides. The verbatim transcript is
provided as the audio reference; slides must be read from the video itself.

Include, as a structured markdown fact sheet:
- Every number and statistic, with its context (e.g. benchmark results,
  percentage changes, star counts, download counts).
- Names: people, projects, tools, companies, frameworks, benchmarks.
- Every list shown or spoken (provider lists, feature lists, sections).
- Verbatim quotes (exact wording) with timestamps where available.
- Dates, version numbers, licenses, pricing.
- Diagrams/frameworks described: their names and components.

Rules:
- Be exhaustive; a fact omitted here will be treated as unsupported later.
- For each fact, mark its source: [audio] or [slide].
- Do not interpret or editorialize. Do not add facts from outside the video.
- If the transcript and slides disagree on a detail, report both with sources.
- Output only the fact sheet, in markdown."""


@dataclass
class GroundTruthMeta:
    """Recorded measurements for one fact-sheet extraction."""

    video_slug: str
    model: str
    model_version: str | None
    elapsed_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float
    output_file: str


def run_ground_truth(
    *,
    video_url: str,
    transcript_file: Path,
    model: str,
    output_dir: Path,
    slug: str,
) -> GroundTruthMeta:
    """Extract one fact sheet, write ground-truth.md, return its metrics."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
    from google import genai

    canonical_url = canonical_video_url(video_url)
    transcript = transcript_file.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    facts_path = output_dir / "ground-truth.md"

    client = genai.Client(api_key=api_key)
    video_part = genai.types.Part.from_uri(file_uri=canonical_url, mime_type="video/mp4")
    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=[
            video_part,
            FACTS_PROMPT,
            f"# TRANSCRIPT (audio reference)\n\n{transcript}",
        ],
    )
    elapsed_seconds = time.perf_counter() - started
    text = getattr(response, "text", None) or ""
    facts_path.write_text(text, encoding="utf-8")

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", None)
    completion_tokens = getattr(usage, "candidates_token_count", None)
    model_version = getattr(response, "model_version", None)
    meta = GroundTruthMeta(
        video_slug=slug,
        model=model,
        model_version=model_version,
        elapsed_seconds=elapsed_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=estimate_cost(model, prompt_tokens, completion_tokens, model_version),
        output_file=facts_path.name,
    )
    meta_path = output_dir / "ground-truth-meta.json"
    meta_path.write_text(json.dumps(asdict(meta), indent=2) + "\n", encoding="utf-8")
    return meta


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-fact-sheet command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_url", help="Bare YouTube ID or a full YouTube URL")
    parser.add_argument("--transcript-file", type=Path, required=True)
    parser.add_argument("--model", default="gemini-2.5-pro", help="Extractor model identifier")
    parser.add_argument("--output-dir", type=Path, default=Path("results/manual-run"))
    parser.add_argument("--slug", default=None, help="Artifact filename prefix (defaults to video ID)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected input failures into concise errors."""
    args = parse_args(argv)
    try:
        canonical_url = canonical_video_url(args.video_url)
        slug = args.slug or canonical_url.rsplit("/", 1)[-1]
        meta = run_ground_truth(
            video_url=canonical_url,
            transcript_file=args.transcript_file,
            model=args.model,
            output_dir=args.output_dir,
            slug=slug,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"wrote {meta.output_file}: {meta.elapsed_seconds:.1f}s, ${meta.cost_usd:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
