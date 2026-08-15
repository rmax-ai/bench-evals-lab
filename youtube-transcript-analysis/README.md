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
`make compare` (full token accounting):

| Model | Elapsed | Input tokens | Output tokens | Cost |
| --- | ---: | ---: | ---: | ---: |
| `gemini-flash-lite-latest` | 44.5s | 92,745 | 3,162 | $0.010539 |
| `gemini-2.5-flash` | 90.4s | 299,191 | 8,003 | $0.109765 |

(`metrics-manual.json` preserves the original manual-run measurements from
2026-08-15, before the scripted pipeline existed.)

## Cost notes

Estimates use the following per-million-token prices (input/output):

| Model | Input | Output |
| --- | ---: | ---: |
| `gemini-2.5-flash` | $0.30 | $2.50 |
| `gemini-flash-lite-latest` | $0.10 | $0.40 |

Actual billed cost can vary with provider pricing and token accounting.
