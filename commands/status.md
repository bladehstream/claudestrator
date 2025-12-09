# /status - Show Current State

Display the current orchestrator and project state without modifying anything.

## Display Format

Read and display information from:
- `.claude/orchestrator_state.md`
- `.claude/journal/index.md`

```
═══════════════════════════════════════════════════════════
ORCHESTRATOR STATUS
═══════════════════════════════════════════════════════════

PROJECT
  Name: [project name]
  Phase: [planning/implementation/testing/complete]
  Started: [date]
  Last checkpoint: [timestamp]

PROGRESS
  Tasks: [completed]/[total] ([percentage]%)
  ████████████░░░░░░░░ [visual progress bar]

CURRENT STATE
  Active task: [task ID and name, or "none"]
  Next task: [task ID and name]
  Blockers: [count, or "none"]

RECENT ACTIVITY
  - [Last few actions/completions]

SESSION
  Duration: [time since /orchestrate]
  Checkpoints: [count]

SKILLS
  Loaded: [count] from [directory]

═══════════════════════════════════════════════════════════
Commands: /checkpoint /tasks /skills /deorchestrate
═══════════════════════════════════════════════════════════
```

## If No State Exists

```
═══════════════════════════════════════════════════════════
NO ORCHESTRATOR STATE FOUND
═══════════════════════════════════════════════════════════

No orchestrator state exists for this project.
Run /orchestrate to initialize.

═══════════════════════════════════════════════════════════
```
