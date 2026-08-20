from pydantic import BaseModel

class Overview(BaseModel):
    title: str = ""
    speaker: str = ""
    channel: str = ""
    main_topic: str = ""
    executive_summary: str = ""
    purpose: str = ""

class TopicMapItem(BaseModel):
    topic: str = ""
    timestamp_range: str | None = None
    explanation: str = ""
    key_claims: list[str] = []
    examples: list[str] = []
    terminology: list[str] = []
    why_it_matters: str = ""

class KeyPoint(BaseModel):
    point: str = ""
    explanation: str = ""
    evidence: str = ""
    practical_implication: str = ""

class Framework(BaseModel):
    name: str = ""
    how_it_works: str = ""
    components: list[str] = []
    when_to_use: str = ""

class Example(BaseModel):
    what_happened: str = ""
    illustrates: str = ""
    lesson: str = ""

class Takeaways(BaseModel):
    immediate: list[str] = []
    strategic: list[str] = []
    questions_to_investigate: list[str] = []

class ClaimToVerify(BaseModel):
    claim: str = ""
    claim_type: str = ""

class Quote(BaseModel):
    text: str = ""
    timestamp: int | None = None

class Compressed(BaseModel):
    bullets: list[str] = []
    keywords: list[str] = []
    core_insight: str = ""

class SummarySchema(BaseModel):
    overview: Overview
    topic_map: list[TopicMapItem] = []
    key_points: list[KeyPoint] = []
    frameworks: list[Framework] = []
    examples: list[Example] = []
    takeaways: Takeaways
    claims_to_verify: list[ClaimToVerify] = []
    quotes: list[Quote] = []
    compressed: Compressed
