# Verification worksheet — openwiki-analysis

Video: Building Docs for Agents, Not Humans: Inside OpenWiki (https://youtu.be/XNX-1h2K-9U)
Ground truth: `../ground-truth.md` · Transcript: `../transcript.md`

Tick each claim after checking it. The durable record of your
verification is `attestation.json` (see README in this folder);
checkbox state is an ephemeral worksheet and is reset by
`--force` regeneration.

Claims: 101 total — [slide] 37, [audio] 8, both 2 · slide-only (verify visually): 12 · [audio] claims missing from transcript (extraction error?): 0

**Triage order:** slide-only claims first (highest risk), then
[audio] claims missing from the transcript, then the rest.

## Names & Entities
- [ ] **C001** [slide, 00:08] — Speaker: Brace Sproul, Head of Applied AI, LangChain
  - **audio-ref: weak (head) — slide-only, verify visually** · slide @ 00:08 (https://youtu.be/XNX-1h2K-9U?t=8)
- [ ] **C002** [audio, 00:11], [audio, 00:42], [audio, 05:17] — People Mentioned: Sean , Harrison (LangChain CEO) , Karpathy
  - audio-ref: strong (people, harrison, karpathy) · audio @ 00:11 (https://youtu.be/XNX-1h2K-9U?t=11) · audio @ 00:42 (https://youtu.be/XNX-1h2K-9U?t=42) · audio @ 05:17 (https://youtu.be/XNX-1h2K-9U?t=317)
- [ ] **C003** [slide, 00:08], [slide, 00:00], [audio, 06:08] — Companies/Organizations: LangChain , LangSmith , Google
  - audio-ref: strong (google) · slide @ 00:08 (https://youtu.be/XNX-1h2K-9U?t=8) · slide @ 00:00 (https://youtu.be/XNX-1h2K-9U?t=0) · audio @ 06:08 (https://youtu.be/XNX-1h2K-9U?t=368)
- [ ] **C004**  — Projects/Tools
  - **audio-ref: weak (tools) — slide-only, verify visually** · 
- [ ] **C005** [audio, 00:14] — OpenWiki: A CLI that writes and maintains documentation for AI agents.
  - audio-ref: strong (openwiki, writes) · audio @ 00:14 (https://youtu.be/XNX-1h2K-9U?t=14)
- [ ] **C006** [audio, 00:48] — OpenClaw: Mentioned as a "big thing" from the previous year, related to personal agents.
  - audio-ref: strong (openclaw, related, personal) · audio @ 00:48 (https://youtu.be/XNX-1h2K-9U?t=48)
- [ ] **C007** [slide, 04:19] — npm: Used for installation.
  - **audio-ref: weak (npm) — slide-only, verify visually** · slide @ 04:19 (https://youtu.be/XNX-1h2K-9U?t=259)
- [ ] **C008** [slide, 11:37] — GitHub Actions: Used for scaffolding and scheduled runs.
  - audio-ref: strong (github, actions, scaffolding) · slide @ 11:37 (https://youtu.be/XNX-1h2K-9U?t=697)
- [ ] **C009** [slide, 10:47] — Mermaid: Used for generating diagrams.
  - audio-ref: strong (generating) · slide @ 10:47 (https://youtu.be/XNX-1h2K-9U?t=647)
- [ ] **C010** [audio, 09:08] — Benchmarks: DeepSWE (a coding agent benchmark)
  - audio-ref: strong (benchmarks, deepswe, coding) · audio @ 09:08 (https://youtu.be/XNX-1h2K-9U?t=548)
- [ ] **C011**  — Frameworks/Formats
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C012** [slide, 07:08] — OKF (Open Knowledge Format): Google's standard used by OpenWiki.
  - **audio-ref: weak (google's, okf, open) — slide-only, verify visually** · slide @ 07:08 (https://youtu.be/XNX-1h2K-9U?t=428)
## Numbers & Statistics
- [ ] **C013**  — OpenWiki GitHub Stats (as of video recording)
  - audio-ref: strong (openwiki, github) · 
- [ ] **C014** [slide, 14:59] — 13.5k GitHub stars
  - audio-ref: strong (github) · slide @ 14:59 (https://youtu.be/XNX-1h2K-9U?t=899)
- [ ] **C015** [slide, 14:59] — 900+ forks
  - **audio-ref: weak (forks) — slide-only, verify visually** · slide @ 14:59 (https://youtu.be/XNX-1h2K-9U?t=899)
- [ ] **C016**  — OpenWiki Usage Stats (as of video recording)
  - audio-ref: strong (openwiki) · 
- [ ] **C017** [slide, 14:59] — 20k+ NPM weekly downloads
  - **audio-ref: weak (npm) — slide-only, verify visually** · slide @ 14:59 (https://youtu.be/XNX-1h2K-9U?t=899)
- [ ] **C018**  — Benchmark Results (DeepSWE 20-task subset)
  - audio-ref: strong (benchmark, results, deepswe) · 
- [ ] **C019** [slide, 08:58] — 24% fewer search commands per task on average (from 12.7 to 9.63).
  - audio-ref: strong (search, commands) · slide @ 08:58 (https://youtu.be/XNX-1h2K-9U?t=538)
- [ ] **C020** [slide, 08:58] — 36% fewer `rg --files` calls.
  - **audio-ref: weak (fewer, files) — slide-only, verify visually** · slide @ 08:58 (https://youtu.be/XNX-1h2K-9U?t=538)
- [ ] **C021** [slide, 08:58] — 38% fewer `find` calls.
  - **audio-ref: weak (fewer) — slide-only, verify visually** · slide @ 08:58 (https://youtu.be/XNX-1h2K-9U?t=538)
- [ ] **C022** [slide, 08:58] — 9% less shell result output.
  - audio-ref: strong (result) · slide @ 08:58 (https://youtu.be/XNX-1h2K-9U?t=538)
- [ ] **C023** [audio, 09:40] — Task success rate improved from 7 or 8 successful tasks (out of 20) without the wiki to 9 or 10 with the wiki.
  - audio-ref: strong (success, successful, 20) · audio @ 09:40 (https://youtu.be/XNX-1h2K-9U?t=580)
- [ ] **C024** [audio, 15:18] — Provider Support: The speaker mentions supporting "like 10 or 15 different providers".
  - audio-ref: strong (provider, 10, 15) · audio @ 15:18 (https://youtu.be/XNX-1h2K-9U?t=918)
- [ ] **C025** [audio, 01:09] — Project History: The speaker mentions "memory" has been a research area for "the last four years, three and a half years".
  - audio-ref: strong (history, research) · audio @ 01:09 (https://youtu.be/XNX-1h2K-9U?t=69)
## Verbatim Text & Quotes
- [ ] **C026** [slide, 00:00] — LangSmith Banner: "Observe, evaluate, and deploy your agents"
  - **audio-ref: none — slide-only, verify visually** · slide @ 00:00 (https://youtu.be/XNX-1h2K-9U?t=0)
- [ ] **C027** [slide, 00:23] — OpenWiki Slogan: "A CLI that writes and maintains the docs your agents actually read."
  - audio-ref: strong (openwiki, writes, actually) · slide @ 00:23 (https://youtu.be/XNX-1h2K-9U?t=23)
- [ ] **C028** [slide, 00:40] — Quote from Harrison (LangChain CEO): "What's the next big thing in the agent space that people will actually use? What's this year's OpenClaw?"
  - audio-ref: strong (harrison, people, actually) · slide @ 00:40 (https://youtu.be/XNX-1h2K-9U?t=40)
- [ ] **C029** [slide, 16:33] — Call to Action: "Try it on your worst-documented repo."
  - audio-ref: strong (action) · slide @ 16:33 (https://youtu.be/XNX-1h2K-9U?t=993)
- [ ] **C030** [slide, 04:19] — Installation Command: `npm install -g openwiki`
  - audio-ref: strong (command, install, openwiki) · slide @ 04:19 (https://youtu.be/XNX-1h2K-9U?t=259)
- [ ] **C031** [slide, 16:33] — GitHub Repository URL: `github.com/langchain-ai/openwiki`
  - audio-ref: strong (github, openwiki) · slide @ 16:33 (https://youtu.be/XNX-1h2K-9U?t=993)
## OpenWiki Thesis
- [ ] **C032** [slide, 01:42] — Built for agents: Structure, cross-references, and summaries an agent can parse in one pass.
  - **audio-ref: weak (built) — slide-only, verify visually** · slide @ 01:42 (https://youtu.be/XNX-1h2K-9U?t=102)
- [ ] **C033** [slide, 01:42] — Trivial to set up: One command, `openwiki --init`, picks a provider, reads the repo, and writes the wiki.
  - audio-ref: strong (trivial, command, openwiki) · slide @ 01:42 (https://youtu.be/XNX-1h2K-9U?t=102)
- [ ] **C034** [slide, 01:42] — Updates itself: Drop in a CI workflow and OpenWiki opens its own PR when the code moves.
  - audio-ref: strong (updates, itself, workflow) · slide @ 01:42 (https://youtu.be/XNX-1h2K-9U?t=102)
## Documentation: Humans vs. Agents
- [ ] **C035**  — Written for humans
  - audio-ref: strong (humans) · 
- [ ] **C036**  — Onboarding narrative, read once, top to bottom.
  - audio-ref: strong (onboarding) · 
- [ ] **C037**  — Prose that assumes you remember page 2 by page 9.
  - audio-ref: strong (2) · 
- [ ] **C038**  — Screenshots, tone, and asides carry meaning.
  - audio-ref: strong (screenshots) · 
- [ ] **C039**  — Optimized for skimming and for being findable.
  - audio-ref: strong (optimized) · 
- [ ] **C040**  — Written for agents
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C041**  — Retrieved in fragments, never read end to end.
  - audio-ref: strong (fragments) · 
- [ ] **C042**  — Every concept self-contained, with explicit links out.
  - audio-ref: strong (concept) · 
- [ ] **C043**  — Predictable headings and front matter, so parsing is cheap (OKF spec).
  - audio-ref: strong (predictable, headings, matter) · 
- [ ] **C044**  — Optimized to fit a context window.
  - audio-ref: strong (optimized) · 
## OKF (Open Knowledge Format)
- [ ] **C045** [slide, 07:08], [audio, 07:14] — It is described as "Google's Open Knowledge Format v0.1" (though v0.2 was just released). ,
  - audio-ref: strong (though) · slide @ 07:08 (https://youtu.be/XNX-1h2K-9U?t=428) · audio @ 07:14 (https://youtu.be/XNX-1h2K-9U?t=434)
- [ ] **C046** [slide, 07:08] — Every page carries a YAML front matter with a `type`.
  - audio-ref: strong (matter) · slide @ 07:08 (https://youtu.be/XNX-1h2K-9U?t=428)
- [ ] **C047** [slide, 07:08] — The front matter includes fields like `type`, `title`, `description`, `resource`, `tags`, and `timestamp`.
  - audio-ref: strong (matter, fields, description) · slide @ 07:08 (https://youtu.be/XNX-1h2K-9U?t=428)
- [ ] **C048** [slide, 07:08] — The format is a specification, not an export script, ensuring interoperability.
  - audio-ref: strong (script) · slide @ 07:08 (https://youtu.be/XNX-1h2K-9U?t=428)
## `openwiki --init` Workflow
- [ ] **C049** [slide, 11:37] — configure (Setup wizard): A one-time-per-machine process that picks a provider and model, saves the key to `~/openwiki.env`, and writes the goal to `INSTRUCTIONS.md`. It does not make model calls.
  - audio-ref: strong (configure, wizard, provider) · slide @ 11:37 (https://youtu.be/XNX-1h2K-9U?t=697)
- [ ] **C050** [slide, 11:37] — scaffold (Repo wiring): A deterministic step that sets up the GitHub Actions workflow, `AGENTS.md` + `CLAUDE.md`, and cron defaults. This is re-run on every command.
  - audio-ref: strong (scaffold, deterministic, github) · slide @ 11:37 (https://youtu.be/XNX-1h2K-9U?t=697)
- [ ] **C051** [slide, 11:37] — generate (deepagents): The only "agentic" step. It inventories the repo, reads the git history, plans into `plan.md`, writes `quickstart.md`, and writes the section pages. This is the `core` `write` step.
  - audio-ref: strong (generate, history, writes) · slide @ 11:37 (https://youtu.be/XNX-1h2K-9U?t=697)
- [ ] **C052** [slide, 11:37] — finalize (Deterministic pass): A final step with no model calls. It indexes the `md` per directory, deletes `plan.md`, stamps `last-update.json`, and hashes content. `index.md` is generated and never authored.
  - audio-ref: strong (deterministic, generated) · slide @ 11:37 (https://youtu.be/XNX-1h2K-9U?t=697)
## `openwiki --update` Workflow
- [ ] **C053** [slide, 14:04] — trigger (Scheduled run): Triggered by GitHub Actions daily (`on: schedule: - cron: '0 0 * * *'`), a `workflow_dispatch`, or running locally.
  - audio-ref: strong (scheduled, github, actions) · slide @ 14:04 (https://youtu.be/XNX-1h2K-9U?t=844)
- [ ] **C054** [slide, 14:04] — check (Anything changed?): Compares the current git HEAD vs. `last-update.json`, checks `git status` for dirt, and does a `wiki-only` diff. If there are no changes, it is a no-op with 0 tokens used.
  - audio-ref: strong (anything, changed, current) · slide @ 14:04 (https://youtu.be/XNX-1h2K-9U?t=844)
- [ ] **C055** [slide, 14:04] — generate (deepagents): Runs the same agent with a new pivot, using the `git log` since the last HEAD change. It can edit stale pages, add missing ones, and leave the rest alone. An update can be a no-op.
  - audio-ref: strong (generate, update) · slide @ 14:04 (https://youtu.be/XNX-1h2K-9U?t=844)
- [ ] **C056** [slide, 14:04] — ship it (Pull request): Creates a pull request with an `index.md` diff for review. If there is no diff, it means no PR is created. It supports GitHub and BitBucket PRs.
  - audio-ref: strong (github) · slide @ 14:04 (https://youtu.be/XNX-1h2K-9U?t=844)
## Diagram Types
- [ ] **C057** [slide, 10:47] — Sequence: For runtime and request flows.
  - audio-ref: strong (sequence) · slide @ 10:47 (https://youtu.be/XNX-1h2K-9U?t=647)
- [ ] **C058** [slide, 10:47] — ER (Entity-Relationship): For data models and relationships.
  - **audio-ref: weak (data) — slide-only, verify visually** · slide @ 10:47 (https://youtu.be/XNX-1h2K-9U?t=647)
- [ ] **C059** [slide, 10:47] — State: For lifecycles and transitions.
  - **audio-ref: weak (state) — slide-only, verify visually** · slide @ 10:47 (https://youtu.be/XNX-1h2K-9U?t=647)
- [ ] **C060** [slide, 10:47] — Flowchart: For control flow and branching.
  - audio-ref: strong (flowchart) · slide @ 10:47 (https://youtu.be/XNX-1h2K-9U?t=647)
## Supported Providers
- [ ] **C061**  — OpenAI
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C062**  — Anthropic
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C063**  — Gemini
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C064**  — Bedrock
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C065**  — OpenRouter
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C066**  — Fireworks
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C067**  — Baseten
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C068**  — NVIDIA NIM
  - **audio-ref: none — slide-only, verify visually** · 
- [ ] **C069**  — Any OpenAI-compatible gateway
  - **audio-ref: none — slide-only, verify visually** · 
## License
- [ ] **C070** [slide, 14:59] — The project uses the MIT license.
  - **audio-ref: weak (mit) — slide-only, verify visually** · slide @ 14:59 (https://youtu.be/XNX-1h2K-9U?t=899)
## Files Generated/Maintained by OpenWiki [slide, 11:37]
- [ ] **C071**  — `~/.openwiki/.env` — key storage during setup (3.1-pro only; 1/7 analyses)
  - audio-ref: strong (openwiki, 1) · 
- [ ] **C072**  — `INSTRUCTIONS.md` — hand-written agent brief, written by the setup wizard (1/7 analyses)
  - audio-ref: strong (wizard, 1) · 
- [ ] **C073**  — `log.md` — change log (5/7 analyses independently report it; audio: "change log")
  - audio-ref: strong (change, 5, change) · 
- [ ] **C074**  — `_plan.md` — temporary planning file, deleted during the finalize pass (1/7 analyses)
  - audio-ref: strong (1) · 
- [ ] **C075**  — `.last-update.json` — tracks last-update state for the check step (4/7 analyses)
  - audio-ref: strong (4) · 
- [ ] **C076**  — `index.md` — generated per directory, never authored (5/7 analyses)
  - audio-ref: strong (generated, 5) · 
- [ ] **C077**  — CLI command variant: `openwiki --update --print` [slide]
  - audio-ref: strong (command, openwiki, update) · 
## OpenWiki Modes [slide]
- [ ] **C078**  — Code mode — for a repository
  - **audio-ref: weak (code, mode) — slide-only, verify visually** · 
- [ ] **C079**  — Personal mode — for a local brain built from your own sources
  - audio-ref: strong (personal) · 
## Providers & Tooling [slide]
- [ ] **C080**  — GitLab and Bitbucket — PR targets alongside GitHub (GitLab in 1/7 analyses)
  - audio-ref: strong (github, 1) · 
- [ ] **C081**  — Claude Code (`CLAUDE.md`) — agent-instruction file alongside `AGENTS.md`
  - **audio-ref: weak (agents.md, code, file) — slide-only, verify visually** · 
## Numbers & Statistics
- [ ] **C082**  — 50,000 tokens — example cost of a stray base64 string in an agent tool call [audio]
  - audio-ref: strong (50, 000, tokens) · 
- [ ] **C083**  — 2,000 commits/day — example threshold for increasing update frequency [audio]
  - audio-ref: strong (2, 000, commits) · 
- [ ] **C084**  — 4 / 6 / 8 hours — suggested cron intervals for high-commit repos [audio]
  - audio-ref: strong (4, 6) · 
- [ ] **C085**  — 00:00 — default daily cron time in the generated GitHub Actions workflow [slide]
  - audio-ref: strong (00, 00, default) · 
- [ ] **C086**  — 0 tokens — cost of the no-change path during an update check [slide]
  - audio-ref: strong (0, tokens, update) · 
- [ ] **C087**  — OKF example front matter timestamp: 2024-07-28 [slide]
  - audio-ref: strong (matter, timestamp) · 
- [ ] **C088** [audio, 07:14] — OKF v0.2: released by Google; OpenWiki support "in the next day or so"
  - audio-ref: strong (google, openwiki) · audio @ 07:14 (https://youtu.be/XNX-1h2K-9U?t=434)
## Verbatim Slide Quotes (verify visually; no timestamps in source extraction)
- [ ] **C089**  — "Memory is a big surface. Code is the one place where we felt the pain daily, could judge the output ourselves, and had a clear signal for whether it worked." (echoed by 3.1-flash-lite as "Documentation is the one place..." — a paraphrase, flagged by both judges)
  - audio-ref: strong (output) · 
- [ ] **C090**  — "None of this works if generating the wiki is itself a project. That constraint drove most of the design." (2/7 analyses)
  - audio-ref: strong (generating, itself, 2) · 
- [ ] **C091**  — "Same repo, same facts. Almost none of the same formatting decisions."
  - **audio-ref: weak (repo) — slide-only, verify visually** · 
- [ ] **C092**  — "So we optimized purely for parse cost. Dense, flat, repetitive on purpose — the kind of document you would never hand to a new hire on their first day."
  - audio-ref: strong (optimized, purely, purpose) · 
- [ ] **C093**  — "The most common feedback after launch came from humans using the wiki to onboard onto unfamiliar repos. So it has two audiences now, and it has to work for both without quietly picking a favorite." (4/7 analyses report the two-audiences claim)
  - audio-ref: strong (feedback, humans, onboard) · 
- [ ] **C094**  — "Every concept is typed" / "Links are the graph" / "Indexes are reserved" / "Your fields survive"
  - audio-ref: strong (concept, fields) · 
- [ ] **C095**  — "The practical payoff: the wiki is not locked to OpenWiki. Anything that reads OKF can read it, and the migration path in and out is a spec rather than an export script."
  - audio-ref: strong (anything) · 
- [ ] **C096**  — "Every write is validated for OKF front matter before it lands. Bad front matter comes straight back to the agent as a warning, and it fixes it in the same run."
  - audio-ref: strong (matter, before, matter) · 
- [ ] **C097**  — "Same agent. The interesting part is deciding not to run it." (1/7 analyses)
  - audio-ref: strong (interesting, 1) · 
- [ ] **C098**  — "Merge the PR and the next scheduled run starts from that new HEAD."
  - audio-ref: strong (scheduled, starts) · 
- [ ] **C099**  — "The quality ceiling right now is the prompt, not the model. Most of the bad pages we've seen trace back to us asking for the wrong thing, not the model failing to deliver it." (3/7 analyses quote it verbatim)
  - audio-ref: strong (prompt) · 
- [ ] **C100**  — "Today the agent reads the index and follows links. Real search over the wiki should cut the number of hops it needs, which is what makes very large repos practical."
  - audio-ref: strong (search) · 
- [ ] **C101**  — "If you try it and it writes something dumb, open an issue please!"
  - audio-ref: strong (writes, something) · 
