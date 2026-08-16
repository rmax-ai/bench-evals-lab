#!/usr/bin/env python3
"""Generate a human-verification package for the latest results directory.

Parses ground-truth.md into individually addressable claims, cross-references
every claim against the audio transcript, and emits:

- verification/claims.md        checklist worksheet for the verifier
- verification/attestation.json durable attestation state (never overwritten)
- verification/README.md        verification guide

The transcript is the independent channel: [slide] claims with no audio
support are flagged for visual verification (highest-risk claims first), and
[audio] claims missing from the transcript are flagged as extraction errors.

Usage:
    uv run python scripts/verify_package.py [--results-dir DIR] [--force]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = EVAL_DIR / "config.json"

TAG_RE = re.compile(r"\[(slide|audio),\s*(\d{1,2}:\d{2})\]")
WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-\.]*")
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "was", "were", "are",
    "not", "you", "your", "our", "its", "they", "their", "them", "also",
    "just", "like", "such", "these", "those", "there", "here", "then", "than",
    "which", "what", "when", "where", "who", "how", "why", "but", "out", "up",
    "over", "more", "most", "some", "any", "all", "each", "both", "other",
    "another", "same", "into", "been", "has", "have", "had", "does", "will",
    "would", "should", "could", "can", "may", "might", "about", "very", "used",
    "use", "using", "uses", "via", "per", "one", "two", "three",
    # domain-generic terms that would false-positive audio support
    "agent", "agents", "applied", "application", "context", "content",
    "details", "documentation", "documents", "examples", "example", "format",
    "formats", "framework", "frameworks", "general", "knowledge", "memory",
    "numbers", "organizations", "process", "project", "projects", "specific",
    "statistics", "stats", "structure", "support", "system", "technical",
    "usage", "version", "entities",
}


def significant_tokens(text: str) -> list[str]:
    """Tokens that signal specific slide content: digits or long words."""
    return [t for t in WORD_RE.findall(text.lower())
            if (re.search(r"\d", t) or (t.isalpha() and len(t) >= 6))
            and t not in STOPWORDS]


def to_seconds(ts: str) -> int:
    """Convert MM:SS to seconds."""
    minutes, seconds = ts.split(":")
    return int(minutes) * 60 + int(seconds)


def parse_claims(text: str) -> list[dict]:
    """Parse ground-truth.md into claims grouped by section header."""
    claims: list[dict] = []
    group: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("###"):
            group = line.lstrip("#").strip()
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line) or re.match(r"^\d+\.\s+(.+)$", line)
        if bullet and group:
            body = bullet.group(1)
            tags = TAG_RE.findall(body)
            cleaned = TAG_RE.sub("", body).strip()
            cleaned = cleaned.replace("**", "").strip(" :*")
            if not cleaned:
                continue
            if re.fullmatch(r"[^:]{1,60}:", cleaned):
                continue  # bare label line ("Projects/Tools:") — a sub-header
            claims.append({
                "group": group,
                "text": cleaned,
                "tags": [{"channel": t[0], "timestamp": t[1]} for t in tags],
            })
    return claims


def cross_reference(claim: str, transcript_lower: str) -> tuple[bool, bool, list[str]]:
    """Return (any_token_found, significant_token_found, display_terms)."""
    tokens = [t for t in WORD_RE.findall(claim.lower())
              if len(t) >= 3 and t not in STOPWORDS and not t.isdigit()]
    any_found = any(t in transcript_lower for t in tokens)
    sig = [t for t in significant_tokens(claim) if t in transcript_lower]
    sig_found = bool(sig)
    display = sig[:3] if sig else sorted({t for t in tokens if t in transcript_lower})[:3]
    return any_found, sig_found, display


def video_deep_link(video_id: str, timestamp: str) -> str:
    return f"https://youtu.be/{video_id}?t={to_seconds(timestamp)}"


def find_results_dir(config: dict, slug: str) -> Path | None:
    """Find the newest results/<date>-<slug> directory."""
    candidates = sorted(
        (EVAL_DIR / "results").glob(f"*-{slug}"), reverse=True
    )
    return candidates[0] if candidates else None


def build_package(results_dir: Path, video: dict, force: bool) -> Path:
    """Generate the verification package; returns its directory."""
    pkg = results_dir / "verification"
    pkg.mkdir(parents=True, exist_ok=True)
    ground_truth = (results_dir / "ground-truth.md").read_text(encoding="utf-8")
    transcript = (results_dir / "transcript.md").read_text(encoding="utf-8")
    transcript_lower = transcript.lower()
    claims = parse_claims(ground_truth)

    claims_path = pkg / "claims.md"
    if not claims_path.exists() or force:
        lines = [
            f"# Verification worksheet — {video['slug']}",
            "",
            f"Video: {video['title']} (https://youtu.be/{video['id']})",
            f"Ground truth: `../ground-truth.md` · Transcript: `../transcript.md`",
            "",
            "Tick each claim after checking it. The durable record of your",
            "verification is `attestation.json` (see README in this folder);",
            "checkbox state is an ephemeral worksheet and is reset by",
            "`--force` regeneration.",
            "",
        ]
        stats = {
            "total": len(claims),
            "slide": 0, "audio": 0, "both": 0,
            "slide_only": 0, "audio_unmatched": 0,
        }
        rows: list[tuple[dict, bool, bool, list[str]]] = []
        for index, claim in enumerate(claims, start=1):
            channels = {t["channel"] for t in claim["tags"]}
            if "slide" in channels and "audio" in channels:
                stats["both"] += 1
            elif "slide" in channels:
                stats["slide"] += 1
            elif "audio" in channels:
                stats["audio"] += 1
            any_found, sig_found, display = cross_reference(claim["text"], transcript_lower)
            if "slide" in channels and not sig_found:
                stats["slide_only"] += 1
            if "audio" in channels and not any_found:
                stats["audio_unmatched"] += 1
            rows.append((claim, any_found, sig_found, display))

        lines += [
            f"Claims: {stats['total']} total — [slide] {stats['slide']}, "
            f"[audio] {stats['audio']}, both {stats['both']} · "
            f"slide-only (verify visually): {stats['slide_only']} · "
            f"[audio] claims missing from transcript (extraction error?): "
            f"{stats['audio_unmatched']}",
            "",
            "**Triage order:** slide-only claims first (highest risk), then",
            "[audio] claims missing from the transcript, then the rest.",
            "",
        ]
        current_group = None
        for index, (claim, any_found, sig_found, display) in enumerate(rows, start=1):
            channels = {t["channel"] for t in claim["tags"]}
            if claim["group"] != current_group:
                current_group = claim["group"]
                lines.append(f"## {current_group}")
            tags = ", ".join(
                f"[{t['channel']}, {t['timestamp']}]" for t in claim["tags"]
            )
            links = " · ".join(
                f"{t['channel']} @ {t['timestamp']} "
                f"({video_deep_link(video['id'], t['timestamp'])})"
                for t in claim["tags"]
            )
            if sig_found:
                cross = f"audio-ref: strong ({', '.join(display)})"
            elif any_found and "audio" in channels:
                cross = f"**CHECK: [audio] claim only generic-match ({', '.join(display)}) — inspect**"
            elif any_found:
                cross = f"**audio-ref: weak ({', '.join(display)}) — slide-only, verify visually**"
            elif "audio" in channels:
                cross = "**CHECK: [audio] claim not found in transcript — extraction error?**"
            else:
                cross = "**audio-ref: none — slide-only, verify visually**"
            lines.append(f"- [ ] **C{index:03d}** {tags} — {claim['text']}")
            lines.append(f"  - {cross} · {links}")
        claims_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    attestation_path = pkg / "attestation.json"
    if not attestation_path.exists():
        document = {
            "video": {"id": video["id"], "slug": video["slug"], "title": video["title"]},
            "results_dir": results_dir.name,
            "ground_truth_file": "ground-truth.md",
            "transcript_file": "transcript.md",
            "claims_total": len(claims),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "attestations": [],
        }
        attestation_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
    else:
        document = json.loads(attestation_path.read_text(encoding="utf-8"))
        document["claims_total"] = len(claims)

    guide_path = pkg / "README.md"
    guide = f"""# Human verification & attestation

Why this exists: every judge verdict is grounded in `../ground-truth.md`. An
extraction miss there becomes a false hallucination flag in downstream
verdicts — indistinguishable from a correct flag. This package exists so a
human can attest that the ground truth faithfully represents the video, or
contest specific claims.

## Three channels

1. `../transcript.md` — the verbatim audio channel (kept for exactly this
   purpose: every [slide] claim is cross-referenced against it).
2. `../ground-truth.md` — the extracted claims, each tagged [slide]/[audio]
   with timestamps.
3. The video itself — every claim in `claims.md` carries a timestamped deep
   link so you can jump straight to the moment and read the slide.

## How to verify

1. Open `claims.md`.
2. Work the triage order stated in its header: slide-only claims first,
   then [audio] claims missing from the transcript, then the rest.
3. For each claim: is it present in the video at that timestamp? Is the
   source tag right ([slide] vs [audio])? Are numbers and wording exact?
   Tick the checkbox; note corrections on the line.
4. Contest a claim when it is wrong, missing context, or the source tag is
   misattributed.

## How to attest

```sh
# full review of every claim
uv run python scripts/attest.py --verifier "Your Name" --status verified \\
  --method full --notes "reviewed all claims against transcript + video"

# spot check of the slide-only subset
uv run python scripts/attest.py --verifier "Your Name" --status verified \\
  --method spot --contested C007:"number is 38% on slide, not 36%" \\
  --resolved C007:"accepted claim as-is after checking video @ 08:58"
```

Attestations are appended to `attestation.json` (re-attesting with the same
verifier name replaces that entry). Commit the attestation: once attested,
`ground-truth.md` is human-blessed ground truth for this run.

Re-attest whenever `ground-truth.md` changes, or when a judge verdict is
challenged and the fact sheet turns out to be the source of the dispute.
"""
    guide_path.write_text(guide, encoding="utf-8")
    return pkg


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="Results directory (default: newest for the first configured video)")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate claims.md (resets checkbox worksheet state)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    video = config["videos"][0]
    results_dir = args.results_dir or find_results_dir(config, video["slug"])
    if results_dir is None:
        print(f"error: no results directory for {video['slug']}", file=sys.stderr)
        return 2
    try:
        pkg = build_package(results_dir, video, args.force)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"verification package: {pkg}")
    print(f"  claims.md (worksheet) + attestation.json + README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
