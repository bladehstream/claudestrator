# /tasks - Show Task List

Display all tasks with their current status.

## Display Format

Read from `.claude/journal/index.md` and display:

```
═══════════════════════════════════════════════════════════
TASK REGISTRY
═══════════════════════════════════════════════════════════

COMPLETED ✓
  [001] Set up project structure
  [002] Design data models
  [003] Implement user model

IN PROGRESS ◐
  [004] Implement auth middleware
        Agent: sonnet | Skills: html5_canvas, security
        Started: [time ago]

PENDING ○
  [005] Implement core API          (depends on: 003, 004)
  [006] Add validation              (depends on: 005)
  [007] Write tests                 (depends on: 005)
  [008] QA verification             (depends on: all)

BLOCKED ✗
  [none]

═══════════════════════════════════════════════════════════
Progress: 3/8 (37.5%)
═══════════════════════════════════════════════════════════
```

## Task Details

To see details on a specific task, user can ask:
"Show me task 004" or "What's the status of the auth task?"

Then display from `journal/task-004-*.md`:
- Full objective
- Acceptance criteria with status
- Execution log summary
- Any blockers or notes
