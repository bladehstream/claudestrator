# /checkpoint - Save Current State

Save the current orchestrator state without exiting. Use this to create a safe restore point.

## Checkpoint Sequence

### Step 1: Save Orchestrator State

Update `.claude/orchestrator_state.md`:
- Current phase
- Any new key decisions since last checkpoint
- New learned context
- Update session duration

### Step 2: Save Journal State

Update `.claude/journal/index.md`:
- Task statuses
- Context map additions
- Any new blockers

### Step 3: Confirm

```
═══════════════════════════════════════════════════════════
CHECKPOINT SAVED
═══════════════════════════════════════════════════════════
Timestamp: [current time]
Project: [name]
Progress: [X/Y] tasks

State saved to:
- .claude/orchestrator_state.md
- .claude/journal/index.md

You can safely pause or continue working.
═══════════════════════════════════════════════════════════
```

## When to Checkpoint

Checkpoints happen automatically:
- After each task completion
- After key decisions
- Every 10 minutes of active work
- Before spawning complex (Opus) agents

Use `/checkpoint` manually when:
- About to make a risky change
- Before stepping away
- After receiving important user input
- Any time you want a known-good restore point
