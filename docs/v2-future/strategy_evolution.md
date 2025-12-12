# Strategy Evolution System

## Overview

The orchestrator's strategies evolve based on execution feedback. Instead of static prompts frozen at "version one," the system learns from doing—updating skill selection heuristics, context gathering rules, and agent configurations based on observed outcomes.

**Principle**: "Agents need systems that update their strategies without collapsing into vagueness." (Anthropic ACE Paper)

---

## Strategy Files

### Location

```
project/.claude/
├── strategies.md           # Evolved strategies for this project
└── strategy_log.json       # Raw feedback data for analysis
```

### Template: strategies.md

```markdown
# Orchestrator Strategies

**Project:** [project name]
**Version:** 1
**Last Updated:** [timestamp]
**Feedback Events:** 0

---

## Skill Selection Strategies

Rules for matching skills to tasks, learned from execution feedback.

### Domain-Specific Rules
| Domain | Rule | Learned From | Confidence |
|--------|------|--------------|------------|
| | | | |

### Task Type Rules
| Task Type | Preferred Skills | Avoid | Learned From |
|-----------|-----------------|-------|--------------|
| | | | |

### Pairing Rules
| When Using | Also Include | Reason | Learned From |
|------------|--------------|--------|--------------|
| | | | |

---

## Context Gathering Strategies

Rules for what context to include, learned from agent performance.

### Inclusion Rules
| Condition | Include | Exclude | Learned From |
|-----------|---------|---------|--------------|
| | | | |

### Limit Adjustments
| Complexity | Default Limit | Adjusted Limit | Reason |
|------------|---------------|----------------|--------|
| | | | |

---

## Agent Configuration Strategies

Rules for model selection and agent setup.

### Model Overrides
| Condition | Default Model | Override To | Reason |
|-----------|---------------|-------------|--------|
| | | | |

### Complexity Adjustments
| Pattern | Adjust Complexity | Reason | Learned From |
|---------|-------------------|--------|--------------|
| | | | |

---

## Anti-Patterns

Things that don't work for this project. Avoid these.

| Anti-Pattern | Why It Failed | Task | Date |
|--------------|---------------|------|------|
| | | | |

---

## Strategy Changelog

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| 1 | [date] | Initial | Project start |

---

*Auto-updated based on execution feedback*
```

---

## Feedback Collection

### When to Collect Feedback

```
COLLECT feedback when:
    - Task completes (success or failure)
    - Agent reports gotcha or pattern
    - Same error occurs twice
    - Task takes significantly longer than expected
    - User intervenes during execution
```

### Feedback Event Schema

```json
{
  "id": "feedback-001",
  "timestamp": "2024-12-10T14:30:00Z",
  "task_id": "task-005",
  "event_type": "task_completion | error_repeat | user_intervention | performance_anomaly",

  "context": {
    "task_type": "implementation",
    "complexity": "normal",
    "model": "sonnet",
    "skills_used": ["html5_canvas", "game_feel"],
    "context_tokens": 1500,
    "duration_minutes": 12
  },

  "outcome": {
    "status": "completed | partial | failed | blocked",
    "acceptance_criteria_met": 3,
    "acceptance_criteria_total": 4,
    "errors_encountered": 1,
    "iterations_required": 1
  },

  "signals": {
    "skill_mismatch": false,
    "context_insufficient": false,
    "context_excessive": false,
    "model_inadequate": false,
    "pattern_discovered": true,
    "gotcha_discovered": false
  },

  "notes": "Agent discovered caching pattern that improved performance"
}
```

---

## Strategy Update Rules

### Rule 1: Skill Selection Adjustment

```
WHEN task fails AND agent reports skill_mismatch:
    RECORD anti-pattern:
        skills_used → "Don't use for [task_type] in [domain]"

    IF alternative skill exists:
        ADD to preferred skills for this task type
        INCREMENT confidence for alternative

WHEN task succeeds AND agent discovers pattern:
    IF pattern relates to skill:
        ADD pairing rule:
            "When using [skill_A], also include [skill_B]"
```

**Example Evolution:**

```markdown
### Pairing Rules
| When Using | Also Include | Reason | Learned From |
|------------|--------------|--------|--------------|
| html5_canvas | security_reviewer | Missed XSS in canvas text rendering | task-015 |
| api_designer | documentation | API changes broke consumer docs | task-022 |
```

### Rule 2: Context Limit Adjustment

```
WHEN agent reports context_insufficient:
    IF complexity == "easy":
        INCREASE limit for this task type
        LOG: "Easy tasks of type [X] need more context"

WHEN agent reports context_excessive (token limit hit):
    DECREASE limit for this complexity
    ADD filter rule for less relevant context types

WHEN same pattern queried > 3 times in session:
    PROMOTE pattern to "always include" for this domain
```

**Example Evolution:**

```markdown
### Limit Adjustments
| Complexity | Default Limit | Adjusted Limit | Reason |
|------------|---------------|----------------|--------|
| easy | 5 code refs | 8 code refs | Auth tasks need more context | task-008 |

### Inclusion Rules
| Condition | Include | Exclude | Learned From |
|-----------|---------|---------|--------------|
| auth tasks | all gotchas | low-severity patterns | task-012 (security miss) |
```

### Rule 3: Model Override

```
WHEN task fails with model_inadequate signal:
    IF complexity was "easy" AND model was "haiku":
        ADD override: "Upgrade to sonnet for [task_type] tasks"

WHEN opus task succeeds easily (< 5 min, 0 errors):
    CONSIDER downgrade: "Try sonnet for [pattern] tasks"
    (Don't auto-apply, just note for review)
```

**Example Evolution:**

```markdown
### Model Overrides
| Condition | Default Model | Override To | Reason |
|-----------|---------------|-------------|--------|
| refactor + typescript | sonnet | opus | Type inference complexity | task-019 |
| testing + simple assertions | sonnet | haiku | Over-specified, haiku sufficient | task-025 |
```

### Rule 4: Anti-Pattern Recording

```
WHEN same error occurs twice:
    RECORD anti-pattern with:
        - What was attempted
        - Why it failed
        - What to do instead

WHEN user intervenes to fix agent mistake:
    PROMPT: "What should the agent have done differently?"
    RECORD as anti-pattern
```

**Example Evolution:**

```markdown
## Anti-Patterns

| Anti-Pattern | Why It Failed | Task | Date |
|--------------|---------------|------|------|
| Using game_feel for menu UI | Adds unnecessary physics to static elements | task-007 | 2024-12-10 |
| Loading full file in context | Token overflow, agent lost focus | task-011 | 2024-12-10 |
```

---

## Strategy Application

### At Task Planning Time

```
FUNCTION applyStrategies(task, base_skills, base_context_limits):
    strategies = LOAD strategies.md

    # Apply skill pairing rules
    FOR rule IN strategies.skill_selection.pairing_rules:
        IF base_skills CONTAINS rule.when_using:
            base_skills.ADD(rule.also_include)

    # Apply skill exclusion rules
    FOR anti IN strategies.anti_patterns:
        IF anti.applies_to(task):
            base_skills.REMOVE(anti.skill)

    # Apply context limit adjustments
    FOR adj IN strategies.context_gathering.limit_adjustments:
        IF adj.matches(task.complexity, task.type):
            base_context_limits.APPLY(adj.adjusted_limit)

    # Apply model overrides
    FOR override IN strategies.agent_configuration.model_overrides:
        IF override.condition.matches(task):
            task.model = override.override_to

    RETURN {skills: base_skills, limits: base_context_limits, model: task.model}
```

### At Execution Feedback Time

```
FUNCTION processExecutionFeedback(task, result):
    feedback = collectFeedback(task, result)
    APPEND feedback TO strategy_log.json

    # Analyze for strategy updates
    updates = analyzeForStrategyUpdates(feedback)

    IF updates.NOT_EMPTY:
        FOR update IN updates:
            APPLY update TO strategies.md
            LOG update to changelog

        INCREMENT strategies.version
        UPDATE strategies.last_updated
```

---

## Strategy Confidence

### Confidence Levels

| Level | Threshold | Meaning |
|-------|-----------|---------|
| `low` | 1-2 events | Tentative, may be coincidence |
| `medium` | 3-5 events | Pattern emerging |
| `high` | 6+ events | Reliable strategy |

### Confidence Decay

```
EVERY 20 tasks:
    FOR strategy IN strategies:
        IF strategy.last_applied > 10 tasks ago:
            strategy.confidence -= 1

        IF strategy.confidence == 0:
            MOVE to "review needed" section
            (Don't auto-delete, human review)
```

---

## Manual Strategy Input

Users can directly add strategies:

```
/strategy add skill-pairing "When using api_designer, include security_reviewer for public APIs"
/strategy add anti-pattern "Don't use game_feel for data visualization"
/strategy add model-override "Use opus for database schema migrations"
```

These are marked as `source: manual` and start with `high` confidence.

---

## Strategy Export/Import

### Export for New Projects

```
/strategy export [domain]

→ Creates: strategies_export_[domain]_[date].md
   Filters to strategies relevant to specified domain
   Strips project-specific task references
```

### Import to New Project

```
/strategy import [file]

→ Imports strategies with confidence reduced by 1 level
   (High → Medium, Medium → Low)
   Marks as imported, tracks original source
```

---

## Integration with Other Systems

### Knowledge Graph

```
WHEN strategy updated:
    CREATE node in knowledge_graph:
        type: "strategy"
        tags: [extracted from strategy content]
        summary: strategy description
        file: "strategies.md"
```

### Cold State (orchestrator_memory.md)

```
WHEN significant strategy discovered:
    APPEND to orchestrator_memory.strategy_notes:
        - What's working
        - What's not working
```

### Hot State (session_state.md)

```
DURING session:
    TRACK in working memory:
        - Strategies applied this session
        - Feedback events collected
        - Pending strategy updates
```

---

## Template: strategy_log.json

```json
{
  "version": 1,
  "project": "",
  "events": []
}
```

---

*Strategy Evolution System Version: 1.0*
