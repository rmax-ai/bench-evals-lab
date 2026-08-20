"""Tests for the judge CLI (verdict parsing, retry, and error handling)."""

import json

import pytest

import judge

JUDGE_RESPONSE = json.dumps({
    "scores": {
        "structure": 4,
        "faithfulness": 3,
        "coverage": 4,
        "precision": 3,
        "compression": 3,
    },
    "rationale": "Mostly faithful; a couple of minor unsupported details.",
    "hallucinations": ["an invented detail"],
})

CANDIDATE_RESULT = {
    "candidate": "gemini-2.5-flash",
    "video_id": "I6aiEf3aEFQ",
    "data": {
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
    },
    "validation_passed": True,
    "retries": 0,
}

FACT_SHEET = {
    "speaker": "S",
    "main_topic": "M",
    "key_claims": ["A claim."],
    "metadata": {"builder_model": "gemini-3.1-pro-preview", "video_id": "I6aiEf3aEFQ"},
}


def _paths(tmp_path):
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps(FACT_SHEET), encoding="utf-8")
    cand = tmp_path / "cand.json"
    cand.write_text(json.dumps(CANDIDATE_RESULT), encoding="utf-8")
    out = tmp_path / "judge.json"
    return facts, cand, out


def test_judge_success_scores_parsed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        judge, "call_judge",
        lambda model, prompt, nudge=False: (JUDGE_RESPONSE, 100, 50, 0.001),
    )
    facts, cand, out = _paths(tmp_path)
    result = judge.run_judgment(
        judge_model="gemini-3.1-pro-preview", fact_sheet_file=facts,
        candidate_json_file=cand, output_file=out)
    assert result["scores"]["structure"] == 4
    assert result["scores"]["faithfulness"] == 3
    assert result["total"] == round((4 + 3 + 4 + 3 + 3) / 5, 2)
    assert result["hallucinations"] == ["an invented detail"]
    assert result["judged_candidate"] == "gemini-2.5-flash"
    assert result["judge_model"] == "gemini-3.1-pro-preview"
    assert result["cost_usd"] > 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["total"] == result["total"]


def test_judge_malformed_retries_once_then_error(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, prompt, nudge=False):
        calls.append((model, prompt, nudge))
        return "definitely not json", 10, 5, 0.0

    monkeypatch.setattr(judge, "call_judge", fake_call)
    facts, cand, out = _paths(tmp_path)
    assert judge.main([
        "--judge", "deepseek-v4-pro",
        "--fact-sheet", str(facts),
        "--candidate-json", str(cand),
        "--output", str(out),
    ]) == 1
    assert len(calls) == 2
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content


def test_judge_out_of_range_score_retries(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, prompt, nudge=False):
        calls.append((model, prompt, nudge))
        bad = json.loads(JUDGE_RESPONSE)
        bad["scores"]["faithfulness"] = 9
        if len(calls) == 1:
            return json.dumps(bad), 10, 5, 0.0
        return JUDGE_RESPONSE, 10, 5, 0.0

    monkeypatch.setattr(judge, "call_judge", fake_call)
    facts, cand, out = _paths(tmp_path)
    result = judge.run_judgment(
        judge_model="deepseek-v4-pro", fact_sheet_file=facts,
        candidate_json_file=cand, output_file=out)
    assert result["scores"]["faithfulness"] == 3
    assert len(calls) == 2
    assert calls[1][2] is True  # retry carries the nudge


def test_judge_null_candidate_data_writes_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        judge, "call_judge",
        lambda model, prompt, nudge=False: (JUDGE_RESPONSE, 10, 5, 0.0),
    )
    facts, cand, out = _paths(tmp_path)
    bad = dict(CANDIDATE_RESULT)
    bad["data"] = None
    cand.write_text(json.dumps(bad), encoding="utf-8")
    assert judge.main([
        "--judge", "gemini-3.1-pro-preview",
        "--fact-sheet", str(facts),
        "--candidate-json", str(cand),
        "--output", str(out),
    ]) == 1
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content
