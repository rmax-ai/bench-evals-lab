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

### Why the extractor must be Gemini's strongest model — and why one isn't enough

Both video-reading roles in this eval — the fact-sheet extractor and the
gemini judge — are pinned to the strongest Gemini tier available. The
primary extractor is `gemini-3.1-pro-preview` (config `ground_truth.model`),
chosen after a head-to-head with `gemini-2.5-pro`:

- **Extraction errors are silent and compound.** A fact the extractor misses
  becomes a false hallucination flag in every downstream verdict —
  indistinguishable from a correct flag. Extractor precision is a hard upper
  bound on judge fairness, so the weakest link in extraction caps the whole
  eval.
- **Slide reading is where model strength shows.** The fact sheet's value is
  precise extraction of dense slide content — numbers, provider lists,
  quotes, timestamps. That is exactly where flash-tier models degrade: they
  drop or smooth over slide details, which produces precisely the
  false-positive hallucination flags seen in the transcript-only judging
  round.
- **Extraction is one-time cost; judging is recurring cost.** The fact sheet
  runs once per video (~$0.22 at 3.1-pro-preview) and grounds unlimited
  future verdicts — 7 models × N judges × M reruns. Extraction is where
  spending buys leverage; judging is where cheap independence pays.
- **Ground truth must not silently drift.** The fact sheet is a committed
  artifact; fixing a miss requires a human to re-watch the video. Getting it
  right once with the strongest model beats re-auditing repeatedly.

**One extractor is not enough — the 2026-08-16 incident:** the original
2.5-pro fact sheet silently missed a set of slide quotes (`log.md`, the
code/personal modes, GitLab/Bitbucket support, ~15 verbatim slide quotes
including "The quality ceiling right now is the prompt, not the model").
Both judges then flagged analyses quoting those slides as fabricated — a
false-positive cascade that nearly became the run's headline finding. The
3.1-pro-preview re-extraction found them, and cross-model agreement among
the analyses corroborated slide origin (5/7 models independently report
`log.md`; 3/7 quote the quality-ceiling line verbatim). The merged fact
sheet is committed with provenance notes; the **cross-extractor diff is now
standard procedure** before any run's ground truth is trusted, and the
human attestation flow (below) exists to close the loop on residual
disagreements.

**Known limitations:** absolute 1-5 scoring saturates at the top for the
gemini judge. The deepseek judge is strict on quote fidelity — near-quotes
and paraphrase-as-quote are flagged — which keeps faithfulness low (2-3)
even after ground-truth corrections. Pairwise ranking is the planned
refinement. The `gemini-2.5-pro` row is self-judged by the gemini judge.

## Human verification & attestation

Ground truth underpins every verdict, so the eval ships a **verification
package** that lets a human attest `ground-truth.md` before its scores are
taken as final.

```sh
make verify        # uv run python scripts/verify_package.py
```

This generates `verification/` inside the latest results directory:

| File | Role |
| --- | --- |
| `claims.md` | Every extracted fact as an individually addressable claim (C001…), each with its [slide]/[audio] source tag, a timestamped deep link into the video, and an automatic cross-reference against the audio transcript |
| `attestation.json` | Durable attestation state — verifier, date, method, status, contested claims and their resolutions. Never overwritten by regeneration |
| `README.md` | The verification guide |

The **transcript is kept as the independent channel**: [slide] claims with no
significant audio support are flagged *slide-only — verify visually* (the
highest-risk triage class), and [audio] claims absent from the transcript are
flagged as extraction errors. The 2026-08-16 worksheet flags 12 slide-only
claims and 0 extraction inconsistencies.

To attest after checking claims:

```sh
uv run python scripts/attest.py --verifier "Your Name" --status verified \
  --method full --notes "reviewed all claims against transcript + video"
uv run python scripts/attest.py --verifier "Your Name" --status contested \
  --method spot --contested C007:"38% on slide, not 36%" \
  --resolved C007:"accepted as-is after checking video @ 08:58"
```

Attestations are committed with the results. Re-attest whenever
`ground-truth.md` changes or a judge verdict is challenged and the fact sheet
turns out to be the source of the dispute.

## Results

The committed [2026-08-16 OpenWiki analysis](results/2026-08-16-openwiki-analysis/)
is a full pipeline run: transcript, fact sheet, 7 analyses, and 7 verdicts
per judge (`*.judge.json`). Costs are priced at the model actually served
(aliases resolved via `model_version`; deepseek costs use cache-hit
accounting):

| Model | Served as | Elapsed | Input tok | Output tok | Cost | Gemini j. | DeepSeek j. |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemini-3.1-flash-lite` | — | 37.8s | 92,745 | 1,924 | $0.026 | 4.80 | 3.60 |
| `gemini-flash-lite-latest` | `gemini-3.5-flash-lite` | 44.4s | 92,745 | 2,546 | $0.034 | 5.00 | **3.80** |
| `gemini-flash-latest` | `gemini-3.7-flash` | 52.3s | 92,745 | 4,221 | $0.085 | 4.60 | 3.40 |
| `gemini-3.7-flash` | — | 57.3s | 92,745 | 4,236 | $0.085 | 4.80 | 3.60 |
| `gemini-3.5-flash` | — | 62.6s | 92,745 | 4,020 | $0.175 | 5.00 | 3.40 |
| `gemini-2.5-pro` | — | 88.8s | 299,191 | 3,429 | $0.408 | 5.00 | 3.60 |
| `gemini-2.5-flash` | — | 127.7s | 299,191 | 7,038 | $0.107 | 5.00 | 3.40 |

### Findings (2026-08-16)

- **Ground truth is extraction-limited — one extractor is not enough.** The
  first 2.5-pro fact sheet missed slide quotes, `log.md`, the code/personal
  modes, and GitLab/Bitbucket support; both judges then flagged analyses
  quoting those slides as fabricated. A 3.1-pro-preview re-extraction found
  them (cross-model agreement corroborates: 5/7 analyses report `log.md`,
  3/7 quote the quality-ceiling line verbatim). After merging, the
  deepseek judge's hallucination lists shrank materially
  (`flash-lite-latest` 6 → 0 flags). Treat ground truth as a hypothesis
  until the cross-extractor diff + human attestation close it.
- **Cross-vendor judging still earns its keep, in a sharper form.** The
  gemini judge (same vendor) awards 4.6-5.0 with zero flags on 4 rows. The
  deepseek judge finds real, specific defects on the merged ground truth:
  fabricated quotes in 6 of 7 analyses (3.5-flash worst at 18 flags —
  invented file paths, an invented interactive demo, "Harrison Chase"),
  garbled slide quotes ("in and out" → "out and out"), and outside-knowledge
  insertion. `flash-lite-latest` is the only model with zero hallucinations.
- **The analysis prompt invites quote fabrication.** Section 8 demands
  quotes; models that cannot find slide quotes invent them rather than emit
  fewer. Models with slide access still garble verbatim text. Fix for any
  such pipeline: require verbatim-only quotes (empty section allowed) or
  [paraphrase] tags.
- **Rankings are stable across judges.** `flash-lite-latest` leads the
  deepseek ranking (3.80) and `3.1-flash-lite` leads the gemini ranking
  (4.80); both are the cheapest models in the matrix. The 2.5-gen models
  cluster at the bottom under the strict judge. Cost and latency remain the
  practical differentiators.
- **Models read slides, not just audio.** All 7 models independently
  reported slide-only facts (13.5k stars, speaker name, DeepSWE
  percentages). The fact sheet exists precisely so text-only judges see
  this content.
- **Judge cost asymmetry:** ~$0.39 per gemini verdict (video ingestion),
  ~$0.005 per deepseek verdict (prefix caching). Cross-vendor judging is
  ~80x cheaper.
- **Tokenization still dominates analysis cost**: Gemini 3.x models ingest
  this video as ~93k input tokens, 2.5-gen as ~299k, so `3.7-flash`
  ($0.75/M) is cheaper per run than `2.5-flash` ($0.30/M).
- **Aliases resolve to new-gen models**: `flash-latest` → 3.7-flash,
  `flash-lite-latest` → 3.5-flash-lite. Pin concrete IDs when cost matters.

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
