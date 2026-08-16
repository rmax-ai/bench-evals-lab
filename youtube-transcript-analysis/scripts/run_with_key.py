#!/usr/bin/env python3
"""Run compare.py with GEMINI_API_KEY resolved from the Hermes pass store.

The key is decrypted into memory and passed via subprocess env — it never
appears in a command string or file. Used because background terminal
sessions don't resolve $(pass ...) refs from ~/.hermes/.env.
"""
import os
import subprocess
import sys

STORE_DIR = os.path.expanduser("~/.hermes/.password-store")


def resolve_key(name: str) -> str:
    gpg_path = os.path.join(STORE_DIR, "hermes", "gemini", f"{name}.gpg")
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
    env = dict(os.environ)
    env["GEMINI_API_KEY"] = resolve_key("api-key")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    eval_dir = os.path.dirname(script_dir)
    return subprocess.run(
        ["uv", "run", "python", "scripts/compare.py", *sys.argv[1:]],
        cwd=eval_dir,
        env=env,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
