# /status - Show Current State

Display the current orchestrator and project state without modifying anything.

## Usage

```
/status                 Show orchestrator overview
/status agents          List all running and recent agents
/status <agent-id>      Show last output from a specific agent
```

---

## /status (No Arguments)

Read and display information from:
- `.claude/session_state.md`
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
  Running agents: [count, or "none"]

RECENT ACTIVITY
  - [Last few actions/completions]

SESSION
  Duration: [time since /orchestrate]
  Checkpoints: [count]
  Autonomy: [supervised/trust-agents/full-autonomy]

SKILLS
  Loaded: [count] from [directory]

═══════════════════════════════════════════════════════════
Commands: /status agents | /checkpoint | /tasks | /skills
═══════════════════════════════════════════════════════════
```

---

## /status agents

List all running and recently completed agents from the current session.

Read from `.claude/session_state.md` (running_agents section).

```
═══════════════════════════════════════════════════════════
AGENT STATUS
═══════════════════════════════════════════════════════════

RUNNING (2)
  agent-abc123  Task 004: Implement auth middleware    2m 34s
  agent-def456  Task 007: Write unit tests             45s

COMPLETED THIS SESSION (3)
  agent-xyz789  Task 003: Design data models      ✓    3m 12s
  agent-uvw321  Task 002: Set up project          ✓    1m 45s
  agent-rst654  Task 001: Initialize structure    ✓    0m 38s

═══════════════════════════════════════════════════════════
Usage: /status <agent-id> to see last agent output
═══════════════════════════════════════════════════════════
```

**Implementation:**
1. Read `session_state.md` for `running_agents` and `completed_agents` arrays
2. For running agents, use `AgentOutputTool(agentId, block=false)` to check status
3. Display agent ID, task reference, and elapsed time

---

## /status <agent-id>

Show detailed status and last output from a specific agent.

```
═══════════════════════════════════════════════════════════
AGENT: agent-abc123
═══════════════════════════════════════════════════════════

Task:     004 - Implement auth middleware
Model:    sonnet
Skills:   authentication, security
Started:  2m 34s ago
Status:   running

LAST OUTPUT (12s ago)
───────────────────────────────────────────────────────────
Created src/middleware/auth.ts with JWT validation.
Now implementing refresh token logic...

Reading src/config/auth.config.ts for token expiry settings.
───────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════
```

**Implementation:**
1. Look up agent-id in `session_state.md`
2. Call `AgentOutputTool(agentId, block=false)` to get latest output
3. Truncate output to last ~500 characters if longer
4. Display agent metadata and output

**For completed agents:**
```
═══════════════════════════════════════════════════════════
AGENT: agent-xyz789 (completed)
═══════════════════════════════════════════════════════════

Task:      003 - Design data models
Model:     sonnet
Skills:    database_designer
Duration:  3m 12s
Outcome:   completed

FINAL OUTPUT
───────────────────────────────────────────────────────────
✓ Created src/models/User.ts
✓ Created src/models/Transaction.ts
✓ Created src/models/Category.ts
✓ Updated src/types/index.ts with exports

All acceptance criteria met. Models follow TypeScript
strict mode with full type coverage.
───────────────────────────────────────────────────────────

See: .claude/journal/task-003-design-data-models.md
═══════════════════════════════════════════════════════════
```

---

## If No State Exists

```
═══════════════════════════════════════════════════════════
NO ORCHESTRATOR STATE FOUND
═══════════════════════════════════════════════════════════

No orchestrator state exists for this project.
Run /orchestrate to initialize.

═══════════════════════════════════════════════════════════
```

## If Agent Not Found

```
═══════════════════════════════════════════════════════════
AGENT NOT FOUND
═══════════════════════════════════════════════════════════

No agent with ID "agent-invalid" found in this session.

Run /status agents to see available agents.

═══════════════════════════════════════════════════════════
```
