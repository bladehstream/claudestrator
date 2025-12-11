# /reject - Reject an Issue

Mark an issue as "won't fix" with a reason. Only works on pending or accepted issues.

## Usage

```
/reject <issue-id> <reason>
```

## Examples

```
/reject ISSUE-20241211-001 "Out of scope for this project"

/reject ISSUE-20241211-002 "Duplicate of task-005 which is already complete"

/reject ISSUE-20241210-003 "Not reproducible - works as expected"
```

## Behavior

```
FUNCTION rejectIssue(issue_id, reason):
    READ .claude/issue_queue.md

    issue = issues.find(i => i.id == issue_id)

    IF NOT issue:
        OUTPUT: "Issue not found: {issue_id}"
        RETURN

    IF issue.status NOT IN ['pending', 'accepted']:
        OUTPUT: "Cannot reject issue in '{issue.status}' state.
                 Only pending or accepted issues can be rejected."
        RETURN

    # Update issue
    issue.status = "wont_fix"
    issue.rejected_at = NOW()
    issue.rejection_reason = reason

    # If task was created, mark it cancelled
    IF issue.task_ref:
        UPDATE journal task to cancelled
        issue.notes += "\nLinked task {issue.task_ref} cancelled."

    WRITE .claude/issue_queue.md

    # Update queue counts
    UPDATE queue status counts

    OUTPUT:
        "═══════════════════════════════════════════════════════════
        ISSUE REJECTED
        ═══════════════════════════════════════════════════════════

        ID:     {issue_id}
        Status: won't fix
        Reason: {reason}

        ═══════════════════════════════════════════════════════════"
```

## Display Format

After rejection, the issue appears in `/issues` as:

```
WON'T FIX (1)
  ISSUE-20241211-001  bug  "Out of scope for this project"
```

## Validation

| Condition | Result |
|-----------|--------|
| Issue not found | Error message |
| Issue already complete | Error: "Cannot reject completed issue" |
| Issue in_progress | Error: "Cannot reject issue with active task" |
| Issue already rejected | Error: "Issue already rejected" |
| No reason provided | Error: "Rejection reason required" |

## Reversing Rejection

To un-reject an issue (reopen), manually edit `.claude/issue_queue.md`:
- Change `status: wont_fix` back to `status: pending`
- Remove `rejected_at` and `rejection_reason` fields

Or report it again via `/issue` if the queue entry is unclear.

## Related Commands

| Command | Purpose |
|---------|---------|
| `/issues` | View issue queue |
| `/issues <id>` | View issue details |
| `/issue` | Report new issue |
