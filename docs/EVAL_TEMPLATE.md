# Eval template

Use this template when creating a new eval. Keep all files and dependencies inside the eval folder.

## Folder structure

```text
my-eval/
├── README.md
├── config/
│   └── default.yaml
├── scripts/
│   └── run.*
└── results/
    └── 2026-08-15-example-run/
```

Add either `pyproject.toml` for Python or `package.json` for TypeScript at the root of `my-eval/`.

## README skeleton

````md
# My eval

## What this evaluates

Describe the task, success criteria, and metrics.

## How to run

```sh
# One command that runs the eval
```

List required environment variables and expected output location.

## Models/inputs

Document the models, datasets, prompts, and input versions used.

## Results

Link to committed result directories and summarize the key metrics.

## Cost notes

State expected API, compute, or other run costs.
````

## Self-containment checklist

- [ ] The folder has its own dependency manifest (`pyproject.toml` or `package.json`).
- [ ] A documented single command runs the eval.
- [ ] Secrets are read only from environment variables.
- [ ] Results are committed under `results/<YYYY-MM-DD>-<slug>/`.
- [ ] The eval README documents inputs, models, results, and costs.
- [ ] The root README index has a row for the new eval.

## Minimal Python flavor

Use `pyproject.toml` and a script such as `scripts/run.py`. A typical one-command path is:

```sh
uv run python scripts/run.py --config config/default.yaml
```

Read credentials with `os.environ["GEMINI_API_KEY"]` (or another named environment variable) and write artifacts to a dated `results/` subdirectory.

## Minimal TypeScript flavor

Use `package.json` and a script such as `scripts/run.ts`. A typical one-command path is:

```sh
npm run eval
```

Set the script to run `tsx scripts/run.ts --config config/default.yaml`. Read credentials from `process.env.GEMINI_API_KEY` and write artifacts to a dated `results/` subdirectory.
