---
name: Agent Model Selection
id: agent_model_selection
version: 1.0
category: orchestrator
domain: [any]
task_types: [planning, optimization]
keywords: [model, selection, haiku, sonnet, opus, cost, latency, complexity, agent, task]
complexity: [easy]
pairs_with: [decomposition_agent, agent_construction]
source: local
---

# Agent Model Selection Guidelines

## Purpose
Define criteria for selecting appropriate models when spawning subagents via the Task tool, balancing capability against cost and latency.

## Model Tiers

### Haiku (Easy Tasks)
**Use when:** Task is straightforward with minimal decision-making required.

**Criteria:**
- Single constant or configuration change
- Text/string updates
- Reading code and reporting findings
- Syntax validation
- Simple file searches
- Formatting or documentation updates
- Grep/find operations with clear targets

**Examples:**
- "Change PLAYER_SPEED from 300 to 400"
- "Find all references to GameState.PLAYING"
- "Check if function X exists in file Y"
- "Update button text from 'Restart' to 'Continue'"

---

### Sonnet (Normal Tasks)
**Use when:** Task requires implementation skill but has clear scope and requirements.

**Criteria:**
- Single feature implementation
- Bug fixes requiring logic changes
- Adding new class or function
- Modifying existing mechanics
- QA verification and testing
- Code review tasks
- Feature specifications with defined parameters

**Examples:**
- "Implement PowerupSplash class with fade animation"
- "Fix GAMEOVER state bypass bug"
- "Add localStorage persistence for high scores"
- "QA verification of recent changes"
- "Create SVG sprite for new enemy type"

---

### Opus (Complex Tasks)
**Use when:** Task involves significant complexity, ambiguity, or architectural impact.

**Criteria:**
- Architectural decisions with tradeoffs
- Multi-system changes (touching 3+ interconnected systems)
- Complex algorithms (physics, pathfinding, procedural generation)
- Design decisions requiring judgment
- Refactoring interconnected systems
- Performance optimization requiring profiling
- Debugging subtle/intermittent issues
- Tasks with unclear requirements needing exploration

**Examples:**
- "Design state machine architecture for game flow"
- "Implement realistic physics bounce with momentum transfer"
- "Refactor rendering system to support layers"
- "Diagnose and fix race condition in async loading"
- "Evaluate authentication approaches and recommend solution"

---

## Decision Process

1. **Assess scope**: How many files/systems affected?
2. **Assess ambiguity**: Are requirements clear or need interpretation?
3. **Assess complexity**: Straightforward logic or nuanced decisions?
4. **Default to Sonnet**: When uncertain, Sonnet handles most development tasks well
5. **Escalate to Opus**: If task fails or produces poor results with Sonnet

## Usage in Task Tool

When spawning an agent, include the model parameter:

- model: "haiku" for easy tasks
- model: "sonnet" for normal tasks
- model: "opus" for complex tasks

Example assessment in task description:
"[Complexity: Normal/Sonnet] Implement feature X..."

---

## Context Efficiency Tips

To avoid context overflow in subagents:

1. **Specify line ranges**: "Read lines 200-250" instead of full file
2. **Pre-summarize**: Include relevant code snippets in prompt
3. **Smaller tasks**: Break large features into focused subtasks
4. **Use Haiku for discovery**: Find what you need, then Sonnet to implement
