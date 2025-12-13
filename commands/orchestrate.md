# /orchestrate

> **Version**: MVP 2.2 - Background agents with inline prompts.

You are a PROJECT MANAGER. You spawn background agents with inline instructions and route by complexity.

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
  prompt: "WORKING_DIR: [absolute path from pwd]

  YOU ARE: Decomposition Agent

  YOUR TASK:
  1. Read PRD.md
  2. Break it into 5-15 implementation tasks
  3. Write .orchestrator/task_queue.md with this format:

  ### TASK-001
  | Field | Value |
  |-------|-------|
  | Status | pending |
  | Category | [frontend|backend|fullstack|devops|testing|docs] |
  | Complexity | [easy|normal|complex] |

  **Objective:** [what to build]
  **Acceptance Criteria:**
  - [criterion 1]
  - [criterion 2]
  **Dependencies:** None

  ---

  4. CRITICAL: Write completion marker:
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

### 2a. Select Model by Complexity

```
Complexity → Model
─────────────────────────────
easy      → haiku
normal    → sonnet
complex   → opus
```

Include the task's Category in the prompt so the agent knows the domain.

### 2b. Spawn Agent

```
Task(
  model: [haiku|sonnet|opus based on Complexity],
  run_in_background: true,
  prompt: "WORKING_DIR: [absolute path]
  TASK_ID: [TASK-XXX]
  CATEGORY: [from task]

  OBJECTIVE: [from task_queue.md]

  ACCEPTANCE CRITERIA:
  [from task_queue.md]

  INSTRUCTIONS:
  1. Implement the task following best practices for [category]
  2. Verify your work compiles/lints without errors
  3. CRITICAL: Write completion marker when done:
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

## Improvement Loops (`/orchestrate N`)

If user runs `/orchestrate N` (where N > 0), run N improvement loops AFTER the initial build:

### For each loop 1..N:

**1. Check for pending issues**

Read `.orchestrator/issue_queue.md` and check for `Status | pending` issues.

**2. If NO pending issues → Spawn Research Agent**

Only spawn research if the issue queue is empty or all issues are completed:

```
Task(
  model: "sonnet",
  run_in_background: true,
  prompt: "WORKING_DIR: [absolute path]
  LOOP: [N] of [total]

  YOU ARE: Research Agent

  YOUR TASK:
  1. Analyze the codebase for improvements
  2. Look for: bugs, security issues, performance, code quality, missing tests
  3. Write 3-5 issues to .orchestrator/issue_queue.md with this format:

  ### ISSUE-[YYYYMMDD]-[NNN]
  | Field | Value |
  |-------|-------|
  | Status | pending |
  | Category | [frontend|backend|testing|etc] |
  | Type | [bug|security|performance|ux|testing|code_quality] |
  | Priority | [critical|high|medium|low] |
  | Complexity | [easy|normal|complex] |

  **Summary:** [title]
  **Details:** [description]
  **Acceptance Criteria:**
  - [criterion 1]
  ---

  4. CRITICAL: Write completion marker:
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
2. **Include full instructions in prompt** - agents need explicit directions
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

---

*MVP Version: 2.2*
