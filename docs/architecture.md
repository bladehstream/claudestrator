# Architecture Guide (MVP 2.0)

This document describes the Claudestrator MVP 2.0 architecture with pre-configured agent profiles and category-based routing.

---

## Core Principles

1. **Orchestrator stays minimal** - only reads `task_queue.md`, never PRD or codebase
2. **Pre-configured agents** - agent profiles in `.claude/agents/` with built-in skills
3. **Category-based routing** - tasks routed to specialized agents by category
4. **File-based coordination** - agents write `.done` markers, orchestrator waits via blocking Bash

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         /orchestrate WORKFLOW                                │
│                              (MVP 2.0)                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   START     │
                              │ /orchestrate│
                              └──────┬──────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      STARTUP CHECKLIST          │
                    │  • PRD.md exists?               │
                    │  • git init if needed           │
                    │  • mkdir .orchestrator/complete │
                    │  • pwd → store WORKING_DIR      │
                    └────────────────┬────────────────┘
                                     │
═══════════════════════════════════════════════════════════════════════════════
                              INITIAL BUILD
═══════════════════════════════════════════════════════════════════════════════
                                     │
                    ┌────────────────▼────────────────┐
                    │     STEP 1: DECOMPOSITION       │
                    │                                 │
                    │  Task(decomposition-agent)      │
                    │         │                       │
                    │         ▼                       │
                    │  ┌─────────────────────┐        │
                    │  │ decomposition-agent │        │
                    │  │  • Read PRD.md      │        │
                    │  │  • Create tasks     │        │
                    │  │  • Write task_queue │        │
                    │  │  • Write .done      │        │
                    │  └─────────────────────┘        │
                    │         │                       │
                    │  while [ ! -f decomposition.done ]
                    │         │                       │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │     STEP 2: EXECUTE TASKS       │
                    │                                 │
                    │  Read task_queue.md             │
                    │         │                       │
                    │         ▼                       │
                    │  ┌─────────────────────────┐    │
                    │  │ For each pending task:  │    │
                    │  │                         │    │
                    │  │  Category → Agent       │    │
                    │  │  ─────────────────────  │    │
                    │  │  frontend → frontend-agent   │
                    │  │  backend  → backend-agent    │
                    │  │  testing  → qa-agent         │
                    │  │  *        → general-purpose  │
                    │  │                         │    │
                    │  │  Complexity → Model     │    │
                    │  │  ─────────────────────  │    │
                    │  │  easy    → haiku        │    │
                    │  │  normal  → sonnet       │    │
                    │  │  complex → opus         │    │
                    │  └───────────┬─────────────┘    │
                    │              │                  │
                    │              ▼                  │
                    │  ┌─────────────────────────┐    │
                    │  │   Task(selected-agent)  │    │
                    │  │   while [ ! TASK-XXX.done ]  │
                    │  │   Update status=completed    │
                    │  │   Next task...          │    │
                    │  └─────────────────────────┘    │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │     STEP 3: FINALIZE            │
                    │                                 │
                    │  session_state.md = complete    │
                    │  git commit "Initial build"     │
                    └────────────────┬────────────────┘
                                     │
                         ┌───────────▼───────────┐
                         │  N improvement loops? │
                         │      /orchestrate N   │
                         └───────────┬───────────┘
                                     │
                              NO ────┴──── YES
                              │             │
                              ▼             ▼
                           ┌────┐    ┌──────────────┐
                           │DONE│    │ LOOP 1..N    │
                           └────┘    └──────┬───────┘
                                            │
═══════════════════════════════════════════════════════════════════════════════
                           IMPROVEMENT LOOPS
═══════════════════════════════════════════════════════════════════════════════
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │              LOOP N START                        │
                    └───────────────────────┬─────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │  1. Check issue_queue.md for pending issues     │
                    └───────────────────────┬─────────────────────────┘
                                            │
                         ┌──────────────────┴──────────────────┐
                         │                                     │
                   PENDING ISSUES                        NO PENDING
                      EXIST                                ISSUES
                         │                                     │
                         │                    ┌────────────────▼────────────────┐
                         │                    │  2. SPAWN RESEARCH AGENT        │
                         │                    │                                 │
                         │                    │  Task(research-agent)           │
                         │                    │         │                       │
                         │                    │         ▼                       │
                         │                    │  ┌─────────────────────┐        │
                         │                    │  │   research-agent    │        │
                         │                    │  │  • Analyze codebase │        │
                         │                    │  │  • Find improvements│        │
                         │                    │  │  • Write 3-5 issues │        │
                         │                    │  │  • Write .done      │        │
                         │                    │  └─────────────────────┘        │
                         │                    │         │                       │
                         │                    │  while [ ! research.done ]      │
                         │                    │         │                       │
                         │                    └────────────────┬────────────────┘
                         │                                     │
                         └──────────────────┬──────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │  3. CONVERT ISSUES → TASKS                       │
                    │                                                  │
                    │  For each pending issue in issue_queue.md:       │
                    │    • Create task in task_queue.md                │
                    │    • Copy Category from issue                    │
                    │    • Set issue Status = in_progress              │
                    └───────────────────────┬─────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │  4. EXECUTE TASKS (same as Step 2)               │
                    │                                                  │
                    │  Route by Category → Agent                       │
                    │  Select Model by Complexity                      │
                    └───────────────────────┬─────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │  5. MARK ISSUES COMPLETE                         │
                    │                                                  │
                    │  Update issue Status = completed                 │
                    └───────────────────────┬─────────────────────────┘
                                            │
                    ┌───────────────────────▼─────────────────────────┐
                    │  6. COMMIT                                       │
                    │                                                  │
                    │  git commit "Improvement loop N"                 │
                    └───────────────────────┬─────────────────────────┘
                                            │
                         ┌──────────────────┴──────────────────┐
                         │                                     │
                    MORE LOOPS?                           LAST LOOP
                         │                                     │
                         ▼                                     ▼
                    ┌─────────┐                           ┌─────────┐
                    │ LOOP N+1│                           │  DONE   │
                    └────┬────┘                           └─────────┘
                         │
                         └────────────────► (back to LOOP START)
```

---

## Agent Catalog

Pre-configured agents in `.claude/agents/`:

| Agent | Model | Skills | Use For |
|-------|-------|--------|---------|
| `decomposition-agent` | sonnet | decomposition_agent | Breaking PRD into tasks |
| `frontend-agent` | sonnet | frontend_design, ui-generator | UI, React, styling |
| `backend-agent` | sonnet | api_development, database_designer, backend_security | API, database, server |
| `qa-agent` | sonnet | qa_agent, webapp_testing, playwright_qa_agent | Tests, validation |
| `research-agent` | sonnet | web_research_agent, qa_agent, security_reviewer | Finding improvements |
| `general-purpose` | varies | (built-in) | Everything else |
| `Explore` | haiku | (built-in, read-only) | Quick codebase search |

---

## Agent Routing

```
                    ┌─────────────────────────────────┐
                    │         ORCHESTRATOR            │
                    │   (reads task_queue.md)         │
                    └────────────────┬────────────────┘
                                     │
                         Category field determines route
                                     │
        ┌────────────┬───────────────┼───────────────┬────────────┐
        │            │               │               │            │
        ▼            ▼               ▼               ▼            ▼
   ┌─────────┐ ┌─────────┐    ┌─────────┐    ┌─────────┐   ┌─────────┐
   │frontend │ │backend  │    │ testing │    │fullstack│   │  docs   │
   │ -agent  │ │ -agent  │    │qa-agent │    │general- │   │general- │
   │         │ │         │    │         │    │purpose  │   │purpose  │
   └─────────┘ └─────────┘    └─────────┘    └─────────┘   └─────────┘
        │            │               │               │            │
        └────────────┴───────────────┴───────────────┴────────────┘
                                     │
                              All agents write
                         .orchestrator/complete/TASK-XXX.done
```

---

## File Structure

```
project/
├── PRD.md                          # Input: Product requirements
├── .claude/
│   └── agents/                     # Pre-configured agent profiles
│       ├── decomposition-agent.md
│       ├── frontend-agent.md
│       ├── backend-agent.md
│       ├── qa-agent.md
│       └── research-agent.md
└── .orchestrator/                  # Runtime data
    ├── task_queue.md               # Tasks with Category, Complexity
    ├── issue_queue.md              # Issues from research/user
    ├── session_state.md            # State tracking
    └── complete/                   # Completion markers
        ├── decomposition.done
        ├── TASK-001.done
        ├── TASK-002.done
        ├── research.done
        └── ...
```

---

## File Ownership

| File | Written By | Read By | Size |
|------|------------|---------|------|
| `PRD.md` | User / PRDGen | decomposition-agent ONLY | 5-10k tokens |
| `.orchestrator/issue_queue.md` | research-agent, user | Orchestrator | Variable |
| `.orchestrator/task_queue.md` | decomposition-agent | **Orchestrator** | ~500 tokens |
| `.orchestrator/session_state.md` | Orchestrator | Orchestrator | ~100 tokens |
| `.orchestrator/complete/*.done` | All agents | Orchestrator (via Bash) | ~10 tokens |

---

## Context Isolation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   Orchestrator Context         Agent Contexts (Isolated)                │
│   ─────────────────────        ────────────────────────                 │
│                                                                         │
│   ┌───────────────────┐        ┌───────────────────┐                    │
│   │ • task_queue.md   │        │ decomposition     │                    │
│   │   (~500 tokens)   │        │ • PRD (5-10k)     │                    │
│   │                   │        │ • skills loaded   │                    │
│   │ • session_state   │        └───────────────────┘                    │
│   │   (~100 tokens)   │                                                 │
│   │                   │        ┌───────────────────┐                    │
│   │ • Wait results    │        │ research-agent    │                    │
│   │   (~100/agent)    │        │ • Full codebase   │                    │
│   │                   │        │ • Web access      │                    │
│   │ TOTAL: ~1000      │        │ • 50k+ tokens OK  │                    │
│   │ tokens/loop       │        └───────────────────┘                    │
│   └───────────────────┘                                                 │
│                                ┌───────────────────┐                    │
│                                │ frontend-agent    │                    │
│                                │ backend-agent     │                    │
│                                │ qa-agent          │                    │
│                                │ • Task context    │                    │
│                                │ • Skills loaded   │                    │
│                                └───────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Waiting for Agents

Orchestrator uses a **single blocking Bash command** - not a polling loop:

```bash
# ✅ CORRECT - ONE tool call, blocks until file exists
Bash("while [ ! -f '.orchestrator/complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# ❌ WRONG - Creates 100+ tool calls that fill context
WHILE Glob(marker).length == 0:
    Bash("sleep 5")
```

**Context savings:**
- Polling loop: 10 min = 120 iterations = ~20k tokens
- Blocking Bash: 10 min = 1 call = ~100 tokens

---

## Context Budget (MVP 2.0)

| Per Loop | Tokens |
|----------|--------|
| Read task_queue.md | ~500 |
| Wait for agents (blocking bash) | ~100/agent |
| Status updates | ~50/agent |
| Git commit | ~100 |
| **Total (5 agents)** | **~1,250** |

**10 loops × 1,250 = 12,500 tokens total**

---

## Sequence Diagram

```
  Orchestrator         Decomposition         Research          Implementation
       │                    │                    │                    │
       │  /orchestrate      │                    │                    │
       │                    │                    │                    │
       │  Task(decomp...)  ─▶│                    │                    │
       │                    │ Read PRD.md        │                    │
       │  Wait (bash)       │ Write task_queue   │                    │
       │◀───────────────────│ Write .done        │                    │
       │                    │                    │                    │
       │  Read task_queue   │                    │                    │
       │  Route by Category │                    │                    │
       │                    │                    │                    │
       │  Task(agent) ──────────────────────────────────────────────▶│
       │  Wait (bash)       │                    │                    │
       │◀─────────────────────────────────────────────────────────────│
       │  Update status     │                    │                    │
       │                    │                    │                    │
       │  Git commit        │                    │                    │
       │                    │                    │                    │
       │  /orchestrate N    │                    │                    │
       │                    │                    │                    │
       │  No pending issues?│                    │                    │
       │  Task(research...) ────────────────────▶│                    │
       │                    │                    │ Analyze codebase   │
       │  Wait (bash)       │                    │ Write issues       │
       │◀───────────────────────────────────────│ Write .done        │
       │                    │                    │                    │
       │  Convert issues    │                    │                    │
       │  → tasks           │                    │                    │
       │                    │                    │                    │
       │  Task(agent) ──────────────────────────────────────────────▶│
       │  Wait (bash)       │                    │                    │
       │◀─────────────────────────────────────────────────────────────│
       │                    │                    │                    │
       │  Git commit        │                    │                    │
       │  ... next loop ... │                    │                    │
```

---

## Prohibited Patterns

```python
# ❌ NEVER - adds 50-100k tokens per agent
TaskOutput(agent_id, block=true)

# ❌ NEVER - polling loop fills context
WHILE Glob(marker).length == 0:
    Bash("sleep 5")

# ❌ NEVER - orchestrator should not read these
Read("PRD.md")           # decomposition-agent reads this
Read("issue_queue.md")   # research-agent writes, orchestrator converts

# ❌ NEVER - outputs fill context
Bash("cat .orchestrator/task_queue.md")
```

---

## Task Format

Tasks in `.orchestrator/task_queue.md` include Category for routing:

```markdown
### TASK-001

| Field | Value |
|-------|-------|
| Status | pending |
| Category | backend |
| Complexity | normal |

**Objective:** Implement user authentication endpoint

**Acceptance Criteria:**
- POST /auth/login accepts email and password
- Returns JWT token on success
- Returns 401 on invalid credentials

**Dependencies:** None

---
```

---

## Issue Format

Issues in `.orchestrator/issue_queue.md` include Category for task routing:

```markdown
### ISSUE-20251213-001

| Field | Value |
|-------|-------|
| Status | pending |
| Category | backend |
| Type | security |
| Priority | high |
| Complexity | normal |
| Source | research |

**Summary:** Add input validation to user registration

**Details:**
The POST /api/users endpoint lacks input validation.

**Acceptance Criteria:**
- Email format validated
- Password minimum length enforced
- Returns 400 on invalid input

---
```

---

*Architecture Version: 2.0*
*Last Updated: December 2025*
