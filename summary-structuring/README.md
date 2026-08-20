# summary-structuring

Stage-2 eval for the yt-insights pipeline: given a markdown video summary,
produce a structured JSON object matching `SummarySchema`. The eval measures
how faithfully each candidate converts the markdown into JSON: the JSON must
contain nothing absent from the markdown, and must not drop material content.

## One-command run

    make compare

This resolves the Gemini and DeepSeek API keys from the Hermes pass store
(`~/.hermes/.password-store`) via `scripts/run_with_key.py` and runs the full
matrix (5 corpus files × 5 candidates × 2 judges), writing artifacts and
`metrics.json` under `results/2026-08-20-summary-structuring/`.

Re-judge existing candidate outputs without re-running structuring:

    make judge-only

## Architecture

- `corpus/` — the reference ground truth: five real markdown summaries
  vendored from the yt-insights pipeline. See `corpus/manifest.json` for
  provenance (source repo, commit, capture times, generating model).
- `schema.py` — the `SummarySchema` pydantic models candidates must produce.
- `scripts/structure.py` — one candidate run: `parser` (deterministic template
  parser, no LLM) or one of four LLM candidates (`deepseek-v4-pro`,
  `deepseek-v4-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`).
- `scripts/judge.py` — one judge run: an LLM judge (`gemini-2.5-pro` or
  `deepseek-v4-pro`) scores the candidate JSON against the markdown on five
  fidelity dimensions and lists hallucinations verbatim.
- `scripts/compare.py` — the full-matrix driver (fail-continue; aggregates
  `metrics.json`).
- `tests/` — unit tests for the schema, parser, structuring CLI, and judge.

## Fidelity rubric

Judges score each candidate on a 1-5 scale (strict; most outputs land 2-4):

- structure: schema fields sensibly populated and organized
- faithfulness: every candidate string is supported by the markdown
- coverage: the markdown's material content is present in the JSON
- precision: quotes verbatim, names and numbers exact
- compression: no redundant restatement, high density

Hallucinations are candidate-JSON strings that cannot be found in the markdown
(whitespace-normalized comparison) and are listed verbatim per judgment.

## Cost note

Structuring calls are text-in (markdown → JSON) with no video ingestion, so
per-call costs are cents-level; a full matrix run typically costs well under a
dollar.

## Parser-roundtrip caveat

The corpus summaries were rendered from the yt-insights pipeline's internal
JSON, so the deterministic `parser` candidate has a best-case advantage: it is
literally recovering the structure the markdown was generated from. Treat the
parser's scores as a ceiling for this eval, not as evidence that template
parsing generalizes to arbitrary markdown.
