# /issue - Report or Reject an Issue

Report new issues or reject existing ones. Issues are written to a queue that the orchestrator polls asynchronously.

## Usage

```
/issue                           Start interactive issue reporting
/issue <brief description>       Start with initial context
/issue reject <id> <reason>      Mark issue as won't fix
```

## Behavior

This command spawns a dedicated Issue Reporter agent that:

1. **Interviews** the user to gather issue details
2. **Categorizes** by type (bug, performance, enhancement, etc.)
3. **Prioritizes** based on impact and urgency
4. **Detects duplicates** against pending issues
5. **Writes** standardized entry to `.claude/issue_queue.md`

The orchestrator polls this queue and creates tasks automatically.

## Agent Spawn

```
Task(
    subagent_type: "general-purpose",
    model: "sonnet",
    prompt: """
        Read and follow: .claudestrator/issue_reporter/issue_protocol.md

        You are the Issue Reporter agent. Your job is to interview the user
        about their issue, gather standardized information, check for duplicates,
        and write to the issue queue.

        {IF initial_description PROVIDED}
        The user started with: "{initial_description}"
        Use this as context but still ask clarifying questions.
        {END IF}

        Project issue queue: .claude/issue_queue.md
        If the queue doesn't exist, create it from .claudestrator/templates/issue_queue.md

        Follow the interview flow in the protocol. Use AskUserQuestion for
        structured choices. Be thorough but efficient.
    """,
    description: "Report issue"
)
```

## Example Session

```
User: /issue

Issue Reporter:
    "What type of issue are you reporting?

    1. Bug - Something isn't working correctly
    2. Performance - Slowness or resource issues
    3. Enhancement - New feature request
    4. UX - User experience improvement
    5. Security - Security concern
    6. Refactor - Code quality issue"

User: [Selects Bug]

Issue Reporter:
    "Briefly describe the issue in one sentence:"

User: "Dashboard crashes when filtering by date range"

Issue Reporter:
    "What steps reproduce this issue?"

User: "1. Go to dashboard
       2. Select date filter
       3. Choose last 30 days
       4. Click apply"

Issue Reporter:
    "What did you expect to happen?"

User: "Dashboard should filter to show only last 30 days"

Issue Reporter:
    "What actually happened?"

User: "Page goes blank and console shows TypeError"

...continues through interview...

Issue Reporter:
    "═══════════════════════════════════════════════════════════
    ISSUE SUBMITTED
    ═══════════════════════════════════════════════════════════

    ID:       ISSUE-20241211-001
    Type:     bug
    Priority: high
    Summary:  Dashboard crashes when filtering by date range

    The orchestrator will pick this up automatically.
    Run /issues to check queue status.

    ═══════════════════════════════════════════════════════════"
```

## Quick Issue (with description)

```
User: /issue Dashboard is very slow with lots of transactions

Issue Reporter:
    "I understand you're reporting a performance issue with the dashboard.
    Let me gather a few more details.

    How long does it currently take to load?"

...shorter interview focused on performance...
```

## Duplicate Detection

If a similar pending issue exists:

```
Issue Reporter:
    "This looks similar to an existing issue:

    ISSUE-20241211-001: Dashboard crashes when filtering by date range
    Type: bug | Priority: high

    Is this the same issue?

    1. Yes, merge with existing (add my details)
    2. No, this is different (create new issue)
    3. Let me review the existing issue first"
```

## Async Operation

This command is designed to run independently of the orchestrator:

- **Session 1**: `/orchestrate` running, executing tasks
- **Session 2**: User runs `/issue` to report a bug
- Issue Reporter writes to queue
- Orchestrator picks up issue on next poll (every 10min or after task completion)

## Queue Location

Issues are written to: `.claude/issue_queue.md`

This file is project-specific and created from template if missing.

## Rejecting Issues

Use `/issue reject` to mark an issue as "won't fix":

```
/issue reject <issue-id> <reason>
```

### Examples

```
/issue reject ISSUE-20241211-001 "Out of scope for this project"

/issue reject ISSUE-20241211-002 "Duplicate of task-005 which is already complete"

/issue reject ISSUE-20241210-003 "Not reproducible - works as expected"
```

### Rejection Behavior

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

    OUTPUT:
        "═══════════════════════════════════════════════════════════
        ISSUE REJECTED
        ═══════════════════════════════════════════════════════════

        ID:     {issue_id}
        Status: won't fix
        Reason: {reason}

        ═══════════════════════════════════════════════════════════"
```

### Rejection Validation

| Condition | Result |
|-----------|--------|
| Issue not found | Error message |
| Issue already complete | Error: "Cannot reject completed issue" |
| Issue in_progress | Error: "Cannot reject issue with active task" |
| Issue already rejected | Error: "Issue already rejected" |
| No reason provided | Error: "Rejection reason required" |

### Reversing Rejection

To un-reject an issue (reopen), manually edit `.claude/issue_queue.md`:
- Change `status: wont_fix` back to `status: pending`
- Remove `rejected_at` and `rejection_reason` fields

Or report it again via `/issue` if the queue entry is unclear.

## Related Commands

| Command | Purpose |
|---------|---------|
| `/issues` | View issue queue status |
| `/issues <id>` | View specific issue details |
| `/progress` | Orchestrator status (includes pending issue count) |

---

*See also: [Issue Reporter Protocol](../issue_reporter/issue_protocol.md)*
