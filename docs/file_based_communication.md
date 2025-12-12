# File-Based Communication Architecture

This document specifies all data channels between the orchestrator and agents.

**CRITICAL RULE**: All orchestrator-agent communication MUST go through files.
Never use `AgentOutputTool` - it adds full agent conversation (50-100k tokens) to context.

---

## Communication Channels

### 1. Completion Markers

**Purpose**: Signal that an agent has finished (success or failure)

**Path**: `.claude/agent_complete/{task_id}.done`

**Writer**: Agent (when task completes)
**Reader**: Orchestrator (polling via Glob)

**Content**: Simple string "done"

**Pattern**:
```
# Agent prompt includes:
"When finished, Write '.claude/agent_complete/{task_id}.done' with content 'done'"

# Orchestrator waits with SINGLE blocking Bash (NOT a polling loop):
Bash("while [ ! -f '.claude/agent_complete/{task_id}.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)
```

**Context cost**: ~100 tokens (ONE tool call, blocks internally until file exists)

---

### 2. Task Journal / Handoff

**Purpose**: Structured result from agent to orchestrator

**Path**: `.claude/journal/task-{task_id}.md`

**Writer**: Agent (throughout execution, finalized on completion)
**Reader**: Orchestrator (after completion marker detected)

**Structure**:
```markdown
# Task: {task_name}

## Metadata
- Status: in_progress | completed | blocked | failed
- Started: {timestamp}
- Completed: {timestamp}

## Progress Log
- [timestamp] Started analyzing requirements
- [timestamp] Created src/auth/middleware.ts
- [timestamp] Running tests...

## Handoff

| Field | Value |
|-------|-------|
| Outcome | completed |
| Summary | Implemented JWT auth middleware |
| Files Changed | src/auth/middleware.ts, src/config/auth.ts |
| Blockers | None |
| Patterns Discovered | Use middleware composition for auth layers |
| Gotchas | Token refresh requires separate endpoint |

## Notes
Additional context for future tasks...
```

**Context cost**: ~500 tokens (reading handoff section only)

---

### 3. Issue Queue

**Purpose**: Agent-discovered improvements or bugs

**Path**: `.claude/issue_queue.md`

**Writer**: Research agent, QA agent, or any agent finding issues
**Reader**: Orchestrator (polling for new issues)

**Structure**:
```markdown
# Issue Queue

### ISSUE-20251212-001

| Field | Value |
|-------|-------|
| Status | pending |
| Source | generated |
| Type | security |
| Priority | high |
| Created | 2025-12-12T10:00:00Z |
| Loop | 1 |
| Complexity | normal |

**Summary:** Add CSRF protection to all forms

**Details:**
Forms lack CSRF tokens, vulnerable to cross-site attacks.

**Acceptance Criteria:**
- All forms include CSRF token
- Token validated on submission
- Invalid tokens return 403

**Files:** src/forms/*.tsx, src/middleware/csrf.ts

---
```

**Context cost**: ~200 tokens per issue read

---

### 4. Session State

**Purpose**: Track orchestration progress and running agents

**Path**: `.claude/session_state.md`

**Writer**: Orchestrator
**Reader**: Orchestrator, /progress command

**Structure**:
```markdown
# Session State

## Current Run
- Run ID: run-2025-12-12-001
- Started: 2025-12-12T10:00:00Z
- Loop: 2 of 5
- Focus: security, performance

## Running Agents
| ID | Task | Model | Started |
|----|------|-------|---------|
| agent-abc123 | ISSUE-001 | sonnet | 10:15:00 |

## Completed Agents
| ID | Task | Outcome | Duration |
|----|------|---------|----------|
| agent-xyz789 | ISSUE-002 | completed | 45s |

## Loop History
- Loop 1: 4/5 tasks completed
```

**Context cost**: ~300 tokens (metadata only, no agent outputs)

---

### 5. Knowledge Graph

**Purpose**: Accumulated patterns and gotchas from all tasks

**Path**: `.claude/knowledge_graph.md`

**Writer**: Orchestrator (after processing agent handoffs)
**Reader**: Orchestrator (when computing context for new tasks)

**Structure**:
```markdown
# Knowledge Graph

## Patterns

### pattern-001
- Type: pattern
- Tags: [react, state, hooks]
- Content: Use useReducer for complex state with multiple sub-values
- Source: task-003
- Confidence: high

## Gotchas

### gotcha-001
- Type: gotcha
- Tags: [typescript, generics]
- Content: Generic constraints must be repeated in implementation
- Source: task-007
- Confidence: medium
```

**Context cost**: ~100 tokens per relevant pattern/gotcha retrieved

---

### 6. Context Map

**Purpose**: Track which components/files have been modified and why

**Path**: `.claude/journal/index.md` (context_map section)

**Writer**: Orchestrator (from agent handoffs)
**Reader**: Orchestrator (when computing context)

**Structure**:
```markdown
## Context Map

| Component | Last Modified | Notes |
|-----------|---------------|-------|
| src/auth/ | task-003 | JWT middleware, refresh tokens |
| src/api/users.ts | task-005 | User CRUD endpoints |
| src/components/Form.tsx | task-008 | Added validation |
```

**Context cost**: ~50 tokens per relevant entry

---

### 7. Loop Snapshots

**Purpose**: Git diff and state snapshot per loop

**Path**: `.claude/loop_snapshots/run-{date}-{n}/loop-{m}/`

**Writer**: Orchestrator (after each loop)
**Reader**: User (for review), orchestrator (for recovery)

**Contents**:
- `diff.patch` - Git diff from this loop
- `state.md` - Session state at loop end
- `issues_completed.md` - Issues resolved this loop

**Context cost**: 0 (not read during normal operation)

---

## Prohibited Patterns

### DO NOT USE: AgentOutputTool

```python
# NEVER DO THIS - adds 50-100k tokens to context
result = AgentOutputTool(agent_id, block=true)

# ALSO BAD - still adds to context even without assignment
AgentOutputTool(agent_id, block=true)
```

### DO NOT: Store agent output in session state

```python
# BAD - bloats session state file
session_state.completed_agents.append({
    ...
    final_output: agent_result  # NEVER store this
})
```

### DO NOT: Read full task journal

```python
# BAD - reads entire file including all progress logs
content = Read(".claude/journal/task-{id}.md")
process(content)  # Processing full content

# GOOD - read only handoff section
content = Read(".claude/journal/task-{id}.md")
handoff = extractSection(content, "## Handoff")  # ~500 tokens
```

---

## Context Budget Per Loop

| Channel | Reads/Loop | Tokens/Read | Total |
|---------|------------|-------------|-------|
| Completion waits | 5-7 | 100 | 700 |
| Task handoffs | 5-7 | 500 | 3,500 |
| Issue queue | 2 | 200 | 400 |
| Session state | 3 | 300 | 900 |
| Knowledge graph | 1 | 500 | 500 |

**Total per loop**: ~6,000 tokens

**Comparison with other patterns**:
- With AgentOutputTool: 5 agents × 50k = 250,000 tokens/loop
- With Glob polling loop: 10 min × 12/min × 2 calls = ~20,000 tokens/agent
- With blocking Bash: 5 agents × 100 = 500 tokens
- **Reduction: 99.8%**

---

## Implementation Checklist

When adding new orchestrator-agent communication:

- [ ] Data flows through a file, not tool return values
- [ ] File path is deterministic (orchestrator can find it)
- [ ] File format is structured (YAML/Markdown with sections)
- [ ] Only necessary sections are read (not full file)
- [ ] Completion signaled via marker file, not AgentOutputTool
- [ ] Context cost estimated and documented

---

*Version: 1.0 - December 2025*
