# /orchestrate

> **Version**: MVP 2.0 - Pre-configured agent profiles with category-based routing.

You are a PROJECT MANAGER. You spawn specialized agents and route tasks by category.

## Usage

```
/orchestrate              # Single pass - decompose PRD and execute tasks
/orchestrate --dry-run    # Preview tasks without executing
```

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Create `.orchestrator/complete/` directory if missing
4. Get absolute working directory with `pwd` (store for agent prompts)

---

## Agent Catalog

Pre-configured agents in `.claude/agents/`:

| Agent | Category | Skills | Use For |
|-------|----------|--------|---------|
| `decomposition-agent` | - | decomposition_agent | Breaking PRD into tasks |
| `frontend-agent` | frontend | frontend_design, ui-generator | UI, React, styling |
| `backend-agent` | backend | api_development, database_designer | API, database, server |
| `qa-agent` | testing | qa_agent, webapp_testing | Tests, validation |
| `general-purpose` | fullstack, devops, docs | (built-in) | Everything else |
| `Explore` | research | (built-in, read-only) | Codebase analysis |

---

## Step 1: Spawn Decomposition Agent

**DO NOT read PRD.md yourself** - that adds thousands of tokens to your context.

```
Task(
  subagent_type: "decomposition-agent",
  run_in_background: true,
  prompt: "WORKING_DIR: [absolute path from pwd]"
)
```

**Wait for completion:**
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && echo 'Decomposition complete'", timeout: 600000)
```

---

## Step 2: Execute Implementation Tasks

Read `.orchestrator/task_queue.md` to get pending tasks.

For each task with `Status | pending`:

### 2a. Select Agent by Category

```
Category → Agent
─────────────────────────────
frontend  → frontend-agent
backend   → backend-agent
testing   → qa-agent
fullstack → general-purpose
devops    → general-purpose
docs      → general-purpose
```

### 2b. Spawn Agent

```
Task(
  subagent_type: "[agent from category mapping]",
  model: [haiku|sonnet|opus based on Complexity],
  run_in_background: true,
  prompt: "WORKING_DIR: [absolute path]
  TASK_ID: [TASK-XXX]

  OBJECTIVE: [from task_queue.md]

  ACCEPTANCE CRITERIA:
  [from task_queue.md]"
)
```

The agent profile already includes:
- Skill loading instructions
- Completion marker requirements
- Best practices for its domain

### 2c. Wait for Completion

```
Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ]; do sleep 10; done && echo '[TASK-ID] done'", timeout: 1800000)
```

### 2d. Update Status

Change `Status | pending` to `Status | completed` in task_queue.md.

### 2e. Repeat

Continue with next pending task.

---

## Step 3: Finalize Initial Build

After all PRD tasks complete:

```
Write(".orchestrator/session_state.md", "initial_prd_tasks_complete: true")
Bash("git add -A && git commit -m 'Initial build complete'")
```

---

## Improvement Loops (`/orchestrate N`)

If user runs `/orchestrate N` (where N > 0), run N improvement loops AFTER the initial build:

### For each loop 1..N:

**1. Spawn Research Agent** (uses built-in Explore agent)
```
Task(
  subagent_type: "Explore",
  prompt: "Analyze the codebase for potential improvements.
  Write findings to .orchestrator/issue_queue.md with Category field."
)
```

**2. Convert issues to tasks** - Add to task_queue.md with same format

**3. Execute tasks** - Same category-based routing as Step 2

**4. Commit:**
```
Bash("git add -A && git commit -m 'Improvement loop [N]'")
```

---

## Complexity → Model Mapping

| Complexity | Model | Token Cost |
|------------|-------|------------|
| easy | haiku | $ |
| normal | sonnet | $$ |
| complex | opus | $$$$ |

---

## Critical Rules

1. **NEVER read PRD.md yourself** - spawn decomposition-agent
2. **Route by Category** - use the right specialized agent
3. **Agents have built-in instructions** - keep prompts minimal
4. **ONE blocking Bash per agent** - not a polling loop
5. **NEVER use TaskOutput** - adds 50-100k tokens to context

---

## File Paths

| Purpose | Path |
|---------|------|
| Agent Profiles | `.claude/agents/*.md` |
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Markers | `.orchestrator/complete/{id}.done` |
| State | `.orchestrator/session_state.md` |

---

*MVP Version: 2.0*
