# /abort - Emergency Stop

Stop the current orchestration run immediately. This is a destructive operation that requires confirmation.

## Usage

```
/abort                    Shows confirmation prompt
/abort confirm            Confirms and executes abort
```

**Warning:** This command purges pending tasks and stops the run. Use only when continuing would waste resources on a fundamentally flawed approach.

---

## When to Use /abort

| Scenario | Use /abort? |
|----------|-------------|
| Fundamental design flaw discovered | ✅ Yes |
| PRD has critical errors | ✅ Yes |
| Wrong project/wrong direction entirely | ✅ Yes |
| Single task is failing | ❌ No - let it fail, orchestrator handles |
| Want to pause and resume later | ❌ No - use `/deorchestrate` |
| Want to change PRD for next run | ❌ No - use `/refresh prd` |

---

## Behavior

### Step 1: Confirmation Required

```
/abort

═══════════════════════════════════════════════════════════
⚠️  ABORT CONFIRMATION REQUIRED
═══════════════════════════════════════════════════════════

This will:
  ✗ Stop any running agents immediately
  ✗ Purge all pending tasks (5 tasks will be removed)
  ✗ Mark current run as aborted

Completed tasks (3) will be archived for reference.

This action cannot be undone.

To confirm: /abort confirm
To cancel:  Do nothing or continue working

═══════════════════════════════════════════════════════════
```

### Step 2: Execution (after confirm)

```
/abort confirm

═══════════════════════════════════════════════════════════
ORCHESTRATION ABORTED
═══════════════════════════════════════════════════════════

Run Status:    aborted
Completed:     3 tasks (archived)
Purged:        5 pending tasks
Running:       1 agent terminated

Archived to:   .claude/journal/archive/run-003-aborted/

To start fresh:
  1. Fix the issues in PRD.md
  2. Run /orchestrate

═══════════════════════════════════════════════════════════
```

---

## What Gets Preserved

| Item | Preserved? | Location |
|------|------------|----------|
| Completed tasks | ✅ Yes | `journal/archive/run-XXX-aborted/` |
| Task execution logs | ✅ Yes | Archived with tasks |
| Files created by agents | ✅ Yes | Remain in project |
| Git commits | ✅ Yes | In git history |
| Knowledge graph entries | ✅ Yes | Retained for future runs |
| PRD | ✅ Yes | Unchanged |
| Pending tasks | ❌ No | Purged |
| Running agent state | ❌ No | Terminated |

---

## What Gets Purged

- All tasks with status `pending`
- Current task if `in_progress` (marked as aborted)
- Any queued PRD restart (`/refresh prd`)
- Running agents are terminated

---

## Implementation

```
FUNCTION abort(confirmed):
    IF NOT confirmed:
        # Show confirmation prompt
        pending_count = journal.tasks.filter(t => t.status == 'pending').length
        completed_count = journal.tasks.filter(t => t.status == 'completed').length
        running_count = session_state.running_agents.length

        OUTPUT confirmation prompt with counts
        RETURN

    # User confirmed - execute abort
    REPORT: "⚠️  Aborting orchestration run..."

    # 1. Terminate running agents
    FOR agent IN session_state.running_agents:
        # Agent will be orphaned when orchestrator stops tracking
        REPORT: "Terminating agent {agent.id}"

    # 2. Archive completed tasks
    archive_path = "journal/archive/run-{run_number}-aborted/"
    MKDIR archive_path

    completed_tasks = journal.tasks.filter(t => t.status == 'completed')
    FOR task IN completed_tasks:
        MOVE task file to archive_path

    # 3. Purge pending tasks
    pending_tasks = journal.tasks.filter(t => t.status == 'pending')
    FOR task IN pending_tasks:
        DELETE task file
        REPORT: "Purged: {task.name}"

    # 4. Mark in-progress task as aborted
    IF current_task AND current_task.status == 'in_progress':
        current_task.status = 'aborted'
        current_task.aborted_at = NOW()
        current_task.abort_reason = "User initiated /abort"
        MOVE task file to archive_path

    # 5. Update journal index
    journal.index.phase = 'aborted'
    journal.index.aborted_at = NOW()
    journal.index.tasks = []  # Clear task registry

    # 6. Clear session state
    session_state.restart_after_completion = false
    session_state.running_agents = []
    session_state.completed_agents = []

    # 7. Clear any pending signals
    DELETE .claude/refresh_signal.md IF EXISTS

    WRITE journal/index.md
    WRITE session_state.md

    OUTPUT abort complete message
```

---

## Archive Structure

After abort:

```
.claude/journal/
├── index.md                           # Reset, phase: aborted
├── archive/
│   └── run-003-aborted/
│       ├── summary.md                 # Run summary with abort reason
│       ├── task-001-setup.md          # Completed task
│       ├── task-002-design.md         # Completed task
│       ├── task-003-implement.md      # Completed task
│       └── task-004-auth.md           # Aborted mid-execution
```

### Archive Summary Format

```markdown
# Run 003 - Aborted

**Status:** Aborted
**Started:** 2025-12-11T10:00:00Z
**Aborted:** 2025-12-11T14:30:00Z
**Reason:** User initiated /abort

## Statistics
- Completed: 3 tasks
- Aborted: 1 task (in progress)
- Purged: 4 tasks (pending)

## Completed Tasks
- task-001: Set up project structure
- task-002: Design database schema
- task-003: Implement user model

## Aborted Task
- task-004: Implement authentication (was in progress)

## Purged Tasks
- task-005: Implement API endpoints
- task-006: Add validation
- task-007: Write tests
- task-008: QA verification

## Files Created
- src/models/User.ts
- src/db/schema.sql
- package.json
```

---

## Safeguards

1. **Confirmation required** - `/abort` alone only shows the prompt
2. **Explicit confirm** - Must type `/abort confirm` to execute
3. **Archive before purge** - Completed work is preserved
4. **Clear messaging** - Shows exactly what will be lost

---

## Recovery After Abort

After aborting:

1. **Review what went wrong** - Check archived tasks and PRD
2. **Fix the PRD** - Correct the fundamental issues
3. **Start fresh** - Run `/orchestrate`

The orchestrator will:
- Detect no active run exists
- Read the (corrected) PRD
- Create new tasks from scratch
- Have access to archived knowledge graph entries

---

## Related Commands

| Command | Purpose | Destructive? |
|---------|---------|--------------|
| `/abort` | Emergency stop, purge pending | ✅ Yes |
| `/deorchestrate` | Clean exit, preserve state | ❌ No |
| `/refresh prd` | Queue restart after completion | ❌ No |
| `/refresh cancel` | Cancel queued restart | ❌ No |
| `/checkpoint` | Save current state | ❌ No |
