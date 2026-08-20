#!/usr/bin/env python3
"""Run the full video-summarization matrix end to end.

Matrix: each corpus video (5) gets one fact-sheet ground truth (built once),
then each video x candidate (4) is summarized via the native generateContent
endpoint, then both judges (gemini-3.1-pro-preview, deepseek-v4-pro) score
every candidate summary against the fact sheet. Fail-continue: a single
candidate or judge failure is recorded in metrics.json, never aborts the run.

Outputs land in results/2026-08-20-video-summarization/:
- <video_id>.fact-sheet.json                  (ground_truth.py result)
- <video_id>.<candidate>.json                 (summarize_video.py result)
- <video_id>.<candidate>.<judge>.judge.json   (judge.py verdict)
- metrics.json                                (aggregates)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ground_truth import run_ground_truth
from judge import run_judgment
from summarize_video import run_summarize

CANDIDATES = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
]
JUDGES = ["gemini-3.1-pro-preview", "deepseek-v4-pro"]
DIMS = ["structure", "faithfulness", "coverage", "precision", "compression"]
RESULTS_DIR = Path("results") / "2026-08-20-video-summarization"

EVAL_DIR = Path(__file__).resolve().parent.parent


def _load_corpus() -> list[dict[str, Any]]:
    """Load the corpus manifest items (each with video_id, title, url)."""
    manifest = EVAL_DIR / "corpus" / "manifest.json"
    document = json.loads(manifest.read_text(encoding="utf-8"))
    items = document.get("items") or []
    return [
        item for item in items
        if isinstance(item, dict) and item.get("video_id")
    ]


CORPUS_ITEMS = _load_corpus()


def init_stats() -> dict[str, Any]:
    """Initialize the accumulator structure for metrics aggregation."""
    stats: dict[str, Any] = {
        "fact_sheets": {
            item["video_id"]: {
                "built": False,
                "builder_model": None,
                "elapsed_seconds": 0.0,
                "cost_usd": 0.0,
                "errors": [],
            }
            for item in CORPUS_ITEMS
        },
        "candidates": {
            candidate: {
                "elapsed": [],
                "cost_usd": 0.0,
                "validation_failures": 0,
                "retries": 0,
                "errors": [],
            }
            for candidate in CANDIDATES
        },
        "judges": {
            candidate: {
                judge_model: {
                    "scores": {dim: [] for dim in DIMS},
                    "accuracy": [],
                    "totals": [],
                    "hallucination_counts": [],
                    "elapsed_seconds": 0.0,
                    "cost_usd": 0.0,
                    "errors": [],
                }
                for judge_model in JUDGES
            }
            for candidate in CANDIDATES
        },
    }
    return stats


def record_candidate_result(stats: dict[str, Any], candidate: str,
                            result: dict) -> None:
    """Accumulate candidate-level metrics from one summarize_video result."""
    entry = stats["candidates"][candidate]
    if result.get("error") or result.get("validation_passed") is False:
        entry["validation_failures"] += 1
        if result.get("error"):
            entry["errors"].append(result["error"])
    entry["retries"] += int(result.get("retries") or 0)
    entry["cost_usd"] += float(result.get("cost_usd") or 0.0)
    entry["elapsed"].append(float(result.get("elapsed_seconds") or 0.0))


def record_judge_result(stats: dict[str, Any], candidate: str,
                        judge_model: str, verdict: dict) -> None:
    """Accumulate per-judge metrics from one judge.py verdict."""
    entry = stats["judges"][candidate][judge_model]
    if verdict.get("error"):
        entry["errors"].append(verdict["error"])
        return
    for dim in DIMS:
        entry["scores"][dim].append(int(verdict["scores"][dim]))
    entry["accuracy"].append(
        (int(verdict["scores"]["faithfulness"]) + int(verdict["scores"]["precision"])) / 2.0
    )
    entry["totals"].append(float(verdict["total"]))
    entry["hallucination_counts"].append(len(verdict.get("hallucinations") or []))
    entry["elapsed_seconds"] += float(verdict.get("elapsed_seconds") or 0.0)
    entry["cost_usd"] += float(verdict.get("cost_usd") or 0.0)


def avg(values: list[float]) -> float | None:
    """Arithmetic mean, or None for an empty list."""
    return round(sum(values) / len(values), 2) if values else None


def build_metrics(stats: dict[str, Any]) -> dict[str, Any]:
    """Aggregate per-candidate, fact-sheet, summary, and total metrics."""
    metrics: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results_dir": str(RESULTS_DIR),
        "fact_sheets": {},
        "candidates": {},
    }
    for video_id, facts in stats["fact_sheets"].items():
        metrics["fact_sheets"][video_id] = {
            "built": facts["built"],
            "builder_model": facts["builder_model"],
            "elapsed_seconds": round(facts["elapsed_seconds"], 4),
            "cost_usd": round(facts["cost_usd"], 6),
            "errors": facts["errors"],
        }

    for candidate in CANDIDATES:
        cand = stats["candidates"][candidate]
        measured = len(cand["elapsed"])
        entry: dict[str, Any] = {
            "latency": {
                "avg": avg(cand["elapsed"]),
                "min": round(min(cand["elapsed"]), 4) if measured else None,
                "max": round(max(cand["elapsed"]), 4) if measured else None,
            },
            "cost_usd": {
                "total": round(cand["cost_usd"], 6),
                "avg": round(cand["cost_usd"] / measured, 6) if measured else None,
            },
            "judges": {},
            "validation_failures": cand["validation_failures"],
            "retries": cand["retries"],
            "errors": cand["errors"],
        }
        for judge_model in JUDGES:
            jstats = stats["judges"][candidate][judge_model]
            dims = {dim: avg(jstats["scores"][dim]) for dim in DIMS}
            entry["judges"][judge_model] = {
                **dims,
                "total": avg(jstats["totals"]),
                "accuracy": avg(jstats["accuracy"]),
                "hallucination_total": sum(jstats["hallucination_counts"]),
                "judged": len(jstats["totals"]),
                "elapsed_seconds": round(jstats["elapsed_seconds"], 4),
                "cost_usd": round(jstats["cost_usd"], 6),
                "errors": jstats["errors"],
            }
        metrics["candidates"][candidate] = entry

    ranked = []
    for candidate in CANDIDATES:
        entry = metrics["candidates"][candidate]
        totals = [
            verdict["total"] for verdict in entry["judges"].values()
            if verdict["total"] is not None
        ]
        quality = avg(totals) if totals else None
        cost_per_video = entry["cost_usd"]["avg"]
        quality_per_cost = (
            round(quality / cost_per_video, 4)
            if quality is not None and cost_per_video
            else None
        )
        ranked.append({
            "candidate": candidate,
            "quality": quality,
            "cost_per_video": cost_per_video,
            "quality_per_cost": quality_per_cost,
        })
    ranked.sort(
        key=lambda item: (item["quality_per_cost"] if item["quality_per_cost"] is not None else -1.0),
        reverse=True,
    )
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank
    metrics["summary"] = {
        "method": "rank by quality/cost (quality = mean judge total, cost = cost per video)",
        "rank": ranked,
    }

    metrics["totals"] = {
        "cost_usd": round(
            sum(c["cost_usd"] for c in stats["candidates"].values()), 6),
        "elapsed_seconds": round(
            sum(sum(c["elapsed"]) for c in stats["candidates"].values())
            + sum(j["elapsed_seconds"]
                  for c in stats["judges"].values()
                  for j in c.values())
            + sum(f["elapsed_seconds"] for f in stats["fact_sheets"].values()),
            4,
        ),
        "retries": sum(c["retries"] for c in stats["candidates"].values()),
        "validation_failures": sum(
            c["validation_failures"] for c in stats["candidates"].values()),
    }
    return metrics


def print_summary(metrics: dict[str, Any]) -> None:
    """Print a compact per-candidate summary table."""
    header = (
        f"{'candidate':<20} {'g31p total':>10} {'g31p acc':>9} {'dsv4 total':>10} "
        f"{'dsv4 acc':>9} {'hall':>5} {'cost_usd':>9} {'lat_s':>7} "
        f"{'retr':>5} {'fail':>5}"
    )
    print(header)
    print("-" * len(header))
    for candidate, entry in metrics["candidates"].items():
        def fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "-"
        g31p = entry["judges"]["gemini-3.1-pro-preview"]
        dsv4 = entry["judges"]["deepseek-v4-pro"]
        hall_total = (
            g31p["hallucination_total"] if g31p["hallucination_total"] else 0
        ) + (dsv4["hallucination_total"] if dsv4["hallucination_total"] else 0)
        print(
            f"{candidate:<20} {fmt(g31p['total']):>10} {fmt(g31p['accuracy']):>9} "
            f"{fmt(dsv4['total']):>10} {fmt(dsv4['accuracy']):>9} {hall_total:>5} "
            f"{entry['cost_usd']['total']:>9.4f} "
            f"{fmt(entry['latency']['avg']):>7} "
            f"{entry['retries']:>5} {entry['validation_failures']:>5}"
        )
    totals = metrics["totals"]
    print(f"\ntotals: cost_usd={totals['cost_usd']:.4f}, "
          f"elapsed_s={totals['elapsed_seconds']:.1f}, "
          f"retries={totals['retries']}, "
          f"validation_failures={totals['validation_failures']}")
    print("\nrank by quality/cost (cost per video):")
    for item in metrics["summary"]["rank"]:
        qpc = f"{item['quality_per_cost']:.4f}" if item["quality_per_cost"] is not None else "-"
        print(f"  {item['rank']}. {item['candidate']:<20} "
              f"quality={item['quality']}, "
              f"cost/video=${item['cost_per_video']:.4f}, "
              f"q/cost={qpc}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the matrix CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge-only", action="store_true",
                        help="Re-judge existing candidate outputs without re-running summarization")
    parser.add_argument("--force", action="store_true",
                        help="Re-run stages that already have artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the full matrix (or judge-only pass) and write metrics.json."""
    args = parse_args(argv)
    eval_dir = Path(__file__).resolve().parent.parent
    results_dir = RESULTS_DIR if RESULTS_DIR.is_absolute() else eval_dir / RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    if not CORPUS_ITEMS:
        print("error: no corpus videos found in manifest.json", file=sys.stderr)
        return 2

    stats = init_stats()
    for item in CORPUS_ITEMS:
        video_id = item["video_id"]
        fact_path = results_dir / f"{video_id}.fact-sheet.json"
        fact_ok = fact_path.exists()
        if fact_ok:
            # Record the committed fact-sheet metadata (builder model, cost,
            # elapsed) whenever the artifact already exists, so judge-only
            # passes keep the fact_sheets section and totals accurate.
            try:
                facts = json.loads(fact_path.read_text(encoding="utf-8"))
                metadata = facts.get("metadata") or {}
                stats["fact_sheets"][video_id]["built"] = True
                stats["fact_sheets"][video_id]["builder_model"] = metadata.get("builder_model")
                stats["fact_sheets"][video_id]["elapsed_seconds"] = float(metadata.get("elapsed_seconds") or 0.0)
                stats["fact_sheets"][video_id]["cost_usd"] = float(metadata.get("cost_usd") or 0.0)
            except (OSError, json.JSONDecodeError):
                pass
        if not args.judge_only and not fact_ok:
            print(f"fact-sheet {video_id} ...", flush=True)
            try:
                facts = run_ground_truth(
                    video_url=item["url"], video_id=video_id, output=fact_path)
                metadata = facts.get("metadata") or {}
                stats["fact_sheets"][video_id]["built"] = True
                stats["fact_sheets"][video_id]["builder_model"] = metadata.get("builder_model")
                stats["fact_sheets"][video_id]["elapsed_seconds"] = float(metadata.get("elapsed_seconds") or 0.0)
                stats["fact_sheets"][video_id]["cost_usd"] = float(metadata.get("cost_usd") or 0.0)
                fact_ok = True
            except Exception as error:  # fail-continue
                error_note = f"{type(error).__name__}: {error}"
                stats["fact_sheets"][video_id]["errors"].append(error_note)
                print(f"error: fact-sheet {video_id}: {error_note}", file=sys.stderr)

        for candidate in CANDIDATES:
            candidate_path = results_dir / f"{video_id}.{candidate}.json"
            result: dict | None = None
            if args.judge_only:
                if not candidate_path.exists():
                    error_note = f"missing candidate output {candidate_path.name}"
                    stats["candidates"][candidate]["errors"].append(f"{video_id}: {error_note}")
                    print(f"error: {video_id} {candidate}: {error_note}", file=sys.stderr)
                    continue
                with open(candidate_path, encoding="utf-8") as handle:
                    result = json.load(handle)
            elif candidate_path.exists() and not args.force:
                with open(candidate_path, encoding="utf-8") as handle:
                    previous = json.load(handle)
                if isinstance(previous.get("data"), dict):
                    result = previous
            if result is None:
                print(f"summarizing {video_id} x {candidate} ...", flush=True)
                try:
                    result = run_summarize(
                        candidate=candidate, video_url=item["url"],
                        video_id=video_id, output=candidate_path)
                except Exception as error:  # fail-continue
                    error_note = f"{type(error).__name__}: {error}"
                    stats["candidates"][candidate]["errors"].append(f"{video_id}: {error_note}")
                    print(f"error: {video_id} {candidate}: {error_note}", file=sys.stderr)
                    continue
            record_candidate_result(stats, candidate, result)
            if result.get("data") is None:
                continue

            for judge_model in JUDGES:
                judge_path = results_dir / f"{video_id}.{candidate}.{judge_model}.judge.json"
                verdict: dict | None = None
                if judge_path.exists() and not args.force:
                    with open(judge_path, encoding="utf-8") as handle:
                        previous = json.load(handle)
                    if "error" not in previous:
                        verdict = previous
                if verdict is None:
                    if not fact_ok:
                        error_note = f"missing fact-sheet {fact_path.name}"
                        stats["judges"][candidate][judge_model]["errors"].append(f"{video_id}: {error_note}")
                        print(f"error: {video_id} {candidate} {judge_model}: {error_note}", file=sys.stderr)
                        continue
                    print(f"judging {video_id} x {candidate} x {judge_model} ...", flush=True)
                    try:
                        verdict = run_judgment(
                            judge_model=judge_model, fact_sheet_file=fact_path,
                            candidate_json_file=candidate_path, output_file=judge_path)
                    except Exception as error:  # fail-continue
                        error_note = f"{type(error).__name__}: {error}"
                        stats["judges"][candidate][judge_model]["errors"].append(f"{video_id}: {error_note}")
                        print(f"error: {video_id} {candidate} {judge_model}: {error_note}", file=sys.stderr)
                        continue
                record_judge_result(stats, candidate, judge_model, verdict)

    metrics = build_metrics(stats)
    metrics_path = results_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {metrics_path}")
    print_summary(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
