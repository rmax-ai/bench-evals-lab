---
type: Digest
title: 'Modern Post-Training: A Deep Dive  — Will Brown, Prime Intellect'
description: 'One-paragraph summary of Modern Post-Training: A Deep Dive  — Will Brown,
  Prime Intellect'
id: urn:rmax-ai:digest:V-EDrhIhHzQ
status: complete
tags:
- post-training
- reinforcement learning
- environments
- Verifiers
- prime-RL
- asynchronous
- large-scale
- tokenization
- agentic
- open-source
confidence: high
visibility: private
source_type: youtube
source_uri: https://www.youtube.com/watch?v=V-EDrhIhHzQ
source_title: 'Modern Post-Training: A Deep Dive  — Will Brown, Prime Intellect'
source_author: Maxi
source_published: '2026-07-13T15:34:07Z'
captured_at: '2026-08-17T07:05:49.156259+00:00'
generated_by: gemini-2.5-flash
review_status: unreviewed
---

## Overview
- **Speaker**: Will Brown
- **Channel**: Maxi
- **Main topic**: Modern Post-Training for AI Models using Prime Intellect's Open-Source Tools
- **Purpose**: To provide an update on Prime Intellect's open-source post-training tools (Verifiers and prime-RL), explain what modern post-training entails, demonstrate how their tools facilitate large-scale, efficient, and customizable AI model training, and empower AI engineers to improve models for their specific use cases.
Will Brown, Head of Applied Research at Prime Intellect, presents a deep dive into modern post-training techniques for AI models, focusing on the company's open-source tools: Verifiers and prime-RL. The talk outlines Prime Intellect's mission to democratize large-scale open-source AI research, enabling companies to train and improve models based on real-world production scenarios. He introduces a refactored Verifiers V1 library for environment creation (tasksets, harnesses, runtimes) and an evolved prime-RL framework for efficient, asynchronous reinforcement learning, supporting custom algorithms and large-scale model training. The discussion emphasizes the importance of evaluations, iterative model refinement, and addresses system-level challenges like tokenization and scaling for frontier models, culminating in the introduction of their Lab platform for hosted training and evaluations.
## Topic Map
### Prime Intellect's Mission and the Open Superintelligence Stack
- **Explanation**: Prime Intellect aims to simplify large-scale open-source AI research, enabling companies to train and deploy their own models that improve based on real-world production use cases. They describe their offering as the 'open superintelligence stack,' providing an open toolkit for real training and customization, believing models are already becoming superhuman in many ways.
- **Key claims**:
  - Our goal is to make doing large-scale open-source AI research easier and to enable companies to train their own models and deploy them and have them improve based on the scenarios that they actually see in production.
  - The models are getting very, very good. They are superhuman in many ways at lots of things.
  - We want to do is give people an open toolkit that they can use to do real training with them.
- **Examples**:
  - Companies training models for applications and products and internal tasks and workflows.
- **Terminology**:
  - Open Superintelligence Stack
- **Why it matters**: Democratizes advanced AI model training, offering control and customization beyond off-the-shelf frontier models, and fostering continuous improvement in real-world applications.
### Prime Intellect's Comprehensive AI Infrastructure
- **Explanation**: Prime Intellect provides a full stack for AI research and deployment, including a global GPU marketplace (operating over 10,000 GPUs), the prime-RL training framework, environments built with Verifiers and Environments Hub, and the Lab platform for research workflows (hosted training, evaluations, inference, sandboxes). This infrastructure supports frontier model training for both internal Intellect models and customer projects.
- **Key claims**:
  - We currently operate over 10,000 GPUs.
  - All of this is in service of empowering and unlocking frontier model training.
- **Examples**:
  - Intellect model series
  - Training models with customers for large-scale model training on their own workflows.
- **Terminology**:
  - prime-RL training framework
  - Verifiers library
  - Environments Hub
  - Lab platform
  - hosted training
  - evaluations
  - inference
  - sandboxes
- **Why it matters**: Offers a complete, integrated solution for AI development, from compute to training and deployment, reducing the need for companies to build extensive internal research teams.
### Modern Post-Training Loop
- **Explanation**: The post-training loop revolves around environments, which define what a model should do, encapsulate data and scenarios, manage interaction, and score performance. This iterative loop typically involves evaluations (evals), followed by various training methods like SFT, RL, on-policy distillation, or self-distillation, and finally deployment for continuous refinement based on real-world feedback.
- **Key claims**:
  - Environments are a language for specifying what you want your model to do.
  - Evals are the thing that opens the door to post-training.
  - The point of this is to have flywheels that make everything get better.
- **Examples**:
  - SFT (Supervised Fine-Tuning)
  - RL (Reinforcement Learning)
  - On-policy distillation
  - Self-distillation
  - Training individual RL experts on top of the same base model and then doing distillation from those teachers into the same checkpoint.
- **Terminology**:
  - Post-training loop
  - environments
  - evals
  - SFT
  - RL
  - on-policy distillation
  - self-distillation
  - RL experts
  - Lora adapter
  - model refinement
- **Why it matters**: Provides a structured approach to continuously improve AI models, ensuring they remain effective and adapt to evolving real-world conditions, justifying the investment in post-training.
### Verifiers V1 Library
- **Explanation**: Verifiers V1 is a complete overhaul of Prime Intellect's open-source environment library, designed for greater flexibility and power. It decomposes environments into composable 'taskset', 'harness', and 'runtime' components. Tasksets define data and rules (agent-agnostic), harnesses manage model interaction (supporting various agent types), and runtimes execute the code (locally, Docker, sandboxes). It also introduces an 'interception server' pattern to allow real-world harnesses to be used without modification for RL.
- **Key claims**:
  - We kind of wanted to redo it all. And so we have a new way of doing everything that we think is going to make a lot more sense, be a lot more powerful for what people are looking to do going forward.
  - The harness doesn't know that it's doing RL. The harness just is a harness running as if it would be running in a real-world environment.
- **Examples**:
  - SWE-bench (agentic code search)
  - Wordle
  - Search over documents with judges
  - Harbor benchmarks
  - Recursive language models (RLM)
  - CLI agents (Codex, Claude Code, OpenAI Code)
  - Mini-SWE agent
  - LangChain or DSPy for building custom harnesses.
- **Terminology**:
  - Verifiers V1
  - taskset
  - harness
  - runtime
  - interception server
  - UV script
  - rollout
  - trace
  - Pydantic
  - decorators
  - rewards
  - metrics
  - group rewards
  - length penalty
  - conciseness bonus
  - user simulators
  - MCP (Multi-Agent Communication Protocol)
- **Why it matters**: Simplifies the creation and management of diverse and complex AI environments, making it easier to evaluate and train models across various tasks and interaction patterns, and bridging the gap between evaluation, training, and deployment.
### prime-RL Training Framework
- **Explanation**: prime-RL is Prime Intellect's full-stack open-source training framework, built from the ground up for asynchronous reinforcement learning. It uses an orchestrator to manage separate inference and trainer processes, allowing for decoupled scaling and overlapping long rollouts. It supports custom algorithms, efficient large-scale training (e.g., GLM 5 on 28 nodes in under 5 minutes per step), and incorporates advanced parallelism techniques (FP8, wide expert parallelism, decentralized pre-fill, router replay) on a Torch Titan base.
- **Key claims**:
  - prime-RL has been async from the ground up.
  - You can go reasonably far off policy. Like, I think 16 is where we typically, are often operating, is like an average.
  - We can do a GLM 5 step on 28 nodes in less than 5 minutes for long-horizon coding tasks with 131k context.
- **Examples**:
  - GLM 5
  - Kimmy K2.5/2.6 series
  - DPPO paper
  - Echo paper
  - Max RL paper
- **Terminology**:
  - prime-RL
  - orchestrator
  - asynchronous reinforcement learning
  - inference server
  - trainer
  - off-policy
  - DPPO
  - FP8
  - wide expert parallelism (YDP)
  - decentralized pre-fill
  - router replay
  - KV offloading
  - Torch Titan
  - Megatron
  - loss function
  - algorithm (data preparation)
- **Why it matters**: Enables highly efficient and scalable training of large, frontier-sized models, making advanced RL accessible and affordable for enterprises, and allowing for rapid iteration on complex agentic tasks.
### Renderers Library and Tokenization Challenges
- **Explanation**: Renderers is a standalone Python library designed to rethink tokenizers and chat templates, addressing subtle numerical problems and mismatches that arise from re-tokenization in large-scale training. It turns chat templates into programmable artifacts, managing token-in/token-out concatenation and maintaining dual streams of logical text and tokens for clean interoperability between users, trainers, and inference engines.
- **Key claims**:
  - Jinja is awful.
  - This causes lots of very subtle numerical problems, especially late in large-scale training runs.
  - You want to be able to maintain these dual streams of the logical text and the, the tokens.
- **Examples**:
  - OpenAI's Harmony with the GPT-OSS release
  - Thinking Machines cookbooks for Tinker
- **Terminology**:
  - Renderers
  - tokenizers
  - chat templates
  - Jinja
  - re-tokenization
  - log-probs
  - logical prefix hit
  - stateful APIs
- **Why it matters**: Solves critical, subtle issues in tokenization that can lead to training instability and off-policy behavior, ensuring robust and reliable large-scale model training and inference.
## Key Points
### The necessity of an open toolkit for real AI model training.
- **Explanation**: While frontier models are becoming very capable, companies need the ability to train their own models, customize them, and deploy them where needed to address specific use cases and maintain control.
- **Evidence**: What we want to do is give people an open toolkit that they can use to do real training with them. And to have the control that they need to deploy it where they need to deploy it and customize it as much as they need to to kind of get the job done.
- **Practical implication**: Businesses should invest in open-source training frameworks to gain autonomy and tailor AI models to their unique operational needs, rather than solely relying on black-box APIs.
### Environments are central to the post-training loop and evaluations.
- **Explanation**: Environments serve as a universal language for defining model tasks, data, interactions, and scoring. They are crucial for both evaluating models (offline) and for driving reinforcement learning and data generation for SFT.
- **Evidence**: The post-training loop in my mind kind of revolves around environments in the sense of environments are a language for specifying what you want your model to do. And evals are the thing that opens the door to post-training. And so environments and evals are essentially the same thing.
- **Practical implication**: Prioritizing the development of robust and flexible environments is fundamental for effective AI model development, enabling both performance assessment and iterative improvement.
### Asynchronous RL is crucial for efficiency in complex agentic tasks.
- **Explanation**: Agentic tasks often have highly variable rollout times, with some taking significantly longer than others. Asynchronous RL decouples forward progress from the slowest rollout, allowing for continuous GPU utilization and efficient training even with long-tail latencies.
- **Evidence**: One of the goals of async RL is to have your, like, forward progress speed not be tied to the speed of your individual rollout. And you can go reasonably far off policy. Like, I think 16 is where we typically, are often operating, is like an average.
- **Practical implication**: When designing training systems for agents, especially those interacting with real-world or simulated complex environments, an asynchronous architecture is vital to maximize compute efficiency and accelerate the training process.
### Tokenization subtleties can cause significant numerical problems in large-scale training.
- **Explanation**: The process of re-tokenizing text messages can introduce subtle changes that lead to mismatches between training and inference, causing numerical instability and off-policy behavior, especially in complex agentic rollouts.
- **Evidence**: re-tokenization or like some messages, if a model will say something and you turn it into text and you put it back through a tokenizer, it can change a little bit. The because tokenization is is many to one. Um, and so this causes lots of very subtle numerical problems, especially late in large-scale training runs.
- **Practical implication**: Developers need robust tools like Renderers to manage the dual streams of logical text and tokens carefully, ensuring consistency between message space and token space to prevent training issues and maintain policy alignment.
### Group rewards are essential for nuanced reward design.
- **Explanation**: Many desirable model behaviors, such as conciseness or optimal length, cannot be determined upfront for individual rollouts. Group-level comparisons allow for shaping rewards based on variance across multiple samples, incentivizing both correctness and efficiency simultaneously.
- **Evidence**: in many RL frameworks, it's actually quite hard to do group rewards because things are very decoupled... But there's a lot of things where you really want to do pairwise judging, or you want to do ranking, or you want to give a bonus to the, uh, the shortest correct answer, uh, in terms of tokens used.
- **Practical implication**: When designing reward functions for RL, consider implementing group rewards to address complex objectives like efficiency and conciseness, which are difficult to define for single instances, thereby leading to more sophisticated and well-behaved models.
## Frameworks, Models & Processes
### Verifiers V1
- **How it works**: A refactored open-source library for building AI environments. It decomposes environments into composable taskset, harness, and runtime components. Tasksets define agent-agnostic data and rules. Harnesses specify how a model interacts with the task, supporting various agent patterns (e.g., RLM, CLI agents). Runtimes execute the harness code in different backends (local, Docker, sandboxes). An 'interception server' allows standard harnesses to be used for RL without modification.
- **Components**:
  - taskset
  - harness
  - runtime
  - interception server
  - rewards
  - metrics
  - group rewards
  - user simulators
  - MCP
- **When to use**: For creating flexible and powerful environments for AI model evaluation (offline evals) and post-training (RL, SFT data generation), especially for complex agentic tasks and multi-turn interactions.
### prime-RL
- **How it works**: A full-stack open-source training framework for asynchronous reinforcement learning. It uses an orchestrator to manage separate inference and trainer processes, enabling decoupled scaling. It supports custom algorithms by separating loss functions from data preparation logic. It incorporates advanced parallelism and optimization techniques for efficient large-scale training of frontier models.
- **Components**:
  - orchestrator
  - inference server
  - trainer
  - environments (from Verifiers)
  - loss functions
  - algorithms (data preparation)
  - FP8
  - wide expert parallelism (YDP)
  - decentralized pre-fill
  - router replay
- **When to use**: For large-scale, efficient, and stable reinforcement learning of AI models, particularly for complex agentic tasks with long and variable rollout times, and when custom algorithms or significant model customization is required.
### Lab Platform
- **How it works**: Prime Intellect's platform for research workflows. It integrates the Environments Hub, hosted training (multi-tenant Lora and full fine-tuning), evaluations, inference, and sandboxes. It abstracts away GPU management, offering auto-scaling, magic restarts, unified billing, and dashboards. Users can develop environments locally and deploy them to the platform.
- **Components**:
  - Environments Hub
  - hosted training (multi-tenant Lora, full fine-tuning)
  - evaluations
  - inference
  - sandboxes
  - dashboard
  - auto-scaling
  - magic restarts
  - unified billing
- **When to use**: For companies and researchers who want to leverage Prime Intellect's infrastructure for large-scale model training and evaluation without managing GPUs directly, offering flexibility from simple reward function changes to deep algorithm customization.
### Renderers
- **How it works**: A standalone Python library that rethinks tokenizers and chat templates. It converts chat templates into programmable artifacts to manage token-in/token-out concatenation, ensuring consistency between logical text and token representations. It helps avoid numerical problems caused by re-tokenization mismatches.
- **Components**:
  - programmable chat templates
  - tokenizer calls
  - history of trace
  - logical text stream
  - token stream
- **When to use**: When dealing with complex chat templates, multi-turn interactions, or any scenario where precise control over tokenization and preventing re-tokenization mismatches is critical for stable and reliable training and inference, especially in large-scale agentic systems.
## Examples & Case Studies
### Training individual RL experts on different environments (tasks) on top of the same base model, then distilling these teachers into a single checkpoint.
- **Illustrates**: A reliable strategy for training a single model to be proficient across multiple diverse tasks.
- **Lesson**: For models needing to excel at various distinct skills, an expert distillation approach can be more effective than direct multi-task RL.
### Using a length penalty or conciseness bonus in reward design, especially through group rewards. For instance, giving a bonus to the shortest correct answer among a group of rollouts.
- **Illustrates**: How to incentivize efficiency and conciseness in model outputs when the optimal length is unknown and varies per problem.
- **Lesson**: Leveraging variance across multiple samples (group rewards) is a powerful technique for shaping complex behaviors like efficiency, which are hard to define with static, per-instance rewards.
### Simulating a user in the loop for training, where the user is an MCP server with a script or LLM that interacts with the agent.
- **Illustrates**: How to incorporate realistic multi-turn user interactions into RL environments for products where users are in the loop.
- **Lesson**: User simulators, especially when implemented as modular components, are crucial for training agents that perform well in real-world interactive product settings.
### Achieving a GLM 5 step on 28 nodes in less than 5 minutes for long-horizon coding tasks with 131k context using prime-RL.
- **Illustrates**: The efficiency and scalability of prime-RL for large-scale, frontier-model training on complex tasks.
- **Lesson**: With optimized asynchronous frameworks and parallelism, large-scale RL for frontier models can become significantly more affordable and feasible for enterprises, offering a cost-effective alternative to continuous token usage.
## Actionable Takeaways
- **Immediate**:
  - Start with evaluations: Environments are key for both evals and training.
  - Embrace asynchronous RL: It's essential for efficient training of agents with variable rollout times.
  - Pay attention to tokenization: Use tools like Renderers to avoid subtle numerical issues.
  - Explore group rewards: For nuanced reward shaping like conciseness.
  - Utilize modular environment components: Tasksets, harnesses, and runtimes offer flexibility.
- **Strategic**:
  - Invest in an open toolkit for AI training: Gain control, customization, and continuous improvement for your specific use cases.
  - Plan for iterative model refinement: Post-training is not a one-time event but a continuous flywheel.
  - Consider expert distillation for multi-skill models: A reliable strategy for broad proficiency.
  - Leverage hosted platforms for scale: Abstract away GPU management to focus on research and development.
  - Integrate user simulators: For training agents in realistic interactive product scenarios.
- **Questions to investigate**:
  - How can real-world feedback be effectively integrated into environments for continuous model refinement?
  - What are the optimal off-policy limits for different agentic tasks and model architectures?
  - How can the cost-effectiveness of large-scale post-training compare to continuous API usage for specific business cases?
  - What are the best practices for designing group rewards to balance multiple objectives (e.g., correctness and efficiency)?
## Claims Worth Verifying
- We currently operate over 10,000 GPUs. (Factual claim about company resources)
- We can do a GLM 5 step on 28 nodes in less than 5 minutes for long-horizon coding tasks with 131k context. (Performance benchmark claim)
- You can go reasonably far off policy. Like, I think 16 is where we typically, are often operating, is like an average. (Empirical claim about RL stability)
- 50k is not cheap, but it's like, if you're doing a full run on a frontier-sized model, on like, a proper real-world agent environment, like, it's a lot cheaper than what OpenAI's raising for. (Comparative cost claim)
## Notable Quotes
> "Our goal is to make doing large-scale open-source AI research easier and to enable companies to train their own models and deploy them and have them improve based on the scenarios that they actually see in production."
> "The models are getting very, very good. They are superhuman in many ways at lots of things."
> "Environments are a language for specifying what you want your model to do."
> "Evals are the thing that opens the door to post-training."
> "The point of this is to have flywheels that make everything get better."
> "The harness doesn't know that it's doing RL. The harness just is a harness running as if it would be running in a real-world environment."
> "Jinja is awful."
> "One of the goals of async RL is to have your, like, forward progress speed not be tied to the speed of your individual rollout."
## Compressed Summary
- Prime Intellect offers open-source tools (Verifiers, prime-RL) and a platform (Lab) for modern, large-scale AI post-training.
- Verifiers V1 refactors environments into composable tasksets, harnesses, and runtimes, supporting diverse agentic tasks and evaluations.
- prime-RL is an asynchronous, scalable training framework optimized for efficient RL of frontier models, enabling custom algorithms.
- Key innovations include an interception server for seamless RL integration, Renderers for robust tokenization, and group rewards for nuanced objective balancing.
- The goal is to empower companies to train, customize, and continuously refine their own AI models, making advanced post-training accessible and affordable.
- **Keywords**: post-training, reinforcement learning, environments, Verifiers, prime-RL, asynchronous, large-scale, tokenization, agentic, open-source
- **Core insight**: Prime Intellect provides a comprehensive, open-source, and scalable toolkit for modern AI post-training, enabling enterprises to efficiently train, customize, and continuously improve frontier models for real-world applications.