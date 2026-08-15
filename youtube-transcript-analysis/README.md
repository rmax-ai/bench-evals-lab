# YouTube transcript analysis eval

## What this evaluates

This eval compares Gemini models on structured analysis of a YouTube video
transcript. It supplies a YouTube URL and the fixed analysis prompt, then
compares response quality alongside latency, token usage, and estimated API
cost.

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

For one video/model pair:

```sh
uv run python scripts/analyze.py XNX-1h2K-9U \
  --model gemini-2.5-flash \
  --prompt-file prompt.md \
  --output-dir results/manual-run \
  --slug openwiki-analysis
```

Use `--json` to also print that run's metrics as JSON.

## Models and inputs

- Models: `gemini-flash-lite-latest`, `gemini-2.5-flash`
- Prompt: [prompt.md](prompt.md)
- Video corpus and matrix: [config.json](config.json)

## Results

The committed [2026-08-15 OpenWiki analysis](results/2026-08-15-openwiki-analysis/)
compares the fixed prompt against the LangChain OpenWiki video. Verified via
`make compare` (full token accounting, costs priced at the model actually
served — aliases resolved via `model_version`):

| Model | Served as | Elapsed | Input tok | Output tok | Cost |
| --- | --- | ---: | ---: | ---: | ---: |
| `gemini-3.1-flash-lite` | — | 40.5s | 92,745 | 1,628 | $0.026 |
| `gemini-flash-lite-latest` | `gemini-3.5-flash-lite` | 44.5s | 92,745 | 3,162 | $0.036 |
| `gemini-3.7-flash` | — | 48.7s | 92,745 | 4,170 | $0.085 |
| `gemini-flash-latest` | `gemini-3.7-flash` | 55.3s | 92,745 | 4,224 | $0.085 |
| `gemini-2.5-flash` | — | 90.4s | 299,191 | 8,003 | $0.110 |
| `gemini-3.5-flash` | — | 112.4s | 92,745 | 3,905 | $0.174 |
| `gemini-2.5-pro` | — | 92.1s | 299,191 | 4,515 | $0.419 |

### Findings (2026-08-15)

- **Tokenization dominates cost, not the rate card.** Gemini 3.x models ingest
  this video as ~93k input tokens; 2.5-gen models as ~299k. So `3.7-flash`
  ($0.75/M) is *cheaper per run* than `2.5-flash` ($0.30/M).
- **Aliases resolve to new-gen models**: `flash-latest` → 3.7-flash,
  `flash-lite-latest` → 3.5-flash-lite. Pinning aliases silently upgrades
  price tier — pin concrete IDs when cost matters.
- **Lite compresses hardest**: 3.1-flash-lite emitted ~1.6k tokens vs ~4k+ for
  the rest; detail density trades off against price.
- **2.5-flash produced the longest output** (8k tokens) — highest verbosity in
  this matrix, not the cheapest.

(`metrics-manual.json` preserves the original manual-run measurements from
2026-08-15, before the scripted pipeline existed.)

## Cost notes

Estimates use the following per-million-token prices (input/output):

| Model | Input | Output |
| --- | ---: | ---: |
| `gemini-2.5-flash` | $0.30 | $2.50 |
| `gemini-flash-lite-latest` | $0.10 | $0.40 |

Actual billed cost can vary with provider pricing and token accounting.
