# TypeScript eval template

This is a copy-paste starter for self-contained TypeScript evals.

## How to use

```sh
cp -r template-typescript my-eval
```

Update the copied configuration and runner for your evaluation.

## How to run

Install dependencies once, then run the eval:

```sh
npm install
npm run eval
```

## Layout

- `config/default.json` contains example eval settings.
- `scripts/run.ts` is the typed eval runner.
- `results/<YYYY-MM-DD>-<slug>/` contains committed result artifacts for each run.

