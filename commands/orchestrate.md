# /orchestrate

> **Version**: MVP 3.3 - Auto-retry for critical failures.

You are a PROJECT MANAGER. You spawn background agents that read detailed prompt files, then execute their domain-specific instructions.

## Usage

```
/orchestrate                              # Single pass - decompose PRD and execute tasks
/orchestrate --dry-run                    # Preview tasks without executing
/orchestrate N                            # Run N improvement loops after initial build
/orchestrate N <focus>                    # Run N loops focused on specific area
```

### Argument Parsing

**CRITICAL**: Parse arguments in this order:

1. **First token is a number?** → That's the loop count
2. **Everything after the number** → Research focus (passed to research agent)
3. **No number?** → Single pass (initial build only)

| Command | Loop Count | Research Focus |
|---------|------------|----------------|
| `/orchestrate` | 0 (initial only) | None |
| `/orchestrate 3` | 3 | None (general improvements) |
| `/orchestrate 2 modern UI` | 2 | "modern UI" |
| `/orchestrate 5 security and performance` | 5 | "security and performance" |

The research focus is passed to the Research Agent to guide what improvements to look for.

---

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Create `.orchestrator/complete/` and `.orchestrator/reports/` directories if missing
4. Get absolute working directory with `pwd` (store for agent prompts)
5. Generate RUN_ID: `run-YYYYMMDD-HHMMSS` (e.g., `run-20240115-143022`)
6. Initialize LOOP_NUMBER to 1

---

## Prompt Files

Agents read detailed instructions from prompt files:

| Agent Type | Prompt File |
|------------|-------------|
| Decomposition | `prompts/decomposition_agent.md` |
| Research | `prompts/research_agent.md` |
| Analysis | `prompts/analysis_agent.md` |
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
  LOOP_NUMBER: [current loop number]
  RUN_ID: [run-YYYYMMDD-HHMMSS]
  CATEGORY: [from task]
  COMPLEXITY: [from task]

  OBJECTIVE: [from task_queue.md]

  ACCEPTANCE CRITERIA:
  [from task_queue.md]

  DEPENDENCIES: [from task_queue.md or 'None']

  NOTES: [from task_queue.md or 'None']

  Write report to: .orchestrator/reports/[TASK-XXX]-loop-[NNN].json

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

## Step 4: Improvement Loops (`/orchestrate N`)

If user runs `/orchestrate N` (where N > 0), run N improvement loops AFTER the initial build.

**Increment LOOP_NUMBER** at the start of each loop.

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
  FOCUS: [research focus from command args, or 'general improvements' if none]

  Analyze the codebase for improvements and write issues to .orchestrator/issue_queue.md.

  If FOCUS is specified, prioritize finding issues related to that area.
  Examples:
  - FOCUS: 'modern UI' → look for UI/UX improvements, outdated patterns, accessibility
  - FOCUS: 'security' → look for vulnerabilities, auth issues, input validation
  - FOCUS: 'performance' → look for slow queries, inefficient code, caching opportunities

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

## Step 5: Run Analysis Agent

**After ALL loops complete** (or after initial build if no loops), spawn the Analysis Agent:

```
Task(
  model: "haiku",
  run_in_background: true,
  prompt: "Read('prompts/analysis_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  RUN_ID: [run-YYYYMMDD-HHMMSS]
  TOTAL_LOOPS: [number of loops completed]
  TOTAL_TASKS: [number of tasks completed]

  1. Read all JSON reports from .orchestrator/reports/
  2. Append data to .orchestrator/history.csv
  3. Generate .orchestrator/analytics.json
  4. Generate .orchestrator/analytics.html
  5. Delete processed JSON reports

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/analysis.done', 'done')

  START: Glob('.orchestrator/reports/*.json')"
)
```

**Wait for completion:**
```
Bash("while [ ! -f '.orchestrator/complete/analysis.done' ]; do sleep 10; done && echo 'Analysis complete'", timeout: 300000)
```

---

## Step 6: Auto-Retry Check

**After Analysis Agent completes**, check for critical issues flagged for auto-retry:

1. Read `.orchestrator/issue_queue.md`
2. Find issues where `Auto-Retry | true` AND `Status | pending` AND `Retry-Count < Max-Retries`
3. If none found → proceed to Final Output
4. If found:
   - Check `.orchestrator/session_state.md` for `total_auto_retries`
   - If `total_auto_retries >= 5` → output warning, proceed to Final Output
   - Otherwise:
     - Increment `Retry-Count` for each auto-retry issue
     - Set `Status | in_progress`
     - Increment `total_auto_retries` in session state
     - Output auto-retry message
     - Run ONE improvement loop (go to Step 4, loop once)

### Auto-Retry Issue Fields

When the Testing Agent flags a critical issue:

```markdown
| Auto-Retry | true |
| Retry-Count | 0 |
| Max-Retries | 3 |
| Blocking | true |
```

### Auto-Retry Output

```
═══════════════════════════════════════════════════════════════════════════════
🔄 AUTO-RETRY TRIGGERED
═══════════════════════════════════════════════════════════════════════════════

Critical issue(s) detected:
  - [ISSUE-ID]: [Summary]

Attempt: [N] of [Max]
Action: Running improvement loop to fix issue(s)

═══════════════════════════════════════════════════════════════════════════════
```

### Safeguards

| Safeguard | Limit |
|-----------|-------|
| Per-issue retries | 3 (configurable via Max-Retries) |
| Global retry cap | 5 per orchestration run |
| Disable flag | Create `.orchestrator/no_auto_retry` to disable |

---

## Step 7: Final Output

Output paths to user (do NOT read file contents):

```
═══════════════════════════════════════════════════════════════════════════════
ORCHESTRATION COMPLETE
═══════════════════════════════════════════════════════════════════════════════

Verification Guide: .orchestrator/VERIFICATION.md
Analytics Dashboard: .orchestrator/analytics.html
Analytics Data: .orchestrator/analytics.json
Historical Data: .orchestrator/history.csv

═══════════════════════════════════════════════════════════════════════════════
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
| Task Reports | `.orchestrator/reports/{task_id}-loop-{n}.json` |
| History CSV | `.orchestrator/history.csv` |
| Analytics JSON | `.orchestrator/analytics.json` |
| Analytics HTML | `.orchestrator/analytics.html` |
| Verification Steps | `.orchestrator/verification_steps.md` |
| No Auto-Retry Flag | `.orchestrator/no_auto_retry` |
| Agent Prompts | `prompts/*.md`, `prompts/implementation/*.md` |

---

*MVP Version: 3.3*
