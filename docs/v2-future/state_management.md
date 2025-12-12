# State Management: Hot/Cold Separation

## Overview

The orchestrator maintains two distinct state files following the "Context Economy" principle: frequently-accessed working memory (hot) and archival long-term memory (cold).

**Source**: Google Cloud ADK and Anthropic's context engineering research show that mixing transient session state with durable memory causes context degradation.

---

## Architecture

```
project/.claude/
├── session_state.md          # HOT: Working memory, read/write constantly
├── orchestrator_memory.md    # COLD: Long-term memory, read at start, append-only
├── knowledge_graph.json      # COLD: Tag-based index for retrieval
├── memories/                 # COLD: Episodic memory entries
└── journal/                  # OPERATIONAL: Task execution logs
```

---

## Hot State: session_state.md

### Purpose
Solves context loss between operations. Contains the "scratchpad" of current work.

### Characteristics
| Property | Value |
|----------|-------|
| Read frequency | Every orchestrator loop |
| Write frequency | After every significant action |
| Lifetime | Single session (cleared on `/deorchestrate`) |
| Content age | Current task only |

### Contents
- **Current Context**: Objective, phase, active task, git branch
- **Working Memory**: Hypotheses, tried approaches, next steps
- **Immediate Task List**: Checkbox items for current work
- **Waiting For**: Blocking items with timestamps
- **Quick Context**: Relevant files and decisions for current task

### Operations

```
ON orchestrator loop start:
    READ session_state.md
    EXTRACT current objective and task list
    RESUME from working memory if populated

ON significant action:
    UPDATE working memory with action result
    UPDATE immediate task list (check/uncheck)
    WRITE session_state.md

ON task completion:
    CLEAR working memory section
    UPDATE current context to next task
    WRITE session_state.md

ON session end (/deorchestrate):
    MIGRATE important discoveries to orchestrator_memory.md
    ARCHIVE session_state.md to memories/ if significant
    RESET session_state.md to template
```

### When to Update Hot State
| Trigger | What to Update |
|---------|----------------|
| Starting a task | Current context, working memory focus |
| Trying an approach | Working memory: tried section |
| Getting stuck | Working memory: hypothesis |
| Making progress | Immediate task list checkboxes |
| Discovering gotcha | Quick context: active gotchas |
| Waiting on something | Waiting for table |

---

## Cold State: orchestrator_memory.md

### Purpose
Preserves project understanding and learnings across sessions. The orchestrator's "institutional knowledge."

### Characteristics
| Property | Value |
|----------|-------|
| Read frequency | Once at session start |
| Write frequency | On key events (append-only) |
| Lifetime | Entire project duration |
| Content age | Historical + current |

### Contents
- **Project Understanding**: Goals, success criteria, constraints (rarely changes)
- **Key Decisions**: Append-only log of architectural choices
- **Learned Context**: Patterns, conventions, gotchas (grows over time)
- **User Preferences**: How user likes things done
- **Blockers & Risks**: Active and historical
- **Session History**: Summary of past sessions
- **Strategy Notes**: What's working, what's not

### Operations

```
ON session start (/orchestrate):
    READ orchestrator_memory.md
    LOAD project understanding into context
    LOAD learned context for reference
    CHECK blockers for active issues

ON key decision:
    APPEND to key decisions table
    DO NOT modify existing entries

ON pattern discovery:
    APPEND to learned context: code patterns
    UPDATE knowledge_graph with pattern node

ON session end:
    APPEND to session history
    CONSOLIDATE: Move significant discoveries from hot state
    UPDATE strategy notes if applicable
```

### What Gets Appended When
| Event | Section Updated |
|-------|-----------------|
| Architectural choice | Key Decisions |
| New code pattern found | Learned Context: Code Patterns |
| Convention established | Learned Context: Project Conventions |
| Gotcha discovered | Learned Context: Gotchas |
| User states preference | User Preferences |
| Blocker encountered | Blockers & Risks |
| Session ends | Session History |
| Strategy insight | Strategy Notes |

---

## State Lifecycle

### Session Start

```
1. LOAD cold state (orchestrator_memory.md)
   - Project understanding → working context
   - Active blockers → check before planning
   - Strategy notes → inform approach

2. CHECK for existing hot state (session_state.md)
   IF populated AND recent (< 1 hour):
       RESUME from working memory
       DISPLAY: "Resuming from: [current context]"
   ELSE:
       RESET hot state to template
       DISPLAY: "Starting fresh session"

3. LOAD operational state (journal/index.md)
   - Current task → populate hot state
   - Progress → display to user
```

### During Execution

```
LOOP:
    READ hot state
    DETERMINE next action

    IF spawning agent:
        SAVE hot state (checkpoint)
        QUERY knowledge_graph for relevant context
        SPAWN agent

    IF agent returns:
        UPDATE hot state with result
        APPEND learnings to cold state
        UPDATE knowledge_graph

    IF user interaction:
        UPDATE hot state with new context
        IF preference expressed:
            APPEND to cold state

    WRITE hot state
```

### Session End

```
1. CONSOLIDATE hot → cold
   FOR each discovery in working memory:
       IF significant (pattern, gotcha, decision):
           APPEND to appropriate cold state section
           ADD node to knowledge_graph

2. LOG session
   APPEND to session history:
       - Date, duration
       - Tasks completed
       - Brief outcome note

3. ARCHIVE hot state (optional)
   IF significant work done:
       COPY session_state.md to memories/YYYY-MM-DD-session.md

4. RESET hot state
   WRITE template to session_state.md
   READY for next session
```

---

## Migration from Legacy orchestrator_state.md

For projects using the old single-file system:

```
1. READ legacy orchestrator_state.md

2. SPLIT into components:
   - Session Info → orchestrator_memory.md (Project, Initialized, etc.)
   - Project Understanding → orchestrator_memory.md (as-is)
   - Key Decisions → orchestrator_memory.md (as-is)
   - Learned Context → orchestrator_memory.md (as-is)
   - Orchestrator Notes → orchestrator_memory.md: Strategy Notes
   - Blockers & Risks → orchestrator_memory.md (as-is)
   - Session Log → orchestrator_memory.md: Session History
   - Resume Context → session_state.md: Current Context + Working Memory

3. CREATE knowledge_graph.json
   - Add nodes for each key decision
   - Add nodes for each gotcha
   - Add nodes for each pattern

4. ARCHIVE legacy file
   MOVE orchestrator_state.md to memories/legacy-state-backup.md
```

---

## Best Practices

### Hot State
1. **Keep it current**: Clear working memory after task completion
2. **Be specific**: "Trying X approach because Y" not just "debugging"
3. **Track state changes**: Note what was tried and what happened
4. **List next actions**: Always have an "Immediate Task List"

### Cold State
1. **Append, don't edit**: Historical entries are immutable
2. **Be concise**: Summaries, not full details (details in memories/)
3. **Tag consistently**: Use same terminology for similar patterns
4. **Date everything**: All entries need timestamps

### General
1. **Save often**: Hot state after every significant action
2. **Query, don't load**: Use knowledge_graph to find relevant cold data
3. **Separate concerns**: Hot = current work, Cold = accumulated knowledge

---

## File Sizes

Expected sizes for healthy state management:

| File | Typical Size | Warning Threshold |
|------|--------------|-------------------|
| session_state.md | 1-5 KB | > 10 KB (too much in working memory) |
| orchestrator_memory.md | 5-50 KB | > 100 KB (needs summarization) |
| knowledge_graph.json | 10-100 KB | > 500 KB (prune old nodes) |
| Individual memory file | 0.5-2 KB | > 5 KB (split into multiple) |

---

*State Management Version: 1.0*
