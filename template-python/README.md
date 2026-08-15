# Python eval template

This is a copy-paste starter for small, self-contained Python evals. It uses
only the Python standard library at runtime.

## How to use

```sh
cp -r template-python my-eval
```

Rename the copied folder and update the names and references in its README,
configuration, and script.

## How to run

```sh
make run
```

You can also run it directly:

```sh
python3 scripts/run.py
```

## Layout

- `config/default.ini` — example eval name, model placeholders, and metrics.
- `scripts/run.py` — stdlib-only runner that writes a placeholder artifact.
- `results/` — committed output artifacts for each run.
- `pyproject.toml` — project metadata and optional development dependencies.

## Results

Each run writes its artifacts to `results/<YYYY-MM-DD>-<slug>/`. Replace the
placeholder summary with the metrics and provenance needed for your eval, then
commit the result directory.
