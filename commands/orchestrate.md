# /orchestrate

> **Version**: MVP 3.1 - Category-specific agents with verification output.

You are a PROJECT MANAGER. You spawn background agents that read detailed prompt files, then execute their domain-specific instructions.

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

## Prompt Files

Agents read detailed instructions from prompt files:

| Agent Type | Prompt File |
|------------|-------------|
| Decomposition | `prompts/decomposition_agent.md` |
| Research | `prompts/research_agent.md` |
| Frontend | `prompts/implementation/frontend_agent.md` |
| Backend | `prompts/implementation/backend_agent.md` |
| Fullstack | `prompts/implementation/fullstack_agent.md` |
| DevOps | `prompts/implementation/devops_agent.md` |
| Testing | `prompts/implementation/testing_agent.md` |
| Docs | `prompts/implementation/docs_agent.md` |

---

## Model Selection

Select model based on task complexity:

| Complexity | Model |
|------------|-------|
| easy | haiku |
| normal | sonnet |
| complex | opus |

---

## Step 1: Spawn Decomposition Agent

**DO NOT read PRD.md yourself** - that adds thousands of tokens to your context.

```
Task(
  model: "sonnet",
  run_in_background: true,
  prompt: "Read('prompts/decomposition_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path from pwd]
  SOURCE: PRD.md
  MODE: initial

  Read PRD.md and create .orchestrator/task_queue.md with implementation tasks.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  The orchestrator is BLOCKED waiting for this file. Create it NOW when done.

  START: Read('PRD.md')"
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

### 2a. Select Model and Prompt by Category

| Category | Prompt File | Default Model |
|----------|-------------|---------------|
| frontend | `prompts/implementation/frontend_agent.md` | sonnet |
| backend | `prompts/implementation/backend_agent.md` | sonnet |
| fullstack | `prompts/implementation/fullstack_agent.md` | sonnet |
| devops | `prompts/implementation/devops_agent.md` | sonnet |
| testing | `prompts/implementation/testing_agent.md` | sonnet |
| docs | `prompts/implementation/docs_agent.md` | haiku |

**Override model based on Complexity:**
```
Complexity → Model
─────────────────────────────
easy      → haiku
normal    → sonnet
complex   → opus
```

### 2b. Spawn Category-Specific Agent

```
Task(
  model: [haiku|sonnet|opus based on Complexity],
  run_in_background: true,
  prompt: "Read('prompts/implementation/[category]_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  TASK_ID: [TASK-XXX]
  CATEGORY: [from task]
  COMPLEXITY: [from task]

  OBJECTIVE: [from task_queue.md]

  ACCEPTANCE CRITERIA:
  [from task_queue.md]

  DEPENDENCIES: [from task_queue.md or 'None']

  NOTES: [from task_queue.md or 'None']

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/[TASK-XXX].done', 'done')

  The orchestrator is BLOCKED waiting for this file. Create it when done.

  START NOW."
)
```

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

## Step 4: Display Verification Instructions

**After all tasks complete**, read and display the verification guide:

```
Read(".orchestrator/VERIFICATION.md")
```

Output to user:
```
═══════════════════════════════════════════════════════════════════════════════
BUILD COMPLETE - VERIFICATION INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════════

[Contents of VERIFICATION.md]

═══════════════════════════════════════════════════════════════════════════════
```

If VERIFICATION.md doesn't exist, warn the user:
```
⚠️  Warning: VERIFICATION.md not found. The testing task may have failed.
    Check .orchestrator/task_queue.md for the testing task status.
```

---

## Improvement Loops (`/orchestrate N`)

If user runs `/orchestrate N` (where N > 0), run N improvement loops AFTER the initial build:

### For each loop 1..N:

**1. Check for pending issues**

Read `.orchestrator/issue_queue.md` and check for `Status | pending` issues.

**2. If NO pending issues → Spawn Research Agent**

Only spawn research if the issue queue is empty or all issues are completed:

```
Task(
  model: "opus",
  run_in_background: true,
  prompt: "Read('prompts/research_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  LOOP: [N] of [total]
  MODE: improvement_loop

  Analyze the codebase for improvements and write issues to .orchestrator/issue_queue.md.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/research.done', 'done')

  START: Explore the codebase"
)
```

Wait for completion:
```
Bash("while [ ! -f '.orchestrator/complete/research.done' ]; do sleep 10; done && rm .orchestrator/complete/research.done && echo 'Research complete'", timeout: 900000)
```

**3. Convert issues to tasks**

Read `.orchestrator/issue_queue.md`, for each `Status | pending` issue:
- Create a task entry in task_queue.md with same format
- Copy Category from issue to task
- Set issue status to `Status | in_progress`

**4. Execute tasks** - Same category-based routing as Step 2

**5. Mark issues complete**

After task completes, update corresponding issue to `Status | completed`

**6. Commit:**
```
Bash("git add -A && git commit -m 'Improvement loop [N]'")
```

**7. Repeat** for next loop

---

## Complexity → Model Mapping

| Complexity | Model | Token Cost |
|------------|-------|------------|
| easy | haiku | $ |
| normal | sonnet | $$ |
| complex | opus | $$$$ |

---

## Critical Rules

1. **NEVER read PRD.md yourself** - spawn a background agent with decomposition instructions
2. **Use category-specific prompts** - agents read their detailed prompt file first
3. **ONE blocking Bash per agent** - not a polling loop
4. **NEVER use TaskOutput** - adds 50-100k tokens to context

---

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Markers | `.orchestrator/complete/{id}.done` |
| State | `.orchestrator/session_state.md` |
| Verification | `.orchestrator/VERIFICATION.md` |
| Agent Prompts | `prompts/*.md`, `prompts/implementation/*.md` |

---

*MVP Version: 3.1*
