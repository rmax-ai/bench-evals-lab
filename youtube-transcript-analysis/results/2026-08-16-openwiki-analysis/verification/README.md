# Human verification & attestation

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
uv run python scripts/attest.py --verifier "Your Name" --status verified \
  --method full --notes "reviewed all claims against transcript + video"

# spot check of the slide-only subset
uv run python scripts/attest.py --verifier "Your Name" --status verified \
  --method spot --contested C007:"number is 38% on slide, not 36%" \
  --resolved C007:"accepted claim as-is after checking video @ 08:58"
```

Attestations are appended to `attestation.json` (re-attesting with the same
verifier name replaces that entry). Commit the attestation: once attested,
`ground-truth.md` is human-blessed ground truth for this run.

Re-attest whenever `ground-truth.md` changes, or when a judge verdict is
challenged and the fact sheet turns out to be the source of the dispute.
