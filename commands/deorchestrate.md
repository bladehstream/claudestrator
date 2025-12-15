# /deorchestrate - Clean Exit with Full Save

You are exiting orchestrator mode. Perform a clean shutdown with full state persistence.

## Exit Sequence

### Step 1: Complete Current Operation

If an agent is currently running:
- Wait for agent to complete
- Process agent result
- Update task file with outcome

If in the middle of a decision:
- Complete the decision
- Log it to orchestrator_state.md

### Step 2: Save Orchestrator State

Update `.orchestrator/session_state.md`:

```markdown
## Session Info
- Last Active: [current timestamp]
- Total Sessions: [increment count]
- Current Phase: [current phase]

## Session Log
[Add entry for this session]:
| [session#] | [date] | [duration] | [tasks completed] | [brief note] |

## Resume Context

**For next session, remember:**

### Immediate Context
- Currently working on: [task ID or "between tasks"]
- Last action taken: [what just happened]
- Waiting for: [user input / nothing / specific info]

### Important Background
- [Key context from this session]
- [Recent decisions that matter]
- [User preferences expressed]

### Recommended Next Steps
1. [First thing to do next session]
2. [Second priority]

### Open Questions
- [Any unresolved questions]
```

### Step 3: Save Journal State

Update `.orchestrator/journal/index.md`:
- All task statuses current
- Context map updated with any new file locations
- Active blockers documented

### Step 4: Generate Exit Summary

```
═══════════════════════════════════════════════════════════
ORCHESTRATOR SESSION COMPLETE
═══════════════════════════════════════════════════════════
Duration: [X minutes/hours]
Tasks completed this session: [list or count]
Current progress: [X/Y] overall

Key accomplishments:
- [What was achieved]

State saved to:
- .orchestrator/session_state.md
- .orchestrator/journal/index.md

Next recommended action:
- [What to do next time]

═══════════════════════════════════════════════════════════
Run /orchestrate to resume.
═══════════════════════════════════════════════════════════
```

### Step 5: Confirm Safe to Exit

State is now fully persisted. Safe to:
- Close the conversation
- Start a new conversation
- Work on a different project

All context will be restored when `/orchestrate` is run again.
