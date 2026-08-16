# YouTube transcript analysis eval

## What this evaluates

This eval compares Gemini models on structured analysis of a YouTube video
transcript. It supplies a YouTube URL and the fixed analysis prompt, then
compares response quality (LLM-as-judge) alongside latency, token usage, and
estimated API cost.

Pipeline per video:

1. **Transcript** — a verbatim transcript is fetched once via the Gemini API
   (`transcript.md`) and kept as the audio-channel reference for judging.
2. **Analysis** — each configured model runs the fixed prompt against the
   video URI; artifacts and metrics are saved per model.
3. **Judge** — an LLM judge scores every analysis on five dimensions
   (structure, faithfulness, coverage, precision, compression), returns a
   rationale, and lists hallucinated statements quoted verbatim. The judge
   ingests the **video itself** (slides + audio), not just the transcript —
   see "Judge design".

## How to run

Create the eval-local environment once:

```sh
cd youtube-transcript-analysis
uv venv && uv pip install -e .
```

Set `GEMINI_API_KEY` in your environment (never commit it), then run the full
matrix:

```sh
make compare        # GNU make (or: uv run python scripts/compare.py)
```

Judge existing artifacts without re-running analyses (e.g. after changing the
judge model in `config.json`):

```sh
make judge          # uv run python scripts/compare.py --judge-only
```

For one video/model pair:

```sh
uv run python scripts/analyze.py XNX-1h2K-9U \
  --model gemini-2.5-flash \
  --prompt-file prompt.md \
  --output-dir results/manual-run \
  --slug openwiki-analysis
```

Judge one artifact standalone:

```sh
uv run python scripts/judge.py results/2026-08-16-openwiki-analysis/openwiki-analysis-gemini-2.5-flash.md \
  --transcript-file results/2026-08-16-openwiki-analysis/transcript.md \
  --video-url XNX-1h2K-9U \
  --judged-model gemini-2.5-flash
```

Use `--json` with `analyze.py` to also print that run's metrics as JSON.
Existing artifacts are skipped unless `--force` is given, so re-runs only pay
for missing work.

## Models and inputs

- Models: `gemini-flash-lite-latest`, `gemini-flash-latest`,
  `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.1-flash-lite`,
  `gemini-3.5-flash`, `gemini-3.7-flash`
- Transcriber: `gemini-2.5-flash` (config `transcript.model`)
- Judge: `gemini-2.5-pro` (config `judge.model`)
- Prompt: [prompt.md](prompt.md)
- Video corpus and matrix: [config.json](config.json)

## Judge design

The judge scores each analysis 1-5 on:

| Dimension | What it measures |
| --- | --- |
| structure | All 9 required sections present, clear headings |
| faithfulness | Every claim/number/quote traceable to the video (spoken content or slides) or transcript; invented content penalized |
| coverage | Key topics, claims, examples, frameworks captured |
| precision | Concrete terminology and detail over generic filler |
| compression | Information density; repetition and boilerplate penalized |

The judge receives the video URI, the verbatim transcript, and the analysis;
output is constrained to JSON (`response_schema`, `temperature=0`). The total
is the arithmetic mean of the five dimensions, computed deterministically in
code.

**The judge must see the video, not just the transcript.** In the 2026-08-16
run, all 7 models independently reported facts absent from the transcript
(e.g. "13.5k GitHub stars", the speaker's name) that were visible on slides.
A transcript-only judge flags these as hallucinations and under-scores
faithfulness by 1.4-2.0 points across the board. The video judge credits them.

**Bias caveats:** the judge is a Gemini model judging Gemini outputs —
same-vendor judging can inherit vendor quirks, and the `gemini-2.5-pro` row is
self-judged. Absolute LLM scoring also saturates near 5 on this task (spread
4.6-5.0); treat deltas below ~0.5 as noise and see "Findings" for the
calibration limitation.

## Results

The committed [2026-08-16 OpenWiki analysis](results/2026-08-16-openwiki-analysis/)
is a full pipeline run: transcript fetch, 7 fresh analyses, and 7 video-judge
verdicts (`*.judge.json`). Costs are priced at the model actually served
(aliases resolved via `model_version`):

| Model | Served as | Elapsed | Input tok | Output tok | Cost | Judge |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `gemini-3.1-flash-lite` | — | 37.8s | 92,745 | 1,924 | $0.026 | 4.80 |
| `gemini-flash-lite-latest` | `gemini-3.5-flash-lite` | 44.4s | 92,745 | 2,546 | $0.034 | 5.00 |
| `gemini-flash-latest` | `gemini-3.7-flash` | 52.3s | 92,745 | 4,221 | $0.085 | 4.60 |
| `gemini-3.7-flash` | — | 57.3s | 92,745 | 4,236 | $0.085 | 4.80 |
| `gemini-3.5-flash` | — | 62.6s | 92,745 | 4,020 | $0.175 | 5.00 |
| `gemini-2.5-pro` | — | 88.8s | 299,191 | 3,429 | $0.408 | 5.00 |
| `gemini-2.5-flash` | — | 127.7s | 299,191 | 7,038 | $0.107 | 5.00 |

### Findings (2026-08-16)

- **Quality is uniformly high; cost is the real differentiator.** Judge
  totals span only 4.6-5.0 while cost per run spans $0.026-$0.408 (16x). For
  this task, the cheapest model (`3.1-flash-lite`, $0.026) scores 4.80 — the
  practical answer is "run the lite model" until a task shows a real quality
  cliff.
- **Deductions are about fidelity, not completeness.** Every sub-5 verdict
  traces to specific defects: paraphrases presented as verbatim quotes, and a
  provider-list error (judge: slide lists "Baseten" and "NVIDIA NIM"; the
  analysis substituted "Groq" and "Ollama"). No model lost points on
  structure, coverage, or compression.
- **Models read slides, not just audio.** All 7 models independently reported
  slide-only facts (13.5k stars, speaker name, DeepSWE percentages). Model
  choice changes the *channel* of extraction, not just quality — worth
  remembering when building video ingestion pipelines.
- **Judge calibration is the weak point.** Absolute 1-5 scoring saturates
  near the top of the scale (4 of 7 rows at 5.00). LLM judges are known to be
  better at relative than absolute judgments; a pairwise/ranked judging mode
  is the planned next step.
- **Tokenization still dominates cost** (from the 2026-08-15 run): Gemini
  3.x models ingest this video as ~93k input tokens, 2.5-gen as ~299k, so
  `3.7-flash` ($0.75/M) is cheaper per run than `2.5-flash` ($0.30/M).
- **Aliases resolve to new-gen models**: `flash-latest` → 3.7-flash,
  `flash-lite-latest` → 3.5-flash-lite. Pinning aliases silently upgrades
  price tier — pin concrete IDs when cost matters.

The [2026-08-15 run](results/2026-08-15-openwiki-analysis/) is retained as
the pre-judge baseline (`metrics-manual.json` preserves the original manual
measurements from before the scripted pipeline existed).

## Cost notes

Estimates use the following per-million-token prices (input/output):

| Model | Input | Output |
| --- | ---: | ---: |
| `gemini-2.5-flash` | $0.30 | $2.50 |
| `gemini-2.5-pro` | $1.25 | $10.00 |
| `gemini-flash-lite-latest` | *alias → 3.5-flash-lite* | |
| `gemini-3.1-flash-lite` | $0.25 | $1.50 |
| `gemini-3.5-flash-lite` | $0.30 | $2.50 |
| `gemini-3.5-flash` | $1.50 | $9.00 |
| `gemini-3.7-flash` | $0.75 | $3.75 |

Alias entries are deliberately absent from the pricing table so aliases are
always priced at their resolved `model_version` — a stale alias entry made
the first run under-price `flash-lite-latest` 3x ($0.010 vs $0.034).

Judging with video ingestion costs ~$0.39 per judgment (2.5-pro, ~307k input
tokens); transcript-only judging costs ~$0.02. The transcript fetch is ~$0.10
once per video. Actual billed cost can vary with provider pricing and token
accounting.
