# video-summarization

Stage-1 eval for the yt-insights pipeline: produce a structured summary
(`SummarySchema` JSON) directly from a YouTube video via Gemini's native
`generateContent` endpoint (YouTube ingestion through `parts[].file_data`).
The eval measures how faithfully each candidate extracts the video's
informational content into the exact schema the pipeline consumes.

## One-command run

    make compare

This resolves the Gemini and DeepSeek API keys from the Hermes pass store
(`~/.hermes/.password-store`) via `scripts/run_with_key.py` and runs the full
matrix (5 videos × 4 candidates × 2 judges), writing artifacts and
`metrics.json` under `results/2026-08-20-video-summarization/`.

Re-judge existing candidate outputs without re-running summarization:

    make judge-only

## Architecture

- `corpus/manifest.json` — the 5 public YouTube videos (id, title, watch URL).
- `prompts/summary.md` — the production yt-insights summary prompt and schema
  contract, copied verbatim so results transfer to the pipeline.
- `schema.py` — the `SummarySchema` pydantic models candidates must emit
  (copied verbatim from `summary-structuring/schema.py`).
- `scripts/summarize_video.py` — one candidate run: mirrors the production
  `summarize_video()` call exactly (native `generateContent`, `file_data`
  YouTube ingestion, JSON output mode, 65536-token cap, `usageMetadata`
  accounting). One retry on JSON/schema failure.
- `scripts/ground_truth.py` — two fact sheets per video (gemini-3.1-pro-preview
  and gemini-2.5-pro), merged into one ground-truth file: union of all
  sections, keeping claims/quotes found by only one extractor and collapsing
  duplicates. If one extractor fails entirely, the other's fact sheet stands
  alone; the metadata records both builder models and any failure. This merged
  ground truth is what every candidate is scored against.
- `scripts/judge.py` — one judge run: gemini-3.1-pro-preview (native text
  prompt, no video) or deepseek-v4-pro (OpenAI-compatible) scores the
  candidate JSON against the fact sheet on five fidelity dimensions and lists
  hallucinations verbatim. The judge NEVER sees the video.
- `scripts/compare.py` — the full-matrix driver (fail-continue; aggregates
  `metrics.json`, ranks candidates by quality/cost).
- `tests/` — unit tests for the schema, summarize CLI, judge, and compare.

## Metrics

Per candidate (aggregated in `metrics.json`):

- latency: avg/min/max `elapsed_seconds` of the candidate call
- cost: total and avg `cost_usd` (candidates dominate the budget)
- per judge: structure, faithfulness, coverage, precision, compression,
  total, accuracy, hallucination totals
- accuracy = mean(faithfulness, precision) per judge
- quality = judge total per judge
- contract_violations: total per candidate of `timestamp_range` values emitted
  as a `[start, end]` integer list instead of the contract's `"start-end"`
  string. These are coerced to `"start-end"` before pydantic validation and
  counted as a metric rather than a validation failure.
- validation_failures, retries, and errors per stage

The summary section ranks candidates by quality/cost (cost per video).

## Fidelity rubric

Judges score each candidate on a 1-5 scale (strict; most outputs land 2-4):

- structure: all schema fields sensibly populated and organized
- faithfulness: every candidate string is supported by the fact sheet
- coverage: the fact sheet's material content is present in the JSON
- precision: quotes verbatim, names and numbers exact
- compression: no redundant restatement, high density

Hallucinations are candidate-JSON strings that cannot be found in the fact
sheet (whitespace-normalized comparison) and are listed verbatim per judgment.

## Cost note

Candidates ingest a full video through the native endpoint, so a full matrix
run is estimated at ~$25 (5 fact sheets + 20 candidate calls + 40 judge calls);
candidate and fact-sheet calls dominate. Judge calls are text-only and cheap.

## Caveat

accuracy and quality are computed in aggregation from the judge dimensions
(accuracy = mean of faithfulness and precision; quality = judge total), so
they are not independent measurements, they are derived scores.
