# Orchestrator Runtime (MVP)

> **Version**: MVP 3.3 - Auto-retry for critical failures.

## Key Principle: Read Prompt Files

Agents read their detailed instructions from prompt files. This keeps prompts:
- **Reusable** - Same prompt file for all tasks of that type
- **Maintainable** - Update once, applies everywhere
- **Consistent** - Reliable outputs across runs

---

## Prompt Files

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

---

## Initial Run (`/orchestrate`)

### Step 1: Spawn Decomposition Agent

```
Task(
  model: "sonnet",
  run_in_background: true,
  prompt: "Read('prompts/decomposition_agent.md') and follow those instructions.

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
   frontend  → prompts/implementation/frontend_agent.md
   backend   → prompts/implementation/backend_agent.md
   fullstack → prompts/implementation/fullstack_agent.md
   devops    → prompts/implementation/devops_agent.md
   testing   → prompts/implementation/testing_agent.md
   docs      → prompts/implementation/docs_agent.md
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

4. **Wait:**
   ```
   Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
   ```

5. **Update task status** to "completed" in task_queue.md

6. **After all tasks:**
   ```
   Write(".orchestrator/session_state.md", "initial_prd_tasks_complete: true")
   Bash("git add -A && git commit -m 'Initial build complete'")
   ```

---

## Improvement Loops (`/orchestrate N`)

**Increment LOOP_NUMBER** at the start of each loop.

For each loop 1..N:

### 1. Research Agent (if initial complete)

```
Task(
  model: "opus",  # Research requires deep analysis
  run_in_background: true,
  prompt: "Read('prompts/research_agent.md') and follow those instructions.

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

### 2. Convert Issues to Tasks

Read `.orchestrator/issue_queue.md`, for each pending issue:
- Create task entry in task_queue.md
- Copy Category from issue
- Set issue status to `in_progress`

### 3. Execute Tasks (max 5)

Same category-based routing as Initial Step 2, limit 5 per loop.

### 4. Mark Issues Complete

Update corresponding issue to `completed` after task completes.

### 5. Commit

```
Bash("git add -A && git commit -m 'Loop [LOOP]'")
```

---

## Analysis Agent (End of Run)

**After ALL loops complete**, spawn the Analysis Agent:

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

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Completion | `.orchestrator/complete/{id}.done` |
| State | `.orchestrator/session_state.md` |
| Verification | `.orchestrator/VERIFICATION.md` |
| Task Reports | `.orchestrator/reports/{task_id}-loop-{n}.json` |
| History CSV | `.orchestrator/history.csv` |
| Analytics JSON | `.orchestrator/analytics.json` |
| Analytics HTML | `.orchestrator/analytics.html` |
| Verification Steps | `.orchestrator/verification_steps.md` |
| No Auto-Retry Flag | `.orchestrator/no_auto_retry` |
| Agent Prompts | `prompts/*.md`, `prompts/implementation/*.md` |

## CRITICAL RULES

1. **NEVER use TaskOutput** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **Use category-specific prompts** - agents read their detailed prompt file first
4. **Manager only** - never write code directly
5. **Pass LOOP_NUMBER and RUN_ID** - to all implementation agents
6. **NEVER spawn ad-hoc agents** - only use predefined agent types
7. **NEVER improvise** - follow the documented flow exactly
8. **ONE Research Agent per loop** - use FOCUS parameter, not topic-specific agents

### Forbidden Behaviors

| ❌ WRONG | ✅ CORRECT |
|----------|-----------|
| Spawn "Security research agent" | Spawn Research Agent with quotas |
| Spawn "UI improvement agent" | Spawn Research Agent with quotas |
| `/orchestrate 3 2 security 3 UI` = 2 sec + 3 UI total | = 6 sec + 9 UI total (per loop × loops) |
| Do 2 security in loop 1, 3 UI in loop 2 | Do 2 security + 3 UI in EACH loop |
| Create agent types not in prompt files | Only use agents listed in Prompt Files table |
| Improvise steps not in this document | Follow documented steps exactly |

## Waiting Pattern

```bash
# CORRECT - single blocking call
Bash("while [ ! -f '.orchestrator/complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# WRONG - fills context
while not exists: Bash("sleep 5")
```

---

*MVP Runtime Version: 3.3*
