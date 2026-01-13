---
name: Decomposition Agent
id: decomposition_agent
version: 2.0
category: orchestrator
domain: [orchestration, project-management]
task_types: [planning, decomposition]
keywords: [task-breakdown, PRD, requirements, decomposition, orchestration, tasks, task-queue, issue-queue, TDD, test-first]
complexity: [normal]
pairs_with: [agent_construction, testing_agent]
source: original
prompt_source: prompts/decomposition_agent.md
---

# Decomposition Agent Skill

> **Role**: Technical Task Manager / Requirements Analyst
> **Purpose**: Break down PRD or issue queue into actionable implementation tasks
> **Source of Truth**: `prompts/decomposition_agent.md`

---

## Quick Reference

This skill provides metadata for the Decomposition Agent. The full prompt with detailed instructions is maintained in:

```
prompts/decomposition_agent.md
```

When spawning this agent, read and follow the prompt source file.

---

## Capabilities Summary

The Decomposition Agent:
- Analyzes PRDs and issue queues
- Creates atomic, testable implementation tasks
- Enforces TDD task ordering (TEST tasks before BUILD tasks)
- Validates 100% test coverage mapping
- Preserves retry fields when converting issues

---

## Modes

| MODE | Source | Behavior |
|------|--------|----------|
| `initial` | PRD.md | Break down all requirements into tasks |
| `improvement_loop` | issue_queue.md | Convert all pending issues to tasks |
| `critical_only` | issue_queue.md | Convert ONLY `Priority | critical` issues |
| `external_spec` | projectspec/*.json | Process spec-final.json + test-plan-output.json |

---

## TDD Task Ordering (v2.0)

**Tests MUST be written BEFORE implementation.**

```
TEST tasks (TASK-T##, Category: testing, Mode: write)
    ↓
BUILD tasks (TASK-###, Dependencies: related TEST tasks)
    ↓
QA verification (TASK-99999)
```

---

## Key Fields for Test Tasks

| Field | Purpose |
|-------|---------|
| `Mode` | `write` (create tests) or `verify` (run tests) |
| `Test IDs` | Which test IDs from test plan this task covers |
| `Integration Level` | `unit` / `mocked` / `real` |
| `Mock Policy` | `none` / `database-seeding-only` / `external-services-only` |
| `Skip If Unavailable` | External services that can be skipped |

---

## Usage

```
Task(
    model: "opus",
    prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

    WORKING_DIR: /path/to/project
    SOURCE: PRD.md
    MODE: initial

    When done: Write('.orchestrator/complete/decomposition.done', 'done')"
)
```

---

## Related Skills

- `testing_agent` - Writes tests before implementation (TDD)
- `implementation_agent` - Implements code to pass existing tests
- `failure_analysis_agent` - Analyzes failed implementations
- `qa_agent` - Spot checks and interactive testing

---

*Skill Version: 2.0 - Updated for TDD workflow*
*Source of Truth: prompts/decomposition_agent.md*
