"""Tests for the structuring CLI's LLM path (retry and error handling)."""

import json

import pytest

import structure
from structure import run_structure

VALID_JSON = {
    "overview": {
        "title": "Synthetic",
        "speaker": "S",
        "channel": "C",
        "main_topic": "M",
        "executive_summary": "E",
        "purpose": "P",
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

MINIMAL_MARKDOWN = "## Overview\n- **Speaker**: S\n"


def _paths(tmp_path):
    inp = tmp_path / "in.md"
    inp.write_text(MINIMAL_MARKDOWN, encoding="utf-8")
    out = tmp_path / "out.json"
    return inp, out


def test_success_no_retry(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, messages):
        calls.append(messages)
        return json.dumps(VALID_JSON), 100, 50, 0.001

    monkeypatch.setattr(structure, "call_llm", fake_call)
    inp, out = _paths(tmp_path)
    result = run_structure(candidate="deepseek-v4-pro", input_path=inp, output_path=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 0
    assert len(calls) == 1
    assert result["data"]["overview"]["speaker"] == "S"
    assert result["cost_usd"] > 0
    assert json.loads(out.read_text(encoding="utf-8"))["validation_passed"] is True


def test_invalid_json_retries_once_then_uses_second_response(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, messages):
        calls.append(messages)
        if len(calls) == 1:
            return "this is not json", 10, 5, 0.0
        return json.dumps(VALID_JSON), 10, 5, 0.0

    monkeypatch.setattr(structure, "call_llm", fake_call)
    inp, out = _paths(tmp_path)
    result = run_structure(candidate="gemini-2.5-flash", input_path=inp, output_path=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 1
    assert len(calls) == 2
    nudge = calls[1][-1]["content"]
    assert "previous response was not valid" in nudge.lower()


def test_two_failures_error_path_exit_code(tmp_path, monkeypatch):
    def fake_call(model, messages):
        return "still not json", 10, 5, 0.0

    monkeypatch.setattr(structure, "call_llm", fake_call)
    inp, out = _paths(tmp_path)
    assert structure.main([
        "--candidate", "deepseek-v4-pro",
        "--input", str(inp),
        "--output", str(out),
    ]) == 1
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content
    assert content["retries"] == 2
    assert content["data"] is None
    assert content["validation_passed"] is False


def test_schema_invalid_json_retries(tmp_path, monkeypatch):
    calls = []

    def fake_call(model, messages):
        calls.append(messages)
        bad = dict(VALID_JSON)
        del bad["overview"]  # schema-valid JSON, but not matching SummarySchema
        if len(calls) == 1:
            return json.dumps(bad), 10, 5, 0.0
        return json.dumps(VALID_JSON), 10, 5, 0.0

    monkeypatch.setattr(structure, "call_llm", fake_call)
    inp, out = _paths(tmp_path)
    result = run_structure(candidate="deepseek-v4-pro", input_path=inp, output_path=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 1
    assert len(calls) == 2


def test_parser_mode_is_deterministic_and_free(tmp_path):
    inp, out = _paths(tmp_path)
    result = run_structure(candidate="parser", input_path=inp, output_path=out)
    assert result["validation_passed"] is True
    assert result["model"] == "parser"
    assert result["cost_usd"] == 0.0
    assert result["retries"] == 0
    assert result["data"]["overview"]["speaker"] == "S"
