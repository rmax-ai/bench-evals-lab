"""Tests for the summarize CLI (native video call, retry, and error handling)."""

import json

import pytest

import summarize_video

VALID_SUMMARY = {
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

VIDEO_URL = "https://www.youtube.com/watch?v=I6aiEf3aEFQ"
VIDEO_ID = "I6aiEf3aEFQ"


class FakeResponse:
    """Minimal stand-in for httpx.Response: json()/text/status_code."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        return self._payload


def _native_payload(text, prompt_tokens=100, completion_tokens=50):
    return {
        "candidates": [{"content": {"parts": [{"text": text}]}}],
        "usageMetadata": {
            "promptTokenCount": prompt_tokens,
            "candidatesTokenCount": completion_tokens,
            "cachedContentTokenCount": 0,
        },
    }


def _paths(tmp_path):
    out = tmp_path / "out.json"
    return out


def test_success_valid_json_no_retry(tmp_path, monkeypatch):
    calls = []

    def fake_generate(model, api_key, payload, timeout=1800):
        calls.append((model, payload))
        return FakeResponse(_native_payload(json.dumps(VALID_SUMMARY)))

    monkeypatch.setattr(summarize_video, "native_generate", fake_generate)
    out = _paths(tmp_path)
    result = summarize_video.run_summarize(
        candidate="gemini-2.5-flash", video_url=VIDEO_URL,
        video_id=VIDEO_ID, output=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 0
    assert result["prompt_tokens"] == 100
    assert result["completion_tokens"] == 50
    assert result["cost_usd"] > 0
    assert len(calls) == 1
    assert json.loads(out.read_text(encoding="utf-8"))["validation_passed"] is True


def test_request_body_uses_native_file_data_endpoint(tmp_path, monkeypatch):
    captured = []

    def fake_generate(model, api_key, payload, timeout=1800):
        captured.append(payload)
        return FakeResponse(_native_payload(json.dumps(VALID_SUMMARY)))

    monkeypatch.setattr(summarize_video, "native_generate", fake_generate)
    out = _paths(tmp_path)
    summarize_video.run_summarize(
        candidate="gemini-3.5-flash-lite", video_url=VIDEO_URL,
        video_id=VIDEO_ID, output=out)
    payload = captured[0]
    parts = payload["contents"][0]["parts"]
    assert parts[0]["file_data"]["mime_type"] == "video/mp4"
    assert parts[0]["file_data"]["file_uri"] == VIDEO_URL
    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    # The URL must be the native :generateContent endpoint, never the
    # OpenAI-compatible chat/completions route (which rejects YouTube URLs).
    url = summarize_video.native_url("gemini-2.5-flash")
    assert ":generateContent" in url
    assert "openai" not in url
    assert "chat/completions" not in url


def test_invalid_json_retries_once_then_succeeds(tmp_path, monkeypatch):
    calls = []

    def fake_generate(model, api_key, payload, timeout=1800):
        calls.append(payload)
        if len(calls) == 1:
            return FakeResponse(_native_payload("this is not json"))
        return FakeResponse(_native_payload(json.dumps(VALID_SUMMARY)))

    monkeypatch.setattr(summarize_video, "native_generate", fake_generate)
    out = _paths(tmp_path)
    result = summarize_video.run_summarize(
        candidate="gemini-2.5-pro", video_url=VIDEO_URL,
        video_id=VIDEO_ID, output=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 1
    assert len(calls) == 2
    parts = calls[1]["contents"][0]["parts"]
    assert "corrected JSON" in parts[-1]["text"]


def test_schema_invalid_json_retries(tmp_path, monkeypatch):
    calls = []

    def fake_generate(model, api_key, payload, timeout=1800):
        calls.append(payload)
        bad = dict(VALID_SUMMARY)
        del bad["overview"]  # valid JSON, but not matching SummarySchema
        if len(calls) == 1:
            return FakeResponse(_native_payload(json.dumps(bad)))
        return FakeResponse(_native_payload(json.dumps(VALID_SUMMARY)))

    monkeypatch.setattr(summarize_video, "native_generate", fake_generate)
    out = _paths(tmp_path)
    result = summarize_video.run_summarize(
        candidate="gemini-3.6-flash", video_url=VIDEO_URL,
        video_id=VIDEO_ID, output=out)
    assert result["validation_passed"] is True
    assert result["retries"] == 1
    assert len(calls) == 2


def test_two_failures_error_path_exit_code(tmp_path, monkeypatch):
    def fake_generate(model, api_key, payload, timeout=1800):
        return FakeResponse(_native_payload("still not json"))

    monkeypatch.setattr(summarize_video, "native_generate", fake_generate)
    out = _paths(tmp_path)
    assert summarize_video.main([
        "--candidate", "gemini-2.5-flash",
        "--video-url", VIDEO_URL,
        "--video-id", VIDEO_ID,
        "--output", str(out),
    ]) == 1
    content = json.loads(out.read_text(encoding="utf-8"))
    assert "error" in content
    assert content["retries"] == 2
    assert content["data"] is None
    assert content["validation_passed"] is False
