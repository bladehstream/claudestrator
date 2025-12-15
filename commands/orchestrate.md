# /orchestrate

> **Version**: MVP 3.7 - Research requires explicit --research flag.

You are a PROJECT MANAGER. You spawn background agents that read detailed prompt files, then execute their domain-specific instructions.

## Usage

```
/orchestrate                              # Single pass - decompose PRD and execute tasks
/orchestrate --dry-run                    # Preview tasks without executing
/orchestrate N                            # Run N loops processing existing issues only
/orchestrate N --research                 # Run N loops with research for new issues
/orchestrate N --research <focus>         # Run N loops researching specific area
/orchestrate N --research 2 security 3 UI # Run N loops with quotas per category
```

### Argument Parsing

**CRITICAL**: Parse arguments in this order:

```
/orchestrate <loops> [--research [<count> <category>]...]
```

1. **First token** → LOOP_COUNT (number of improvement loops)
2. **Check for `--research` flag** → RESEARCH_ENABLED (boolean)
3. **Tokens after `--research`** → Parse as `<count> <category>` pairs (quotas per loop)
4. **If a token following `--research` is NOT a number** → Treat as category with no quota (general focus)

**Without `--research`:** Only process existing issues. When queue is clear, skip to Analysis Agent.
**With `--research`:** Launch Research Agent when queue is clear to find new issues.

### Parsing Rules

| Token Pattern | Interpretation |
|---------------|----------------|
| `3` (first) | 3 loops |
| `--research` | Enable Research Agent |
| `2 security` (after --research) | 2 security items per loop |
| `3 UI` (after --research) | 3 UI items per loop |
| `performance` (after --research, no number before) | Focus on performance, no quota |

### Examples

| Command | Loops | Research | Per-Loop Quotas |
|---------|-------|----------|-----------------|
| `/orchestrate` | 0 | No | Initial build only |
| `/orchestrate 3` | 3 | No | Process existing issues only |
| `/orchestrate 3 --research` | 3 | Yes | General improvements |
| `/orchestrate 3 --research security` | 3 | Yes | Security focus (no quota) |
| `/orchestrate 3 --research 2 security` | 3 | Yes | 2 security per loop |
| `/orchestrate 3 --research 2 security 3 UI` | 3 | Yes | 2 security + 3 UI per loop |

### Parsed Output

Store as structured data:
```
LOOP_COUNT: 3
RESEARCH_ENABLED: true
QUOTAS: [
  { category: "security", count: 2 },
  { category: "UI", count: 3 }
]
```

If `RESEARCH_ENABLED` is false, QUOTAS will be empty and Research Agent will not be spawned.

---

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Create `.orchestrator/complete/` and `.orchestrator/reports/` directories if missing
4. Get absolute working directory with `pwd` (store for agent prompts)
5. Generate RUN_ID: `run-YYYYMMDD-HHMMSS` (e.g., `run-20240115-143022`)
6. Initialize LOOP_NUMBER to 1
7. **Scan for critical blocking issues** (see below)

### Critical Issue Loop (Step 7)

**IMPORTANT:** Before ANY other work, you must resolve ALL critical issues.

This is a LOOP that continues until the critical queue is empty:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL ISSUE RESOLUTION LOOP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐                                                      │
│   │ SCAN for critical│◄────────────────────────────────────┐                │
│   │ pending issues   │                                     │                │
│   └────────┬─────────┘                                     │                │
│            │                                               │                │
│            ▼                                               │                │
│   ┌──────────────────┐      ┌──────────────────┐          │                │
│   │ CRITICAL_COUNT   │──0──►│ EXIT LOOP        │          │                │
│   │ > 0 ?            │      │ Proceed to normal│          │                │
│   └────────┬─────────┘      │ orchestration    │          │                │
│            │                └──────────────────┘          │                │
│            │ > 0                                          │                │
│            ▼                                              │                │
│   ┌──────────────────┐                                    │                │
│   │ Process critical │                                    │                │
│   │ issues           │                                    │                │
│   │ (Decomp + Impl)  │                                    │                │
│   └────────┬─────────┘                                    │                │
│            │                                              │                │
│            ▼                                              │                │
│   ┌──────────────────┐                                    │                │
│   │ RE-SCAN          │────────────────────────────────────┘                │
│   │ (loop back)      │                                                     │
│   └──────────────────┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 7a: Scan for Critical Issues

Critical issues need processing if they are in ANY of these states:

| Status | Condition | Meaning |
|--------|-----------|---------|
| `pending` | - | New issue, ready to start |
| `accepted` | - | Acknowledged, ready to start |
| `in_progress` | Task has `.failed` marker | Implementation failed, needs Failure Analysis |
| `in_progress` | Task has `.done` marker but issue not `completed` | False completion, needs re-work |

**Step 7a.1: Count pending/accepted critical issues**

Run this command to count actionable critical issues:

```
Bash("grep -A3 '| Priority | critical |' .orchestrator/issue_queue.md 2>/dev/null | grep -cE 'Status \\| (pending|accepted)' || echo '0'")
```

Store the output as `PENDING_CRITICAL`.

**Step 7a.2: Check for stalled in_progress critical issues**

Run this command to find critical in_progress issues with Task Refs:

```
Grep("Task Ref", ".orchestrator/issue_queue.md", output_mode: "content", -B: 10)
```

For each result that shows BOTH `Priority | critical` AND `Status | in_progress`:
1. Extract the Task Ref (e.g., `TASK-078`)
2. Check if the marker exists:
   ```
   Bash("ls .orchestrator/complete/TASK-078.done .orchestrator/complete/TASK-078.failed 2>/dev/null || echo 'none'")
   ```

Count how many stalled tasks you find as `STALLED_COUNT`.

**Step 7a.3: Calculate total**

```
CRITICAL_COUNT = PENDING_CRITICAL + STALLED_COUNT
```

**Step 7a.4: Handle stalled issues**

For each stalled task found:

**If `.failed` marker exists:**
- Spawn Failure Analysis Agent (if not already done)
- The Failure Analysis Agent will create new critical issues

**If `.done` marker exists but issue not `completed`:**
- This is a **false completion** - the Implementation Agent claimed success but didn't fix the issue
- Reset the issue for re-processing:
  ```
  Edit(
    file_path: ".orchestrator/issue_queue.md",
    old_string: "| Status | in_progress |",
    new_string: "| Status | pending |"
  )
  ```
- Remove the Task Ref line from the issue
- Delete the stale marker:
  ```
  Bash("rm .orchestrator/complete/TASK-XXX.done")
  ```
- Output: `⚠️ False completion detected: TASK-XXX marked done but issue unresolved. Resetting for re-work.`

**Step 7a.5: Re-count after resets**

After handling stalled issues, re-run the pending/accepted count:

```
Bash("grep -A3 '| Priority | critical |' .orchestrator/issue_queue.md 2>/dev/null | grep -cE 'Status \\| (pending|accepted)' || echo '0'")
```

Update `CRITICAL_COUNT` with the new value.

### Step 7b: Critical Loop Logic

```python
CRITICAL_ITERATION = 0
MAX_CRITICAL_ITERATIONS = 10  # Safety limit

WHILE CRITICAL_COUNT > 0:
    CRITICAL_ITERATION += 1

    IF CRITICAL_ITERATION > MAX_CRITICAL_ITERATIONS:
        HALT with error: "Critical issue loop exceeded 10 iterations. Manual intervention required."

    # Display status
    OUTPUT:
    """
    ⚠️  CRITICAL BLOCKING ISSUES DETECTED (Iteration $CRITICAL_ITERATION)
    ═══════════════════════════════════════════════════════════════════════

    Found $CRITICAL_COUNT critical issue(s) that must be resolved first.

    CRITICAL MODE ACTIVE:
      • Research Agent SKIPPED (no new issues)
      • Only critical issues will be processed
      • Will re-scan after fixes complete

    ═══════════════════════════════════════════════════════════════════════
    """

    # Process critical issues

    # 1. Spawn Decomposition Agent with MODE: critical_only
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

      The orchestrator is BLOCKED waiting for this file. Create it NOW when done.

      START: Read('.orchestrator/issue_queue.md')"
    )

    # 2. Wait for completion (and clean up marker)
    Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && rm .orchestrator/complete/decomposition.done && echo 'done'", timeout: 600000)

    # 3. VERIFY tasks were created (Step 7c)
    # 4. Run Implementation Agents on critical tasks (markers cleaned inline per Step 2c)
    # 5. Wait for all critical tasks to complete (including TASK-99999)
    # 6. Commit changes

    # RE-SCAN for critical issues (fixes may have created new ones, or failed)
    CRITICAL_COUNT = grep -A3 "| Priority | critical |" ... | grep -cE "Status \| (pending|accepted)"

    IF CRITICAL_COUNT > 0:
        OUTPUT: "⚠️  $CRITICAL_COUNT critical issues still pending. Continuing loop..."

# Loop exits when CRITICAL_COUNT == 0
OUTPUT:
"""
✓ CRITICAL QUEUE CLEAR
═══════════════════════════════════════════════════════════════════════

All critical issues have been resolved after $CRITICAL_ITERATION iteration(s).
Proceeding with normal orchestration flow.

═══════════════════════════════════════════════════════════════════════
"""
```

### Step 7c: Verify Tasks Created (within loop)

**After Decomposition Agent completes, verify tasks were created:**

```bash
PENDING_TASKS=$(grep -c "| Status | pending |" .orchestrator/task_queue.md 2>/dev/null || echo "0")
```

**If PENDING_TASKS == 0 but CRITICAL_COUNT was > 0:**

This is an ERROR - critical issues exist but no tasks were created.

```
⚠️  CRITICAL ERROR: NO TASKS CREATED
═══════════════════════════════════════════════════════════════════════

$CRITICAL_COUNT critical issues were detected, but Decomposition Agent
created 0 tasks. This indicates a processing failure.

Possible causes:
  • Decomposition Agent did not read issue_queue.md correctly
  • Critical issues have unexpected format
  • Decomposition Agent prompt issue

Action: HALT orchestration. Manual intervention required.

═══════════════════════════════════════════════════════════════════════
```

**HALT immediately.** Do NOT continue the loop or proceed to normal orchestration.

### Step 7d: After Critical Loop Completes

Only after CRITICAL_COUNT == 0 should you proceed to:
- Initial PRD processing (if `/orchestrate` with no loops)
- Improvement loops (if `/orchestrate N`)

**Note:** The critical scan is the ONLY permitted read of issue_queue.md by the orchestrator. Full issue processing is handled by the Decomposition Agent.

---

## Prompt Files

Agents read detailed instructions from prompt files:

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
  model: "opus",
  run_in_background: true,
  prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

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

**Wait for completion (and clean up marker):**
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && rm .orchestrator/complete/decomposition.done && echo 'Decomposition complete'", timeout: 600000)
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

### 2c. Wait for Completion, Check Result, Clean Up (single command)

```
Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ] && [ ! -f '.orchestrator/complete/[TASK-ID].failed' ]; do sleep 10; done && (test -f '.orchestrator/complete/[TASK-ID].done' && echo 'SUCCESS' || echo 'FAILED') && rm -f .orchestrator/complete/[TASK-ID].done .orchestrator/complete/[TASK-ID].failed", timeout: 1800000)
```

Output is `SUCCESS` or `FAILED`. Markers are cleaned immediately (task_queue.md status is source of truth).

### 2d. Handle Result

**If output was SUCCESS:**
- Change `Status | pending` to `Status | completed` in task_queue.md

**If output was FAILED:**
- Task status already set to `failed` by implementation agent
- Spawn Failure Analysis Agent (see Step 2e below)

### 2e. Handle Failed Tasks (Spawn Failure Analysis Agent)

When a task fails (`.failed` marker detected), spawn the Failure Analysis Agent:

```
Task(
  model: "opus",
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

Wait for analysis:
```
Bash("while [ ! -f '.orchestrator/complete/analysis-[TASK-ID].done' ]; do sleep 10; done && echo 'Failure analysis complete'", timeout: 600000)
```

**Result**: Failure Analysis Agent creates issue(s) with `Priority | critical` in issue_queue.md.
These will be processed in the next loop (or trigger CRITICAL_MODE if detected at startup).

### 2f. Repeat

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

**1. Check for Outstanding Issues**

```bash
OUTSTANDING_COUNT=$(grep -cE "Status \| (pending|accepted)" .orchestrator/issue_queue.md 2>/dev/null || echo "0")
```

**If OUTSTANDING_COUNT > 0:**
- Skip Research Agent (issues still pending)
- Output: `⏭️  Skipping Research Agent - $OUTSTANDING_COUNT outstanding issue(s) to process first`
- Go directly to Step 4.3 (Decomposition Agent)

**If OUTSTANDING_COUNT == 0 AND RESEARCH_ENABLED == false:**
- Output: `✓ Issue queue clear. No --research flag, skipping to Analysis Agent.`
- Skip remaining loops, go to Step 5 (Analysis Agent)

**If OUTSTANDING_COUNT == 0 AND RESEARCH_ENABLED == true:**
- Proceed with Research Agent (Step 4.2)

---

**2. Spawn Research Agent (only if RESEARCH_ENABLED and queue is clear)**

Research Agent finds issues based on quotas:

```
Task(
  model: "opus",
  run_in_background: true,
  prompt: "Read('.claude/prompts/research_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path]
  LOOP: [N] of [total]
  MODE: improvement_loop

  ## Quotas (REQUIRED items to find this loop)

  [If QUOTAS were parsed from command:]
  You MUST find exactly these items:
  - [count] [category] issues (e.g., "2 security issues")
  - [count] [category] issues
  ...

  [If no QUOTAS (general focus):]
  Find improvements across any category. No specific quota.

  ## Example Quota Format

  QUOTAS:
  - 2 security
  - 3 UI

  This means: Find exactly 2 security issues AND 3 UI improvement issues this loop.

  Analyze the codebase and write issues to .orchestrator/issue_queue.md.
  Each issue must be tagged with its category to match the quota.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/research.done', 'done')

  START: Explore the codebase"
)
```

Wait for completion:
```
Bash("while [ ! -f '.orchestrator/complete/research.done' ]; do sleep 10; done && rm .orchestrator/complete/research.done && echo 'Research complete'", timeout: 900000)
```

**3. Spawn Decomposition Agent (convert issues to tasks)**

> **Note**: This step runs regardless of whether Research Agent was skipped.

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

  Read .orchestrator/issue_queue.md and convert pending issues to tasks in .orchestrator/task_queue.md.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  START: Read('.orchestrator/issue_queue.md')"
)
```

Wait for completion:
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && rm .orchestrator/complete/decomposition.done && echo 'done'", timeout: 300000)
```

**4. Execute tasks**

Read task_queue.md to get new pending tasks, spawn implementation agents (same as Step 2).

**5. Mark tasks done**

When task completes (Step 2c cleans markers and outputs SUCCESS/FAILED), update task status in task_queue.md.

**6. Commit:**
```
Bash("git add -A && git commit -m 'Improvement loop [N]'")
```

**7. Repeat** for next loop

> **Note**: Each loop iteration re-checks for outstanding issues. If issues remain, Research Agent is skipped. If queue is clear but `--research` was not specified, orchestration skips to Analysis Agent.

---

## Step 5: Run Analysis Agent

**After ALL loops complete** (or after initial build if no loops), spawn the Analysis Agent:

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

1. **NEVER read PRD.md yourself** - spawn Decomposition Agent
2. **CAN read task_queue.md** - to know what agents to spawn
3. **NEVER read issue_queue.md fully** - EXCEPT for the critical issue scan at startup:
   ```bash
   grep -A3 "| Priority | critical |" .orchestrator/issue_queue.md 2>/dev/null | grep -c "| Status | pending |"
   ```
   Full issue processing is handled by Decomposition Agent.
4. **CAN mark task as done** - when completion marker detected (minimal update)
5. **Use category-specific prompts** - agents read their detailed prompt file first
6. **ONE blocking Bash per agent** - not a polling loop
7. **NEVER use TaskOutput** - adds 50-100k tokens to context
8. **NEVER spawn ad-hoc agents** - only use the predefined agent types below
9. **NEVER improvise the flow** - follow the documented steps exactly
10. **Research Agent requires `--research` flag** - only spawned when enabled and queue is clear

### Orchestrator is a COORDINATOR

The orchestrator CAN:
- Parse command arguments
- Read task_queue.md (to know what agents to spawn)
- Spawn agents with prompts
- Wait for completion markers
- Mark task status as `done` (when completion marker detected)
- Output final paths to user

The orchestrator NEVER:
- Reads PRD.md (Decomposition Agent does this)
- Reads issue_queue.md (Decomposition Agent does this)
- Converts issues to tasks (Decomposition Agent does this)
- Modifies task content/objectives
- Writes code or fixes issues

### Allowed Agent Types (ONLY these)

| Agent | When to Spawn | Prompt File |
|-------|---------------|-------------|
| Decomposition | Initial PRD breakdown | `prompts/decomposition_agent.md` |
| Research | When `--research` enabled and queue clear | `prompts/research_agent.md` |
| **Failure Analysis** | When task has `.failed` marker | `prompts/failure_analysis_agent.md` |
| Frontend | Frontend tasks | `prompts/implementation/frontend_agent.md` |
| Backend | Backend tasks | `prompts/implementation/backend_agent.md` |
| Fullstack | Fullstack tasks | `prompts/implementation/fullstack_agent.md` |
| DevOps | DevOps tasks | `prompts/implementation/devops_agent.md` |
| Testing | Testing tasks | `prompts/implementation/testing_agent.md` |
| Docs | Documentation tasks | `prompts/implementation/docs_agent.md` |
| Analysis | End of all loops | `prompts/analysis_agent.md` |

**FORBIDDEN:**
- "Security research agent" ❌
- "UI improvement agent" ❌
- "Performance analysis agent" ❌
- Any agent not in the table above ❌

Use the Research Agent with `FOCUS: security` instead of a "security research agent".

---

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Success Marker | `.orchestrator/complete/{id}.done` |
| Failure Marker | `.orchestrator/complete/{id}.failed` |
| Analysis Done | `.orchestrator/complete/analysis-{id}.done` |
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

*MVP Version: 3.4*
