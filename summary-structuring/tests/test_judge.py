"""Tests for the judge CLI (verdict parsing, retry, and error handling)."""

import json

import pytest

import judge
import structure

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
    "candidate": "parser",
    "model": "parser",
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

MARKDOWN = "## Overview\n- **Speaker**: S\n"


def _paths(tmp_path):
    md = tmp_path / "ref.md"
    md.write_text(MARKDOWN, encoding="utf-8")
    cand = tmp_path / "cand.json"
    cand.write_text(json.dumps(CANDIDATE_RESULT), encoding="utf-8")
    out = tmp_path / "judge.json"
    return md, cand, out


def test_judge_success_scores_parsed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        structure, "call_llm",
        lambda model, messages: (JUDGE_RESPONSE, 100, 50, 0.001),
    )
    md, cand, out = _paths(tmp_path)
    result = judge.run_judgment(
        judge_model="gemini-2.5-pro", markdown_file=md,
        candidate_json_file=cand, output_file=out)
    assert result["scores"]["structure"] == 4
    assert result["scores"]["faithfulness"] == 3
    assert result["total"] == round((4 + 3 + 4 + 3 + 3) / 5, 2)
    assert result["hallucinations"] == ["an invented detail"]
    assert result["judged_candidate"] == "parser"
    assert result["judge_model"] == "gemini-2.5-pro"
    assert result["cost_usd"] > 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["total"] == result["total"]


def test_judge_malformed_retries_once_then_error(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, messages):
        calls.append(messages)
        return "definitely not json", 10, 5, 0.0

    monkeypatch.setattr(structure, "call_llm", fake_call)
    md, cand, out = _paths(tmp_path)
    assert judge.main([
        "--judge", "deepseek-v4-pro",
        "--markdown", str(md),
        "--candidate-json", str(cand),
        "--output", str(out),
    ]) == 1
    assert len(calls) == 2
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content


def test_judge_out_of_range_score_retries(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, messages):
        calls.append(messages)
        bad = json.loads(JUDGE_RESPONSE)
        bad["scores"]["faithfulness"] = 9
        if len(calls) == 1:
            return json.dumps(bad), 10, 5, 0.0
        return JUDGE_RESPONSE, 10, 5, 0.0

    monkeypatch.setattr(structure, "call_llm", fake_call)
    md, cand, out = _paths(tmp_path)
    result = judge.run_judgment(
        judge_model="deepseek-v4-pro", markdown_file=md,
        candidate_json_file=cand, output_file=out)
    assert result["scores"]["faithfulness"] == 3
    assert len(calls) == 2


def test_judge_null_candidate_data_writes_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        structure, "call_llm",
        lambda model, messages: (JUDGE_RESPONSE, 10, 5, 0.0),
    )
    md, cand, out = _paths(tmp_path)
    bad = dict(CANDIDATE_RESULT)
    bad["data"] = None
    cand.write_text(json.dumps(bad), encoding="utf-8")
    assert judge.main([
        "--judge", "gemini-2.5-pro",
        "--markdown", str(md),
        "--candidate-json", str(cand),
        "--output", str(out),
    ]) == 1
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content
