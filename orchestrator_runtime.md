# Orchestrator Runtime (MVP)

> **Version**: MVP 3.6 - Inline marker cleanup in wait commands.

## Key Principle: Read Prompt Files

Agents read their detailed instructions from prompt files. This keeps prompts:
- **Reusable** - Same prompt file for all tasks of that type
- **Maintainable** - Update once, applies everywhere
- **Consistent** - Reliable outputs across runs

---

## Prompt Files

| Agent Type | Prompt File |
|------------|-------------|
| Decomposition | `.claude/prompts/decomposition_agent.md` |
| Research | `.claude/prompts/research_agent.md` |
| Analysis | `.claude/prompts/analysis_agent.md` |
| **Failure Analysis** | `.claude/prompts/failure_analysis_agent.md` |
| Frontend | `.claude/prompts/implementation/frontend_agent.md` |
| Backend | `.claude/prompts/implementation/backend_agent.md` |
| Fullstack | `.claude/prompts/implementation/fullstack_agent.md` |
| DevOps | `.claude/prompts/implementation/devops_agent.md` |
| Testing | `.claude/prompts/implementation/testing_agent.md` |
| Docs | `.claude/prompts/implementation/docs_agent.md` |

---

## Argument Parsing

**CRITICAL**: Parse as `<loops> [<count> <category>]...`

1. **First token** → LOOP_COUNT (number of loops)
2. **Remaining tokens** → Parse as `<count> <category>` pairs (quotas)
3. **Token without preceding number** → Category with no quota

| Command | Loops | Quotas (per loop) |
|---------|-------|-------------------|
| `/orchestrate` | 0 | Initial only |
| `/orchestrate 3` | 3 | General (no quota) |
| `/orchestrate 3 security` | 3 | Security focus (no quota) |
| `/orchestrate 3 2 security` | 3 | 2 security per loop |
| `/orchestrate 3 2 security 3 UI` | 3 | 2 security + 3 UI per loop |

Store parsed values:
```
LOOP_COUNT: 3
QUOTAS: [
  { category: "security", count: 2 },
  { category: "UI", count: 3 }
]
```

Pass QUOTAS to Research Agent each loop.

---

## Startup

1. Check PRD.md exists
2. Check git → init if needed
3. Create `.orchestrator/complete/` and `.orchestrator/reports/` directories
4. Get absolute working directory with `pwd`
5. Generate RUN_ID: `run-YYYYMMDD-HHMMSS`
6. Initialize LOOP_NUMBER to 1
7. Parse arguments → set LOOP_COUNT and RESEARCH_FOCUS
8. **Run Critical Issue Resolution Loop** (see below)

---

## Critical Issue Resolution Loop (BEFORE any other work)

**This loop runs BEFORE initial processing or improvement loops.**

### Actionable Critical Issues

An issue needs processing if it matches ANY of these conditions:

| Status | Condition | Action |
|--------|-----------|--------|
| `pending` | - | Process normally |
| `accepted` | - | Process normally |
| `in_progress` | Task has `.failed` marker | Run Failure Analysis |
| `in_progress` | Task has `.done` but issue not `completed` | Reset to `pending` (false completion) |

### Stalled Issue Detection

Before counting, check for stalled `in_progress` issues:

1. Find critical in_progress issues with Task Refs:
   ```
   Grep("Task Ref", ".orchestrator/issue_queue.md", output_mode: "content", -B: 10)
   ```

2. For each result showing BOTH `Priority | critical` AND `Status | in_progress`:
   - Extract the Task Ref (e.g., `TASK-078`)
   - Check for markers: `Bash("ls .orchestrator/complete/TASK-078.done .orchestrator/complete/TASK-078.failed 2>/dev/null || echo 'none'")`

3. Handle each stalled task:
   - If `.failed` marker → Spawn Failure Analysis Agent
   - If `.done` marker → Reset issue to `pending`, delete the `.done` marker

### Critical Loop

```
CRITICAL_ITERATION = 0
MAX_CRITICAL_ITERATIONS = 10

WHILE true:
    # First: Handle stalled in_progress issues (resets them to pending)
    # Use Grep to find, then Edit to reset, Bash to delete markers

    # Then: Count actionable critical issues
    CRITICAL_COUNT = Bash("grep -A3 '| Priority | critical |' .orchestrator/issue_queue.md 2>/dev/null | grep -cE 'Status \\| (pending|accepted)' || echo '0'")

    IF CRITICAL_COUNT == 0:
        BREAK  # Exit loop, proceed to normal orchestration

    # Spawn Decomposition Agent with critical_only mode
    Task(
      model: "opus",
      run_in_background: true,
      prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

      ---

      ## Your Task

      WORKING_DIR: [absolute path from pwd]
      SOURCE: .orchestrator/issue_queue.md
      MODE: critical_only

      Read .orchestrator/issue_queue.md and create tasks ONLY for issues with Priority: critical.
      Ignore all non-critical issues.

      For each critical pending/accepted issue:
      1. Create a task in .orchestrator/task_queue.md
      2. Mark the issue as in_progress
      3. Add Task Ref to the issue

      CRITICAL: Write completion marker when done:
      Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

      START: Read('.orchestrator/issue_queue.md')"
    )

    # Wait for completion
    Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done", timeout: 600000)

    # Verify tasks were created, run implementation agents, commit
    # RE-SCAN at end of loop (continues WHILE loop)

    CRITICAL_ITERATION += 1
    IF CRITICAL_ITERATION > MAX_CRITICAL_ITERATIONS:
        HALT "Critical loop exceeded 10 iterations"

    # Process critical issues
    OUTPUT "⚠️ CRITICAL: $CRITICAL_COUNT issues (iteration $CRITICAL_ITERATION)"

    # Spawn Decomposition Agent (critical_only mode)
    Task(
      model: "opus",
      prompt: "Read('.claude/prompts/decomposition_agent.md')...
        MODE: critical_only
        SOURCE: .orchestrator/issue_queue.md"
    )
    Wait for decomposition.done

    # Verify tasks created
    PENDING_TASKS = grep -c "| Status | pending |" .orchestrator/task_queue.md
    IF PENDING_TASKS == 0:
        HALT "ERROR: Critical issues exist but no tasks created"

    # Run implementation agents on critical tasks
    FOR each pending task:
        Spawn implementation agent
        Wait for completion
        Update task status

    # Commit and RE-SCAN (loop continues)
    Bash("git add -A && git commit -m 'Critical fixes iteration $CRITICAL_ITERATION'")

# Only reaches here when CRITICAL_COUNT == 0
OUTPUT "✓ Critical queue clear. Proceeding with normal orchestration."
```

**Key points:**
- Runs at startup BEFORE initial PRD processing or improvement loops
- Loops until ALL critical issues resolved
- Re-scans after each iteration (fixes may create new critical issues)
- Safety limit of 10 iterations
- HALTs if tasks aren't created for detected critical issues

---

## Initial Run (`/orchestrate`)

### Step 1: Spawn Decomposition Agent

```
Task(
  model: "opus",
  run_in_background: true,
  prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  SOURCE: PRD.md
  MODE: initial

  Read PRD.md and create .orchestrator/task_queue.md with implementation tasks.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  The orchestrator is BLOCKED waiting for this file. Create it NOW when done.

  START: Read('PRD.md')"
)
```

Wait for completion:
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)
```

### Step 2: Execute Tasks

For each pending task in `.orchestrator/task_queue.md`:

1. **Select prompt file by category:**
   ```
   Category → Prompt File
   ─────────────────────────────────────────────
   frontend  → .claude/prompts/implementation/frontend_agent.md
   backend   → .claude/prompts/implementation/backend_agent.md
   fullstack → .claude/prompts/implementation/fullstack_agent.md
   devops    → .claude/prompts/implementation/devops_agent.md
   testing   → .claude/prompts/implementation/testing_agent.md
   docs      → .claude/prompts/implementation/docs_agent.md
   ```

2. **Select model by complexity:**
   ```
   Complexity → Model
   ─────────────────────────────
   easy      → haiku
   normal    → sonnet
   complex   → opus
   ```

3. **Spawn agent:**
   ```
   Task(
     model: [haiku|sonnet|opus based on complexity],
     run_in_background: true,
     prompt: "Read('.claude/prompts/implementation/[category]_agent.md') and follow those instructions.

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

4. **Wait for completion, check result, clean up (single command):**
   ```
   Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ] && [ ! -f '.orchestrator/complete/[TASK-ID].failed' ]; do sleep 10; done && (test -f '.orchestrator/complete/[TASK-ID].done' && echo 'SUCCESS' || echo 'FAILED') && rm -f .orchestrator/complete/[TASK-ID].done .orchestrator/complete/[TASK-ID].failed", timeout: 1800000)
   ```

5. **Handle result based on output:**
   - If output shows `SUCCESS`: Update task status to "completed" in task_queue.md
   - If output shows `FAILED`: Spawn Failure Analysis Agent (see below)

6. **After all tasks:**
   ```
   Write(".orchestrator/session_state.md", "initial_prd_tasks_complete: true")
   Bash("git add -A && git commit -m 'Initial build complete'")
   ```

---

## Failure Analysis (When Task Fails)

When a `.failed` marker is detected, spawn the Failure Analysis Agent:

```
Task(
  model: "opus",  # Deep analysis requires strong reasoning
  run_in_background: true,
  prompt: "Read('.claude/prompts/failure_analysis_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  TASK_ID: [TASK-XXX]
  LOOP_NUMBER: [current loop number]
  RUN_ID: [run-YYYYMMDD-HHMMSS]

  The implementation agent failed after 3 attempts.
  Analyze the failure and create remediation issues with Priority: critical.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/analysis-[TASK-XXX].done', 'done')

  START: Read('.orchestrator/reports/[TASK-XXX]-loop-[N].json')"
)
```

Wait for analysis completion:
```
Bash("while [ ! -f '.orchestrator/complete/analysis-[TASK-ID].done' ]; do sleep 10; done && echo 'done'", timeout: 600000)
```

**Result**: Failure Analysis Agent creates issue(s) with `Priority | critical` in issue_queue.md.
These will be processed in the next loop (or trigger CRITICAL_MODE if detected at startup).

---

## Improvement Loops (`/orchestrate N`)

**Increment LOOP_NUMBER** at the start of each loop.

For each loop 1..N:

### 1. Check for Outstanding Issues

```bash
OUTSTANDING_COUNT=$(grep -cE "Status \| (pending|accepted)" .orchestrator/issue_queue.md 2>/dev/null || echo "0")
```

**If OUTSTANDING_COUNT > 0:**
- Skip Research Agent
- Output: `⏭️ Skipping Research Agent - $OUTSTANDING_COUNT outstanding issue(s) to process first`
- Go directly to Step 2 (Decomposition)

**If OUTSTANDING_COUNT == 0:**
- Proceed with Research Agent

### 2. Research Agent (only if queue is clear)

```
Task(
  model: "opus",  # Research requires deep analysis
  run_in_background: true,
  prompt: "Read('.claude/prompts/research_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  LOOP: [N] of [total]
  MODE: improvement_loop

  ## Quotas (REQUIRED items to find this loop)

  [Include QUOTAS from parsed args, or 'general improvements' if none]

  Example with quotas:
  QUOTAS:
  - 2 security
  - 3 UI

  You MUST find exactly 2 security issues AND 3 UI issues this loop.

  Analyze the codebase and write issues to .orchestrator/issue_queue.md.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/research.done', 'done')

  START: Explore the codebase"
)
Bash("while [ ! -f '.orchestrator/complete/research.done' ]; do sleep 10; done && rm .orchestrator/complete/research.done && echo 'done'", timeout: 900000)
```

### 3. Spawn Decomposition Agent (convert issues to tasks)

> Runs regardless of whether Research Agent was skipped.

```
Task(
  model: "opus",
  run_in_background: true,
  prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  SOURCE: issue_queue.md
  MODE: convert_issues

  Read .orchestrator/issue_queue.md and convert pending issues to tasks.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  START: Read('.orchestrator/issue_queue.md')"
)
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && rm .orchestrator/complete/decomposition.done && echo 'done'", timeout: 300000)
```

### 4. Execute Tasks

Read task_queue.md, spawn implementation agents for pending tasks (same as Initial Step 2).

### 5. Mark Tasks Done

When implementation agent's completion marker is detected, update task status to `done`.

### 6. Commit

```
Bash("git add -A && git commit -m 'Loop [LOOP]'")
```

### 7. Repeat

Each iteration re-checks outstanding issues. Research Agent stays skipped until the queue is clear.

---

## Analysis Agent (End of Run)

**After ALL loops complete**, spawn the Analysis Agent:

```
Task(
  model: "haiku",
  run_in_background: true,
  prompt: "Read('.claude/prompts/analysis_agent.md') and follow those instructions.

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
Bash("while [ ! -f '.orchestrator/complete/analysis.done' ]; do sleep 10; done && echo 'done'", timeout: 300000)
```

---

## Auto-Retry Check (End of Loop)

**After Analysis Agent completes**, check for critical issues flagged for auto-retry:

```
READ .orchestrator/issue_queue.md

auto_retry_issues = issues WHERE:
  - Auto-Retry == true
  - Status == pending
  - Retry-Count < Max-Retries

IF auto_retry_issues is empty:
    GOTO Final Output

# Check global cap
READ .orchestrator/session_state.md
IF total_auto_retries >= 5:
    OUTPUT "⚠️ Auto-retry limit (5) reached. Manual intervention required."
    GOTO Final Output

# Trigger retry
FOR each issue IN auto_retry_issues:
    INCREMENT issue.Retry-Count
    SET issue.Status = "in_progress"

INCREMENT session.total_auto_retries
WRITE updated files

OUTPUT:
    "═══════════════════════════════════════════════════════════════════════════════
    🔄 AUTO-RETRY TRIGGERED
    ═══════════════════════════════════════════════════════════════════════════════

    Critical issue(s) detected:
    [list issues]

    Attempt: [retry_count] of [max_retries]
    Action: Running improvement loop to fix issue(s)

    ═══════════════════════════════════════════════════════════════════════════════"

# Run ONE improvement loop targeting auto-retry issues
GOTO "Improvement Loops" (run 1 loop)
```

### Auto-Retry Issue Format

Issues flagged for auto-retry include these fields:

```markdown
| Auto-Retry | true |
| Retry-Count | 0 |
| Max-Retries | 3 |
| Blocking | true |
```

### Safeguards

| Safeguard | Limit |
|-----------|-------|
| Per-issue retries | 3 (configurable via Max-Retries) |
| Global retry cap | 5 per orchestration run |
| Disable flag | `.orchestrator/no_auto_retry` file |

---

## Final Output

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

## Model Selection

| Complexity | Model |
|------------|-------|
| easy | haiku |
| normal | sonnet |
| complex | opus |

## Task Statuses

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `pending` | Not yet started | Spawn implementation agent |
| `in_progress` | Currently being worked on | Wait for completion |
| `completed` | Tests passed, work verified | None (done) |
| `failed` | 3 attempts exhausted, tests still failing | Spawn Failure Analysis Agent |

## Issue Lifecycle

Issues in `.orchestrator/issue_queue.md` follow this lifecycle:

| Status | Meaning | Who Sets It |
|--------|---------|-------------|
| `pending` | New issue, not yet processed | `/issue` command or Research Agent |
| `accepted` | Acknowledged, ready for work | User (manual) |
| `in_progress` | Task created, being worked on | **Decomposition Agent** |
| `completed` | Fix verified, tests pass | **Testing Agent** |
| `wont_fix` | Rejected | `/issue reject` command |

### Issue-to-Task Linkage

When tasks are created from issues:

1. **Decomposition Agent** creates task with `| Source Issue | ISSUE-XXX |` field
2. **Decomposition Agent** marks issue as `in_progress` and adds `| Task Ref | TASK-XXX |`
3. **Testing Agent** verifies task completion
4. **Testing Agent** marks source issue as `completed` (if tests pass)

```
Issue Lifecycle:
  pending ──► in_progress ──► completed
     │             │
     └──► wont_fix │
                   └──► (stays in_progress if tests fail)
```

**Why this matters:** The orchestrator RE-SCANS for critical issues. If issues aren't marked as `in_progress` when tasks are created, or `completed` when verified, the critical loop will process the same issues repeatedly.

## Issue Priority Enforcement

| Priority | When Processed |
|----------|----------------|
| `critical` | Immediately, exclusively (blocks all other work) |
| `high` | Normal mode, first |
| `medium` | Normal mode, second |
| `low` | Normal mode, last |

**Key Rules:**
- Critical issues block ALL other work until resolved
- Failing tests automatically create `Priority: critical` issues
- Research Agent is skipped while critical issues exist
- Once critical queue is empty, normal priority processing resumes

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Completion (success) | `.orchestrator/complete/{id}.done` |
| Completion (failure) | `.orchestrator/complete/{id}.failed` |
| Failure Analysis Done | `.orchestrator/complete/analysis-{id}.done` |
| State | `.orchestrator/session_state.md` |
| Verification | `.orchestrator/VERIFICATION.md` |
| Task Reports | `.orchestrator/reports/{task_id}-loop-{n}.json` |
| History CSV | `.orchestrator/history.csv` |
| Analytics JSON | `.orchestrator/analytics.json` |
| Analytics HTML | `.orchestrator/analytics.html` |
| Verification Steps | `.orchestrator/verification_steps.md` |
| No Auto-Retry Flag | `.orchestrator/no_auto_retry` |
| Agent Prompts | `.claude/prompts/*.md`, `.claude/prompts/implementation/*.md` |

## CRITICAL RULES

1. **NEVER use TaskOutput** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **Use category-specific prompts** - agents read their detailed prompt file first
4. **Manager only** - never write code directly
5. **Pass LOOP_NUMBER and RUN_ID** - to all implementation agents
6. **NEVER spawn ad-hoc agents** - only use predefined agent types
7. **NEVER improvise** - follow the documented flow exactly
8. **ONE Research Agent per loop** - with quotas, not topic-specific agents
9. **Research Agent ONLY when queue is clear** - skip if any pending/accepted issues exist
10. **CAN read task_queue.md** - to know what agents to spawn
11. **CAN mark task as done** - when completion marker detected
12. **NEVER read issue_queue.md fully** - EXCEPT for critical issue scan and outstanding check at startup:
    `grep -A3 "| Priority | critical |" .orchestrator/issue_queue.md | grep -qE "Status \| (pending|accepted)"`
13. **NEVER convert issues to tasks** - Decomposition Agent handles this

### Orchestrator CAN vs CANNOT

| CAN | CANNOT |
|-----|--------|
| Read task_queue.md | Read PRD.md |
| Mark task status as `done` | Read issue_queue.md fully |
| Spawn predefined agents | Convert issues to tasks |
| Wait for completion markers | Modify task content |
| Output final paths | Write code or fix issues |
| Grep issue_queue for critical blockers | Process issue content directly |

### Forbidden Behaviors

| ❌ WRONG | ✅ CORRECT |
|----------|-----------|
| Spawn "Security research agent" | Spawn Research Agent with quotas |
| Read issue_queue.md directly | Spawn Decomposition Agent to convert |
| Convert issues to tasks yourself | Decomposition Agent converts issues |
| `/orchestrate 3 2 security 3 UI` = 2 sec + 3 UI total | = 6 sec + 9 UI total (per loop × loops) |
| Do 2 security in loop 1, 3 UI in loop 2 | Do 2 security + 3 UI in EACH loop |

## Waiting Pattern

```bash
# CORRECT - single blocking call that waits, checks result, AND cleans up markers
Bash("while [ ! -f '.orchestrator/complete/{id}.done' ] && [ ! -f '.orchestrator/complete/{id}.failed' ]; do sleep 10; done && (test -f '.orchestrator/complete/{id}.done' && echo 'SUCCESS' || echo 'FAILED') && rm -f .orchestrator/complete/{id}.done .orchestrator/complete/{id}.failed", timeout: 1800000)

# Handle based on output:
# - 'SUCCESS' = task completed, update status
# - 'FAILED' = spawn Failure Analysis Agent

# WRONG - fills context
while not exists: Bash("sleep 5")

# WRONG - separate check/cleanup steps add complexity
Bash("while ... ; do sleep 10; done")
Bash("test -f .done && echo SUCCESS")  # separate check
Bash("rm -f .done .failed")             # separate cleanup
```

---

*MVP Runtime Version: 3.6*
