# /refresh - Signal Orchestrator to Reload

Signal the orchestrator (running in another session) to immediately reload a specific resource. Writes a flag file that the orchestrator checks.

## Usage

```
/refresh issues       Reload issue queue immediately
/refresh skills       Reload skill directory
/refresh prd          Re-read PRD.md
```

**Important:** `/refresh` without an argument does nothing. You must specify what to refresh.

## Behavior

This command writes a signal file that the orchestrator detects and acts upon:

```
.claude/refresh_signal.md
```

### Signal File Format

```markdown
# Refresh Signal

- **Type**: {issues|skills|prd}
- **Requested**: {ISO timestamp}
- **Requested By**: Terminal 2 (support session)
- **Reason**: User requested immediate refresh via /refresh command
```

### Orchestrator Response

The orchestrator checks for this signal file:
- Before selecting the next task
- After each agent completes

When detected:

| Signal | Orchestrator Action |
|--------|---------------------|
| `issues` | Poll `.claude/issue_queue.md` immediately |
| `skills` | Re-scan skill directory, rebuild runtime index |
| `prd` | Re-read `PRD.md`, update project understanding |

After processing, the orchestrator deletes the signal file.

## Examples

### Refresh Issues (Most Common)

You've just reported a critical bug and want it picked up immediately:

```
Terminal 2:
  /issue "Production database connection failing"
  [completes interview, priority: critical]

  /refresh issues
  "Refresh signal sent: issues
   The orchestrator will poll the issue queue before its next task."
```

### Refresh Skills

You've added or modified a skill and want it available for the next agent:

```
Terminal 2:
  /ingest-skill https://example.com/new-skill.md
  [skill imported]

  /refresh skills
  "Refresh signal sent: skills
   The orchestrator will reload the skill directory before its next task."
```

### Refresh PRD

You've updated requirements and want the orchestrator to be aware (use with caution):

```
Terminal 2:
  [manually edited PRD.md to clarify a requirement]

  /refresh prd
  "Refresh signal sent: prd
   The orchestrator will re-read PRD.md before its next task.

   ⚠️  Note: In-flight tasks won't be affected. PRD changes apply to
   future task planning and iteration cycles."
```

## Implementation

```
FUNCTION refresh(target):
    IF target NOT IN ['issues', 'skills', 'prd']:
        OUTPUT: "Usage: /refresh issues|skills|prd

                 You must specify what to refresh:
                   /refresh issues  - Poll issue queue immediately
                   /refresh skills  - Reload skill directory
                   /refresh prd     - Re-read PRD.md"
        RETURN

    signal = {
        type: target,
        requested: NOW(),
        requested_by: "support session"
    }

    WRITE .claude/refresh_signal.md with signal

    IF target == 'issues':
        OUTPUT: "Refresh signal sent: issues
                 The orchestrator will poll the issue queue before its next task."

    ELSE IF target == 'skills':
        OUTPUT: "Refresh signal sent: skills
                 The orchestrator will reload the skill directory before its next task."

    ELSE IF target == 'prd':
        OUTPUT: "Refresh signal sent: prd
                 The orchestrator will re-read PRD.md before its next task.

                 ⚠️  Note: In-flight tasks won't be affected. PRD changes apply to
                 future task planning and iteration cycles."
```

## Display Format

### Success

```
═══════════════════════════════════════════════════════════
REFRESH SIGNAL SENT
═══════════════════════════════════════════════════════════

Type:      issues
Sent:      2025-12-11T15:30:00Z

The orchestrator will poll the issue queue before its next task.

═══════════════════════════════════════════════════════════
```

### No Argument

```
═══════════════════════════════════════════════════════════
REFRESH: ARGUMENT REQUIRED
═══════════════════════════════════════════════════════════

Usage: /refresh issues|skills|prd

  /refresh issues  - Poll issue queue immediately
  /refresh skills  - Reload skill directory
  /refresh prd     - Re-read PRD.md

═══════════════════════════════════════════════════════════
```

### Invalid Argument

```
═══════════════════════════════════════════════════════════
REFRESH: INVALID TARGET
═══════════════════════════════════════════════════════════

Unknown refresh target: "foo"

Valid targets:
  /refresh issues  - Poll issue queue immediately
  /refresh skills  - Reload skill directory
  /refresh prd     - Re-read PRD.md

═══════════════════════════════════════════════════════════
```

## Cautions

### PRD Refresh

Re-reading the PRD mid-orchestration has limited effect:
- **Won't affect** tasks already in the journal
- **Won't affect** agents currently executing
- **Will affect** future iteration/extension cycles
- **Will affect** how the orchestrator describes the project in status reports

For substantial PRD changes, consider waiting for the current run to complete and using the iteration/extension flow.

### Multiple Signals

If multiple `/refresh` commands are sent before the orchestrator checks:
- Only the most recent signal file exists
- Use separate commands if you need multiple refreshes

If you need to refresh multiple things:
```
/refresh issues
/refresh skills
```

The orchestrator will process each signal file it finds.

## Related Commands

| Command | Purpose |
|---------|---------|
| `/issue` | Report new issue |
| `/issues` | View issue queue |
| `/ingest-skill` | Import new skill |
| `/audit-skills` | Check skill library |
| `/status` | View orchestrator state |
