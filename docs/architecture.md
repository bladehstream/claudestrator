# Architecture Guide (MVP)

This document describes the Claudestrator MVP architecture focused on minimal orchestrator context.

---

## Core Principle

**The orchestrator only reads `task_queue.md`.** All heavy documents (PRD, issue_queue, codebase) are processed by specialized agents in their own isolated contexts.

---

## Agent Pipeline

### Initial Run (`/orchestrate`)

```
┌──────────┐      ┌─────────────┐      ┌────────────┐      ┌──────────────┐
│  PRD.md  │─────▶│ DECOMPOSE   │─────▶│ task_queue │─────▶│ IMPLEMENT    │
│  (user)  │      │   AGENT     │      │    .md     │      │   AGENTS     │
└──────────┘      └─────────────┘      └────────────┘      └──────────────┘
   5-10k              isolated            ~500 tokens         per task
   tokens             context
```

### Improvement Loops (`/orchestrate N`)

```
┌──────────┐      ┌─────────────┐      ┌─────────────┐      ┌────────────┐      ┌──────────────┐
│ Codebase │─────▶│  RESEARCH   │─────▶│ issue_queue │─────▶│ DECOMPOSE  │─────▶│ task_queue   │
│          │      │   AGENT     │      │     .md     │      │   AGENT    │      │    .md       │
└──────────┘      └─────────────┘      └─────────────┘      └────────────┘      └──────┬───────┘
  large              isolated              grows              isolated             ~500 │
                     context                                  context              tokens│
                                                                                        ▼
                                                                              ┌──────────────┐
                                                                              │ IMPLEMENT    │
                                                                              │   AGENTS     │
                                                                              └──────────────┘
```

---

## File Ownership

| File | Written By | Read By | Size |
|------|------------|---------|------|
| `PRD.md` | User / PRDGen | Decomposition Agent ONLY | 5-10k tokens |
| `.claude/issue_queue.md` | Research Agent | Decomposition Agent ONLY | Variable |
| `.claude/task_queue.md` | Decomposition Agent | **Orchestrator** | ~500 tokens |
| `.claude/session_state.md` | Orchestrator | Orchestrator | ~100 tokens |
| `.claude/agent_complete/*.done` | All agents | Orchestrator (via Bash) | ~10 tokens |

---

## Context Isolation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Orchestrator Context         Agent Contexts (Isolated)                │
│   ─────────────────────        ────────────────────────                 │
│                                                                         │
│   ┌───────────────────┐        ┌───────────────────┐                    │
│   │ • task_queue.md   │        │ Research Agent    │                    │
│   │   (~500 tokens)   │        │ • Full codebase   │                    │
│   │                   │        │ • Web access      │                    │
│   │ • session_state   │        │ • 50k+ tokens OK  │                    │
│   │   (~100 tokens)   │        └───────────────────┘                    │
│   │                   │                                                 │
│   │ • Wait results    │        ┌───────────────────┐                    │
│   │   (~100/agent)    │        │ Decomposition     │                    │
│   │                   │        │ • PRD (5-10k)     │                    │
│   │ TOTAL: ~1000      │        │ • issue_queue     │                    │
│   │ tokens/loop       │        │ • 10k+ tokens OK  │                    │
│   └───────────────────┘        └───────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Waiting for Agents

Orchestrator uses a **single blocking Bash command** - not a polling loop:

```bash
# ✅ CORRECT - ONE tool call, blocks until file exists
Bash("while [ ! -f '.claude/agent_complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# ❌ WRONG - Creates 100+ tool calls that fill context
WHILE Glob(marker).length == 0:
    Bash("sleep 5")
```

**Context savings:**
- Polling loop: 10 min = 120 iterations = ~20k tokens
- Blocking Bash: 10 min = 1 call = ~100 tokens

---

## Context Budget (MVP)

| Per Loop | Tokens |
|----------|--------|
| Read task_queue.md | ~500 |
| Wait for agents (blocking bash) | ~100/agent |
| Status updates | ~50/agent |
| Git commit | ~100 |
| **Total (5 agents)** | **~1,250** |

**10 loops × 1,250 = 12,500 tokens total**

Compare to previous architecture with journalling/knowledge graph: 175,000+ tokens

---

## Prohibited Patterns

```python
# ❌ NEVER - adds 50-100k tokens per agent
AgentOutputTool(agent_id, block=true)

# ❌ NEVER - polling loop fills context
WHILE Glob(marker).length == 0:
    Bash("sleep 5")

# ❌ NEVER - orchestrator should not read these
Read("PRD.md")           # Decomposition Agent reads this
Read("issue_queue.md")   # Decomposition Agent reads this
Read("knowledge_graph.json")  # Not used in MVP

# ❌ NEVER - outputs fill context
Bash("ls .claude/agent_complete/")
Bash("cat .claude/task_queue.md")
```

---

## Future: Memory Agent (v2)

After MVP is stable, add a Memory Agent that runs between loops:

```
End of Loop ──▶ MEMORY AGENT ──▶ loop_summary.md ──▶ Next Loop
                     │
                     ├── Read git diff
                     ├── Extract patterns/gotchas
                     ├── Update knowledge_graph.json
                     └── Write 500-token summary
```

Orchestrator reads ONLY the summary, keeping context minimal while enabling learning.

---

## Sequence Diagram

```
  Orchestrator         Decomposition         Research          Implementation
       │                    │                    │                    │
       │  /orchestrate      │                    │                    │
       │                    │                    │                    │
       │  Spawn ───────────▶│                    │                    │
       │                    │ Read PRD.md        │                    │
       │  Wait (bash)       │ Write task_queue   │                    │
       │◀───────────────────│ Write .done        │                    │
       │                    │                    │                    │
       │  Read task_queue   │                    │                    │
       │                    │                    │                    │
       │  FOR each task:    │                    │                    │
       │  Spawn ─────────────────────────────────────────────────────▶│
       │  Wait (bash)       │                    │                    │
       │◀─────────────────────────────────────────────────────────────│
       │  Update status     │                    │                    │
       │                    │                    │                    │
       │  Git commit        │                    │                    │
       │                    │                    │                    │
       │  /orchestrate N    │                    │                    │
       │                    │                    │                    │
       │  Spawn ────────────────────────────────▶│                    │
       │                    │                    │ Analyze codebase   │
       │  Wait (bash)       │                    │ Write issues       │
       │◀───────────────────────────────────────│ Write .done        │
       │                    │                    │                    │
       │  Spawn ───────────▶│                    │                    │
       │                    │ Read issue_queue   │                    │
       │  Wait (bash)       │ Write task_queue   │                    │
       │◀───────────────────│ Write .done        │                    │
       │                    │                    │                    │
       │  Read task_queue   │                    │                    │
       │  ... continue ...  │                    │                    │
```

---

*MVP Architecture Version: 1.0*
