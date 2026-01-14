# /orchestrate

> **Version**: MVP 4.2 - Test-only mode, skip rate verification, environmental detection.

You are a PROJECT MANAGER. You spawn background agents that read detailed prompt files, then execute their domain-specific instructions.

## Help (--help)

**If the user runs `/orchestrate --help` or `/orchestrate -h`, output this help text and stop:**

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                            /orchestrate - Help                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  USAGE:                                                                        ║
║    /orchestrate [OPTIONS] [LOOPS] [--research [QUOTAS...]]                     ║
║                                                                                ║
║  OPTIONS:                                                                      ║
║    --help, -h              Show this help message                              ║
║    --dry-run               Preview tasks without executing                     ║
║    --test-only             Create/run tests only (skip BUILD/QA)               ║
║    --source <type>         Source type: prd (default) or external_spec         ║
║    --research [quotas]     Enable Research Agent with optional quotas          ║
║                                                                                ║
║  LOOPS:                                                                        ║
║    N                       Number of improvement loops (default: 0)            ║
║                                                                                ║
║  EXAMPLES:                                                                     ║
║    /orchestrate                        Single pass from PRD.md                 ║
║    /orchestrate --dry-run              Preview without executing               ║
║    /orchestrate --test-only            Create tests, verify, skip builds       ║
║    /orchestrate 3                      3 improvement loops                     ║
║    /orchestrate 3 --research           3 loops with research                   ║
║    /orchestrate 3 --research 2 security 3 UI    Quotas per category            ║
║    /orchestrate --source external_spec          Use projectspec/*.json         ║
║                                                                                ║
║  TASK TYPES:                                                                   ║
║    TASK-T##     Test creation (runs first)                                     ║
║    TASK-###     Build/implementation                                           ║
║    TASK-V##     Test verification (runs after build)                           ║
║    TASK-99999   Final QA                                                       ║
║                                                                                ║
║  MODES:                                                                        ║
║    Normal       All tasks: TEST → BUILD → VERIFY → QA                          ║
║    --test-only  TEST → VERIFY only (for testing existing implementation)       ║
║    --dry-run    Show tasks without executing                                   ║
║                                                                                ║
║  See: /claudestrator-help for all commands                                     ║
║                                                                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**After outputting help, do NOT proceed with orchestration. Exit immediately.**

---

## Usage

```
/orchestrate                              # Single pass - decompose PRD and execute tasks
/orchestrate --help                       # Show help message
/orchestrate --dry-run                    # Preview tasks without executing
/orchestrate --test-only                  # Create and verify tests (skip BUILD/QA)
/orchestrate N                            # Run N loops processing existing issues only
/orchestrate N --research                 # Run N loops with research for new issues
/orchestrate N --research <focus>         # Run N loops researching specific area
/orchestrate N --research 2 security 3 UI # Run N loops with quotas per category
/orchestrate --source external_spec       # Use projectspec/*.json instead of PRD.md
```

### Argument Parsing

**CRITICAL**: Parse arguments in this order:

```
/orchestrate <loops> [--dry-run] [--test-only] [--source <source_type>] [--research [<count> <category>]...]
```

1. **First token** → LOOP_COUNT (number of improvement loops)
2. **Check for `--dry-run` flag** → DRY_RUN (boolean) - preview tasks without executing
3. **Check for `--test-only` flag** → TEST_ONLY (boolean) - create and run tests only
4. **Check for `--source` flag** → SOURCE_TYPE (default: "prd", or "external_spec")
5. **Check for `--research` flag** → RESEARCH_ENABLED (boolean)
6. **Tokens after `--research`** → Parse as `<count> <category>` pairs (quotas per loop)
7. **If a token following `--research` is NOT a number** → Treat as category with no quota (general focus)

**Without `--research`:** Only process existing issues. When queue is clear, skip to Analysis Agent.
**With `--research`:** Launch Research Agent when queue is clear to find new issues.
**With `--source external_spec`:** Use projectspec/spec-final.json and projectspec/test-plan-output.json instead of PRD.md.
**With `--test-only`:** Only create and execute TEST (TASK-T##) and VERIFY (TASK-V##) tasks. Skip BUILD and QA tasks. Useful for testing existing implementation.

### Parsing Rules

| Token Pattern | Interpretation |
|---------------|----------------|
| `3` (first) | 3 loops |
| `--dry-run` | Preview tasks without executing |
| `--test-only` | Create tests and verify against existing implementation (skip BUILD/QA) |
| `--source external_spec` | Use projectspec/*.json files |
| `--source prd` | Use PRD.md (default) |
| `--research` | Enable Research Agent |
| `2 security` (after --research) | 2 security items per loop |
| `3 UI` (after --research) | 3 UI items per loop |
| `performance` (after --research, no number before) | Focus on performance, no quota |

### Examples

| Command | Loops | Source | Research | Behavior |
|---------|-------|--------|----------|----------|
| `/orchestrate` | 0 | prd | No | Initial build OR process pending issues (single pass) |
| `/orchestrate 3` | 3 | prd | No | Process existing issues only (3 loops max) |
| `/orchestrate --dry-run` | 0 | prd | No | Preview tasks without executing |
| `/orchestrate --test-only` | 0 | prd | No | Create and verify tests (skip BUILD/QA) |
| `/orchestrate --source external_spec` | 0 | external_spec | No | Build from projectspec/*.json files |
| `/orchestrate 3 --source external_spec` | 3 | external_spec | No | Build + 3 improvement loops |
| `/orchestrate 3 --research` | 3 | prd | Yes | General improvements + new issue discovery |
| `/orchestrate 3 --research security` | 3 | prd | Yes | Security focus (no quota) |
| `/orchestrate 3 --research 2 security` | 3 | prd | Yes | 2 security items per loop |
| `/orchestrate 3 --research 2 security 3 UI` | 3 | prd | Yes | 2 security + 3 UI per loop |

**Note on `/orchestrate` (no loops):**
- On a **new project** (no task_queue.md): Processes PRD.md → creates tasks → executes → Analysis Agent
- On an **existing project** with pending issues: Processes those issues → Analysis Agent
- On an **existing project** with no pending issues: Runs Analysis Agent only

### Parsed Output

Store as structured data:
```
LOOP_COUNT: 3
DRY_RUN: false
TEST_ONLY: false
SOURCE_TYPE: prd | external_spec
RESEARCH_ENABLED: true
QUOTAS: [
  { category: "security", count: 2 },
  { category: "UI", count: 3 }
]
```

If `DRY_RUN` is true, preview tasks without executing any agents.
If `TEST_ONLY` is true, only create and execute TEST (TASK-T##) and VERIFY (TASK-V##) tasks. Skip BUILD and QA tasks.
If `RESEARCH_ENABLED` is false, QUOTAS will be empty and Research Agent will not be spawned.
If `SOURCE_TYPE` is `external_spec`, use projectspec/*.json files instead of PRD.md.

---

## Concurrency Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| MAX_CONCURRENT_AGENTS | 10 | Maximum agents running simultaneously |
| RUNNING_TASKS_FILE | `.orchestrator/running_tasks.txt` | Tracks active task IDs |

**Why this matters:** Without limits, tasks with no dependencies (e.g., all TEST tasks) spawn simultaneously, causing resource exhaustion.

## System Dependencies

No external dependencies required. Completion waits use polling (120-second intervals).

---

## TDD Workflow Overview

The orchestrator enforces **Test-Driven Development**: tests are written BEFORE implementation.

### Task Execution Order

```
1. TEST tasks (TASK-T##) execute first → Test Creation Agent writes tests
2. BUILD tasks (TASK-###) execute after → Implementation Agents code to pass tests
3. VERIFY tasks (TASK-V##) execute after BUILD → Test Verification Agent validates
4. QA Agent spot-checks completed work
```

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| Tests first | TASK-T## tasks run before related TASK-### tasks |
| Dependencies enforced | BUILD tasks depend on their TEST tasks |
| No test modification | Implementation agents read tests, don't modify them |
| Coverage validation | 100% of test plan IDs must map to tasks |

### Task Routing by Category

| Task ID Pattern | Category | Agent Type |
|-----------------|----------|------------|
| TASK-T## | test_creation | Test Creation Agent |
| TASK-V## | test_verification | Test Verification Agent |
| TASK-### | backend | Backend Implementation Agent |
| TASK-### | frontend | Frontend Implementation Agent |
| TASK-### | fullstack | Fullstack Implementation Agent |
| TASK-### | devops | DevOps Implementation Agent |
| TASK-### | docs | Documentation Agent |
| TASK-99999 | qa | QA Agent (final verification) |

The Decomposition Agent creates both TEST and BUILD tasks with proper dependencies. See `prompts/decomposition_agent.md` for task generation rules.

---

## Startup Checklist

1. **Check for existing work FIRST (before requiring source files):**
   ```bash
   # Check for pending issues
   PENDING_ISSUES=$(grep -cE "Status \| (pending|accepted)" .orchestrator/issue_queue.md 2>/dev/null || echo "0")

   # Check for pending tasks
   PENDING_TASKS=$(grep -c "| Status | pending |" .orchestrator/task_queue.md 2>/dev/null || echo "0")

   # Check if task queue exists at all
   TASK_QUEUE_EXISTS=$(test -f .orchestrator/task_queue.md && echo "yes" || echo "no")
   ```

   **If PENDING_ISSUES > 0 OR PENDING_TASKS > 0:** Skip source file check, proceed with existing work.

   **If no existing work:** Continue to step 2 (source file check).

2. **Check source files exist (only if no existing work):**
   - If `SOURCE_TYPE = external_spec`: Check projectspec/spec-final.json AND projectspec/test-plan-output.json exist
   - If `SOURCE_TYPE = prd`: Check PRD.md exists
     - If PRD.md missing, check for external spec files as fallback:
       ```bash
       if [ -f "projectspec/spec-final.json" ] && [ -f "projectspec/test-plan-output.json" ]; then
         echo "PRD.md not found, but external spec files exist. Switching to external_spec mode."
         SOURCE_TYPE="external_spec"
       else
         echo "ERROR: No PRD.md and no external spec files found."
         echo "Run /prdgen to create a PRD, or provide projectspec/*.json files"
         exit 1
       fi
       ```
3. Check git → init if needed
4. **Pre-flight checks for directory structure:**
   ```bash
   # Verify no project files in framework repo
   for dir in tests app dashboard; do
     if [ -d "claudestrator/$dir" ]; then
       echo "ERROR: Project directory '$dir' found in framework repo"
       echo "Remove with: rm -rf claudestrator/$dir"
       exit 1
     fi
   done

   # Verify no project files in .claudestrator/ (runtime only)
   for dir in tests app; do
     if [ -d ".claudestrator/$dir" ]; then
       echo "ERROR: Project directory '$dir' found in .claudestrator/"
       echo ".claudestrator/ is for runtime config only"
       echo "Project files should be in .orchestrator/"
       exit 1
     fi
   done
   ```
5. **Initialize project output directory (.orchestrator/):**
   ```bash
   # Create project output directory structure
   mkdir -p .orchestrator/{app,tests,docs,complete,reports,pids,process-logs}
   ```
   **CRITICAL:** All project files (app/, tests/, docs/) go in `.orchestrator/`, NOT `.claudestrator/`.

   **Architecture:**
   - `claudestrator/` = Framework repo (commands, prompts, skills)
   - `.claudestrator/` = Runtime config (symlinks to framework)
   - `.orchestrator/` = Project OUTPUT (app/, tests/, docs/, task_queue.md, reports/)
6. Create `.orchestrator/complete/` and `.orchestrator/reports/` directories if missing
7. Get absolute working directory with `pwd` (store for agent prompts)
8. Generate RUN_ID: `run-YYYYMMDD-HHMMSS` (e.g., `run-20240115-143022`)
9. Initialize LOOP_NUMBER to 1
10. **Scan for failed tasks** (see Step 10 below)
11. **Scan for critical blocking issues** (see Step 11 below)

### Step 10: Failed Task Detection (BEFORE Critical Issues)

**IMPORTANT:** Failed tasks must be processed FIRST because they generate critical issues.

```bash
# Count tasks with failed status
FAILED_COUNT=$(grep -c "| Status | failed |" .orchestrator/task_queue.md 2>/dev/null || echo "0")
```

**If FAILED_COUNT > 0:**

For each failed task, spawn Failure Analysis Agent:

```bash
# Get list of failed task IDs
FAILED_TASKS=$(grep -B5 "| Status | failed |" .orchestrator/task_queue.md | grep "^### TASK-" | sed 's/### //')
```

For each TASK_ID in FAILED_TASKS:

1. **Check if analysis already done:**
   ```bash
   ls .orchestrator/complete/analysis-${TASK_ID}.done 2>/dev/null && echo "SKIP" || echo "ANALYZE"
   ```

2. **If not analyzed, spawn Failure Analysis Agent:**
   ```
   Task(
     model: "opus",
     run_in_background: true,
     prompt: "Read('.claude/prompts/failure_analysis_agent.md') and follow those instructions.

     ---

     FAILED_TASK_ID: ${TASK_ID}
     WORKING_DIR: ${WORKING_DIR}

     Analyze why this task failed and create critical issue(s) in issue_queue.md.
     Write marker when done: .orchestrator/complete/analysis-${TASK_ID}.done"
   )
   ```

3. **Wait for all analysis to complete:**
   ```bash
   for TASK_ID in $FAILED_TASKS; do
     while [ ! -f ".orchestrator/complete/analysis-${TASK_ID}.done" ]; do sleep 120; done
   done
   echo "All failure analysis complete"
   ```

**Result:** Critical issues now exist in issue_queue.md. Proceed to Step 11.

---

### Critical Issue Loop (Step 11)

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

### Step 11a: Scan for Critical Issues

Critical issues need processing if they are in ANY of these states:

| Status | Condition | Meaning |
|--------|-----------|---------|
| `pending` | - | New issue, ready to start |
| `accepted` | - | Acknowledged, ready to start |
| `in_progress` | Task has `.failed` marker | Implementation failed, needs Failure Analysis |
| `in_progress` | Task has `.done` marker but issue not `completed` | False completion, needs re-work |

**Step 11a.1: Count pending/accepted critical issues**

Run this command to count actionable critical issues:

```
Bash("grep -A3 '| Priority | critical |' .orchestrator/issue_queue.md 2>/dev/null | grep -cE 'Status \\| (pending|accepted)' || echo '0'")
```

Store the output as `PENDING_CRITICAL`.

**Step 11a.2: Check for stalled in_progress critical issues**

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

**Step 11a.3: Calculate total**

```
CRITICAL_COUNT = PENDING_CRITICAL + STALLED_COUNT
```

**Step 11a.4: Handle stalled issues**

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

**Step 11a.5: Re-count after resets**

After handling stalled issues, re-run the pending/accepted count:

```
Bash("grep -A3 '| Priority | critical |' .orchestrator/issue_queue.md 2>/dev/null | grep -cE 'Status \\| (pending|accepted)' || echo '0'")
```

Update `CRITICAL_COUNT` with the new value.

### Step 11b: Critical Loop Logic

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
      TEST_ONLY: false

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
    Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 120; done && rm .orchestrator/complete/decomposition.done && echo 'done'", timeout: 600000)

    # 3. VERIFY tasks were created (Step 11c)
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

### Step 11c: Verify Tasks Created (within loop)

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

### Step 11d: After Critical Loop Completes

Only after CRITICAL_COUNT == 0 should you proceed. The next step depends on:

**1. Check for pending non-critical issues:**

```bash
PENDING_ISSUES=$(grep -cE "Status \| (pending|accepted)" .orchestrator/issue_queue.md 2>/dev/null || echo "0")
```

**2. Check if task queue exists (indicates prior PRD processing):**

```bash
TASK_QUEUE_EXISTS=$(test -f .orchestrator/task_queue.md && echo "yes" || echo "no")
```

**3. Check for pending tasks in task queue:**

```bash
PENDING_TASKS=$(grep -c "| Status | pending |" .orchestrator/task_queue.md 2>/dev/null || echo "0")
```

**4. Route based on state:**

| LOOP_COUNT | PENDING_ISSUES | PENDING_TASKS | TASK_QUEUE_EXISTS | Action |
|------------|----------------|---------------|-------------------|--------|
| 0 | > 0 | any | yes | **Process issues** - Go to Step 4.3 (Decomposition for issues) |
| 0 | 0 | > 0 | yes | **Execute pending tasks** - Go to Step 2 (skip decomposition) |
| 0 | 0 | 0 | no | **Initial build** - Go to Step 1 (Decomposition for PRD.md) |
| 0 | 0 | 0 | yes | **Nothing to do** - Go to Step 5 (Analysis Agent) |
| > 0 | any | any | any | **Improvement loops** - Go to Step 4 |

**Key insight:** `/orchestrate` (no loops) on an existing project with pending issues OR pending tasks should still process them. This is critical for `external_spec` mode where TEST tasks are created alongside BUILD tasks but executed in a separate pass. The "no loops" setting means no Research Agent loops, NOT "ignore pending work."

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
| Frontend | `.claude/prompts/frontend_agent.md` |
| Backend | `.claude/prompts/backend_agent.md` |
| Fullstack | `.claude/prompts/fullstack_agent.md` |
| DevOps | `.claude/prompts/devops_agent.md` |
| Test Creation | `.claude/prompts/test_creation_agent.md` |
| Test Verification | `.claude/prompts/test_verification_agent.md` |
| Docs | `.claude/prompts/docs_agent.md` |

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

**DO NOT read source files yourself** - that adds thousands of tokens to your context.

### Step 1a: Choose Mode Based on SOURCE_TYPE

| SOURCE_TYPE | MODE | SOURCE | START Action |
|-------------|------|--------|--------------|
| `prd` | `initial` | PRD.md | `Read('PRD.md')` |
| `external_spec` | `external_spec` | projectspec/*.json | `Read('.claude/prompts/external_spec_mapping.md')` |

### Step 1b: Spawn Agent

**For SOURCE_TYPE = prd (default):**

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
  TEST_ONLY: [value from parsed TEST_ONLY flag]

  Read PRD.md and create .orchestrator/task_queue.md with implementation tasks.

  If TEST_ONLY is true, only create TEST (TASK-T##) and VERIFY (TASK-V##) tasks. Skip BUILD and QA tasks.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  The orchestrator is BLOCKED waiting for this file. Create it NOW when done.

  START: Read('PRD.md')"
)
```

**For SOURCE_TYPE = external_spec:**

```
Task(
  model: "opus",
  run_in_background: true,
  prompt: "Read('.claude/prompts/decomposition_agent.md') and follow those instructions.

  ---

  ## Your Task

  WORKING_DIR: [absolute path from pwd]
  SOURCE: projectspec/spec-final.json + projectspec/test-plan-output.json
  MODE: external_spec
  TEST_ONLY: [value from parsed TEST_ONLY flag]

  Parse the external spec files and create .orchestrator/task_queue.md with:
  - TEST tasks from test-plan-output.json
  - If TEST_ONLY is false: also create BUILD tasks from spec-final.json core_functionality, linked to TEST tasks via dependencies

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  The orchestrator is BLOCKED waiting for this file. Create it NOW when done.

  START: Read('.claude/prompts/external_spec_mapping.md')"
)
```

**Wait for completion (and clean up marker):**
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 120; done && rm .orchestrator/complete/decomposition.done && echo 'Decomposition complete'", timeout: 600000)
```

---

## Step 2: Execute Implementation Tasks

Read `.orchestrator/task_queue.md` to get pending tasks.

For each task with `Status | pending`:

### 2a-0-pre. TEST_ONLY Mode Filtering

**If `TEST_ONLY` is true**, filter tasks before execution:

```bash
# Get task category
TASK_CATEGORY=$(grep -A10 "### $TASK_ID" .orchestrator/task_queue.md | grep "Category" | head -1 | sed 's/.*| //' | tr -d ' ')

# Only execute TEST (TASK-T##) and VERIFY (TASK-V##) tasks in test-only mode
if [ "$TEST_ONLY" = "true" ]; then
  if [[ ! "$TASK_ID" =~ ^TASK-[TV][0-9]+$ ]]; then
    echo "⏸ Skipping $TASK_ID: TEST_ONLY mode - only TEST and VERIFY tasks execute"
    continue
  fi
fi
```

| Mode | Tasks Executed | Tasks Skipped |
|------|----------------|---------------|
| Normal | All pending tasks | None |
| `--test-only` | TASK-T## (test_creation), TASK-V## (verification) | BUILD (TASK-###), TASK-99999 (QA) |

**In TEST_ONLY mode:**
- TASK-T## creates/reworks test files
- TASK-V## runs tests against existing implementation
- Tests pass/fail results are recorded
- Skip BUILD tasks (implementation already exists) and TASK-99999 (QA)
- Skip improvement loops

**After all TEST and VERIFY tasks complete:**
- Output: `✓ TEST_ONLY mode complete. Tests created and verified.`
- Exit orchestration

### 2a-0. Check Dependencies (MANDATORY)

**Before spawning any agent, verify all dependencies are satisfied.**

```bash
# For a task with "Depends On | TASK-001, TASK-002, TASK-003":
# Check each dependency's status

for DEP in TASK-001 TASK-002 TASK-003; do
  STATUS=$(grep -A5 "### $DEP" .orchestrator/task_queue.md | grep "Status" | head -1 | sed 's/.*| //' | tr -d ' ')
  if [ "$STATUS" != "completed" ]; then
    echo "BLOCKED: $DEP is $STATUS (not completed)"
    BLOCKED=true
  fi
done
```

**Dependency States:**

| Dependency Status | Action |
|-------------------|--------|
| `completed` | ✓ Satisfied - can proceed |
| `pending` | ⏸ Not ready - skip this task, run dependency first |
| `in_progress` | ⏸ Not ready - wait for dependency to finish |
| `failed` | ⛔ BLOCKED - cannot proceed until dependency is fixed |
| `blocked` | ⛔ BLOCKED - transitive block |

**If ANY dependency is not `completed`:**
- Skip this task
- Output: `⏸ Skipping [TASK-ID]: dependency [DEP-ID] is [STATUS]`
- Continue to next pending task

**If ALL dependencies are `completed` (or task has no dependencies):**
- Proceed to concurrency gate (2a-1)

### 2a-1. Concurrency Gate (Wait for Available Slot)

**Before spawning any agent, enforce MAX_CONCURRENT_AGENTS = 10:**

```bash
# Initialize running tasks file
touch .orchestrator/running_tasks.txt

# Count currently running tasks
RUNNING=$(wc -l < .orchestrator/running_tasks.txt 2>/dev/null | tr -d ' ')
RUNNING=${RUNNING:-0}

if [ "$RUNNING" -ge 10 ]; then
  echo "⏸ At capacity ($RUNNING/10 agents). Waiting for slot..."

  # Single blocking wait - poll until ANY task completes
  while true; do
    for TASK in $(cat .orchestrator/running_tasks.txt); do
      if [ -f ".orchestrator/complete/${TASK}.done" ] || [ -f ".orchestrator/complete/${TASK}.failed" ]; then
        # Remove completed task from running list
        sed -i "/${TASK}/d" .orchestrator/running_tasks.txt
        echo "✓ Slot freed: $TASK"
        break 2  # Exit both loops
      fi
    done
    sleep 5
  done
fi

# Add task to running list BEFORE spawning
echo "[TASK-ID]" >> .orchestrator/running_tasks.txt
echo "▶ Spawning [TASK-ID] ($(wc -l < .orchestrator/running_tasks.txt | tr -d ' ')/10 slots used)"
```

**Then proceed to spawn agent (2b).**

**Special Case: TASK-99999 (Final Verification)**

TASK-99999 depends on ALL other tasks. Before running it:
```bash
# Count non-completed tasks (excluding TASK-99999 itself)
INCOMPLETE=$(grep -E "^### TASK-" .orchestrator/task_queue.md | grep -v "TASK-99999" | while read task; do
  grep -A5 "$task" .orchestrator/task_queue.md | grep -q "Status | completed" || echo "incomplete"
done | wc -l)

if [ "$INCOMPLETE" -gt 0 ]; then
  echo "⛔ TASK-99999 blocked: $INCOMPLETE task(s) not completed"
  # Do not run TASK-99999
fi
```

### 2a-0.5: Test Verification (Handled via TASK-V## Tasks)

**NOTE:** Test verification is now handled via TASK-V## tasks in the task queue, NOT inline here.

The decomposition agent creates TASK-V## tasks for each TASK-T## test task:
- TASK-V01 verifies TASK-T01 (unit tests)
- TASK-V10 verifies TASK-T10 (integration tests)
- TASK-V20 verifies TASK-T20 (E2E tests)
- etc.

VERIFY tasks use Category: `test_verification` and are routed to `prompts/test_verification_agent.md`.

**Execution Order:**
```
TASK-T## (write tests) → TASK-### (build) → TASK-V## (verify tests) → TASK-99999 (QA)
```

The Test Verification Agent ensures:
1. Tests compile and run without errors
2. No cheating patterns (try/catch swallowing, mocks in E2E)
3. Skip rate < 10%
4. No environmental issues (Ollama not running, port conflicts)

If verification fails, a critical issue is created and TASK-99999 is blocked.

### 2a-1. TDD Validation (For BUILD Tasks Only)

**Before running any BUILD task (frontend/backend/fullstack/devops), verify tests exist.**

```bash
# For BUILD tasks, check that related TEST tasks are complete
TASK_CATEGORY=$(grep -A10 "### $TASK_ID" .orchestrator/task_queue.md | grep "Category" | head -1 | sed 's/.*| //' | tr -d ' ')

if [[ "$TASK_CATEGORY" =~ ^(frontend|backend|fullstack|devops)$ ]]; then
  # This is a BUILD task - verify TEST dependencies exist
  TEST_DEPS=$(grep -A10 "### $TASK_ID" .orchestrator/task_queue.md | grep "Depends On" | grep -oE "TASK-T[0-9]+" | head -5)

  if [ -z "$TEST_DEPS" ]; then
    echo "⚠️ WARNING: BUILD task $TASK_ID has no TEST task dependencies"
    echo "   TDD requires tests to be written before implementation"
  else
    for TEST_TASK in $TEST_DEPS; do
      TEST_STATUS=$(grep -A5 "### $TEST_TASK" .orchestrator/task_queue.md | grep "Status" | head -1 | sed 's/.*| //' | tr -d ' ')
      if [ "$TEST_STATUS" != "completed" ]; then
        echo "⛔ TDD VIOLATION: $TASK_ID cannot run - $TEST_TASK (tests) is $TEST_STATUS"
        BLOCKED=true
      fi
    done
  fi

  # Also verify test files actually exist in the project
  PROJECT_TESTS=$(find .orchestrator/app/src -name "*.test.ts" 2>/dev/null | wc -l)
  if [ "$PROJECT_TESTS" -eq 0 ]; then
    echo "⚠️ WARNING: No test files found in project - TDD may not be enforced"
  fi
fi
```

**TDD Enforcement Rules:**

| Task Type | Can Run If |
|-----------|------------|
| TEST task (TASK-Txx) | No special requirements (runs first) |
| BUILD task | All TASK-Txx dependencies are `completed` |

**If TDD validation fails:**
- Do NOT run the BUILD task
- Output violation message
- Skip to next pending task

### 2a. Select Model and Prompt by Category

| Category | Prompt File | Default Model |
|----------|-------------|---------------|
| frontend | `prompts/frontend_agent.md` | sonnet |
| backend | `prompts/backend_agent.md` | sonnet |
| fullstack | `prompts/fullstack_agent.md` | sonnet |
| devops | `prompts/devops_agent.md` | sonnet |
| test_creation | `prompts/test_creation_agent.md` | sonnet |
| test_verification | `prompts/test_verification_agent.md` | sonnet |
| docs | `prompts/docs_agent.md` | haiku |

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
  prompt: "Read('.claude/prompts/[category]_agent.md') and follow those instructions.

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
Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ] && [ ! -f '.orchestrator/complete/[TASK-ID].failed' ]; do sleep 120; done && (test -f '.orchestrator/complete/[TASK-ID].done' && echo 'SUCCESS' || echo 'FAILED') && rm -f .orchestrator/complete/[TASK-ID].done .orchestrator/complete/[TASK-ID].failed", timeout: 1800000)
```

Output is `SUCCESS` or `FAILED`. Markers are cleaned immediately (task_queue.md status is source of truth).

**Note:** Uses 120-second polling intervals. No external dependencies required.

**Remove task from running list immediately after completion:**
```bash
sed -i "/[TASK-ID]/d" .orchestrator/running_tasks.txt
echo "✓ [TASK-ID] complete. $(wc -l < .orchestrator/running_tasks.txt | tr -d ' ')/10 slots used"
```

### 2c-1. Post-Completion Agent Cleanup (CRITICAL - Prevents Resource Exhaustion)

**After the Bash wait returns**, the agent SHOULD have terminated. However, agents can get stuck in verification loops after writing the completion marker, consuming tokens indefinitely.

**MANDATORY**: After each task completes, check if the agent is still running and attempt cleanup:

```python
# Store agent_id when spawning (from Task() return value)
agent_id = <from Task() call>

# After Bash wait returns (marker detected):
# 1. Wait 30 seconds for agent to terminate gracefully
Bash("sleep 30")

# 2. Check if agent is still running (non-blocking)
TaskOutput(agent_id, block: false)

# 3. If output shows "Task is still running":
#    - Output warning: "⚠️ Agent {agent_id} still running after completion. Attempting cleanup..."
#    - Write kill signal file for agent to detect:
Bash("echo 'kill' > '.orchestrator/complete/[TASK-ID].kill'")

#    - Wait 15 more seconds for cooperative termination
Bash("sleep 15")

#    - Clean up kill signal
Bash("rm -f '.orchestrator/complete/[TASK-ID].kill'")

#    - If STILL running, log it but proceed (agent will eventually exhaust context)
#    - Output: "⚠️ Runaway agent {agent_id} detected. Task complete, proceeding. Agent will timeout."
```

**Why this matters:** A runaway agent can consume 100k+ tokens after completion, wasting resources. The orchestrator must actively detect and attempt to stop these agents.

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
Bash("while [ ! -f '.orchestrator/complete/analysis-[TASK-ID].done' ]; do sleep 120; done && echo 'Failure analysis complete'", timeout: 600000)
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
Bash("while [ ! -f '.orchestrator/complete/research.done' ]; do sleep 120; done && rm .orchestrator/complete/research.done && echo 'Research complete'", timeout: 900000)
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
  TEST_ONLY: false

  Read .orchestrator/issue_queue.md and convert pending issues to tasks in .orchestrator/task_queue.md.

  CRITICAL: Write completion marker when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  START: Read('.orchestrator/issue_queue.md')"
)
```

Wait for completion:
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 120; done && rm .orchestrator/complete/decomposition.done && echo 'done'", timeout: 300000)
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
Bash("while [ ! -f '.orchestrator/complete/analysis.done' ]; do sleep 120; done && echo 'Analysis complete'", timeout: 300000)
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
6. **ONE blocking Bash per agent** - uses 120-second polling (no output until complete)
7. **NEVER use TaskOutput** - adds 50-100k tokens to context
8. **NEVER spawn ad-hoc agents** - only use the predefined agent types below
9. **NEVER improvise the flow** - follow the documented steps exactly
10. **Research Agent requires `--research` flag** - only spawned when enabled and queue is clear
11. **ALWAYS check for runaway agents** - after .done marker detected, verify agent terminated (see Step 2c-1)

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
| Frontend | Frontend tasks | `prompts/frontend_agent.md` |
| Backend | Backend tasks | `prompts/backend_agent.md` |
| Fullstack | Fullstack tasks | `prompts/fullstack_agent.md` |
| DevOps | DevOps tasks | `prompts/devops_agent.md` |
| Test Creation | Test writing (MODE: write) | `prompts/test_creation_agent.md` |
| Test Verification | Test execution & validation (MODE: verify) | `prompts/test_verification_agent.md` |
| Docs | Documentation tasks | `prompts/docs_agent.md` |
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
| Agent Prompts | `prompts/*.md`, `prompts/*.md` |

---

*MVP Version: 3.4*
