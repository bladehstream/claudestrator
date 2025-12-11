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

---

## Issues

<!-- Issues are appended below this line -->

