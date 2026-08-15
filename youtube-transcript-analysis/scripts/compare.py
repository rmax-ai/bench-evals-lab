#!/usr/bin/env python3
"""Run every configured YouTube transcript-analysis comparison."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from analyze import RunMetrics, append_metrics, run_analysis, safe_model_name


EVAL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = EVAL_DIR / "config.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse comparison options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-run pairs with existing Markdown artifacts")
    return parser.parse_args(argv)


def print_table(runs: list[tuple[str, RunMetrics, Path]]) -> None:
    """Print compact measurements suitable for a terminal run log."""
    print("model | video | seconds | in_tokens | out_tokens | cost | output_bytes")
    for video_slug, run, output_path in runs:
        output_bytes = output_path.stat().st_size if output_path.exists() else 0
        print(
            f"{run.model} | {video_slug} | {run.elapsed_seconds:.1f} | "
            f"{run.prompt_tokens if run.prompt_tokens is not None else '-'} | "
            f"{run.completion_tokens if run.completion_tokens is not None else '-'} | "
            f"${run.cost_usd:.6f} | {output_bytes}"
        )


def main(argv: list[str] | None = None) -> int:
    """Run the configured video/model matrix and write combined artifacts."""
    args = parse_args(argv)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    prompt_file = EVAL_DIR / config["prompt_file"]
    all_runs: list[tuple[str, RunMetrics, Path]] = []
    failures: list[tuple[str, str, str]] = []

    for video in config["videos"]:
        output_dir = EVAL_DIR / "results" / f"{date.today().isoformat()}-{video['slug']}"
        output_dir.mkdir(parents=True, exist_ok=True)
        for model in config["models"]:
            output_path = output_dir / f"{video['slug']}-{safe_model_name(model)}.md"
            if output_path.exists() and not args.force:
                print(f"skip: {output_path.name}")
                continue
            try:
                run = run_analysis(
                    video_url=video["id"],
                    model=model,
                    prompt_file=prompt_file,
                    output_dir=output_dir,
                    slug=video["slug"],
                )
            except (OSError, RuntimeError, ValueError) as error:
                failures.append((model, video["slug"], str(error)))
                print(f"error: {model} / {video['slug']}: {error}", file=sys.stderr)
                continue
            append_metrics(output_dir, run)
            all_runs.append((video["slug"], run, output_path))

    print_table(all_runs)
    if failures:
        print(f"\n{len(failures)} failed pair(s):", file=sys.stderr)
        for model, slug, err in failures:
            print(f"  - {model} / {slug}: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
