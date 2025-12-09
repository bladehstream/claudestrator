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

**Max Skills**: 3

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

**Max Skills**: 7

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

**Max Skills**: 15

**Examples:**
- "Design state machine architecture for game flow"
- "Implement realistic physics bounce with momentum transfer"
- "Refactor rendering system to support layers"
- "Diagnose and fix race condition in async loading"
- "Evaluate authentication approaches and recommend solution"

---

## Decision Process

```
FUNCTION selectModel(task):

    # Check explicit complexity if set
    IF task.complexity IS SET:
        RETURN complexityToModel(task.complexity)

    # Assess based on characteristics
    score = 0

    # Scope assessment
    IF task affects 1 file: score += 0
    IF task affects 2-3 files: score += 1
    IF task affects 4+ files: score += 2

    # Ambiguity assessment
    IF requirements are explicit: score += 0
    IF some interpretation needed: score += 1
    IF significant judgment required: score += 2

    # Decision complexity
    IF single obvious approach: score += 0
    IF few clear alternatives: score += 1
    IF many tradeoffs to consider: score += 2

    # Map score to model
    IF score <= 1: RETURN 'haiku'
    IF score <= 4: RETURN 'sonnet'
    RETURN 'opus'
```

## Quick Reference

| Complexity | Model | Max Skills | Typical Tasks |
|------------|-------|------------|---------------|
| Easy | Haiku | 3 | Constants, searches, simple edits |
| Normal | Sonnet | 7 | Features, fixes, single components |
| Complex | Opus | 15 | Architecture, algorithms, multi-system |

## Context Efficiency Tips

To avoid context overflow in subagents:

1. **Specify line ranges**: "Read lines 200-250" instead of full file
2. **Pre-summarize**: Include relevant code snippets in prompt
3. **Smaller tasks**: Break large features into focused subtasks
4. **Use Haiku for discovery**: Find what you need, then Sonnet to implement

## Escalation Rules

- If task **fails** with Haiku → retry with Sonnet
- If task **fails** with Sonnet → retry with Opus
- If task **fails** with Opus → break into smaller tasks or escalate to user

---

*Version: 1.0*
*Created: December 2024*
