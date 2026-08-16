# YouTube transcript analysis eval

## What this evaluates

This eval compares Gemini models on structured analysis of a YouTube video
transcript. It supplies a YouTube URL and the fixed analysis prompt, then
compares response quality (dual LLM-as-judge, one same-vendor and one
cross-vendor) alongside latency, token usage, and estimated API cost.

Pipeline per video:

1. **Transcript** — a verbatim transcript is fetched once via the Gemini API
   (`transcript.md`) and kept as the audio-channel reference.
2. **Fact sheet** — a text ground-truth document extracted once from the
   video (`ground-truth.md`): all factual claims from audio *and slides*,
   source-tagged and timestamped. This is what text-only judges score
   against; it is inspectable and can be amended by hand.
3. **Analysis** — each configured model runs the fixed prompt against the
   video URI; artifacts and metrics are saved per model.
4. **Judges** — each configured judge scores every analysis on five
   dimensions (structure, faithfulness, coverage, precision, compression),
   returns a rationale, and lists hallucinated statements quoted verbatim.

## How to run

Create the eval-local environment once:

```sh
cd youtube-transcript-analysis
uv venv && uv pip install -e .
```

Set `GEMINI_API_KEY` in your environment (never commit it), and
`DEEPSEEK_API_KEY` if a deepseek judge is configured, then run the full
matrix:

```sh
make compare        # GNU make (or: uv run python scripts/compare.py)
```

Judge existing artifacts without re-running analyses:

```sh
make judge          # both configured judges
uv run python scripts/compare.py --judge-only --only-judge deepseek-v4-pro
uv run python scripts/compare.py --judge-only --only-judge gemini --force
```

For one video/model pair:

```sh
uv run python scripts/analyze.py XNX-1h2K-9U \
  --model gemini-2.5-flash \
  --prompt-file prompt.md \
  --output-dir results/manual-run \
  --slug openwiki-analysis
```

Existing artifacts are skipped unless `--force` is given, so re-runs only pay
for missing work. `--only-judge <substring>` restricts re-runs to one judge
(re-running the gemini judge costs ~$0.39 per verdict; deepseek ~$0.005).

## Models and inputs

- Models: `gemini-flash-lite-latest`, `gemini-flash-latest`,
  `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.1-flash-lite`,
  `gemini-3.5-flash`, `gemini-3.7-flash`
- Transcriber: `gemini-2.5-flash` (config `transcript.model`)
- Fact-sheet extractor: `gemini-2.5-pro` (config `ground_truth.model`)
- Judges (config `judges`):
  - `gemini-2.5-pro` — same-vendor, ingests the video itself (slides +
    audio) plus the transcript
  - `deepseek-v4-pro` — cross-vendor, scores against the fact sheet plus
    the transcript (DeepSeek cannot ingest video)
- Prompt: [prompt.md](prompt.md)
- Video corpus and matrix: [config.json](config.json)

## Judge design

The judge scores each analysis 1-5 on:

| Dimension | What it measures |
| --- | --- |
| structure | All 9 required sections present, clear headings |
| faithfulness | Every claim/number/quote traceable to the source material; invented content penalized |
| coverage | Key topics, claims, examples, frameworks captured |
| precision | Concrete terminology and detail over generic filler |
| compression | Information density; repetition and boilerplate penalized |

Gemini-judge output is constrained to JSON via `response_schema`
(temperature 0); DeepSeek-judge output via `response_format: json_object`
plus tolerant client-side parsing (markdown fences, flat score objects) and a
one-shot schema-nudge retry. The total is the arithmetic mean of the five
dimensions, computed deterministically in code.

**Why two judges:** a same-vendor judge inherits vendor priors and inflates
scores; a cross-vendor judge is independent but cannot ingest video, so it
scores against the extracted fact sheet. Disagreements between the two are
the interesting signal. In the 2026-08-16 run the gemini judge scored 4.6-5.0
across the board while the deepseek judge scored 3.4-3.8 — and the deepseek
judge caught a systematic quote-fabrication pattern the same-vendor judge
missed (see Findings).

**Known limitations:** absolute 1-5 scoring saturates at the top for the
gemini judge; the deepseek judge's faithfulness scores saturate at 2 because
every model shares the same defect class (fabricated quotes). Pairwise
ranking is the planned refinement. The `gemini-2.5-pro` row is self-judged by
the gemini judge.

## Results

The committed [2026-08-16 OpenWiki analysis](results/2026-08-16-openwiki-analysis/)
is a full pipeline run: transcript, fact sheet, 7 analyses, and 7 verdicts
per judge (`*.judge.json`). Costs are priced at the model actually served
(aliases resolved via `model_version`; deepseek costs use cache-hit
accounting):

| Model | Served as | Elapsed | Input tok | Output tok | Cost | Gemini j. | DeepSeek j. |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemini-3.1-flash-lite` | — | 37.8s | 92,745 | 1,924 | $0.026 | 4.80 | **3.80** |
| `gemini-flash-lite-latest` | `gemini-3.5-flash-lite` | 44.4s | 92,745 | 2,546 | $0.034 | 5.00 | 3.60 |
| `gemini-flash-latest` | `gemini-3.7-flash` | 52.3s | 92,745 | 4,221 | $0.085 | 4.60 | 3.60 |
| `gemini-3.7-flash` | — | 57.3s | 92,745 | 4,236 | $0.085 | 4.80 | 3.60 |
| `gemini-3.5-flash` | — | 62.6s | 92,745 | 4,020 | $0.175 | 5.00 | 3.40 |
| `gemini-2.5-pro` | — | 88.8s | 299,191 | 3,429 | $0.408 | 5.00 | 3.40 |
| `gemini-2.5-flash` | — | 127.7s | 299,191 | 7,038 | $0.107 | 5.00 | 3.40 |

### Findings (2026-08-16)

- **Cross-vendor judging earned its keep.** The gemini judge (same vendor)
  awarded 4.6-5.0 and zero hallucination flags on 4 of 7 rows. The deepseek
  judge found **fabricated quotes in all 7 analyses** — every model invented
  plausible-sounding quotes for the "Notable Quotes" section instead of
  extracting them, plus recurring invented details (`log.md` filename,
  "Harrison Chase" surname, code/personal modes, provider list errors).
  Where the judges' coverage overlaps, their hallucination lists agree; the
  gap is same-vendor leniency, not noise.
- **The analysis prompt invites fabrication.** Section 8 demands quotes, but
  this talk is quote-poor; all 7 models resolved the conflict by inventing
  them rather than emitting fewer quotes. Actionable fix for any such
  pipeline: require verbatim-only quotes (empty section allowed) or demand
  [paraphrase] tags. This is a prompt defect, not a model defect — the
  models differ only in how many quotes they fabricate.
- **Rankings stay roughly stable across judges.** `3.1-flash-lite` is best
  under both judges (4.80 / 3.80) at 16x lower cost than the pro model. The
  2.5-gen models cluster at the bottom under the strict judge. Cost and
  latency remain the practical differentiators.
- **Models read slides, not just audio.** All 7 models independently reported
  slide-only facts (13.5k stars, speaker name, DeepSWE percentages) that a
  transcript-only judge would flag as hallucinations. The fact sheet exists
  precisely so text-only judges see this content.
- **Judge cost asymmetry:** ~$0.39 per gemini verdict (video ingestion),
  ~$0.005 per deepseek verdict (prefix caching: 13.4k of 13.6k input tokens
  cached across the run). Cross-vendor judging is ~80x cheaper *and* more
  discriminative here.
- **Tokenization still dominates analysis cost** (from the 2026-08-15 run):
  Gemini 3.x models ingest this video as ~93k input tokens, 2.5-gen as
  ~299k, so `3.7-flash` ($0.75/M) is cheaper per run than `2.5-flash`
  ($0.30/M).
- **Aliases resolve to new-gen models**: `flash-latest` → 3.7-flash,
  `flash-lite-latest` → 3.5-flash-lite. Pinning aliases silently upgrades
  price tier — pin concrete IDs when cost matters.

The [2026-08-15 run](results/2026-08-15-openwiki-analysis/) is retained as
the pre-judge baseline.

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
| `deepseek-v4-pro` | $0.435 ($0.003625 cache hit) | $0.87 |

Alias entries are deliberately absent from the pricing table so aliases are
always priced at their resolved `model_version` — a stale alias entry made
the first run under-price `flash-lite-latest` 3x ($0.010 vs $0.034). DeepSeek
moved to peak/off-peak billing on 2026-08-16 16:00 UTC; the flat rates above
are estimates until billing data confirms otherwise. Actual billed cost can
vary with provider pricing and token accounting.
