#!/usr/bin/env python3
"""Build the fact-sheet ground truth for one YouTube video (audio + slides).

One fact sheet per video, built once: the builder model (gemini-3.1-pro-preview,
falling back to gemini-2.5-pro when the native endpoint rejects video input)
ingests the video through the native generateContent endpoint and returns an
exhaustive JSON fact sheet covering speaker, channel, main topic, key claims,
frameworks, examples, terminology, takeaways, notable quotes, and statistics.
The fact sheet is the ground truth every candidate summary is scored against.

Output file: the fact-sheet JSON object plus a ``metadata`` key recording
``{builder_model, video_id, elapsed_seconds, cost_usd, tokens}``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

from summarize_video import (
    build_payload,
    estimate_cost,
    native_generate,
    native_response_text,
    native_usage,
    parse_json_response,
    write_json,
)

FACTSHEET_BUILDER = "gemini-3.1-pro-preview"
FACTSHEET_FALLBACK = "gemini-2.5-pro"

FACTS_PROMPT = (
    "Create a comprehensive fact sheet for this video: speaker, channel, main "
    "topic, all key claims with supporting details, all frameworks with "
    "components, all examples with lessons, all terminology, all takeaways, all "
    "notable quotes (verbatim, with approximate timestamps), and any statistics "
    "or numbers mentioned. Be exhaustive \u2014 this is the ground truth for "
    "scoring summaries.\n\n"
    "Output ONLY a single JSON object with exactly these keys: speaker, "
    "channel, main_topic, key_claims, frameworks, examples, terminology, "
    "takeaways, notable_quotes, statistics. No markdown, no code fences, no "
    "commentary."
)


def _build_once(model: str, api_key: str, video_url: str) -> tuple[str, int, int]:
    """Run one native fact-sheet extraction; returns (text, prompt_tokens, completion_tokens)."""
    payload = build_payload(FACTS_PROMPT, video_url)
    response = native_generate(model, api_key, payload)
    pt, ct, _ = native_usage(response)
    text = native_response_text(response)
    if not text.strip():
        raise RuntimeError(f"{model} returned an empty fact-sheet response")
    return text, pt, ct


def run_ground_truth(
    *, video_url: str, video_id: str, output: Path
) -> dict:
    """Build one fact sheet, write it, and return the fact-sheet dict."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required; set it in the environment before running."
        )
    builder = FACTSHEET_BUILDER
    started = time.perf_counter()
    try:
        text, prompt_tokens, completion_tokens = _build_once(builder, api_key, video_url)
    except (httpx.HTTPError, RuntimeError) as error:
        # Native-video rejection (or empty response): retry once on the fallback
        # builder and record which model actually built the sheet.
        print(f"note: {builder} rejected native video input ({error}); "
              f"falling back to {FACTSHEET_FALLBACK}", file=sys.stderr)
        builder = FACTSHEET_FALLBACK
        text, prompt_tokens, completion_tokens = _build_once(builder, api_key, video_url)
    elapsed_seconds = time.perf_counter() - started
    cost_usd = estimate_cost(builder, prompt_tokens, completion_tokens)

    fact_sheet = parse_json_response(text)
    fact_sheet["metadata"] = {
        "builder_model": builder,
        "video_id": video_id,
        "elapsed_seconds": round(elapsed_seconds, 4),
        "cost_usd": round(cost_usd, 6),
        "tokens": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }
    write_json(output, fact_sheet)
    return fact_sheet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-fact-sheet command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-url", required=True,
                        help="YouTube watch URL the native endpoint ingests")
    parser.add_argument("--video-id", required=True,
                        help="YouTube video ID (recorded in the fact-sheet metadata)")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the fact-sheet JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected failures into concise errors."""
    args = parse_args(argv)
    try:
        fact_sheet = run_ground_truth(
            video_url=args.video_url, video_id=args.video_id, output=args.output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    metadata = fact_sheet.get("metadata") or {}
    print(f"wrote {args.output}: builder={metadata.get('builder_model')}, "
          f"{metadata.get('elapsed_seconds'):.1f}s, "
          f"${metadata.get('cost_usd'):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
