Here is a structured fact sheet containing all factual claims from the video.

### Names & Entities

*   **Speaker:** Brace Sproul, Head of Applied AI, LangChain [slide, 00:08]
*   **People Mentioned:** Sean [audio, 00:11], Harrison (LangChain CEO) [audio, 00:42], Karpathy [audio, 05:17]
*   **Companies/Organizations:** LangChain [slide, 00:08], LangSmith [slide, 00:00], Google [audio, 06:08]
*   **Projects/Tools:**
    *   **OpenWiki:** A CLI that writes and maintains documentation for AI agents. [audio, 00:14]
    *   **OpenClaw:** Mentioned as a "big thing" from the previous year, related to personal agents. [audio, 00:48]
    *   **npm:** Used for installation. [slide, 04:19]
    *   **GitHub Actions:** Used for scaffolding and scheduled runs. [slide, 11:37]
    *   **Mermaid:** Used for generating diagrams. [slide, 10:47]
*   **Benchmarks:** DeepSWE (a coding agent benchmark) [audio, 09:08]
*   **Frameworks/Formats:**
    *   **OKF (Open Knowledge Format):** Google's standard used by OpenWiki. [slide, 07:08]

### Numbers & Statistics

*   **OpenWiki GitHub Stats (as of video recording):**
    *   **13.5k** GitHub stars [slide, 14:59]
    *   **900+** forks [slide, 14:59]
*   **OpenWiki Usage Stats (as of video recording):**
    *   **20k+** NPM weekly downloads [slide, 14:59]
*   **Benchmark Results (DeepSWE 20-task subset):**
    *   **24%** fewer search commands per task on average (from 12.7 to 9.63). [slide, 08:58]
    *   **36%** fewer `rg --files` calls. [slide, 08:58]
    *   **38%** fewer `find` calls. [slide, 08:58]
    *   **9%** less shell result output. [slide, 08:58]
    *   Task success rate improved from **7 or 8** successful tasks (out of 20) without the wiki to **9 or 10** with the wiki. [audio, 09:40]
*   **Provider Support:** The speaker mentions supporting "like 10 or 15 different providers". [audio, 15:18]
*   **Project History:** The speaker mentions "memory" has been a research area for "the last four years, three and a half years". [audio, 01:09]

### Verbatim Text & Quotes

*   **LangSmith Banner:** "Observe, evaluate, and deploy your agents" [slide, 00:00]
*   **OpenWiki Slogan:** "A CLI that writes and maintains the docs your agents actually read." [slide, 00:23]
*   **Quote from Harrison (LangChain CEO):** "What's the next big thing in the agent space that people will actually use? What's this year's OpenClaw?" [slide, 00:40]
*   **Call to Action:** "Try it on your worst-documented repo." [slide, 16:33]
*   **Installation Command:** `npm install -g openwiki` [slide, 04:19]
*   **GitHub Repository URL:** `github.com/langchain-ai/openwiki` [slide, 16:33]

### Technical Details, Lists, and Frameworks

#### OpenWiki Thesis
The project's thesis has three main points:
1.  **Built for agents:** Structure, cross-references, and summaries an agent can parse in one pass. [slide, 01:42]
2.  **Trivial to set up:** One command, `openwiki --init`, picks a provider, reads the repo, and writes the wiki. [slide, 01:42]
3.  **Updates itself:** Drop in a CI workflow and OpenWiki opens its own PR when the code moves. [slide, 01:42]

#### Documentation: Humans vs. Agents
The slide at [03:04] contrasts documentation styles:
*   **Written for humans:**
    *   Onboarding narrative, read once, top to bottom.
    *   Prose that assumes you remember page 2 by page 9.
    *   Screenshots, tone, and asides carry meaning.
    *   Optimized for skimming and for being findable.
*   **Written for agents:**
    *   Retrieved in fragments, never read end to end.
    *   Every concept self-contained, with explicit links out.
    *   Predictable headings and front matter, so parsing is cheap (OKF spec).
    *   Optimized to fit a context window.

#### OKF (Open Knowledge Format)
*   It is described as "Google's Open Knowledge Format v0.1" (though v0.2 was just released). [slide, 07:08], [audio, 07:14]
*   Every page carries a YAML front matter with a `type`. [slide, 07:08]
*   The front matter includes fields like `type`, `title`, `description`, `resource`, `tags`, and `timestamp`. [slide, 07:08]
*   The format is a specification, not an export script, ensuring interoperability. [slide, 07:08]

#### `openwiki --init` Workflow
The initialization process consists of four main steps:
1.  **configure (Setup wizard):** A one-time-per-machine process that picks a provider and model, saves the key to `~/openwiki.env`, and writes the goal to `INSTRUCTIONS.md`. It does not make model calls. [slide, 11:37]
2.  **scaffold (Repo wiring):** A deterministic step that sets up the GitHub Actions workflow, `AGENTS.md` + `CLAUDE.md`, and cron defaults. This is re-run on every command. [slide, 11:37]
3.  **generate (deepagents):** The only "agentic" step. It inventories the repo, reads the git history, plans into `plan.md`, writes `quickstart.md`, and writes the section pages. This is the `core` `write` step. [slide, 11:37]
4.  **finalize (Deterministic pass):** A final step with no model calls. It indexes the `md` per directory, deletes `plan.md`, stamps `last-update.json`, and hashes content. `index.md` is generated and never authored. [slide, 11:37]

#### `openwiki --update` Workflow
The update process consists of four main steps:
1.  **trigger (Scheduled run):** Triggered by GitHub Actions daily (`on: schedule: - cron: '0 0 * * *'`), a `workflow_dispatch`, or running locally. [slide, 14:04]
2.  **check (Anything changed?):** Compares the current git HEAD vs. `last-update.json`, checks `git status` for dirt, and does a `wiki-only` diff. If there are no changes, it is a no-op with 0 tokens used. [slide, 14:04]
3.  **generate (deepagents):** Runs the same agent with a new pivot, using the `git log` since the last HEAD change. It can edit stale pages, add missing ones, and leave the rest alone. An update can be a no-op. [slide, 14:04]
4.  **ship it (Pull request):** Creates a pull request with an `index.md` diff for review. If there is no diff, it means no PR is created. It supports GitHub and BitBucket PRs. [slide, 14:04]

#### Diagram Types
OpenWiki added support for four types of diagrams using Mermaid:
1.  **Sequence:** For runtime and request flows. [slide, 10:47]
2.  **ER (Entity-Relationship):** For data models and relationships. [slide, 10:47]
3.  **State:** For lifecycles and transitions. [slide, 10:47]
4.  **Flowchart:** For control flow and branching. [slide, 10:47]

#### Supported Providers
The tool runs against a list of providers:
*   OpenAI
*   Anthropic
*   Gemini
*   Bedrock
*   OpenRouter
*   Fireworks
*   Baseten
*   NVIDIA NIM
*   Any OpenAI-compatible gateway
[slide, 14:59]

#### License
*   The project uses the **MIT** license. [slide, 14:59]