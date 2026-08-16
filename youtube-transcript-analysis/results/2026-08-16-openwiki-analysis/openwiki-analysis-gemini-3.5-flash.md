# Video Analysis: How We Built OpenWiki

---

## 1. Video Overview

### Title
How We Built OpenWiki

### Speaker
Brace Sproul, Head of Applied AI at LangChain

### Main Topic
Building and optimizing **OpenWiki**, an open-source Command Line Interface (CLI) tool designed to automatically generate, structure, and maintain codebase documentation engineered specifically for consumption by AI coding agents rather than humans.

### Executive Summary
In this presentation, Brace Sproul introduces OpenWiki, a developer tool created to solve the "general-purpose memory" problem for AI agents working on codebases. Unlike traditional documentation intended for human onboarding, OpenWiki generates self-contained, modular Markdown files following Google's **Open Knowledge Format (OKF)**. This structure features deterministic YAML front matter and explicit cross-linking to optimize agent retrieval, reduce LLM search loops, and minimize context window bloat. Sproul details the developer thesis behind the CLI, shows how it implements automatic background maintenance through GitHub Actions (`openwiki --update`), shares performance benchmarks using the DeepSWE evaluation set, and discusses the unexpected human utility that forced them to integrate Mermaid diagram support into the project.

---

## 2. Detailed Topic Map

### Topic 1: What is OpenWiki & Why We Built It
* **Timestamp Range:** 00:00 - 01:42
* **Detailed Explanation:** Sproul introduces OpenWiki as a CLI tool designed to build and maintain the codebase documentation that AI agents actually read. The idea emerged after LangChain's CEO, Harrison Chase, asked what the "next big thing" in the agent space would be. Sproul’s thesis is that **general-purpose memory** is the next major frontier for agents. While LLMs have expanded context windows, they still struggle with synthesizing massive, unstructured knowledge bases. OpenWiki targets codebase documentation as a well-defined starting point to establish structured agent memory.
* **Key Claims:** Codebase memory is highly actionable because developers feel the pain of poorly documented code daily, making output quality easily testable.
* **Terminology:** *General-purpose memory*, *Agent memory space*, *OpenClaw* (previous agent project reference).

### Topic 2: The Core Thesis of OpenWiki
* **Timestamp Range:** 01:42 - 03:04
* **Detailed Explanation:** Sproul outlines the three foundational assumptions behind OpenWiki's design:
  1. **Built for Agents:** The structure, cross-references, and summaries must be readable by an LLM in a single pass.
  2. **Trivial Setup:** Developers will abandon a tool if it is painful to install. Setup requires only two quick commands.
  3. **Self-Updating:** Manual documentation is notoriously fragile and quickly falls out of date. OpenWiki must update itself silently in the background.
* **Why This Matters:** If generating or maintaining documentation becomes "a project in itself" for the developer, the tool fails. The constraints of developer adoption drove the entire system design.

### Topic 3: Human Documentation vs. Agent Documentation
* **Timestamp Range:** 03:04 - 04:19
* **Detailed Explanation:** Traditionally, codebase docs are written as linear, narrative-driven onboarding guides for humans. Sproul explains why this structure is incredibly inefficient for AI agents:
  * **Human Docs:** Structured from top to bottom, filled with visual screenshots, written in conversational prose, and optimized for high-level skimming.
  * **Agent Docs:** Retrieved in random fragments rather than sequentially. Every concept must be isolated and self-contained. They require explicit cross-links, predictable headings, and lightweight formatting optimized for limited, cost-sensitive context windows (e.g., omitting heavy Base64 image strings).
* **Key Claims:** Writing documentation for agents requires completely rethinking how information is chunked and linked.

### Topic 4: CLI Setup and Output Structure
* **Timestamp Range:** 04:19 - 07:08
* **Detailed Explanation:** Sproul demonstrates how to initialize OpenWiki using a single global CLI command:
  1. `npm install -g openwiki` (Global installation)
  2. `openwiki --init` (Initializes configuration)
  The setup wizard asks the developer to pick their LLM provider, enter their API key, and configure their "Wiki Brief" (high-level instructions on how the agent should navigate the unique properties of the repository). 
  Once initialized, OpenWiki reads the repository and generates a structured directory `/openwiki` containing:
  * `index.md`: The root index declaring the schema version and file mappings.
  * Modular files (one per codebase concept) mapped inside subdirectories like `/architecture`, `/operations`, and `/workflows`.
  * `instructions.json` and an updated `agents.md` / `CLAUDE.md` to instruct incoming coding agents to consult OpenWiki.
* **Supporting Examples:** An interactive terminal demo showing OpenWiki reading a codebase and mapping out code relations.

### Topic 5: Standardizing with Google's Open Knowledge Format (OKF)
* **Timestamp Range:** 07:08 - 08:57
* **Detailed Explanation:** To allow any third-party agent to read OpenWiki files seamlessly, the tool adopts Google's **Open Knowledge Format (OKF)**. Under OKF, every markdown document contains strict YAML front matter containing key-value metadata pairs.
* **Key Fields:** 
  * `type`: (e.g., architecture, operations)
  * `title`: Descriptive topic name.
  * `description`: One-sentence summary of the file's scope.
  * `resources`: Explicit file paths in the codebase that this doc references (e.g., `src/agent/index.ts`).
  * `tags`: Array of labels for filtering.
  * `timestamp`: Date/time of generation.
* **Why It Matters:** Having highly standardized, searchable YAML front matter makes document filtering and retrieval incredibly cheap and deterministic for the LLM. It transforms document search from a fuzzy semantic search task into a clean structured database query.

### Topic 6: Performance Evaluations (DeepSWE Benchmarks)
* **Timestamp Range:** 08:57 - 10:09
* **Detailed Explanation:** To prove that agent-optimized documentation actually improves performance, Sproul and his team ran evaluations using a 20-task subset of **DeepSWE** (a benchmark evaluating AI agents on real-world software engineering issues). They ran the agent with and without the generated OpenWiki directories.
* **Key Statistics:**
  * **24% fewer search commands** executed per task.
  * **36% fewer file-grepping (`rg --files`) calls**.
  * **38% fewer file `find` calls**.
  * **9% reduction in raw shell output text** returned to the LLM.
  * **Token & Success Improvements:** Baseline task success rose from 7-8 solved tasks (without OpenWiki) to 9-10 solved tasks (with OpenWiki), achieved alongside a major reduction in overall token costs.

### Topic 7: Lessons Learned: Humans Read Agent Docs Too
* **Timestamp Range:** 10:09 - 11:35
* **Detailed Explanation:** OpenWiki's creators originally assumed that *only* agents would read these documents, allowing them to make the text incredibly flat, dry, and highly repetitive for cost efficiency. However, early beta users quickly started using the OpenWiki folder to onboard *human* developers to unfamiliar repositories.
* **The Solution:** Because the tool now serves two audiences, the team added support for **Mermaid diagrams**. The agent automatically generates sequence, entity-relationship (ER), state, and flowcharts directly inside the markdown files, vastly improving human comprehension without adding overhead for the LLM.

### Topic 8: Under the Hood: `init` and `update` Workflows
* **Timestamp Range:** 11:35 - 14:58
* **Detailed Explanation:** Sproul walks through the dual-command workflow engines:
  * **`openwiki --init` Workflow:**
    1. *Setup Wizard*: Configures API keys, LLM selections, and custom instructions.
    2. *Repo Wiring*: Scaffolds Github Action workflows and updates `agents.md`.
    3. *Deepagents Generation*: A specialized agent inspects current code, parses the repository's git history (commit logs, PR descriptions) to capture context, plans a doc schema, and writes raw pages.
    4. *Finalize*: Runs a deterministic pass to construct clean indices and content hash lists.
  * **`openwiki --update` Workflow:**
    Designed to run daily or on a cron cycle inside GitHub Actions:
    1. *Check*: Compares current HEAD state with the recorded hashes in `last-update.json` (runs entirely locally/deterministically; costs **0 LLM tokens** if no changes are found).
    2. *Plan*: If changes exist, it extracts git diffs and logs since the last update.
    3. *Diff/Write*: The agent edits only the specific files impacted by the code changes.
    4. *PR generation*: Automatically packages and pushes a Pull Request back to the main repository.

### Topic 9: Current Status & What's Next
* **Timestamp Range:** 14:58 - end
* **Detailed Explanation:** OpenWiki is MIT-licensed and fully open-source. Sproul closes the presentation with current community statistics and outlines future goals: developing better agent prompting structures for large scale repositories and engineering native search/retrieval tools specifically paired with the OKF structure.

---

## 3. Key Points in Detail

### Point 1: Rethinking Documentation Structure for Non-Human Readers
* **Explanation:** Standard developer documentation prioritizes narrative flow, developer empathy, and quick tutorials. AI agents do not read linearly; they parse files dynamically based on search queries. 
* **Evidence:** Sproul contrasts human onboarding narratives with agent-optimized fragmentation. Agents require modular, self-contained concepts where any file can be read in isolation without losing context.
* **Practical Implication:** When building directories for agent usage, developers must enforce rigid schemas, limit narrative fluff, and rely heavily on descriptive YAML headers to avoid wasting context windows and inflating token costs.

### Point 2: The Critical Role of Repository History in Code Understanding
* **Explanation:** Simply analyzing a static snapshot of a codebase is insufficient for an agent to write highly accurate documentation. Understanding *why* certain architectural choices were made requires exploring temporal context.
* **Evidence:** The OpenWiki `init` and `update` engines are designed to read the git commit history and pull request logs to contextualize code modifications.
* **Practical Implication:** When configuring AI tools for codebase understanding, ensuring the agent has access to version control history (git logs) yields far richer documentation than standard file parsing.

### Point 3: Minimizing CI Token Overhead through State Verification
* **Explanation:** Running LLM calls on every single repository commit or pull request to check for documentation updates is prohibitively expensive.
* **Evidence:** OpenWiki utilizes a lightweight file named `last-update.json` that stores code hashes. The `openwiki --update` cron script first runs a local git status check. If the code hashes match, the script immediately exits without making a single external API call.
* **Practical Implication:** Always build a deterministic local check (such as content hashing or git diff checks) ahead of your LLM pipelines to keep continuous integration costs negligible.

---

## 4. Frameworks, Models, or Processes

### Google's Open Knowledge Format (OKF)
OpenWiki relies on OKF to construct highly parseable, deterministic files for external AI agents.

```
+--------------------------------------------------------------+
|                         OKF Schema                           |
+--------------------------------------------------------------+
|  ---                                                         |
|  type: [architecture | operations | workflows]               |
|  title: "Topic Name"                                         |
|  description: "One sentence summary"                          |
|  resources: ["src/path/to/file.ts"]                          |
|  tags: ["tag1", "tag2"]                                      |
|  timestamp: 2026-07-28                                       |
|  ---                                                         |
|                                                              |
|  ## Markdown Content (with explicit cross-links)             |
|                                                              |
+--------------------------------------------------------------+
```

* **When to use:** Use this structured metadata standard whenever you are generating Markdown documents meant to be systematically queried, filtered, and parsed by semantic search agents or LLM tools.

### The `openwiki --update` Process

```
                      [Trigger scheduled Github cron]
                                     │
                                     ▼
                   [Check git status / last-update.json]
                                     │
                   ┌─────────────────┴─────────────────┐
          (No changes found)                   (Changes found)
                   │                                   │
                   ▼                                   ▼
          [Exit: 0 Token Cost]                [Fetch git diff & logs]
                                                       │
                                                       ▼
                                            [Plan and edit OKF docs]
                                                       │
                                                       ▼
                                            [Compile index & log.md]
                                                       │
                                                       ▼
                                            [Generate Pull Request]
```

---

## 5. Concrete Examples and Case Studies

### DeepSWE Case Study
* **What Happened:** The LangChain team ran an agent over a 20-task software engineering benchmark comparing performance with and without OpenWiki docs.
* **What it Illustrates:** Standard agents spend immense amounts of context and execution time executing manual file discovery commands (`find`, `grep`, `rg`) when dropped into raw codebases.
* **The Lesson:** Providing a pre-computed, structured index (OpenWiki) allows agents to skip manual exploration cycles, leading to a **24% reduction in overall search queries** and preventing the context window from being cluttered with redundant file pathways.

### The Mermaid Diagram Integration
* **What Happened:** Although designed purely for AI agents, real-world users immediately used OpenWiki files for human onboarding. This prompted the development team to add automatic Mermaid diagram rendering.
* **What it Illustrates:** Code visualizers are highly effective bridge formats. Mermaid charts are written in structured plain text (making them highly efficient for LLMs to output) but render as complex architectural graphics for humans.
* **The Lesson:** When designing tools for LLMs, look for clean text-based schemas (like Markdown and Mermaid) that translate efficiently to both machine processing and human visualization.

---

## 6. Actionable Takeaways

### Immediate Actions
* **Install OpenWiki:** Run `npm install -g openwiki` to explore the CLI locally.
* **Initialize Codebase Wiki:** Navigate to your most poorly documented repository and execute `openwiki --init` to generate agent-ready guides.
* **Inject into Agent Profiles:** Ensure your `.cursorrules`, `agents.md`, or `CLAUDE.md` files explicitly direct your coding assistants to read the `/openwiki` folder first.

### Strategic Actions
* **Incorporate OKF into Internal Tooling:** Standardize all internal team knowledge bases and system design documents using Google's Open Knowledge Format schemas to ensure compatibility with future enterprise search agents.
* **Build Deterministic Filters for LLM Pipelines:** Implement hash checks (`last-update.json` style) in all developer-facing LLM cron actions to prevent runaway API billing cycles.

### Questions to Investigate Further
* How can semantic vector databases be natively paired with structured OKF documents to minimize search-hop latency?
* Can agent-optimized documentation standards be extended automatically to parse microservice boundaries across separate repositories?

---

## 7. Claims Worth Verifying

* **DeepSWE Performance Metrics:** The reported statistics (24% fewer search commands, 36% fewer `rg` calls, 38% fewer `find` calls) are based on a small 20-task subset and should be benchmarked across larger, multi-repository test frameworks.
* **Google's OKF Version Support:** Sproul references the transition from OKF v0.1 to v0.2. Developers should verify current support status and specification details of Google's Open Knowledge Format project on GitHub.
* **Star and Fork Metrics:** The slides show "13.5k GitHub stars, 900+ forks, 20k+ weekly npm downloads." This likely references parent repository statistics (such as LangChain templates) and should be verified for the standalone `openwiki` package.

---

## 8. Notable Quotes

* *"General-purpose memory is finally possible. Models got long enough context and good enough at synthesis that maintaining a knowledge base stopped being a research project."* (01:04)
* *"People use agents for everything nowadays... which means these docs should be built specifically for agents to consume."* (02:03)
* *"Generating docs is fairly easy with agents. Retrieving from these docs is a lot more difficult."* (08:12)
* *"Only agents would read it... that was our assumption. But very quickly we found out: people read it too."* (10:10)

---

## 9. Final Compressed Summary

### 5-Bullet Summary
* **Agent-First Design:** OpenWiki is a CLI that builds codebase documentation optimized for AI agents, focusing on modularity, flat structures, and explicit cross-linking rather than sequential onboarding narratives.
* **OKF Schema Integration:** The tool utilizes Google's Open Knowledge Format, embedding deterministic YAML front matter headers into files so LLMs can execute fast, cheap, database-style queries.
* **0-Token Update Verification:** The CLI utilizes a GitHub Actions workflow that performs local file hash checks, ensuring the update process costs zero LLM tokens when no code changes are detected.
* **Proven Efficiency Gains:** Testing on the DeepSWE benchmark demonstrated up to a 38% drop in resource-intensive file search commands and a 24% reduction in overall semantic search loops.
* **Human-Agent Hybrid Utility:** Due to human developers using the generated files for manual codebase onboarding, OpenWiki automatically generates Mermaid flowcharts to serve both developer audiences.

### 10 Keywords/Tags
OpenWiki, AI Agents, Codebase Documentation, Google OKF, YAML Front Matter, DeepSWE Benchmark, LLM Token Optimization, GitHub Actions CI, Mermaid Diagrams, LangChain

### One-Sentence Core Insight
To maximize the accuracy and cost-efficiency of AI coding assistants, codebases must be documented using modular, self-contained Markdown files featuring deterministic metadata headers designed for non-linear agent retrieval.