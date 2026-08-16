#!/usr/bin/env python3
"""Run one Gemini YouTube transcript-analysis request and save its artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

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
}


@dataclass
class RunMetrics:
    """Recorded measurements for one model/video request."""

    model: str
    model_version: str | None
    elapsed_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float
    output_file: str


def canonical_video_url(video_url: str) -> str:
    """Return a canonical youtu.be URL from a bare YouTube ID or URL."""
    candidate = video_url.strip()
    if not candidate:
        raise ValueError("video_url must be a non-empty YouTube ID or URL")
    if "://" not in candidate and not candidate.startswith("www."):
        video_id = candidate
    else:
        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        host = parsed.netloc.lower().removeprefix("www.")
        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/")[0]
        elif host.endswith("youtube.com"):
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
                video_id = parsed.path.strip("/").split("/")[1]
            else:
                video_id = ""
        else:
            raise ValueError("video_url must be a YouTube URL or a bare video ID")
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id):
        raise ValueError(f"invalid YouTube video ID: {video_id!r}")
    return f"https://youtu.be/{video_id}"


def safe_model_name(model: str) -> str:
    """Convert a model identifier into a portable artifact filename component."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-.")


def estimate_cost(model: str, prompt_tokens: int | None,
                  completion_tokens: int | None,
                  model_version: str | None = None) -> float:
    """Estimate request cost; fall back to the resolved model_version for aliases."""
    prices = PRICING_PER_MILLION.get(model)
    if prices is None and model_version and model_version in PRICING_PER_MILLION:
        prices = PRICING_PER_MILLION[model_version]
        print(f"note: priced alias {model} at {model_version} rates", file=sys.stderr)
    if prices is None:
        print(f"warning: no price configured for {model}; reporting cost as $0", file=sys.stderr)
        return 0.0
    return ((prompt_tokens or 0) * prices[0] + (completion_tokens or 0) * prices[1]) / 1_000_000


def _response_text(response: Any) -> str:
    """Extract text while tolerating responses with no text part."""
    text = getattr(response, "text", None)
    return text if isinstance(text, str) else ""


def _usage_value(response: Any, attribute: str) -> int | None:
    """Read one optional usage count from a GenerateContent response."""
    usage = getattr(response, "usage_metadata", None)
    value = getattr(usage, attribute, None)
    return value if isinstance(value, int) else None


def run_analysis(
    *,
    video_url: str,
    model: str,
    prompt_file: Path,
    output_dir: Path,
    slug: str,
) -> RunMetrics:
    """Generate one analysis, write its Markdown artifact, and return its metrics."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required; set it in the environment before running.")
    from google import genai

    prompt = prompt_file.read_text(encoding="utf-8")
    canonical_url = canonical_video_url(video_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}-{safe_model_name(model)}.md"

    client = genai.Client(api_key=api_key)
    video_part = genai.types.Part.from_uri(file_uri=canonical_url, mime_type="video/mp4")
    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=[video_part, prompt],
    )
    elapsed_seconds = time.perf_counter() - started
    output_path.write_text(_response_text(response), encoding="utf-8")

    prompt_tokens = _usage_value(response, "prompt_token_count")
    completion_tokens = _usage_value(response, "candidates_token_count")
    return RunMetrics(
        model=model,
        model_version=getattr(response, "model_version", None),
        elapsed_seconds=elapsed_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=estimate_cost(model, prompt_tokens, completion_tokens,
                               getattr(response, "model_version", None)),
        output_file=output_path.name,
    )


def append_metrics(output_dir: Path, run: RunMetrics) -> Path:
    """Append a run object to the output directory's combined metrics file."""
    metrics_path = output_dir / "metrics.json"
    if metrics_path.exists():
        existing = json.loads(metrics_path.read_text(encoding="utf-8"))
        document = existing if isinstance(existing, dict) else {"runs": []}
    else:
        document = {"runs": []}
    runs = document.setdefault("runs", [])
    if not isinstance(runs, list):
        raise ValueError(f"{metrics_path} has a non-list 'runs' field")
    runs.append(asdict(run))
    metrics_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return metrics_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the single-run command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_url", help="Bare YouTube ID or a full YouTube URL")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model identifier")
    parser.add_argument("--prompt-file", type=Path, default=Path("prompt.md"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/manual-run"))
    parser.add_argument("--slug", default=None, help="Artifact filename prefix (defaults to video ID)")
    parser.add_argument("--json", action="store_true", help="Print metrics JSON after writing artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and convert expected input failures into concise errors."""
    args = parse_args(argv)
    try:
        canonical_url = canonical_video_url(args.video_url)
        slug = args.slug or canonical_url.rsplit("/", 1)[-1]
        run = run_analysis(
            video_url=canonical_url,
            model=args.model,
            prompt_file=args.prompt_file,
            output_dir=args.output_dir,
            slug=slug,
        )
        append_metrics(args.output_dir, run)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(asdict(run), indent=2))
    else:
        print(f"wrote {run.output_file}: {run.elapsed_seconds:.1f}s, ${run.cost_usd:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
