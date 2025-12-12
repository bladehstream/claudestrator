# Issue Queue

Project issue queue for asynchronous issue reporting. The Issue Reporter agent appends issues here; the Orchestrator polls and creates tasks.

## Queue Status

| Field | Value |
|-------|-------|
| Last Updated | - |
| Last Polled | - |
| Pending | 0 |
| Accepted | 0 |
| In Progress | 0 |
| Completed | 0 |
| Won't Fix | 0 |

## Issue Sources

| Source | Description |
|--------|-------------|
| `user` | Reported by human user via `/issue` command |
| `generated` | Discovered by sub-agent (research, QA, etc.) via `[generated]` tag |

## Issue States

| State | Description |
|-------|-------------|
| `pending` | Submitted by Issue Reporter, awaiting orchestrator pickup |
| `duplicate` | Merged into another issue |
| `accepted` | Task created by orchestrator |
| `in_progress` | Linked task is being executed |
| `complete` | Linked task finished successfully |
| `wont_fix` | Rejected by user with reason |

## Priority Levels

| Priority | Orchestrator Behavior |
|----------|----------------------|
| `critical` | Interrupts queue - becomes next task |
| `high` | Inserted at top of pending tasks |
| `medium` | Normal queue position |
| `low` | End of queue |

## Issue Entry Format

```markdown
### ISSUE-YYYYMMDD-NNN

| Field | Value |
|-------|-------|
| Status | pending |
| Source | user / generated |
| Type | bug / enhancement / performance / security / etc. |
| Priority | critical / high / medium / low |
| Created | YYYY-MM-DDTHH:MM:SSZ |
| Loop | (if generated during loop N) |

**Summary:** Brief description

**Details:** Full description with context

**Acceptance Criteria:**
- Criterion 1
- Criterion 2

**Files:** (if known)
- file1.ts
- file2.ts

**Task Ref:** (filled by orchestrator when accepted)
```

---

## Issues

<!-- Issues are appended below this line -->

