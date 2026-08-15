# bench-evals-lab

`bench-evals-lab` is a meta repository for assorted evaluations and benchmarks. It supports both Python and TypeScript evals.

Each eval or benchmark lives in its own fully self-contained folder: it owns its dependencies, documentation, run command, and committed results.

## Layout

Current and planned top-level contents:

- `youtube-transcript-analysis/` — seed eval (Gemini model comparison).
- `template-python/` — template for Python evals.
- `template-typescript/` — template for TypeScript evals.
- `docs/EVAL_TEMPLATE.md` — checklist and starting structure for a new eval.

## Conventions

- Every eval folder is self-contained, including its dependency manifest and README.
- Each eval has a documented one-command run path.
- Commit result artifacts under that eval's `results/` directory.
- Read secrets only from environment variables, such as `GEMINI_API_KEY`; never commit secrets or `.env` files.

## Add a new eval

1. Copy the appropriate Python or TypeScript template.
2. Rename the copied folder for the eval.
3. Fill in its configuration, scripts, README, and one-command run path.
4. Add a row for it to the index below.

## Eval index

More evals will be added over time.

| Eval | Language | Status | Notes |
| --- | --- | --- | --- |
| `youtube-transcript-analysis` | Python | Seeded 2026-08-15 | Gemini model comparison (YouTube URL → structured analysis) |
| `template-python` | Python | Template | Copy-paste starter for Python evals |
| `template-typescript` | TypeScript | Template | Copy-paste starter for TS evals |

## Toolchain notes

- Python evals use a virtual environment or `uv`, with only the dependencies they need.
- TypeScript evals use `npm` and `tsx`; do not add frameworks unless the eval needs them.
