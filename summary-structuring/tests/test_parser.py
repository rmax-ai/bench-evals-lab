"""Tests for the deterministic markdown template parser."""

import pytest

from structure import parse_markdown, strip_frontmatter

SYNTHETIC_MARKDOWN = """---
type: Digest
title: Synthetic Talk - Test Speaker
id: urn:test:123
tags:
- synthetic
description: A synthetic description.
  continued here.
---
## Overview
- **Speaker**: Test Speaker
- **Channel**: Test Channel
- **Main topic**: Synthetic main topic
- **Purpose**: Test purpose sentence.
A synthetic executive summary paragraph for the parser test.

## Topic Map
### First Topic (10-20)
- **Explanation**: First explanation.
- **Key claims**:
  - Claim one.
  - Claim two.
- **Examples**:
  - Example one.
- **Terminology**:
  - Term one.
- **Why it matters**: First why.

### Second Topic
- **Explanation**: Second explanation.
- **Key claims**:
- **Examples**:
- **Terminology**:
- **Why it matters**: Second why.

## Key Points
### A key point
- **Explanation**: Point explanation.
- **Evidence**: Point evidence.
- **Practical implication**: Point implication.

## Frameworks, Models & Processes
### Test Framework
- **How it works**: Works like this.
- **Components**:
  - Component A
  - Component B
- **When to use**: Use it now.

## Examples & Case Studies
### Something happened.
- **Illustrates**: It illustrates testing.
- **Lesson**: The lesson is to test.

## Actionable Takeaways
- **Immediate**:
  - Do it now.
  - Do it twice.
- **Strategic**:
  - Think long term.
- **Questions to investigate**:
  - Why?

## Claims Worth Verifying
- The parser works. (Empirical)

## Notable Quotes
> "A verbatim quote." (at 1:23)
> A plain quote without quotes. (at 2:05)

## Compressed Summary
- A compressed bullet.
- **Keywords**: one, two
- **Core insight**: The core insight.

## Unknown Section
- **Random**: stuff
"""


def test_parser_full_roundtrip():
    data = parse_markdown(SYNTHETIC_MARKDOWN)

    assert data["overview"]["title"] == "Synthetic Talk - Test Speaker"
    assert data["overview"]["speaker"] == "Test Speaker"
    assert data["overview"]["channel"] == "Test Channel"
    assert data["overview"]["main_topic"] == "Synthetic main topic"
    assert data["overview"]["purpose"] == "Test purpose sentence."
    assert "synthetic executive summary paragraph" in data["overview"]["executive_summary"]

    topic_map = data["topic_map"]
    assert len(topic_map) == 2
    first = topic_map[0]
    assert first["topic"] == "First Topic"
    assert first["timestamp_range"] == "10-20"
    assert first["explanation"] == "First explanation."
    assert first["key_claims"] == ["Claim one.", "Claim two."]
    assert first["examples"] == ["Example one."]
    assert first["terminology"] == ["Term one."]
    assert first["why_it_matters"] == "First why."
    assert topic_map[1]["topic"] == "Second Topic"
    assert topic_map[1]["timestamp_range"] is None
    assert topic_map[1]["key_claims"] == []
    assert topic_map[1]["examples"] == []

    key_points = data["key_points"]
    assert key_points[0]["point"] == "A key point"
    assert key_points[0]["explanation"] == "Point explanation."
    assert key_points[0]["evidence"] == "Point evidence."
    assert key_points[0]["practical_implication"] == "Point implication."

    frameworks = data["frameworks"]
    assert frameworks[0]["name"] == "Test Framework"
    assert frameworks[0]["how_it_works"] == "Works like this."
    assert frameworks[0]["components"] == ["Component A", "Component B"]
    assert frameworks[0]["when_to_use"] == "Use it now."

    examples = data["examples"]
    assert examples[0]["what_happened"] == "Something happened."
    assert examples[0]["illustrates"] == "It illustrates testing."
    assert examples[0]["lesson"] == "The lesson is to test."

    takeaways = data["takeaways"]
    assert takeaways["immediate"] == ["Do it now.", "Do it twice."]
    assert takeaways["strategic"] == ["Think long term."]
    assert takeaways["questions_to_investigate"] == ["Why?"]

    claims = data["claims_to_verify"]
    assert claims[0]["claim"] == "The parser works."
    assert claims[0]["claim_type"] == "Empirical"

    quotes = data["quotes"]
    assert quotes[0]["text"] == "A verbatim quote."
    assert quotes[0]["timestamp"] == 83
    assert quotes[1]["text"] == "A plain quote without quotes."
    assert quotes[1]["timestamp"] == 125

    compressed = data["compressed"]
    assert compressed["bullets"] == ["A compressed bullet."]
    assert compressed["keywords"] == ["one", "two"]
    assert compressed["core_insight"] == "The core insight."

    # The unrecognized section contributes nothing.
    assert len(data["claims_to_verify"]) == 1


def test_absent_sections_produce_empty_values():
    markdown = "---\ntitle: Minimal\n---\n## Overview\n- **Speaker**: Someone\n"
    data = parse_markdown(markdown)
    assert data["overview"]["speaker"] == "Someone"
    assert data["overview"]["title"] == "Minimal"
    assert data["topic_map"] == []
    assert data["key_points"] == []
    assert data["frameworks"] == []
    assert data["examples"] == []
    assert data["takeaways"] == {"immediate": [], "strategic": [], "questions_to_investigate": []}
    assert data["claims_to_verify"] == []
    assert data["quotes"] == []
    assert data["compressed"] == {"bullets": [], "keywords": [], "core_insight": ""}


def test_frontmatter_stripped_without_breaking_body():
    body, frontmatter = strip_frontmatter(SYNTHETIC_MARKDOWN)
    assert frontmatter["title"] == "Synthetic Talk - Test Speaker"
    assert frontmatter["id"] == "urn:test:123"
    assert "## Overview" in body
    assert "---" not in body.splitlines()[0]

    data = parse_markdown(SYNTHETIC_MARKDOWN)
    assert data["overview"]["title"] == frontmatter["title"]


def test_no_frontmatter_still_parses():
    data = parse_markdown("## Overview\n- **Channel**: NoFront\n")
    assert data["overview"]["channel"] == "NoFront"
    assert data["overview"]["title"] == ""
    assert data["topic_map"] == []
