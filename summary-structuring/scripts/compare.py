#!/usr/bin/env python3
"""Run the full summary-structuring matrix end to end.

Matrix: each corpus/*.md (5 files) x each candidate (parser, deepseek-v4-pro,
deepseek-v4-flash, gemini-3.5-flash-lite, gemini-2.5-flash), then both judges
(gemini-2.5-pro, deepseek-v4-pro) against every candidate result.
Fail-continue: a single candidate or judge failure is recorded in metrics.json,
never aborts the run.

Outputs land in results/2026-08-20-summary-structuring/:
- <video_id>.<candidate>.json                      (structure.py result)
- <video_id>.<candidate>.<judge>.judge.json        (judge.py verdict)
- metrics.json                                     (aggregates)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import judge
import structure

CANDIDATES = ["parser", "deepseek-v4-pro", "deepseek-v4-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
JUDGES = ["gemini-2.5-pro", "deepseek-v4-pro"]
DIMS = ["structure", "faithfulness", "coverage", "precision", "compression"]
RESULTS_DIR = Path("results") / "2026-08-20-summary-structuring"


def whitespace_normalize(text: str) -> str:
    """Collapse all whitespace runs into single spaces."""
    return " ".join(text.split())


def quote_contained(quote_text: str, markdown_norm: str) -> bool:
    """True if the quote text is a whitespace-normalized substring of the markdown."""
    return bool(quote_text) and whitespace_normalize(quote_text) in markdown_norm


def init_stats() -> dict[str, Any]:
    stats: dict[str, Any] = {
        "candidates": {
            c: {
                "structure_failures": 0,
                "retries": 0,
                "cost_usd": 0.0,
                "elapsed_seconds": 0.0,
                "quote_hits": 0,
                "quote_total": 0,
                "errors": [],
            }
            for c in CANDIDATES
        },
        "judges": {
            c: {
                j: {
                    "scores": {dim: [] for dim in DIMS},
                    "totals": [],
                    "hallucination_counts": [],
                    "elapsed_seconds": 0.0,
                    "cost_usd": 0.0,
                    "errors": [],
                }
                for j in JUDGES
            }
            for c in CANDIDATES
        },
    }
    return stats


def record_candidate_result(stats: dict[str, Any], candidate: str,
                            result: dict, markdown_norm: str) -> None:
    """Accumulate candidate-level metrics from one structure.py result."""
    entry = stats["candidates"][candidate]
    if result.get("error") or result.get("validation_passed") is False:
        entry["structure_failures"] += 1
        if result.get("error"):
            entry["errors"].append(result["error"])
    entry["retries"] += int(result.get("retries") or 0)
    entry["cost_usd"] += float(result.get("cost_usd") or 0.0)
    entry["elapsed_seconds"] += float(result.get("elapsed_seconds") or 0.0)
    data = result.get("data")
    if isinstance(data, dict):
        for quote in data.get("quotes") or []:
            text = quote.get("text", "") if isinstance(quote, dict) else ""
            entry["quote_total"] += 1
            if quote_contained(text, markdown_norm):
                entry["quote_hits"] += 1


def record_judge_result(stats: dict[str, Any], candidate: str,
                        judge_model: str, verdict: dict) -> None:
    """Accumulate per-judge metrics from one judge.py verdict."""
    entry = stats["judges"][candidate][judge_model]
    if verdict.get("error"):
        entry["errors"].append(verdict["error"])
        return
    for dim in DIMS:
        entry["scores"][dim].append(int(verdict["scores"][dim]))
    entry["totals"].append(float(verdict["total"]))
    entry["hallucination_counts"].append(len(verdict.get("hallucinations") or []))
    entry["elapsed_seconds"] += float(verdict.get("elapsed_seconds") or 0.0)
    entry["cost_usd"] += float(verdict.get("cost_usd") or 0.0)


def avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def build_metrics(stats: dict[str, Any]) -> dict[str, Any]:
    """Aggregate per-candidate and global metrics from accumulated stats."""
    metrics: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results_dir": str(RESULTS_DIR),
        "candidates": {},
    }
    for candidate in CANDIDATES:
        cand = stats["candidates"][candidate]
        quote_pct = (
            round(100.0 * cand["quote_hits"] / cand["quote_total"], 2)
            if cand["quote_total"] else None
        )
        entry: dict[str, Any] = {
            "judges": {},
            "validation_failures": cand["structure_failures"],
            "retries": cand["retries"],
            "cost_usd": round(cand["cost_usd"], 6),
            "elapsed_seconds": round(cand["elapsed_seconds"], 4),
            "quote_containment_pct": quote_pct,
            "errors": cand["errors"],
        }
        for judge_model in JUDGES:
            j = stats["judges"][candidate][judge_model]
            dims = {dim: avg(j["scores"][dim]) for dim in DIMS}
            entry["judges"][judge_model] = {
                **dims,
                "total_avg": avg(j["totals"]),
                "hallucination_avg": avg(j["hallucination_counts"]),
                "hallucination_total": sum(j["hallucination_counts"]),
                "quote_containment_pct": quote_pct,
                "judged": len(j["totals"]),
                "elapsed_seconds": round(j["elapsed_seconds"], 4),
                "cost_usd": round(j["cost_usd"], 6),
                "errors": j["errors"],
            }
        metrics["candidates"][candidate] = entry

    metrics["totals"] = {
        "cost_usd": round(sum(
            c["cost_usd"] for c in stats["candidates"].values()), 6),
        "elapsed_seconds": round(sum(
            c["elapsed_seconds"] for c in stats["candidates"].values())
            + sum(j["elapsed_seconds"]
                  for c in stats["judges"].values()
                  for j in c.values()), 4),
        "retries": sum(c["retries"] for c in stats["candidates"].values()),
        "validation_failures": sum(
            c["structure_failures"] for c in stats["candidates"].values()),
    }
    return metrics


def print_summary(metrics: dict[str, Any]) -> None:
    """Print a compact per-candidate summary table."""
    header = (f"{'candidate':<20} {'g25pro total':>13} {'dsv4pro total':>13} "
              f"{'cost_usd':>9} {'elapsed_s':>9} {'retries':>8} {'failures':>8}")
    print(header)
    print("-" * len(header))
    for candidate, entry in metrics["candidates"].items():
        def fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "-"
        g_total = fmt(entry["judges"]["gemini-2.5-pro"]["total_avg"])
        d_total = fmt(entry["judges"]["deepseek-v4-pro"]["total_avg"])
        print(f"{candidate:<20} {g_total:>13} {d_total:>13} "
              f"{entry['cost_usd']:>9.4f} {entry['elapsed_seconds']:>9.1f} "
              f"{entry['retries']:>8} {entry['validation_failures']:>8}")
    totals = metrics["totals"]
    print(f"\ntotals: cost_usd={totals['cost_usd']:.4f}, "
          f"elapsed_s={totals['elapsed_seconds']:.1f}, "
          f"retries={totals['retries']}, validation_failures={totals['validation_failures']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the matrix CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge-only", action="store_true",
                        help="Re-judge existing candidate outputs without re-running structure.py")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the full matrix (or judge-only pass) and write metrics.json."""
    args = parse_args(argv)
    eval_dir = Path(__file__).resolve().parent.parent
    corpus_dir = eval_dir / "corpus"
    results_dir = eval_dir / RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(corpus_dir.glob("*.md"))
    if not md_files:
        print("error: no corpus markdown files found", file=sys.stderr)
        return 2

    stats = init_stats()
    for md_path in md_files:
        video_id = md_path.stem
        markdown_norm = whitespace_normalize(md_path.read_text(encoding="utf-8"))
        for candidate in CANDIDATES:
            candidate_path = results_dir / f"{video_id}.{candidate}.json"
            if args.judge_only:
                if not candidate_path.exists():
                    error_note = f"missing candidate output {candidate_path.name}"
                    stats["candidates"][candidate]["errors"].append(f"{video_id}: {error_note}")
                    print(f"error: {video_id} {candidate}: {error_note}", file=sys.stderr)
                    continue
                with open(candidate_path, encoding="utf-8") as handle:
                    result = json.load(handle)
            else:
                print(f"structuring {video_id} x {candidate} ...", flush=True)
                try:
                    result = structure.run_structure(
                        candidate=candidate, input_path=md_path,
                        output_path=candidate_path)
                except Exception as error:  # fail-continue
                    error_note = f"{type(error).__name__}: {error}"
                    stats["candidates"][candidate]["errors"].append(f"{video_id}: {error_note}")
                    print(f"error: {video_id} {candidate}: {error_note}", file=sys.stderr)
                    continue
            record_candidate_result(stats, candidate, result, markdown_norm)
            if result.get("data") is None:
                continue
            for judge_model in JUDGES:
                judge_path = results_dir / f"{video_id}.{candidate}.{judge_model}.judge.json"
                print(f"judging {video_id} x {candidate} x {judge_model} ...", flush=True)
                try:
                    verdict = judge.run_judgment(
                        judge_model=judge_model, markdown_file=md_path,
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
