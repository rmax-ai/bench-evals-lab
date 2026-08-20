"""Tests for the SummarySchema pydantic models."""

import json

import pytest
from pydantic import ValidationError

from schema import SummarySchema

FIXTURE = {
    "overview": {
        "title": "Synthetic Video Title",
        "speaker": "Jane Doe",
        "channel": "Example Channel",
        "main_topic": "A synthetic main topic",
        "executive_summary": "A synthetic executive summary paragraph.",
        "purpose": "To exercise schema validation.",
    },
    "topic_map": [
        {
            "topic": "Synthetic topic",
            "timestamp_range": "10-20",
            "explanation": "A synthetic explanation.",
            "key_claims": ["A key claim.", "Another key claim."],
            "examples": ["An example."],
            "terminology": ["term one"],
            "why_it_matters": "Because tests matter.",
        }
    ],
    "key_points": [
        {
            "point": "A key point",
            "explanation": "The explanation.",
            "evidence": "The evidence.",
            "practical_implication": "Do the thing.",
        }
    ],
    "frameworks": [
        {
            "name": "Test Framework",
            "how_it_works": "It works.",
            "components": ["component a"],
            "when_to_use": "Use it now.",
        }
    ],
    "examples": [
        {
            "what_happened": "Something happened.",
            "illustrates": "Testing.",
            "lesson": "Always test.",
        }
    ],
    "takeaways": {
        "immediate": ["Do this."],
        "strategic": ["Plan for that."],
        "questions_to_investigate": ["Why?"],
    },
    "claims_to_verify": [
        {"claim": "A claim to verify.", "claim_type": "Empirical"}
    ],
    "quotes": [
        {"text": "A verbatim quote.", "timestamp": 83}
    ],
    "compressed": {
        "bullets": ["A compressed bullet."],
        "keywords": ["one", "two"],
        "core_insight": "The core insight.",
    },
}


def test_valid_fixture_validates():
    parsed = SummarySchema.model_validate_json(json.dumps(FIXTURE))
    assert parsed.overview.speaker == "Jane Doe"
    assert parsed.topic_map[0].timestamp_range == "10-20"
    assert parsed.quotes[0].timestamp == 83
    assert parsed.takeaways.immediate == ["Do this."]


def test_missing_required_section_raises():
    bad = dict(FIXTURE)
    del bad["overview"]
    with pytest.raises(ValidationError):
        SummarySchema.model_validate_json(json.dumps(bad))


def test_truncated_json_raises():
    with pytest.raises(ValidationError):
        SummarySchema.model_validate_json('{"overview": {"speaker": ')


def test_wrong_type_raises():
    bad = dict(FIXTURE)
    bad["quotes"] = [{"text": "q", "timestamp": "not-an-int"}]
    with pytest.raises(ValidationError):
        SummarySchema.model_validate_json(json.dumps(bad))


def test_empty_object_raises():
    with pytest.raises(ValidationError):
        SummarySchema.model_validate_json("{}")
