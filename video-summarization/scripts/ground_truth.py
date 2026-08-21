#!/usr/bin/env python3
"""Build the fact-sheet ground truth for one YouTube video (audio + slides).

Two fact sheets are built per video, one per extractor: the primary builder
(gemini-3.1-pro-preview) and the secondary builder (gemini-2.5-pro), both
ingesting the video through the native generateContent endpoint and returning
an exhaustive JSON fact sheet covering speaker, channel, main topic, key
claims, frameworks, examples, terminology, takeaways, notable quotes, and
statistics. The two sheets are merged into a single ground-truth file that
every candidate summary is scored against.

Merge semantics: union of all sections. Claims/quotes appearing in only one
extractor are kept (both extractors are independent evidence the video
contains them); duplicates are collapsed. If either extractor fails entirely,
the other's fact sheet stands alone and the metadata records which model
failed.

Output file: the merged fact-sheet JSON object plus a ``metadata`` key
recording ``{video_id, builder_model, builder_models, builders, elapsed_seconds,
cost_usd}`` where ``builders`` holds per-model status (ok/failed), elapsed,
cost, and tokens.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

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
FACTSHEET_MODELS = [FACTSHEET_BUILDER, FACTSHEET_FALLBACK]

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


def _extract_sheet(model: str, api_key: str, video_url: str) -> tuple[dict, dict]:
    """Run one extractor; returns (fact_sheet, builder_metadata).

    Any failure (transport, empty, unparseable) is raised as RuntimeError so
    the caller can record it as a failed builder and keep the other one.
    """
    started = time.perf_counter()
    try:
        text, prompt_tokens, completion_tokens = _build_once(model, api_key, video_url)
        sheet = parse_json_response(text)
    except (httpx.HTTPError, RuntimeError, json.JSONDecodeError,
            ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"{type(error).__name__}: {error}") from error
    sheet.pop("metadata", None)
    builder_metadata = {
        "status": "ok",
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "cost_usd": round(
            estimate_cost(model, prompt_tokens, completion_tokens), 6),
        "tokens": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }
    return sheet, builder_metadata


# Identity keys used to collapse duplicate entries when merging sections.
_IDENTITY_KEYS = {
    "key_claims": "claim",
    "frameworks": "name",
    "examples": "example",
    "terminology": "term",
    "notable_quotes": "quote",
}


def _norm_text(value: Any) -> str:
    """Whitespace-normalized lowercase string used for duplicate detection."""
    return " ".join(str(value).lower().split())


def _merge_lists(primary: Any, secondary: Any, identity_key: str | None) -> list:
    """Union two fact-sheet list sections, collapsing near-duplicate entries."""
    primary = primary if isinstance(primary, list) else []
    secondary = secondary if isinstance(secondary, list) else []
    seen: set[str] = set()
    merged: list = []
    for item in [*primary, *secondary]:
        if isinstance(item, dict) and identity_key:
            identity = _norm_text(item.get(identity_key) or "")
        else:
            identity = ""
        if not identity:
            identity = _norm_text(json.dumps(item, ensure_ascii=False, sort_keys=True))
        if not identity:
            merged.append(item)
            continue
        if identity not in seen:
            seen.add(identity)
            merged.append(item)
    return merged


def _merge_sections(primary: dict, secondary: dict) -> dict:
    """Merge two fact-sheet objects: union of sections, primary preferred."""
    merged: dict = {}
    keys = list(primary.keys())
    for key in secondary:
        if key not in merged:
            keys.append(key)
    for key in keys:
        if key == "metadata":
            continue
        primary_value = primary.get(key)
        secondary_value = secondary.get(key)
        if isinstance(primary_value, list) or isinstance(secondary_value, list):
            merged[key] = _merge_lists(
                primary_value, secondary_value, _IDENTITY_KEYS.get(key))
        elif isinstance(primary_value, dict) and isinstance(secondary_value, dict):
            merged[key] = _merge_sections(primary_value, secondary_value)
        elif primary_value not in (None, ""):
            merged[key] = primary_value
        else:
            merged[key] = secondary_value
    return merged


def merge_fact_sheets(sheets: dict[str, dict]) -> dict:
    """Merge per-builder fact sheets into one ground truth (union of sections)."""
    ordered = [model for model in FACTSHEET_MODELS if model in sheets]
    if not ordered:
        raise RuntimeError("no fact-sheet extractor produced a sheet")
    merged = copy.deepcopy(sheets[ordered[0]])
    for model in ordered[1:]:
        merged = _merge_sections(merged, sheets[model])
    return merged


def run_ground_truth(
    *, video_url: str, video_id: str, output: Path
) -> dict:
    """Build both fact sheets, merge them, write them, and return the result."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required; set it in the environment before running."
        )
    started = time.perf_counter()
    sheets: dict[str, dict] = {}
    builders: dict[str, dict] = {}
    for model in FACTSHEET_MODELS:
        try:
            sheet, builder_metadata = _extract_sheet(model, api_key, video_url)
        except RuntimeError as error:
            builders[model] = {"status": "failed", "error": str(error)}
            print(f"note: {model} fact-sheet extraction failed ({error})",
                  file=sys.stderr)
            continue
        sheets[model] = sheet
        builders[model] = builder_metadata
    if not sheets:
        raise RuntimeError(
            "both fact-sheet extractors failed; no ground truth built")

    fact_sheet = merge_fact_sheets(sheets)
    fact_sheet["metadata"] = {
        "video_id": video_id,
        "builder_model": FACTSHEET_BUILDER if FACTSHEET_BUILDER in sheets
        else FACTSHEET_FALLBACK,
        "builder_models": [model for model in FACTSHEET_MODELS if model in sheets],
        "builders": builders,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "cost_usd": round(sum(
            meta.get("cost_usd", 0.0) for meta in builders.values()
            if meta.get("status") == "ok"
        ), 6),
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
    print(f"wrote {args.output}: builders={metadata.get('builder_models')}, "
          f"{metadata.get('elapsed_seconds'):.1f}s, "
          f"${metadata.get('cost_usd'):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
