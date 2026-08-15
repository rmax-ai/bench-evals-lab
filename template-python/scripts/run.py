#!/usr/bin/env python3
"""Create a dated placeholder summary for a zero-dependency Python eval."""

from __future__ import annotations

import configparser
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "default.ini"


def main() -> None:
    """Read the example config and write one dated result artifact."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    name = config["eval"]["name"]
    models = [model.strip() for model in config["models"]["names"].split(",")]
    timestamp = datetime.now(timezone.utc)
    slug = name.lower().replace(" ", "-")
    result_dir = ROOT / "results" / f"{timestamp:%Y-%m-%d}-{slug}"
    result_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "name": name,
        "models": models,
        "timestamp": timestamp.isoformat(),
        "metrics": {field.strip(): None for field in config["metrics"]["fields"].split(",")},
    }
    summary_path = result_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"API_KEY: {'set' if os.environ.get('API_KEY') else 'unset'}")
    print(summary_path)


if __name__ == "__main__":
    main()
