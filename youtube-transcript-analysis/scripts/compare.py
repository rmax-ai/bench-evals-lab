#!/usr/bin/env python3
"""Run every configured YouTube transcript-analysis comparison.

Pipeline per video: fetch a verbatim transcript once (audio reference),
extract a text fact sheet once (ground truth for text-only judges), run each
configured model's analysis, then judge every analysis with each configured
judge. Existing artifacts are skipped unless --force is given, so the matrix
is resumable and re-runs only charge for missing work.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from analyze import RunMetrics, append_metrics, run_analysis, safe_model_name
from ground_truth import GroundTruthMeta, run_ground_truth
from judge import Judgment, run_judgment, safe_model_name as judge_file_safe
from transcript import TranscriptMeta, run_transcript

EVAL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = EVAL_DIR / "config.json"

HEADER = "model | served_as | seconds | in_tok | out_tok | cost"
TABLE_SEP = " | "


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse comparison options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-run pairs with existing artifacts")
    parser.add_argument("--judge-only", action="store_true",
                        help="Skip analysis runs; judge existing artifacts only")
    parser.add_argument("--only-judge", default=None,
                        help="Run only the judge whose model name matches (substring)")
    return parser.parse_args(argv)


def _config_model(config: dict, section: str, default: str) -> str:
    """Read an optional config model with a default fallback."""
    value = config.get(section, {}).get("model", default)
    if not isinstance(value, str) or not value:
        return default
    return value


def _config_judges(config: dict) -> list[tuple[str, str]]:
    """Read judge config into (provider, model) pairs.

    Accepts both the new `judges` array and the legacy `judge.model` string.
    """
    judges = config.get("judges")
    if isinstance(judges, list) and judges:
        pairs = []
        for entry in judges:
            provider = entry.get("provider", "gemini")
            model = entry.get("model")
            if isinstance(provider, str) and isinstance(model, str) and model:
                pairs.append((provider, model))
        if pairs:
            return pairs
    model = _config_model(config, "judge", "gemini-2.5-pro")
    return [("gemini", model)]


def print_table(runs: list[tuple[str, RunMetrics, Path, dict[str, Judgment | None]]]) -> None:
    """Print compact measurements suitable for a terminal run log."""
    judge_columns = sorted({name for _, _, _, judges in runs for name in judges})
    print(HEADER + " | " + " | ".join(f"judge:{name}" for name in judge_columns))
    for video_slug, run, output_path, judgments in runs:
        row = [
            run.model,
            run.model_version or "-",
            f"{run.elapsed_seconds:.1f}",
            str(run.prompt_tokens if run.prompt_tokens is not None else "-"),
            str(run.completion_tokens if run.completion_tokens is not None else "-"),
            f"${run.cost_usd:.6f}",
        ]
        for name in judge_columns:
            judgment = judgments.get(name)
            row.append(f"{judgment.total:.2f}/5" if judgment else "-")
        print(TABLE_SEP.join(row))


def main(argv: list[str] | None = None) -> int:
    """Run the configured video/model matrix and write combined artifacts."""
    args = parse_args(argv)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    prompt_file = EVAL_DIR / config["prompt_file"]
    transcript_model = _config_model(config, "transcript", "gemini-2.5-flash")
    ground_truth_model = _config_model(config, "ground_truth", "gemini-2.5-pro")
    judges = _config_judges(config)
    if args.only_judge:
        judges = [(p, m) for p, m in judges if args.only_judge in m]
        if not judges:
            print(f"error: no configured judge matches {args.only_judge!r}", file=sys.stderr)
            return 2
    all_runs: list[tuple[str, RunMetrics, Path, dict[str, Judgment | None]]] = []
    failures: list[tuple[str, str, str]] = []

    for video in config["videos"]:
        output_dir = EVAL_DIR / "results" / f"{date.today().isoformat()}-{video['slug']}"
        output_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = output_dir / "transcript.md"
        facts_path = output_dir / "ground-truth.md"

        if transcript_path.exists() and (not args.force or args.judge_only):
            print(f"skip: {transcript_path.name}")
        else:
            try:
                meta: TranscriptMeta = run_transcript(
                    video_url=video["id"],
                    model=transcript_model,
                    output_dir=output_dir,
                    slug=video["slug"],
                )
                print(f"transcript: {meta.elapsed_seconds:.1f}s, ${meta.cost_usd:.6f}")
            except (OSError, RuntimeError, ValueError) as error:
                failures.append(("transcript", video["slug"], str(error)))
                print(f"error: transcript / {video['slug']}: {error}", file=sys.stderr)
                continue

        needs_facts = any(provider == "deepseek" for provider, _ in judges)
        if needs_facts and transcript_path.exists():
            if facts_path.exists() and (not args.force or args.judge_only):
                print(f"skip: {facts_path.name}")
            else:
                try:
                    facts_meta: GroundTruthMeta = run_ground_truth(
                        video_url=video["id"],
                        transcript_file=transcript_path,
                        model=ground_truth_model,
                        output_dir=output_dir,
                        slug=video["slug"],
                    )
                    print(f"ground-truth: {facts_meta.elapsed_seconds:.1f}s, ${facts_meta.cost_usd:.6f}")
                except (OSError, RuntimeError, ValueError) as error:
                    failures.append(("ground-truth", video["slug"], str(error)))
                    print(f"error: ground-truth / {video['slug']}: {error}", file=sys.stderr)

        for model in config["models"]:
            output_path = output_dir / f"{video['slug']}-{safe_model_name(model)}.md"
            run: RunMetrics | None = None
            if output_path.exists() and not args.force and not args.judge_only:
                print(f"skip: {output_path.name}")
            elif not args.judge_only:
                try:
                    run = run_analysis(
                        video_url=video["id"],
                        model=model,
                        prompt_file=prompt_file,
                        output_dir=output_dir,
                        slug=video["slug"],
                    )
                    append_metrics(output_dir, run)
                except (OSError, RuntimeError, ValueError) as error:
                    failures.append((model, video["slug"], str(error)))
                    print(f"error: {model} / {video['slug']}: {error}", file=sys.stderr)
                    continue

            if not output_path.exists():
                failures.append((model, video["slug"], "missing analysis artifact"))
                print(f"error: {model} / {video['slug']}: no analysis artifact", file=sys.stderr)
                continue

            if run is None:
                run = _read_metrics(output_dir, model) or RunMetrics(
                    model=model, model_version=None, elapsed_seconds=0.0,
                    prompt_tokens=None, completion_tokens=None, cost_usd=0.0,
                    output_file=output_path.name,
                )

            judgments: dict[str, Judgment | None] = {}
            for provider, judge_model in judges:
                judge_name = judge_file_safe(judge_model)
                judgment_path = output_dir / f"{output_path.stem}.{judge_name}.judge.json"
                judgment: Judgment | None = None
                if judgment_path.exists() and not args.force:
                    try:
                        document = json.loads(judgment_path.read_text(encoding="utf-8"))
                        document.setdefault("provider", provider)
                        judgment = Judgment(**document)
                    except (TypeError, json.JSONDecodeError):
                        pass
                if judgment is None:
                    try:
                        judgment = run_judgment(
                            transcript_file=transcript_path,
                            analysis_file=output_path,
                            judge_model=judge_model,
                            output_dir=output_dir,
                            judged_model=model,
                            provider=provider,
                            video_url=video["id"] if provider == "gemini" else None,
                            ground_truth_file=facts_path if provider == "deepseek" else None,
                        )
                    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, KeyError) as error:
                        failures.append((f"judge:{judge_name}/{model}", video["slug"], str(error)))
                        print(f"error: judge:{judge_name} / {model}: {error}", file=sys.stderr)
                judgments[judge_name] = judgment
            all_runs.append((video["slug"], run, output_path, judgments))

    print_table(all_runs)
    if failures:
        print(f"\n{len(failures)} failed pair(s):", file=sys.stderr)
        for model, slug, err in failures:
            print(f"  - {model} / {slug}: {err}", file=sys.stderr)
        return 2
    return 0


def _read_metrics(output_dir: Path, model: str) -> RunMetrics | None:
    """Read a previously recorded run for `model` from metrics.json, if present."""
    metrics_path = output_dir / "metrics.json"
    if not metrics_path.exists():
        return None
    document = json.loads(metrics_path.read_text(encoding="utf-8"))
    fields = set(RunMetrics.__dataclass_fields__)
    for item in document.get("runs", []):
        if item.get("model") == model:
            return RunMetrics(**{k: v for k, v in item.items() if k in fields})
    return None


if __name__ == "__main__":
    raise SystemExit(main())
