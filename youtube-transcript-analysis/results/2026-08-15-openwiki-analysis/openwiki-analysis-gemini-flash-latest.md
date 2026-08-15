# OpenWiki: AI Agent-Focused Codebase Documentation & Memory

---

## 1. Video Overview

- **Title:** How We Built OpenWiki: A CLI that writes and maintains the docs your agents actually read
- **Speaker / Channel:** Brace Sproul (Head of Applied AI at LangChain) / LangChain
- **Main Topic:** Building an automated, self-maintaining codebase wiki and general-purpose memory system tailored specifically for AI coding agents.
- **Executive Summary:** Brace Sproul presents OpenWiki, an open-source CLI tool designed to solve codebase memory and context management for AI agents. Rather than designing documentation for human narrative reading, OpenWiki structures Markdown docs using Google's Open Knowledge Format (OKF) so AI agents can retrieve isolated, predictable, cross-linked snippets within tight context windows. The tool automatically scaffolds integration hooks (`AGENTS.md`, `CLAUDE.md`, CI/CD workflows via GitHub Actions), updates documentation incrementally from Git history changes, and demonstrably reduces agent token usage and redundant codebase search operations.
- **Purpose:** To explain the architecture, design decisions, format choices (OKF), empirical benchmark results, unexpected user feedback, and future roadmap of OpenWiki.

---

## 2. Detailed Topic Map

### Topic 1: Introduction & What is OpenWiki
- **Timestamp Range:** 00:00 – 00:39
- **Detailed Explanation:** Introduction to OpenWiki as an open-source CLI tool that generates and maintains repository documentation explicitly optimized for AI agent consumption rather than traditional human documentation.
- **Key Claims:** Agent-facing documentation requires a fundamentally different architecture and format than human-facing documentation.
- **Important Terminology:** CLI, Agent-first documentation, Knowledge base.
- **Why It Matters:** Modern AI coding agents struggle with navigating large, unfamiliar codebases without concise, well-indexed context.

---

### Topic 2: Origin & Why We Built It
- **Timestamp Range:** 00:39 – 01:42
- **Detailed Explanation:** Originating from an inquiry by LangChain CEO Harrison Chase regarding the next breakthrough in the agent space, general-purpose memory was identified as the frontier. Large language models (LLMs) have achieved sufficient context windows and synthesis capability to maintain knowledge bases. Codebase documentation was chosen as the initial test ground because it is a concrete, high-pain area with clear success signals.
- **Key Claims:** General-purpose memory for agents is transitioning from an academic research problem to practical production utility.
- **Why It Matters:** Memory remains one of the largest unsolved operational surfaces for autonomous agents.

---

### Topic 3: The Three Thesis Bets
- **Timestamp Range:** 01:42 – 03:04
- **Detailed Explanation:** The design of OpenWiki rests on three core tenets:
  1. *Built for agents:* Structured, cross-referenced, modular files parsed in single passes.
  2. *Trivial to set up:* A zero-friction CLI onboarding flow (`openwiki --init`) requiring single-command execution.
  3. *Updates itself:* Autonomous incremental updates via CI/CD workflows opening PRs when code shifts.
- **Key Claims:** If generating and maintaining the wiki feels like an active manual chore, developers will abandon it.
- **Why It Matters:** Tooling friction and stale documentation are the primary causes of project documentation failure.

---

### Topic 4: Docs for Agents vs. Docs for Humans
- **Timestamp Range:** 03:04 – 04:19
- **Detailed Explanation:** A side-by-side contrast between human-targeted and agent-targeted documentation:
  - *Human docs:* Linear onboarding narratives, top-to-bottom reading, prose assuming prior context, screenshots/videos, optimized for scanning.
  - *Agent docs:* Non-linear fragment retrieval, strictly self-contained concepts, explicit Markdown links for relational graphs, predictable YAML frontmatter for cheap parsing, and context-window token optimization.
- **Key Claims:** Agents do not read docs end-to-end; they pull granular, isolated snippets into prompt context.
- **Important Terminology:** Context window optimization, Fragment retrieval, OKF spec.
- **Why It Matters:** Feeding narrative prose or multi-modal UI guides into LLM context wastes tokens and causes hallucination or confusion.

---

### Topic 5: Onboarding & Setup Workflow (`openwiki --init`)
- **Timestamp Range:** 04:19 – 05:13
- **Detailed Explanation:** Overview of the single-command CLI setup via `npm install -g openwiki` and `openwiki --init`. The CLI prompts for model/provider choice, API keys, and custom brief instructions, then inspects the repository and generates all required scaffolding.
- **Key Claims:** Developer tool adoption is strictly tied to setup friction.
- **Supporting Files Generated:** `AGENTS.md`, `CLAUDE.md`, `.github/workflows/openwiki.yml`, and `openwiki/` folder structure.
- **Why It Matters:** Standardizing agent instruction files (`AGENTS.md`) ensures coding assistants immediately know where to find repo architecture context.

---

### Topic 6: Anatomy of Generated Files & Open Knowledge Format (OKF)
- **Timestamp Range:** 05:13 – 08:57
- **Detailed Explanation:** Detailed breakdown of the OpenWiki directory layout:
  - `openwiki/index.md`: Root index declaring OKF spec version and top-level directory links.
  - `quickstart.md`: Entry point summarizing repo architecture and routing agents to specific modules.
  - `log.md`: Chronological changelog tracking repo evolution and wiki updates over time.
  - Granular Markdown pages: Split into subdirectories (e.g., `architecture/`, `operations/`, `workflows/`) containing strictly one concept per file.
  - **OKF (Google Open Knowledge Format):** Strict YAML front matter specifying `type`, `title`, `description`, `resources` (file associations), `tags`, and `timestamp`.
- **Key Claims:** OKF front matter enables deterministic filtering, sorting, and cheap parsing before loading full file contents into LLM context.
- **Important Terminology:** Google Open Knowledge Format (OKF v0.1 / v0.2), Front matter, Relational Markdown linking.
- **Why It Matters:** Explicit cross-linking allows agents to traverse codebase concepts as a graph rather than performing brute-force keyword searches.

---

### Topic 7: Empirical Evidence & Benchmark Results
- **Timestamp Range:** 08:57 – 10:09
- **Detailed Explanation:** Benchmark evaluations using a 20-task subset of DeepSWE (a software engineering agent benchmark) comparing an agent running without OpenWiki vs. with OpenWiki.
- **Key Claims / Metric Improvements:**
  - **24% reduction** in total search commands executed per task (12.7 $\rightarrow$ 9.63).
  - **36% fewer** `rg --files` (ripgrep) calls.
  - **38% fewer** `find` system calls.
  - **9% reduction** in raw shell output volume.
  - Higher task success rate (from 7–8 successful tasks up to 9–10 out of 20).
- **Why It Matters:** Validates that structured external documentation directly improves agent execution efficiency and reduces token consumption costs.

---

### Topic 8: Learnings & Humans as Dual Audience
- **Timestamp Range:** 10:09 – 11:35
- **Detailed Explanation:** The initial assumption that *only* agents would read these docs was proven false by user feedback. Developers used OpenWiki to onboard themselves onto unfamiliar repositories. To accommodate human comprehension without breaking agent parsing, OpenWiki incorporated inline Mermaid diagrams (sequence, ER, state, and flowchart diagrams).
- **Key Claims:** External documentation tools must serve a dual audience: machines (for automated tasks) and humans (for verification and onboarding).
- **Important Terminology:** Mermaid.js diagrams, Sequence flows, Entity-Relationship (ER) models.
- **Why It Matters:** Visual diagrams provide high-density summaries for human eyes while remaining plain text for LLM parsing.

---

### Topic 9: Under the Hood: `openwiki --init` and `openwiki --update` Workflows
- **Timestamp Range:** 11:35 – 14:58
- **Detailed Explanation:** 
  - **`openwiki --init`:** 4-step pipeline: (1) Setup wizard (config, provider, keys, instructions), (2) Repo scaffolding (`AGENTS.md`, `.github/workflows`), (3) Agent generation pass (analyzes code & Git history, writes section pages), (4) Final deterministic pass (validates OKF front matter, builds `index.md` per directory, computes content hash stamps in `last-update.json`).
  - **`openwiki --update`:** Triggered via cron or CLI. Checks `git diff` against `last-update.json`. If no changes, exits cleanly at zero token cost. If changes exist, runs an agent diff planner, updates only affected docs, increments `log.md`, and opens a pull request.
- **Why It Matters:** The `last-update.json` no-op check prevents unnecessary LLM API spend during automated daily cron runs.

---

### Topic 10: Project Status & Future Roadmap
- **Timestamp Range:** 14:58 – 16:51
- **Detailed Explanation:** 
  - *Current Status:* MIT License, 13.5k+ GitHub stars, 900+ forks, 20k+ weekly NPM downloads. Supports models across OpenAI, Anthropic, Gemini, AWS Bedrock, OpenRouter, Fireworks, Baseten, NVIDIA NIM, and local OpenAI-compatible endpoints.
  - *Roadmap Items:* Better agent prompt engineering for large repos, OKF v0.2 spec adoption, and dedicated search/retrieval agent tools (e.g., custom tool-calling endpoints to reduce wiki hop counts).
- **Why It Matters:** Transitioning from passive text injection (`AGENTS.md`) to active tool calling makes querying massive repositories practical.

---

## 3. Key Points in Detail

### 1. Agent Documentation is Structurally Distinct from Human Documentation
- **Explanation:** Human documentation relies on narrative continuity, linear progression, screenshots, and tutorials. Agent documentation requires atomicity (each file is self-contained), explicit graph links, predictable metadata schemas (YAML front matter), and strict token budget awareness.
- **Evidence:** Agents fetch doc fragments dynamically rather than reading top-to-bottom; linear prose leads to wasted tokens and missing context.
- **Practical Implication:** Do not feed human-oriented tutorial pages or UI walkthroughs directly to coding agents. Convert documentation into modular, typed concept files.

### 2. General-Purpose Memory Starts with Structured Codebase Docs
- **Explanation:** Memory for autonomous agents has long been restricted to academic research. Codebase documentation represents a bounded, objective domain where inputs (Git commits, file trees) and outputs (agent task success, reduced token usage) can be evaluated deterministically.
- **Evidence:** OpenWiki acts as persistent externalized repository memory that survives agent session resets.
- **Practical Implication:** Treat repository documentation as a shared persistent cache between developer and agent.

### 3. Automated Self-Maintenance via Git History
- **Explanation:** Documentation rot happens because keeping docs current requires manual effort. OpenWiki ties maintenance into Git history and CI/CD workflows.
- **Evidence:** Using `git log` and `last-update.json` tracking, the `--update` command runs on a schedule, detects new commits, updates only the affected wiki files, and creates a GitHub pull request.
- **Practical Implication:** Automate wiki synchronization via GitHub Actions or GitLab CI to ensure agents never work from obsolete architectural assumptions.

### 4. OKF (Open Knowledge Format) Solves Agent Retrieval Bottlenecks
- **Explanation:** Google's Open Knowledge Format enforces standardized YAML front matter (`type`, `title`, `description`, `resources`, `tags`, `timestamp`).
- **Evidence:** Allows an agent to cheaply scan top-level directory indices (`index.md`) and filter documents by type or resource file association without loading the full text of every page into the context window.
- **Practical Implication:** Adopt standardized metadata schemas across internal documentation to simplify programmatic agent search and retrieval.

---

## 4. Frameworks, Models, and Processes

### 1. Open Knowledge Format (OKF) Metadata Model
- **Description:** A metadata standard developed by Google for machine-readable knowledge bases.
- **Components:**
  - `type`: Category of documentation (e.g., `architecture`, `operations`, `workflows`).
  - `title`: Short descriptive name of the concept.
  - `description`: Plain-text summary of what the document covers.
  - `resources`: Array of explicit codebase file paths tied to this concept (e.g., `src/agent/index.ts`).
  - `tags`: Freeform keyword taxonomy for faceted search.
  - `timestamp`: Generation/update date (e.g., `2026-07-28`).
- **When to Use:** Whenever generating Markdown-based knowledge stores designed for LLM indexing and selective retrieval.

---

### 2. OpenWiki Dual-Command Lifecycle
```
[openwiki --init]
   │
   ├── 1. Setup Wizard (Provider, Keys, Instructions)
   ├── 2. Scaffolding (AGENTS.md, CLAUDE.md, GitHub Actions)
   ├── 3. Deep Agent Synthesis (Reads code + Git history -> Generates docs)
   └── 4. Deterministic Pass (Validates OKF, builds index.md, writes last-update.json)

[openwiki --update] (Scheduled / CI Trigger)
   │
   ├── Check Git changes against last-update.json
   │      ├── No changes ──> Exit (No-Op, 0 token cost)
   │      └── Changes found
   │             │
   │             ├── Deep Agent Plan & Diff
   │             ├── Incremental Doc Edits & log.md update
   │             └── Open GitHub Pull Request
```

---

## 5. Concrete Examples and Case Studies

### DeepSWE Benchmark Evaluation
- **Context:** LangChain tested coding agent performance on a 20-task subset of the DeepSWE benchmark with and without OpenWiki.
- **Results:**
  - Search tool calls (`rg --files`) decreased by 36%.
  - System `find` calls decreased by 38%.
  - Overall search commands reduced from 12.7 to 9.63 per task (24% reduction).
  - Shell output bloat decreased by 9%.
  - Task completion rose from ~7–8 successful tasks to ~9–10 out of 20.
- **Lesson:** Providing structured, cross-linked architectural docs reduces exploratory search overhead, directly lowering API latency, token costs, and compounding error rates.

---

## 6. Actionable Takeaways

### Immediate Actions
1. Install OpenWiki globally: `npm install -g openwiki`.
2. Initialize OpenWiki in your primary repository: `openwiki --init`.
3. Choose your preferred LLM provider (OpenAI, Anthropic, Gemini, Bedrock, Fireworks, local endpoints).
4. Review and merge the generated `openwiki/`, `AGENTS.md`, and GitHub Actions workflow files.

### Strategic Actions
1. **Implement `AGENTS.md` Standards:** Use standardized agent context pointers in repositories so tools like Cursor, Claude Code, and custom LangChain agents know where architectural references live.
2. **Automate CI Documentation PRs:** Enable the GitHub Action workflow to regularly submit automated documentation update PRs based on merged commits.
3. **Audit Token Spend in Agent Workflows:** Measure whether agents are over-indexing on brute-force search commands (`ripgrep`, directory listings) and provide pre-indexed wikis to truncate their search tree.

### Questions to Investigate Further
- How can custom tool calling (e.g., OpenWiki MCP server or vector index) further reduce the hops an agent needs to resolve a query?
- What are the scaling characteristics of OpenWiki on mono-repos containing millions of lines of code?
- How does OKF v0.2 improve over v0.1 in terms of taxonomy and validation?

---

## 7. Claims Worth Verifying

- **DeepSWE Benchmark Performance:** The claim of a 24% reduction in search commands and improvement from 7–8 to 9–10 task completions on a 20-task DeepSWE subset.
- **OKF v0.2 Release Details:** The release and feature specification differences between Google Open Knowledge Format v0.1 and v0.2.
- **Repository Statistics:** GitHub star count (13.5k+), forks (900+), and weekly NPM downloads (20k+) as of the presentation date.

---

## 8. Notable Quotes

> *"General-purpose memory is finally possible. Models got long enough context and good enough at synthesis that maintaining a knowledge base stopped being a research project."* — **Brace Sproul** (00:40)

> *"None of this works if generating the wiki is itself a project."* — **Brace Sproul** (01:43)

> *"People use agents for everything nowadays. You're probably not writing a ton of code manually anymore... which means these docs should be built specifically for agents to consume."* — **Brace Sproul** (02:03)

> *"Generating docs is fairly easy with agents. Retrieving from these docs is a lot more difficult."* — **Brace Sproul** (08:12)

---

## 9. Final Compressed Summary

### 5-Bullet Summary
- **Agent-First Architecture:** OpenWiki is an open-source CLI that builds and maintains codebase documentation designed for LLM agent consumption rather than traditional human reading.
- **OKF Standard Compliance:** Documentation is formatted using Google's Open Knowledge Format with strict YAML front matter and explicit relational Markdown links to enable fast, token-efficient snippet retrieval.
- **Zero-Friction & Self-Updating:** Single-command setup (`openwiki --init`) scaffolds all necessary configs and installs CI/CD cron jobs (`openwiki --update`) that open automated pull requests as code changes.
- **Empirically Proven Efficiency:** Benchmarks on DeepSWE demonstrated a 24% drop in agent search commands, over 36% fewer file search calls, and higher task success rates.
- **Dual Human/Agent Usability:** In response to human developers using the wiki for onboarding, OpenWiki automatically generates inline Mermaid diagrams without breaking LLM readability.

### 10 Keywords / Tags
1. OpenWiki
2. AI Coding Agents
3. LangChain
4. Open Knowledge Format (OKF)
5. General-Purpose Memory
6. Codebase Documentation
7. DeepSWE Benchmark
8. Context Window Optimization
9. Mermaid.js Diagrams
10. Developer Tooling

### Core Insight
By replacing narrative, human-centric documentation with modular, typed, and self-updating knowledge graphs (OKF), developers can provide AI agents with a persistent memory layer that significantly cuts context costs and eliminates repetitive codebase exploration.