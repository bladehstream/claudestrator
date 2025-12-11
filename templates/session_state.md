# Session State

**Last Updated:** [YYYY-MM-DD HH:MM]
**Session Started:** [YYYY-MM-DD HH:MM]

## Current Context

| Field | Value |
|-------|-------|
| Objective | [One sentence goal of current session] |
| Phase | [Planning | Implementation | Testing | Documentation | Review] |
| Active Task | [task-XXX or "none"] |
| Active Branch | [git branch name] |
| Autonomy Level | [Supervised | Trust Agents | Full Autonomy] |
| Git Enabled | [true | false] |

## Working Memory

Scratchpad for current task execution. Cleared after each task.

### Current Focus
[What we're working on right now]

### Hypotheses
- [Current hypothesis about approach or issue]

### Tried
- [Approach 1]: [Result]
- [Approach 2]: [Result]

### Next Try
[What to attempt next]

### Temporary Notes
[Any notes that don't need to persist beyond this task]

## Immediate Task List

- [ ] [Next immediate action]
- [ ] [Following action]
- [ ] [Action after that]

## Waiting For

| Item | Since | Expected |
|------|-------|----------|
| [What we're waiting for] | [timestamp] | [when expected] |

## Queued Actions

Signals received from Terminal 2 that affect run lifecycle.

```yaml
restart_after_completion: false
restart_reason: null
# When /refresh prd is called:
# restart_after_completion: true
# restart_reason: "PRD updated via /refresh prd"
```

## Running Agents

Active sub-agents spawned this session. Use `/progress agents` to view or `/progress <agent-id>` for details.

```yaml
running_agents: []
# Example entry:
# - id: agent-abc123
#   task_id: "004"
#   task_name: "Implement auth middleware"
#   model: sonnet
#   skills: [authentication, security]
#   started_at: "2024-12-11T10:30:00Z"
```

## Completed Agents

Sub-agents that finished this session. Stored for `/progress <agent-id>` lookups.

```yaml
completed_agents: []
# Example entry:
# - id: agent-xyz789
#   task_id: "003"
#   task_name: "Design data models"
#   model: sonnet
#   skills: [database_designer]
#   started_at: "2024-12-11T10:25:00Z"
#   completed_at: "2024-12-11T10:28:12Z"
#   duration: "3m 12s"
#   outcome: completed
#   final_output: |
#     ✓ Created src/models/User.ts
#     ✓ Created src/models/Transaction.ts
#     All acceptance criteria met.
```

## Quick Context

Essential context for current work (refreshed per-task):

### Relevant Files
| File | Purpose |
|------|---------|
| [path] | [why relevant to current task] |

### Recent Decisions
| Decision | Impact on Current Task |
|----------|----------------------|
| [decision] | [how it affects this work] |

### Active Gotchas
- [Warning relevant to current task]

---
*Hot state - read/write frequently during execution*
*Clear working memory after task completion*
