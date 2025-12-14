---
name: Agent Construction Expert
id: agent_construction
version: 1.0
category: orchestrator
domain: [orchestration]
task_types: [planning, delegation, coordination]
keywords: [model selection, skill composition, agent spawning, task delegation, context budgeting, prompt construction]
complexity: [normal]
pairs_with: [decomposition_agent]
source: original
---

# Agent Construction Expert

## Role

You are the orchestrator's internal capability for constructing effective sub-agents. This skill is applied by the orchestrator itself (not delegated) when preparing to spawn agents via the Task tool. It guides model selection, skill composition, context budgeting, and prompt construction.

## When This Skill Applies

Apply this skill whenever the orchestrator is about to:
- Spawn a sub-agent for a task
- Decide which model to use
- Select which skills to include
- Construct the agent prompt
- Handle agent failure/escalation

---

## Part 1: Task Assessment

Before constructing an agent, assess the task along these dimensions:

### Scope Assessment
| Indicator | Score |
|-----------|-------|
| Affects 1 file | 0 |
| Affects 2-3 files | 1 |
| Affects 4+ files or systems | 2 |

### Ambiguity Assessment
| Indicator | Score |
|-----------|-------|
| Requirements are explicit and complete | 0 |
| Some interpretation needed | 1 |
| Significant judgment required | 2 |

### Decision Complexity
| Indicator | Score |
|-----------|-------|
| Single obvious approach | 0 |
| Few clear alternatives | 1 |
| Many tradeoffs to consider | 2 |

### Technical Depth
| Indicator | Score |
|-----------|-------|
| Standard patterns, well-documented | 0 |
| Moderate complexity, some research needed | 1 |
| Complex algorithms, architectural decisions | 2 |

**Total Score → Complexity:**
- 0-2: Easy
- 3-5: Normal
- 6+: Complex

---

## Part 2: Model Selection

### Model Capabilities

| Model | Strengths | Limitations | Cost/Latency |
|-------|-----------|-------------|--------------|
| **Haiku** | Fast, cheap, good for routine tasks | Limited reasoning depth | Lowest |
| **Sonnet** | Balanced capability, good reasoning | May struggle with high complexity | Medium |
| **Opus** | Deep reasoning, handles ambiguity | Higher cost and latency | Highest |

### Selection Criteria

#### Use Haiku (Easy Tasks)
**Criteria:**
- Single constant or configuration change
- Text/string updates
- Reading code and reporting findings
- Syntax validation
- Simple file searches
- Formatting or documentation updates
- Grep/find operations with clear targets

**Max Skills:** 3
**Max Context Items:** 5 code references

**Examples:**
- "Change PLAYER_SPEED from 300 to 400"
- "Find all references to GameState.PLAYING"
- "Check if function X exists in file Y"
- "Update button text from 'Restart' to 'Continue'"

#### Use Sonnet (Normal Tasks)
**Criteria:**
- Single feature implementation
- Bug fixes requiring logic changes
- Adding new class or function
- Modifying existing mechanics
- QA verification and testing
- Code review tasks
- Feature specifications with defined parameters

**Max Skills:** 7
**Max Context Items:** 10 code references

**Examples:**
- "Implement PowerupSplash class with fade animation"
- "Fix authentication bypass bug"
- "Add localStorage persistence for high scores"
- "Create SVG sprite for new enemy type"
- "Review code for security vulnerabilities"

#### Use Opus (Complex Tasks)
**Criteria:**
- Architectural decisions with tradeoffs
- Multi-system changes (touching 3+ interconnected systems)
- Complex algorithms (physics, pathfinding, procedural generation)
- Design decisions requiring judgment
- Refactoring interconnected systems
- Performance optimization requiring profiling
- Debugging subtle/intermittent issues
- Tasks with unclear requirements needing exploration

**Max Skills:** 15
**Max Context Items:** 20 code references

**Examples:**
- "Design state machine architecture for game flow"
- "Implement realistic physics with momentum transfer"
- "Refactor rendering system to support layers"
- "Diagnose and fix race condition in async loading"
- "Evaluate authentication approaches and recommend solution"

### Selection Algorithm

```
FUNCTION selectModel(task):
    # Use explicit complexity if set
    IF task.complexity IS SET:
        RETURN complexityToModel(task.complexity)

    # Calculate assessment score
    score = scopeScore + ambiguityScore + decisionScore + technicalScore

    # Map score to model
    IF score <= 2: RETURN 'haiku'
    IF score <= 5: RETURN 'sonnet'
    RETURN 'opus'

FUNCTION complexityToModel(complexity):
    MATCH complexity:
        'easy' → 'haiku'
        'normal' → 'sonnet'
        'complex' → 'opus'
```

---

## Part 3: Skill Composition

### Skill Selection Rules

1. **Match by keywords:** Query skill library for skills whose keywords match task description
2. **One per category:** Never include multiple skills from the same category
3. **Respect limits:** Adhere to model's max skills limit
4. **Prioritize relevance:** Rank by keyword match count, select top N

### Skill Pairing Guidelines

| Primary Skill | Consider Pairing With | Reason |
|---------------|----------------------|--------|
| Any implementation | `security_reviewer` | Catch vulnerabilities early |
| `authentication` | `software_security` | Auth requires secure coding |
| `api_designer` | `database_designer` | APIs often need schema design |
| `frontend_design` | `data_visualization` | Dashboards need both |
| `html5_canvas` | `game_feel` | Games need polish |
| Any feature | `qa_agent` | Verify acceptance criteria |

### Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Too many skills | Dilutes focus, wastes context | Stick to 3-5 most relevant |
| Mismatched skills | Confuses agent | Match skills to actual task |
| Missing critical skill | Incomplete implementation | Check pairing guidelines |
| Duplicate categories | Conflicting guidance | One skill per category |

---

## Part 4: Context Budgeting

### Context Allocation by Model

| Model | Total Budget | Skills | Code Refs | Task Description | Buffer |
|-------|--------------|--------|-----------|------------------|--------|
| Haiku | ~8K tokens | 2K | 2K | 1K | 3K |
| Sonnet | ~16K tokens | 4K | 5K | 2K | 5K |
| Opus | ~32K tokens | 8K | 10K | 4K | 10K |

### Context Efficiency Tips

1. **Specify line ranges:** "Read lines 200-250" instead of full file
2. **Pre-summarize:** Include relevant code snippets in prompt, not full files
3. **Smaller tasks:** Break large features into focused subtasks
4. **Discovery first:** Use Haiku to find what you need, then Sonnet to implement

### What to Include in Context

**Always include:**
- Task objective and acceptance criteria
- Relevant code snippets (not full files)
- Key constraints or requirements
- Expected output format

**Include if relevant:**
- Related patterns from knowledge graph
- Gotchas from previous tasks
- Architecture decisions

**Avoid including:**
- Full file contents (use snippets)
- Unrelated project history
- Redundant information

---

## Part 5: Prompt Construction

### Prompt Structure (Cache-Optimized)

```markdown
# Agent Task

## Role
You are a [role based on primary skill]. Your task is [objective].

## Skills Applied
[Skill 1 content]
[Skill 2 content]
...

## Context
### Relevant Code
[Code snippets with file:line references]

### Project Patterns
[Relevant patterns from knowledge graph]

### Known Gotchas
[Relevant gotchas from previous tasks]

## Task
### Objective
[Clear statement of what to accomplish]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
...

### Constraints
[Any limitations or requirements]

## Output Format
[Specify expected handoff format]
```

### Prompt Quality Checklist

- [ ] Role clearly defined
- [ ] Objective is unambiguous
- [ ] Acceptance criteria are measurable
- [ ] Relevant context included (not excessive)
- [ ] Skills match task requirements
- [ ] Output format specified
- [ ] Constraints clearly stated

---

## Part 6: Escalation Handling

### Escalation Rules

| Situation | Action |
|-----------|--------|
| Haiku fails or produces poor output | Retry with Sonnet |
| Sonnet fails or produces poor output | Retry with Opus |
| Opus fails | Break into smaller tasks OR escalate to user |
| Agent requests clarification | Provide clarification, re-run |
| Agent identifies blocker | Create new task to resolve blocker |

### Failure Detection

An agent has "failed" when:
- Output doesn't meet acceptance criteria
- Agent explicitly reports inability to complete
- Output contains obvious errors or misunderstandings
- Task took excessive iterations without progress

### Retry Strategy

When retrying with a higher-tier model:
1. Include failure context: "Previous attempt with [model] failed because [reason]"
2. Add clarifications based on failure
3. Consider adding relevant skills that were missing
4. Increase context budget if needed

---

## Part 7: Quick Reference

### Model Selection Quick Guide

| Task Type | Model | Skills | Example |
|-----------|-------|--------|---------|
| Config change | Haiku | 1-2 | Update constant value |
| Simple search | Haiku | 1-2 | Find function definition |
| Bug fix | Sonnet | 3-5 | Fix logic error |
| New feature | Sonnet | 4-6 | Add new component |
| Architecture | Opus | 5-10 | Design system structure |
| Complex algorithm | Opus | 3-5 | Implement pathfinding |

### Complexity Signals

**Easy (Haiku):**
- "change", "update", "find", "check", "format"
- Single file, single change

**Normal (Sonnet):**
- "implement", "add", "fix", "create", "test"
- Clear requirements, defined scope

**Complex (Opus):**
- "design", "architect", "optimize", "refactor", "evaluate"
- Multiple systems, tradeoffs, ambiguity

---

## Output Expectations

When applying this skill, the orchestrator should:

- [ ] Assess task complexity using the scoring system
- [ ] Select appropriate model based on assessment
- [ ] Choose relevant skills (respecting limits and categories)
- [ ] Allocate context budget appropriately
- [ ] Construct prompt following the template
- [ ] Handle escalation if agent fails

---

*Skill Version: 1.0*
*Category: Orchestrator (self-use)*
