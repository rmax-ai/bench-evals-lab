---
type: Digest
title: Building pi in a World of Slop — Mario Zechner
description: One-paragraph summary of Building pi in a World of Slop — Mario Zechner
id: urn:rmax-ai:digest:RjfbvDXpFls
status: complete
tags:
- ai agents
- extensibility
- open-source
- code quality
- human-in-the-loop
- self-modifying
confidence: high
visibility: private
source_type: youtube
source_uri: https://www.youtube.com/watch?v=RjfbvDXpFls
source_title: Building pi in a World of Slop — Mario Zechner
source_author: Maxi
source_published: '2026-04-16T22:58:06Z'
captured_at: '2026-08-17T10:33:44.836312+00:00'
generated_by: gemini-2.5-flash
review_status: unreviewed
---

## Overview
- **Speaker**: Mario Zechner
- **Channel**: Maxi
- **Main topic**: Critique of current AI agent development, introduction of a highly extensible agent framework (Pi), and warnings about the pitfalls of uncritical agent adoption in software development and open-source.
- **Purpose**: To share the speaker's personal journey and motivations for building a new agent framework (Pi), to critique the shortcomings of existing AI coding agent tools, to highlight the challenges AI-generated content poses to open-source projects, and to advocate for a more disciplined, human-centric approach to using AI agents in software development.
Mario Zechner presents a three-act tragedy detailing his journey from dissatisfaction with existing AI coding agents (Claude Code, OpenCode) to building his own highly extensible and self-modifying agent, Pi. He critiques the 'slop' in current agent tools, highlighting issues like context management, lack of observability, and poor extensibility. Act II addresses the challenges faced by open-source projects due to 'clankers' (AI-generated contributions). Act III delivers a stark warning against the uncritical adoption of agents, arguing that they compound errors, learn from 'garbage code,' and lead to unmanageable complexity, emphasizing the indispensable role of human discipline, learning, and 'pain' in maintaining code quality and understanding.
## Topic Map
### Act I: Building Pi - Critique of Existing Agent Tools
- **Explanation**: Mario recounts his experience with Claude Code, initially finding it simple and predictable, but eventually encountering 'token madness,' increased features leading to bugs, and critical issues with context management (system prompt changes, tool modifications, injected reminders) and lack of observability, model choice, and extensibility. He then examines OpenCode, finding issues like tool output pruning, LSP server integration that confuses the model, and security vulnerabilities (default CORS settings).
- **Key claims**:
  - Claude Code's context management is problematic, with system prompts and tool definitions changing, and system reminders confusing the model.
  - Existing agent tools lack observability, model choice, and deep extensibility.
  - OpenCode's context handling can 'lobotomize' the model by pruning tool outputs and its LSP integration confuses the model's editing process.
  - Many agent tools have security flaws, such as default open CORS headers.
- **Examples**:
  - Claude Code's flicker bug and subsequent iterations of TUI renderers.
  - Claude Code inserting 'it may or may not be relevant' system reminders.
  - OpenCode pruning tool outputs after a minimum token amount.
  - OpenCode's LSP server injecting errors mid-edit, confusing the model.
  - OpenCode's default server spinning up with open CORS headers.
- **Terminology**:
  - Claude Code
  - OpenCode
  - Token madness
  - Dogfooding
  - TUI renderer
  - Context
  - System prompt
  - Tool definitions
  - System reminders
  - Observability
  - Model choice
  - Extensibility
  - Hooks
  - Amp
  - FactoryDroid
  - LSP server
  - Pruning tool outputs
  - CORS headers
- **Why it matters**: These issues highlight fundamental design flaws in popular agent tools that hinder developer productivity, introduce unpredictability, and can lead to security vulnerabilities, justifying the need for alternative, more robust solutions.
### Terminal Bench and the 'Fuck Around and Find Out' Phase
- **Explanation**: Mario introduces Terminal Bench, a minimalist benchmark for coding agent harnesses that only provides keystroke and output reading tools for a tmux session. He notes its surprisingly high performance on leaderboards, leading to two theses about the current state of AI agents.
- **Key claims**:
  - Minimalist agent harnesses can outperform more complex ones.
  - We are in the 'fuck around and find out' phase of coding agents, and their current form is not final.
  - We need better ways to 'fuck around,' meaning self-modifying, malleable agents.
- **Examples**:
  - Terminal Bench, which only provides keystroke and tmux output tools, scores highly on leaderboards, often higher than native model harnesses.
- **Terminology**:
  - Terminal Bench
  - Tmux session
  - Model family
  - Native harness
  - Fuck around and find out phase
  - Self-modifying agents
  - Malleable agents
- **Why it matters**: This suggests that complexity in agent design doesn't necessarily lead to better performance and that the core problem might be in how agents interact with their environment and how adaptable they are, rather than just raw model power.
### Pi: An Extensible, Self-Modifying Agent
- **Explanation**: Mario introduces Pi, his solution to the problems identified. Pi is designed with a minimal core but is super extensible, allowing the agent and user to modify it. It adapts to the user's workflow, not the other way around. It comes with four packages: AI abstraction, agent core (while loop + tool calling), a bespoke TUI framework, and the coding agent itself. Its system prompt is minimal, and it uses 'skills' (markdown files) for standard definitions. The key is its ability to modify itself by understanding documentation and code examples for extensions.
- **Key claims**:
  - Pi is an agent that adapts to your workflow, not the other way around.
  - Pi has a minimal core but is super extensible and self-modifying.
  - Agents are already reinforcement trained to understand what a coding agent is, so minimal system prompts are sufficient.
  - Pi is YOLO by default, providing users with the flexibility to build their own security mechanisms.
  - Extensions in Pi are TypeScript modules, offering deep hooks into the harness and full control over its behavior and UI.
- **Examples**:
  - Pi's system prompt is very short, with only a few lines added for 'skills'.
  - Pi's four core tools: read, write, edit, bash.
  - A user built a '/by the way' feature (similar to Anthropic's) in five minutes using Pi, without forking.
  - Nico built a custom chat room UI for his Pi agents to talk to each other.
  - Pi can be used to play NES games or Doom.
  - Users can tell Pi to build extensions for them based on specifications.
- **Terminology**:
  - Pi
  - AI package
  - Agent core
  - Bespoke TUI framework
  - Coding agent
  - System prompt
  - Skills
  - Reinforcement trained
  - YOLO (You Only Live Once)
  - Sub-agent support
  - Plan mode
  - MCP support
  - Extensibility
  - TypeScript modules
  - Extension API
  - Slash command shortcuts
  - Custom compaction
  - Custom providers
  - Hot reload
  - NPM
  - GitHub
- **Why it matters**: Pi offers a paradigm shift in agent design, moving towards user-centric, adaptable, and deeply extensible tools that empower developers to tailor agents to their specific needs, addressing the limitations of rigid, black-box systems.
### Act II: OSS in the Age of Clankers
- **Explanation**: Mario describes the problem of 'clankers' – AI-generated pull requests and issues – overwhelming open-source projects. He recounts how his project, Pi, became a target after being integrated into OpenClaw. He developed strategies to filter these contributions, such as auto-closing PRs with a human-verification request and deprioritizing issues from users who interacted with OpenClaw.
- **Key claims**:
  - AI-generated contributions ('clankers') are destroying open-source projects by flooding them with garbage.
  - Traditional OSS contribution mechanisms (issues, PRs) are not designed to handle the volume and low quality of clanker output.
  - Creative filtering mechanisms are necessary to manage clanker contributions and protect maintainer sanity.
- **Examples**:
  - Peter putting Pi inside OpenClaw, making Pi a target for many OpenClaw instances.
  - Dilraj closing issue and pull request trackers due to clanker overload.
  - Mario's auto-closing PR system that asks for a human-written issue, filtering out clankers.
  - Labeling and deprioritizing issues from users with OpenClaw interactions.
  - Embedding issue/PR texts into 3D space to see clusters.
  - Inventing 'OSS vacation' by closing trackers when needed.
- **Terminology**:
  - Clankers
  - OSS (Open Source Software)
  - Pull request (PR)
  - Issue tracker
  - Auto-closed
  - Human voice
  - Vouch
  - Deprioritized
  - OSS vacation
- **Why it matters**: The rise of AI-generated content poses a significant threat to the sustainability and quality of open-source projects, requiring new strategies for community management and contribution filtering to prevent maintainer burnout and preserve project integrity.
### Act III: Slow the Fuck Down - The Dangers of Uncritical Agent Adoption
- **Explanation**: Mario warns against the hype surrounding agents and the belief that they will solve all software problems. He argues that agents compound errors ('booboos') with zero learning, no bottlenecks, and delayed pain for humans. They learn from the 'garbage code' on the internet, leading to local decisions, excessive abstractions, duplication, and enterprise-grade complexity. He contrasts this with humans, who learn, act as bottlenecks for errors, and feel 'pain' which drives refactoring. He emphasizes that long context windows and agentic search are not panaceas.
- **Key claims**:
  - Products '100% built by agents' often 'fucking suck' due to compounded errors.
  - Agents compound 'booboos' (errors) with zero learning, no bottlenecks, and delayed pain for humans.
  - Agents are 'merchants of learned complexity,' deriving their knowledge from the vast amount of 'old garbage code' on the internet.
  - Agent decisions are often local, leading to excessive abstractions, duplication, and backwards compatibility issues.
  - Humans, despite being fallible, learn, act as bottlenecks for errors, and feel pain, which drives necessary refactoring.
  - Long context windows and agentic search are 'hacks' that fail to solve the fundamental problem of agents lacking global context and understanding.
- **Examples**:
  - The claim 'our product's been 100% built by agents' is met with 'it fucking sucks now'.
  - The analogy of an army of agents using 'uninstallable malware' or a broken C compiler.
  - Comparison of codebase growth and 'booboos' per day with human vs. agent contributions.
  - The 'Oroboro' (review agent reviewing agent code) doesn't work effectively.
  - Agents happily 'keep shitting into your codebase' without feeling pain.
- **Terminology**:
  - Booboos
  - Zero learning
  - No bottlenecks
  - Delayed pain
  - Merchants of learned complexity
  - Local decisions
  - Abstractions
  - Duplication
  - Backwards compatibility
  - Defense in depth
  - Enterprise-grade complexity
  - Sufficiently detailed spec
  - Oroboro
  - AGENTS.md
  - Memory systems
  - Long context windows
  - Agentic search
  - Patches locally, fucks shit up globally
- **Why it matters**: This section serves as a critical warning against the over-reliance on AI agents, highlighting the hidden costs and long-term damage they can inflict on codebases and development processes if not managed with extreme caution and human oversight. It underscores the irreplaceable value of human understanding, learning, and critical thinking in software engineering.
### How We Should Work with Agents
- **Explanation**: Mario outlines a disciplined approach to integrating agents into workflows. He emphasizes scoping tasks, providing evaluation functions, using agents for non-mission-critical or boring tasks, and always evaluating their output. The core message is to 'slow the fuck down,' think critically, learn to say no, prioritize fewer but more impactful features, and cap the amount of generated code. Critical code must be read line-by-line and written by hand, with agents only assisting, not making decisions.
- **Key claims**:
  - Good agent tasks are well-scoped, allowing the agent to find all necessary information.
  - Agents are best used for non-mission-critical tasks, boring work, or reproducing user issues.
  - Human evaluation and finalization of agent output are crucial.
  - Developers must 'slow the fuck down,' think about 'what and why,' and learn to say no to unnecessary features.
  - Cap the amount of generated code that needs review.
  - Critical code must be read every line and preferably written by hand, with agents only as helpers.
  - Friction in writing code by hand builds understanding and learning, which agents cannot replicate.
- **Examples**:
  - Using agents for hill-climbing, auto-research, or reproducing user issues.
  - Taking what's reasonable from agent output and finalizing it.
  - Using agents to 'polish the shit out' of important features.
  - Reading every line of critical code.
  - Writing important code by hand, using agents only to help.
- **Terminology**:
  - Scope
  - Modularize codebase
  - Evaluation function
  - Hill-climbing
  - Auto-research
  - Non-mission critical
  - Boring stuff
  - Reproduction cases
  - Rubber duck
  - Finalize
  - Cap generated code
  - Wipe-slop
  - Critical code
  - Friction
  - Discipline
  - Agency
- **Why it matters**: This provides practical, actionable advice for developers and teams on how to leverage AI agents effectively and responsibly, mitigating the risks of poor code quality and unmanageable complexity while preserving human understanding and control over the development process.
## Key Points
### Current AI coding agents suffer from fundamental design flaws.
- **Explanation**: Tools like Claude Code and OpenCode exhibit issues with context management (changing system prompts, injected reminders), lack of observability, limited extensibility, and design choices that confuse models or introduce security risks.
- **Evidence**: Claude Code's 'token madness,' changing system prompts, and injected 'may or may not be relevant' reminders. OpenCode's tool output pruning, LSP server integration that interrupts editing flow, and default open CORS headers.
- **Practical implication**: Developers should be wary of adopting existing agent tools uncritically and be prepared for unpredictable behavior, debugging challenges, and potential security vulnerabilities.
### Minimalist agent harnesses can be highly effective, suggesting a need for more malleable agents.
- **Explanation**: The success of simple benchmarks like Terminal Bench, which only provide basic interaction tools, indicates that current agent complexity might be counterproductive. This points to the need for agents that are self-modifying and adaptable to specific workflows.
- **Evidence**: Terminal Bench, despite its minimal toolset (keystrokes to tmux, read tmux output), scores higher than many complex harnesses on leaderboards.
- **Practical implication**: Focus should shift from complex, feature-rich agent frameworks to minimal, highly extensible, and self-modifying agents that allow users to tailor them precisely to their needs, rather than conforming to a rigid tool.
### Pi offers a solution through extreme extensibility and self-modification.
- **Explanation**: Pi is designed with a minimal core but allows both the user and the agent itself to modify its behavior and add functionality via TypeScript modules. This enables deep customization and adaptation to individual workflows.
- **Evidence**: Pi's minimal system prompt, its ability to modify itself based on documentation and code examples, and examples of users building complex custom features (e.g., chat rooms for agents, NES/Doom games) and UI modifications.
- **Practical implication**: Developers seeking more control and adaptability from their AI agents should explore frameworks like Pi that prioritize extensibility and self-modification, allowing them to build bespoke tools rather than being constrained by off-the-shelf solutions.
### AI-generated contributions ('clankers') pose a significant threat to open-source sustainability.
- **Explanation**: The ease with which AI can generate pull requests and issues leads to a flood of low-quality, often nonsensical contributions that overwhelm human maintainers, making it difficult to manage projects.
- **Evidence**: Mario's experience with Pi becoming a target of OpenClaw instances, leading to a deluge of garbage PRs/issues. The need for filtering mechanisms like auto-closing PRs with human-verification requests and deprioritizing issues from suspected AI sources.
- **Practical implication**: Open-source projects need to develop new strategies and tools to filter and manage AI-generated contributions, potentially involving human verification steps or reputation systems, to protect maintainers from burnout and preserve project quality.
### Uncritical reliance on AI agents leads to compounding errors, learned complexity, and unmanageable codebases.
- **Explanation**: Agents, lacking true learning and the 'pain' that drives human refactoring, will happily inject 'booboos' into a codebase. They learn from the internet's 'garbage code,' leading to excessive abstractions, duplication, and enterprise-grade complexity that becomes impossible for humans or even other agents to manage.
- **Evidence**: The claim that '100% built by agents' products 'fucking suck.' The analogy of agents compounding errors with 'zero learning, no bottlenecks, and delayed pain.' The observation that agents are 'merchants of learned complexity' from 'old garbage code.' The inability of review agents (Oroboro) to solve the problem.
- **Practical implication**: Teams must avoid the temptation to fully automate development with agents. Instead, they should maintain strong human oversight, understand the limitations of agents, and recognize that agents can quickly degrade codebase quality if not carefully managed.
### Humans are indispensable for learning, bottlenecking errors, and driving quality in software development.
- **Explanation**: Unlike agents, humans learn from their mistakes, act as natural bottlenecks for introducing errors, and experience 'pain' when codebases become unmanageable, which motivates them to refactor and improve quality. This human element is crucial for sustainable software development.
- **Evidence**: The contrast between agents 'happily shitting into your codebase' and humans feeling pain, which leads to quitting, blaming, or refactoring. The argument that 'friction' from writing code by hand builds understanding and learning.
- **Practical implication**: Development workflows should prioritize human understanding, discipline, and critical thinking. Agents should augment human capabilities, not replace them, especially in critical code paths. The focus should be on empowering humans, not maximizing agent output.
## Frameworks, Models & Processes
### Pi (Agent Harness)
- **How it works**: Pi is an agent framework with a minimal core designed for extreme extensibility and self-modification. It consists of an AI abstraction layer, an agent core (a while loop for tool calling), a bespoke TUI framework, and the coding agent itself. It uses a minimal system prompt and 'skills' (markdown files). Its core magic is the ability for the agent to modify itself by understanding documentation and code examples for extensions. Extensions are TypeScript modules that can hook into any part of the harness, define tools, shortcuts, listen to events, save state, and control the TUI. These extensions can be bundled and shared via package managers like NPM.
- **Components**:
  - AI package (abstraction across providers and context hand-off)
  - Agent core (while loop and tool calling)
  - Bespoke TUI framework
  - Coding agent
  - Minimal system prompt
  - Skills (markdown files)
  - Four core tools: read, write, edit, bash
  - Extension API (TypeScript modules)
  - Hot reloading
- **When to use**: When developers need an AI agent that is highly adaptable to their specific workflow, offers deep customization, allows for self-modification by the agent, and provides full control over its behavior and UI. Ideal for those who want to build bespoke agent functionalities without being constrained by rigid frameworks.
### Terminal Bench (Benchmark)
- **How it works**: Terminal Bench is a minimalist benchmark for coding agent harnesses. It provides the model with only two tools: one to send keystrokes to a tmux session and another to read the output of that tmux session. It explicitly lacks file tools, sub-agents, or other complex features.
- **Components**:
  - Tool to send keystrokes to a tmux session
  - Tool to read the output of a tmux session
- **When to use**: To evaluate the raw problem-solving capabilities of an AI agent in a highly constrained, terminal-based environment, without the influence of complex file system interactions or sub-agent orchestration. Useful for understanding fundamental agent performance.
### Vouch (Clanker Filtering)
- **How it works**: Vouch is a system, inspired by Mario's 'rage against the clankers' method, designed to filter out AI-generated (clanker) contributions in open-source projects. It involves auto-closing pull requests with a comment asking the contributor to write a nice issue in their human voice. If a human-written issue is detected, the contributor's account is whitelisted for future PRs. Clankers typically don't read or respond to such comments, serving as an effective filter.
- **Components**:
  - Auto-closing pull request mechanism
  - Comment requesting human-written issue
  - Human voice detection/verification
  - Account whitelisting for verified human contributors
- **When to use**: For open-source project maintainers struggling with a high volume of low-quality, AI-generated pull requests and issues, to reduce noise and protect maintainer time and sanity.
## Examples & Case Studies
### Claude Code's context management issues, including changing system prompts, modifying/removing tools, and inserting 'may or may not be relevant' system reminders.
- **Illustrates**: The unpredictability and lack of control users have over the internal workings and context provided to models in black-box agent tools.
- **Lesson**: Agent tools that abstract away or frequently modify the model's context can lead to confusion, broken workflows, and a lack of trust in the tool's behavior.
### OpenCode's pruning of tool outputs after a minimum token amount and its LSP server injecting errors mid-edit.
- **Illustrates**: Design choices in agent tools that can 'lobotomize' the model or disrupt its natural workflow, leading to suboptimal performance and confusion.
- **Lesson**: Agent tools should respect the model's full output and allow it to complete tasks before injecting feedback, mirroring human development practices, to avoid confusing the model.
### Terminal Bench, a minimalist agent harness, consistently scores high on leaderboards despite only providing keystroke and tmux output tools.
- **Illustrates**: That complexity in agent design does not necessarily equate to better performance, and that a minimal, well-defined interaction surface can be highly effective.
- **Lesson**: The 'fuck around and find out' phase of agents suggests that simplicity and malleability might be more important than feature bloat, leading to the need for self-modifying agents.
### A user built a '/by the way' feature (similar to Anthropic's) in five minutes using Pi, based on a prompt, without forking or cloning Pi.
- **Illustrates**: The power of Pi's extensibility and self-modification, allowing users to rapidly build and integrate custom features directly into the agent's workflow.
- **Lesson**: A truly extensible agent framework empowers users to quickly adapt the tool to their specific needs and even have the agent build its own extensions, fostering rapid iteration and customization.
### Mario's 'rage against the clankers' system for filtering AI-generated pull requests in his OSS project.
- **Illustrates**: The overwhelming challenge posed by AI-generated 'garbage' contributions to open-source projects and the necessity for creative, human-centric filtering mechanisms.
- **Lesson**: Open-source maintainers must develop new strategies to combat the influx of low-quality AI contributions to protect their projects and their own sanity, as traditional methods are insufficient.
### The claim that products '100% built by agents' 'fucking suck' and the analogy of agents compounding 'booboos' with zero learning.
- **Illustrates**: The inherent dangers of uncritical, full automation with AI agents, leading to rapid degradation of code quality and unmanageable complexity.
- **Lesson**: Agents lack the capacity for true learning, bottlenecking errors, and feeling 'pain' that drives human refactoring, making human oversight and intervention indispensable for maintaining code quality and system understanding.
## Actionable Takeaways
- **Immediate**:
  - Be highly skeptical of current AI coding agent tools; they often have fundamental flaws in context management, observability, and extensibility.
  - Consider minimalist and highly extensible agent frameworks like Pi that allow for self-modification and deep customization to your workflow.
  - If you're an open-source maintainer, implement filtering mechanisms (like Vouch) to manage the influx of low-quality, AI-generated contributions ('clankers').
  - Do not blindly trust agents to write critical code or manage complex codebases; their output needs rigorous human review and evaluation.
- **Strategic**:
  - Prioritize human understanding, discipline, and 'friction' in the development process, as these are crucial for learning and building robust systems.
  - Use AI agents strategically for well-scoped, non-mission-critical, or boring tasks, always with a human in the loop for evaluation and finalization.
  - Modularize your codebase to enable agents to work on smaller, manageable scopes, reducing the risk of global breakage from local patches.
  - Cap the amount of agent-generated code that needs to be reviewed, and commit to reading every line of critical code yourself.
  - Invest in tools and processes that empower humans to control and adapt agents, rather than being controlled by them.
- **Questions to investigate**:
  - How can we effectively modularize existing codebases to create 'good agent tasks' with guaranteed scope?
  - What are the best practices for defining 'critical code' that requires human-only writing and line-by-line review?
  - How can the 'pain' mechanism that drives human refactoring be simulated or integrated into agent feedback loops to encourage better code quality?
  - What new metrics or evaluation methods are needed to assess the long-term maintainability and complexity introduced by agent-generated code?
## Claims Worth Verifying
- Terminal Bench, despite its minimalism, is one of the best performing harnesses in the leaderboard, even higher than native model harnesses. (Empirical/Performance)
- Agents are actually compounding booboos (errors) with zero learning, no bottlenecks, and delayed pain. (Conceptual/Behavioral)
- Agents are merchants of learned complexity, deriving their knowledge from 90% 'old garbage code' on the Internet. (Conceptual/Source of Knowledge)
- Long context windows are a hack, and agentic search is also failing. (Technical/Effectiveness)
## Notable Quotes
> "My context is not your context. Claude Code is the thing that controls my context. And behind my back, Claude Code does things, uh, to the context."
> "We are in the fuck around and find out phase of (coding) agents. And their current form is not their final form, right?"
> "Pi's also YOLO by default. Because my security needs are different than yours. And I don't think a little dialog that pops up every now, every time you call bash, asking you to approve, is a smart security, uh, mechanism."
> "Clankers are destroying OSS."
> "Agents are actually compounding booboos, which is my word for errors, with zero learning, no bottlenecks, and delayed pain."
> "Slow the fuck down. Think about what you're building and why, and don't just build because your agent can do it now. That's stupid."
> "Critical code, read every fucking line."
## Compressed Summary
- Existing AI coding agents (e.g., Claude Code, OpenCode) suffer from critical flaws in context management, observability, and extensibility.
- Minimalist agent harnesses (like Terminal Bench) often outperform complex ones, suggesting a need for more malleable and self-modifying agents.
- Pi is an extensible, self-modifying agent framework designed to adapt to user workflows, offering deep customization via TypeScript modules and hot reloading.
- AI-generated contributions ('clankers') are overwhelming open-source projects, necessitating new filtering mechanisms like Vouch.
- Uncritical reliance on agents leads to compounding errors, learned complexity from 'garbage code,' and unmanageable codebases, as agents lack human learning and 'pain' mechanisms.
- Effective agent use requires careful task scoping, human evaluation, and a disciplined approach that prioritizes human understanding, reads critical code, and caps agent-generated output.
- **Keywords**: ai agents, extensibility, open-source, code quality, human-in-the-loop, self-modifying
- **Core insight**: Uncritical reliance on current AI agents leads to unmanageable codebases and overwhelms open-source, necessitating highly extensible, human-controlled tools like Pi and a disciplined, human-centric approach to development that prioritizes understanding and quality over unbridled automation.