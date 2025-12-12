# File-Based Communication Architecture (MVP)

> **Version**: MVP - Minimal communication channels, no learning overhead.
> **Future**: Full architecture with journalling/knowledge graph handled by Memory Agent.

**CRITICAL RULE**: Never use `AgentOutputTool` - it adds 50-100k tokens to context.

---

## MVP Communication Channels

### 1. Completion Markers (Required)

**Purpose**: Signal agent has finished

**Path**: `.orchestrator/complete/{task_id}.done`

**Writer**: Agent (when done)
**Reader**: Orchestrator (blocking wait)

**Pattern**:
```bash
# Orchestrator waits (SINGLE blocking call):
Bash("while [ ! -f '.orchestrator/complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
```

**Context cost**: ~100 tokens

---

### 2. Issue Queue (Required)

**Purpose**: Track pending/completed tasks

**Path**: `.orchestrator/issue_queue.md`

**Writer**: Research agent, user via `/issue`
**Reader**: Orchestrator (get pending tasks)

**Structure**:
```markdown
### ISSUE-001

| Field | Value |
|-------|-------|
| Status | pending |
| Complexity | normal |

**Summary:** Add CSRF protection

**Acceptance Criteria:**
- Forms include CSRF token
- Token validated on submission
```

**Context cost**: ~200 tokens per issue

---

### 3. Session State (Required)

**Purpose**: Track orchestration progress

**Path**: `.orchestrator/session_state.md`

**Structure**:
```markdown
# Session State

initial_prd_tasks_complete: true
current_loop: 2
total_loops: 5
```

**Context cost**: ~100 tokens

---

## MVP Context Budget

| Operation | Tokens |
|-----------|--------|
| Blocking wait for agent | ~100 |
| Update issue status | ~50 |
| Read session state | ~100 |
| Git commit | ~100 |
| **Total per agent** | **~350** |

**5 agents × 10 loops = 17,500 tokens total**

---

## Prohibited Patterns

```python
# ❌ NEVER - adds 50-100k tokens
AgentOutputTool(agent_id)

# ❌ NEVER - polling loop fills context
WHILE Glob(marker).length == 0:
    Bash("sleep 5")

# ❌ NEVER - reading journals (MVP doesn't use them)
Read(".claude/journal/task-{id}.md")

# ❌ NEVER - knowledge graph queries (MVP doesn't use it)
knowledge_graph.queryByTags(...)
```

---

## Deferred to v2 (Memory Agent)

The following channels are NOT used in MVP:

| Channel | Path | Reason |
|---------|------|--------|
| Task Journal | `.claude/journal/task-*.md` | Agents don't write journals |
| Knowledge Graph | `.claude/knowledge_graph.json` | No pattern extraction |
| Context Map | `.claude/journal/index.md` | No context computation |
| Loop Snapshots | `.claude/loop_snapshots/` | No snapshot management |

**When Memory Agent is implemented:**
- Memory Agent reads git diff after each loop
- Extracts patterns/gotchas from code changes
- Updates knowledge graph
- Writes 500-token loop summary
- Orchestrator reads ONLY the summary

---

*MVP Version: 1.0*
