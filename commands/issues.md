# /issues - View Issue Queue

Display the current state of the project issue queue.

## Usage

```
/issues                 Show queue summary and all issues
/issues pending         Show only pending issues
/issues <issue-id>      Show details of a specific issue
```

## Display Format

### Queue Summary (/issues)

```
═══════════════════════════════════════════════════════════
ISSUE QUEUE
═══════════════════════════════════════════════════════════

SUMMARY
  Pending:     3
  Accepted:    2  (tasks created)
  In Progress: 1
  Completed:   5
  Won't Fix:   1

PENDING ISSUES (3)
  ISSUE-20241211-003  critical  bug          App crashes on login
  ISSUE-20241211-002  high      performance  Dashboard slow with 100+ items
  ISSUE-20241210-001  medium    enhancement  Add CSV export headers

ACCEPTED (awaiting execution)
  ISSUE-20241209-002  medium    bug          → task-012
  ISSUE-20241209-001  low       ux           → task-013

IN PROGRESS
  ISSUE-20241208-001  high      bug          → task-011 (agent-abc123)

═══════════════════════════════════════════════════════════
Commands: /issue (new) | /issues <id> (detail) | /reject <id>
═══════════════════════════════════════════════════════════
```

### Pending Only (/issues pending)

```
═══════════════════════════════════════════════════════════
PENDING ISSUES (3)
═══════════════════════════════════════════════════════════

ISSUE-20241211-003  [critical]  bug
  App crashes on login
  Reported: 10 minutes ago

ISSUE-20241211-002  [high]  performance
  Dashboard slow with 100+ items
  Reported: 2 hours ago

ISSUE-20241210-001  [medium]  enhancement
  Add CSV export headers
  Reported: 1 day ago

═══════════════════════════════════════════════════════════
Next poll: 8 minutes | After next task completion
═══════════════════════════════════════════════════════════
```

### Issue Detail (/issues ISSUE-20241211-002)

```
═══════════════════════════════════════════════════════════
ISSUE-20241211-002
═══════════════════════════════════════════════════════════

Status:    pending
Type:      performance
Priority:  high
Reported:  2024-12-11T14:30:00Z (2 hours ago)

SUMMARY
Dashboard slow with 100+ items

DETAILS
The dashboard takes over 5 seconds to render when there are
more than 100 transactions. This makes the app feel sluggish
for power users.

Current: 5+ seconds
Expected: < 1 second

CONDITIONS
- Occurs with 100+ transactions
- Worse on mobile devices
- First load after login is slowest

AFFECTED COMPONENTS
- src/components/Dashboard.tsx
- src/components/TransactionList.tsx

SUGGESTED FIX
Consider implementing virtualization or pagination for the
transaction list.

═══════════════════════════════════════════════════════════
Actions: /reject ISSUE-20241211-002 "reason"
═══════════════════════════════════════════════════════════
```

### Linked Issue (accepted/in_progress/complete)

```
═══════════════════════════════════════════════════════════
ISSUE-20241208-001
═══════════════════════════════════════════════════════════

Status:    in_progress
Type:      bug
Priority:  high
Reported:  2024-12-08T09:15:00Z (3 days ago)

SUMMARY
Date picker doesn't respond on mobile Safari

LINKED TASK
  Task ID:  task-011
  Status:   in_progress
  Agent:    agent-abc123
  Started:  5 minutes ago

Run /status agent-abc123 for agent output.

═══════════════════════════════════════════════════════════
```

## Implementation

```
FUNCTION displayIssues(filter):
    IF NOT EXISTS .claude/issue_queue.md:
        OUTPUT: "No issue queue found. Run /issue to report an issue."
        RETURN

    issues = PARSE .claude/issue_queue.md

    IF filter == "pending":
        issues = issues.filter(i => i.status == "pending")
        DISPLAY pending list format
    ELSE IF filter matches ISSUE-* pattern:
        issue = issues.find(i => i.id == filter)
        IF issue:
            DISPLAY detail format
        ELSE:
            OUTPUT: "Issue not found: {filter}"
    ELSE:
        DISPLAY full summary format
```

## If No Queue Exists

```
═══════════════════════════════════════════════════════════
NO ISSUE QUEUE
═══════════════════════════════════════════════════════════

No issue queue exists for this project.
Run /issue to report your first issue.

═══════════════════════════════════════════════════════════
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/issue` | Report a new issue |
| `/reject <id> <reason>` | Mark issue as won't fix |
| `/status` | Orchestrator status |
| `/status <agent-id>` | View agent working on issue |
