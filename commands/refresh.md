# /refresh - Signal Orchestrator to Reload

Signal the orchestrator (running in another session) to reload a specific resource.

## Usage

```
/refresh issues       Poll issue queue immediately
/refresh skills       Reload skill directory immediately
/refresh prd          Queue restart with new PRD after current run completes
/refresh cancel       Cancel a queued PRD restart
```

**Important:** `/refresh` without an argument does nothing. You must specify what to refresh.

## Behavior by Target

| Target | Timing | Action |
|--------|--------|--------|
| `issues` | **Immediate** | Poll issue queue before next task |
| `skills` | **Immediate** | Reload skill directory before next task |
| `prd` | **Queued** | Complete current run, then restart with new PRD |
| `cancel` | **Immediate** | Cancel a queued PRD restart |

### Why PRD is Queued (Not Immediate)

PRD changes mid-run can cause architectural conflicts:
- Existing tasks were planned against the old PRD
- New tasks would be planned against the new PRD
- Dependencies between old and new tasks may not align

Instead, `/refresh prd`:
1. Flags the orchestrator to restart after the current run
2. Current run completes normally (all tasks finish)
3. Orchestrator archives the completed run
4. New run begins with the updated PRD
5. Orchestrator analyzes PRD differences and creates tasks for changes

---

## Examples

### Refresh Issues (Immediate)

```
Terminal 2:
  /issue "Critical bug in production"
  /refresh issues

  "═══════════════════════════════════════════════════════════
  REFRESH SIGNAL SENT
  ═══════════════════════════════════════════════════════════

  Type:    issues
  Action:  Immediate poll

  The orchestrator will poll the issue queue before its next task.

  ═══════════════════════════════════════════════════════════"
```

### Refresh Skills (Immediate)

```
Terminal 2:
  /ingest-skill https://example.com/new-skill.md
  /refresh skills

  "═══════════════════════════════════════════════════════════
  REFRESH SIGNAL SENT
  ═══════════════════════════════════════════════════════════

  Type:    skills
  Action:  Immediate reload

  The orchestrator will reload the skill directory before its next task.

  ═══════════════════════════════════════════════════════════"
```

### Refresh PRD (Queued Restart)

```
Terminal 2:
  [edits PRD.md with significant changes]
  /refresh prd

  "═══════════════════════════════════════════════════════════
  PRD RESTART QUEUED
  ═══════════════════════════════════════════════════════════

  The orchestrator will:
  1. Complete all tasks in the current run (3 remaining)
  2. Archive completed tasks for reference
  3. Analyze differences between old and new PRD
  4. Create tasks for the changes
  5. Begin new run automatically

  To cancel: /refresh cancel

  ═══════════════════════════════════════════════════════════"
```

### Cancel Queued Restart

```
Terminal 2:
  /refresh cancel

  "═══════════════════════════════════════════════════════════
  PRD RESTART CANCELLED
  ═══════════════════════════════════════════════════════════

  The queued PRD restart has been cancelled.
  The current run will continue normally.

  ═══════════════════════════════════════════════════════════"
```

If no restart is queued:
```
  "═══════════════════════════════════════════════════════════
  NOTHING TO CANCEL
  ═══════════════════════════════════════════════════════════

  No PRD restart is currently queued.

  ═══════════════════════════════════════════════════════════"
```

---

## Signal File Format

### For issues/skills (immediate):

```markdown
# Refresh Signal

- **Type**: issues
- **Requested**: 2025-12-11T15:30:00Z
- **Action**: immediate
```

### For prd (queued):

```markdown
# Refresh Signal

- **Type**: prd
- **Requested**: 2025-12-11T15:30:00Z
- **Action**: restart_after_completion
- **Reason**: PRD updated - restart queued after current run completes
```

### For cancel:

```markdown
# Refresh Signal

- **Type**: cancel
- **Requested**: 2025-12-11T15:35:00Z
- **Action**: cancel_restart
```

---

## Implementation

```
FUNCTION refresh(target):
    IF target NOT IN ['issues', 'skills', 'prd', 'cancel']:
        OUTPUT: "Usage: /refresh issues|skills|prd|cancel

                 /refresh issues  - Poll issue queue immediately
                 /refresh skills  - Reload skill directory immediately
                 /refresh prd     - Queue restart after current run
                 /refresh cancel  - Cancel queued PRD restart"
        RETURN

    IF target == 'cancel':
        signal = {
            type: "cancel",
            requested: NOW(),
            action: "cancel_restart"
        }
        WRITE .claude/refresh_signal.md

        OUTPUT: "PRD restart cancelled (if one was queued)."
        RETURN

    IF target == 'prd':
        signal = {
            type: "prd",
            requested: NOW(),
            action: "restart_after_completion",
            reason: "PRD updated via /refresh prd"
        }
        WRITE .claude/refresh_signal.md

        OUTPUT: "PRD restart queued.
                 Current run will complete, then restart with new PRD.
                 To cancel: /refresh cancel"
        RETURN

    # issues or skills - immediate
    signal = {
        type: target,
        requested: NOW(),
        action: "immediate"
    }
    WRITE .claude/refresh_signal.md

    OUTPUT: "Refresh signal sent: {target}
             The orchestrator will process this before its next task."
```

---

## Orchestrator Response

### Immediate Signals (issues, skills)

```
checkRefreshSignals():
    IF signal.type == 'issues':
        REPORT: "🔄 Refresh signal: polling issue queue"
        pollIssueQueue()
        DELETE signal file

    IF signal.type == 'skills':
        REPORT: "🔄 Refresh signal: reloading skills"
        reloadSkillDirectory()
        DELETE signal file
```

### Queued Signal (prd)

```
checkRefreshSignals():
    IF signal.type == 'prd':
        session_state.restart_after_completion = true
        session_state.restart_reason = signal.reason
        REPORT: "📋 PRD restart queued - current run will complete first"
        DELETE signal file

    IF signal.type == 'cancel':
        session_state.restart_after_completion = false
        session_state.restart_reason = null
        REPORT: "📋 PRD restart cancelled"
        DELETE signal file
```

### On Run Completion (with queued restart)

```
Phase 5 Completion:
    IF session_state.restart_after_completion:
        REPORT: "🔄 Restarting with updated PRD..."

        # Archive current run
        archiveCompletedRun()

        # Analyze PRD differences
        old_prd = READ PRD-history/latest
        new_prd = READ PRD.md
        changes = analyzePRDDifferences(old_prd, new_prd)

        # Create tasks for changes
        tasks = decomposeChanges(changes, archived_context)

        # Begin new run
        GOTO Phase 2 (Planning) with new tasks
```

---

## Display in /progress

When a PRD restart is queued:

```
CURRENT STATE
  Active task: task-006
  Next task: task-007
  Blockers: none
  ⏳ PRD restart queued (2 tasks remaining)
```

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/abort` | Stop current run immediately (destructive) |
| `/issue` | Report new issue |
| `/issues` | View issue queue |
| `/progress` | View orchestrator state (shows if restart queued) |
| `/ingest-skill` | Import new skill |
