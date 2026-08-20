"""Tests for the compare matrix driver (metrics aggregation over a mini matrix)."""

import json

import pytest

import compare

VALID_DATA = {
    "overview": {
        "title": "T", "speaker": "S", "channel": "C",
        "main_topic": "M", "executive_summary": "E", "purpose": "P",
    },
    "topic_map": [],
    "key_points": [],
    "frameworks": [],
    "examples": [],
    "takeaways": {"immediate": [], "strategic": [], "questions_to_investigate": []},
    "claims_to_verify": [],
    "quotes": [],
    "compressed": {"bullets": [], "keywords": [], "core_insight": ""},
}

VIDEOS = [
    {"video_id": "VIDEO-ONE", "title": "First", "url": "https://www.youtube.com/watch?v=VIDEO-ONE"},
    {"video_id": "VIDEO-TWO", "title": "Second", "url": "https://www.youtube.com/watch?v=VIDEO-TWO"},
]

MINI_CANDIDATES = ["cand-a", "cand-b"]


def test_metrics_aggregation_over_mini_matrix(tmp_path, monkeypatch):
    results_dir = tmp_path / "results"
    summarize_counts: dict[str, int] = {}

    def fake_ground_truth(*, video_url, video_id, output):
        facts = {
            "speaker": "S",
            "main_topic": "M",
            "key_claims": ["A claim."],
            "metadata": {
                "builder_model": "gemini-3.1-pro-preview",
                "video_id": video_id,
                "elapsed_seconds": 0.4,
                "cost_usd": 0.001,
                "tokens": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        }
        output.write_text(json.dumps(facts), encoding="utf-8")
        return facts

    def fake_summarize(*, candidate, video_url, video_id, output):
        n = summarize_counts.get(candidate, 0)
        summarize_counts[candidate] = n + 1
        result = {
            "candidate": candidate,
            "video_id": video_id,
            "data": VALID_DATA,
            "validation_passed": True,
            "retries": 0,
            "elapsed_seconds": 1.0 + n,  # 1.0 on video 1, 2.0 on video 2
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost_usd": 0.01,
        }
        output.write_text(json.dumps(result), encoding="utf-8")
        return result

    def fake_judge(*, judge_model, fact_sheet_file, candidate_json_file, output_file):
        candidate = json.loads(candidate_json_file.read_text(encoding="utf-8"))["candidate"]
        verdict = {
            "judged_candidate": candidate,
            "judge_model": judge_model,
            "scores": {
                "structure": 4, "faithfulness": 3,
                "coverage": 4, "precision": 4, "compression": 3,
            },
            "total": 3.6,
            "rationale": "ok",
            "hallucinations": ["unsupported detail"],
            "elapsed_seconds": 0.5,
            "cost_usd": 0.002,
        }
        output_file.write_text(json.dumps(verdict), encoding="utf-8")
        return verdict

    monkeypatch.setattr(compare, "CANDIDATES", MINI_CANDIDATES)
    monkeypatch.setattr(compare, "CORPUS_ITEMS", VIDEOS)
    monkeypatch.setattr(compare, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(compare, "run_ground_truth", fake_ground_truth)
    monkeypatch.setattr(compare, "run_summarize", fake_summarize)
    monkeypatch.setattr(compare, "run_judgment", fake_judge)

    assert compare.main([]) == 0
    metrics_path = results_dir / "metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    for candidate in MINI_CANDIDATES:
        entry = metrics["candidates"][candidate]
        # latency avg/min/max over 2 videos
        assert entry["latency"]["avg"] == 1.5
        assert entry["latency"]["min"] == 1.0
        assert entry["latency"]["max"] == 2.0
        # cost totals and average
        assert entry["cost_usd"]["total"] == 0.02
        assert entry["cost_usd"]["avg"] == 0.01
        assert entry["validation_failures"] == 0
        assert entry["retries"] == 0
        # per-judge dims: total = 3.6, accuracy = mean(faithfulness=3, precision=4)
        for judge_model in compare.JUDGES:
            jentry = entry["judges"][judge_model]
            assert jentry["total"] == 3.6
            assert jentry["accuracy"] == 3.5
            assert jentry["structure"] == 4
            assert jentry["hallucination_total"] == 2  # one per video
            assert jentry["judged"] == 2

    # fact sheets built once per video
    assert metrics["fact_sheets"]["VIDEO-ONE"]["built"] is True
    assert metrics["fact_sheets"]["VIDEO-TWO"]["builder_model"] == "gemini-3.1-pro-preview"

    # summary rank present, sorted by quality/cost
    ranked = metrics["summary"]["rank"]
    assert len(ranked) == 2
    assert {item["candidate"] for item in ranked} == set(MINI_CANDIDATES)
    assert ranked[0]["quality"] == 3.6
    assert ranked[0]["cost_per_video"] == 0.01
    assert ranked[0]["rank"] == 1


def test_fail_continue_records_errors(tmp_path, monkeypatch):
    results_dir = tmp_path / "results"

    def fake_ground_truth(*, video_url, video_id, output):
        raise RuntimeError("fact-sheet builder failed")

    def fake_summarize(*, candidate, video_url, video_id, output):
        result = {
            "candidate": candidate,
            "video_id": video_id,
            "data": None,
            "validation_passed": False,
            "retries": 2,
            "elapsed_seconds": 3.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": 0.0,
            "error": "boom",
        }
        output.write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(compare, "CANDIDATES", MINI_CANDIDATES)
    monkeypatch.setattr(compare, "CORPUS_ITEMS", VIDEOS[:1])
    monkeypatch.setattr(compare, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(compare, "run_ground_truth", fake_ground_truth)
    monkeypatch.setattr(compare, "run_summarize", fake_summarize)

    assert compare.main([]) == 0  # fail-continue: no abort
    metrics = json.loads((results_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["fact_sheets"]["VIDEO-ONE"]["built"] is False
    assert metrics["fact_sheets"]["VIDEO-ONE"]["errors"]
    entry = metrics["candidates"]["cand-a"]
    assert entry["validation_failures"] == 1
    assert entry["retries"] == 2
    assert "boom" in entry["errors"]
