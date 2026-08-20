#!/usr/bin/env python3
"""Run an eval script with API keys resolved from the Hermes pass store.

Keys are decrypted into memory and passed via subprocess env -- they never
appear in a command string or file. Used because background terminal
sessions don't resolve $(pass ...) refs from ~/.hermes/.env.

The first non-flag argument selects the wrapped command (default ``compare``);
everything else is passed through to it. Examples::

    uv run python scripts/run_with_key.py
    uv run python scripts/run_with_key.py --judge-only
    uv run python scripts/run_with_key.py ground_truth --video-id <id> --video-url <url> --output out.json
"""
import os
import subprocess
import sys

STORE_DIR = os.path.expanduser("~/.hermes/.password-store")

KEY_MAP = {
    "GEMINI_API_KEY": "gemini/api-key",
    "DEEPSEEK_API_KEY": "deepseek/api-key",
}

COMMANDS = {
    "compare": "scripts/compare.py",
    "summarize_video": "scripts/summarize_video.py",
    "ground_truth": "scripts/ground_truth.py",
    "judge": "scripts/judge.py",
}


def resolve_key(name: str) -> str:
    gpg_path = os.path.join(STORE_DIR, "hermes", f"{name}.gpg")
    result = subprocess.run(
        ["gpg", "-d", "-q", gpg_path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gpg failed for {gpg_path}: {result.stderr.strip()}")
    value = result.stdout.strip().splitlines()[0]
    if not value:
        raise RuntimeError("empty credential")
    return value


def main() -> int:
    args = list(sys.argv[1:])
    command = "compare"
    if args and not args[0].startswith("-"):
        command = args.pop(0)
    script = COMMANDS.get(command)
    if script is None:
        print(f"error: unknown command {command!r}; choose from "
              f"{sorted(COMMANDS)}", file=sys.stderr)
        return 2

    env = dict(os.environ)
    for env_name, store_path in KEY_MAP.items():
        if not env.get(env_name):
            env[env_name] = resolve_key(store_path)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    eval_dir = os.path.dirname(script_dir)
    return subprocess.run(
        ["uv", "run", "python", script, *args],
        cwd=eval_dir,
        env=env,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
