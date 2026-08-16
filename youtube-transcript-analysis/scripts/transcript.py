#!/usr/bin/env python3
"""Fetch a verbatim transcript for one YouTube video via the Gemini API.

The transcript is the ground-truth document the judge scores analyses
against. Fetching it through the same API the analyzed models ingest the
video with keeps the judge's reference aligned with what those models saw.
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

TRANSCRIPT_PROMPT = (
    "Transcribe this video verbatim. Output the full transcript as markdown.\n"
    "Include speaker labels and [MM:SS] timestamps where available.\n"
    "Do not summarize, clean up, or omit any content.\n"
    "Mark inaudible or uncertain parts as [inaudible].\n"
    "Output only the transcript."
)


@dataclass
class TranscriptMeta:
    """Recorded measurements for one transcript fetch."""

    video_slug: str
    model: str
    model_version: str | None
    elapsed_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float
    output_file: str


def run_transcript(
    *,
    video_url: str,
    model: str,
    output_dir: Path,
    slug: str,
) -> TranscriptMeta:
    """Fetch one verbatim transcript, write transcript.md, return its metrics."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
    from google import genai

    canonical_url = canonical_video_url(video_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = output_dir / "transcript.md"

    client = genai.Client(api_key=api_key)
    video_part = genai.types.Part.from_uri(file_uri=canonical_url, mime_type="video/mp4")
    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=[video_part, TRANSCRIPT_PROMPT],
    )
    elapsed_seconds = time.perf_counter() - started
    text = getattr(response, "text", None) or ""
    transcript_path.write_text(text, encoding="utf-8")

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", None)
    completion_tokens = getattr(usage, "candidates_token_count", None)
    model_version = getattr(response, "model_version", None)
    meta = TranscriptMeta(
        video_slug=slug,
        model=model,
        model_version=model_version,
        elapsed_seconds=elapsed_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=estimate_cost(model, prompt_tokens, completion_tokens, model_version),
        output_file=transcript_path.name,
    )
    meta_path = output_dir / "transcript-meta.json"
    meta_path.write_text(json.dumps(asdict(meta), indent=2) + "\n", encoding="utf-8")
    return meta


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-transcript command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_url", help="Bare YouTube ID or a full YouTube URL")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Transcriber model identifier")
    parser.add_argument("--output-dir", type=Path, default=Path("results/manual-run"))
    parser.add_argument("--slug", default=None, help="Artifact filename prefix (defaults to video ID)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected input failures into concise errors."""
    args = parse_args(argv)
    try:
        canonical_url = canonical_video_url(args.video_url)
        slug = args.slug or canonical_url.rsplit("/", 1)[-1]
        meta = run_transcript(
            video_url=canonical_url,
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
