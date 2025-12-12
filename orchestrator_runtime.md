# Orchestrator Runtime (Slim)

> **Full reference**: See `orchestrator_protocol_v3.md` for detailed documentation.
> **This file**: ~2k tokens - load this, not the full protocol.

## Initial Run (`/orchestrate` - first time)

Decompose PRD into tasks, execute them. No research agent.

```
tasks = decompose_prd_into_tasks()
FOR task IN tasks:
    marker = ".claude/agent_complete/{task.id}.done"
    Task(..., run_in_background: true)

    # SINGLE blocking wait (ONE tool call, not a loop)
    Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)

# Mark initial run complete
Write(".claude/session_state.md", "initial_prd_tasks_complete: true")
```

## Improvement Loops (`/orchestrate N` - after initial complete)

Research agent ONLY runs if initial PRD tasks are done.

```
initial_complete = read_session_state("initial_prd_tasks_complete")

FOR loop IN 1..total_loops:
    # 1. Research phase - ONLY if initial build is done
    IF initial_complete:
        research_marker = ".claude/agent_complete/research-{loop}.done"
        spawn_research_agent(loop, focus_areas)
        # SINGLE blocking wait
        Bash("while [ ! -f '{research_marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)
    ELSE:
        # Still building - execute remaining PRD tasks
        continue_prd_tasks()

    # 2. Execute issues (max 5 per loop)
    FOR issue IN read_pending_issues().slice(0, 5):
        marker = ".claude/agent_complete/{issue.id}.done"
        Task(..., run_in_background: true)

        # SINGLE blocking wait (ONE tool call, blocks until file exists)
        Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)

        handoff = read_handoff(issue.id)
        update_issue(issue, handoff)

    # 3. Commit & snapshot
    git add -A && git commit
    save_snapshot(loop)
```

## Model Selection

| Complexity | Model |
|------------|-------|
| easy | haiku |
| normal | sonnet |
| complex | opus |

## Agent Prompt Template

```
You are executing task {task.id}: {task.summary}

## Acceptance Criteria
{task.acceptance_criteria}

## Instructions
1. Implement the requirement
2. Write to .claude/journal/task-{task.id}.md
3. When done: Write ".claude/agent_complete/{task.id}.done" with "done"

## Confidence Check
If LOW confidence: WebSearch for official docs first.
Prefer: vendor docs > GitHub > tutorials > forums
```

## File Paths

| Purpose | Path |
|---------|------|
| Issues | `.claude/issue_queue.md` |
| Journal | `.claude/journal/task-{id}.md` |
| Completion | `.claude/agent_complete/{id}.done` |
| State | `.claude/session_state.md` |
| Snapshots | `.claude/loop_snapshots/` |

## CRITICAL RULES

1. **NEVER use AgentOutputTool** - causes 50k+ token context bloat
2. **ONE blocking Bash per agent** - not a polling loop (see below)
3. **Read only handoff section** from journals (~500 tokens)
4. **Spawn agents with run_in_background: true**
5. **Don't read full protocol** - use this runtime doc only

## WAITING FOR AGENTS (CRITICAL - FOLLOW EXACTLY)

**Use a SINGLE blocking Bash command - NOT a loop of Glob + sleep calls**

```bash
# ✅ CORRECT - ONE tool call, blocks internally until file exists
Bash("while [ ! -f '.claude/agent_complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)

# ❌ WRONG - Creates 100+ tool calls that fill context:
WHILE Glob(".claude/agent_complete/{id}.done").length == 0:
    Bash("sleep 5")
```

**Why this matters:**
- The WRONG pattern: 10 min wait = 120 iterations = 240 tool calls = ~20k tokens
- The CORRECT pattern: 10 min wait = 1 tool call = ~100 tokens

**For multiple agents (wait for all N to complete):**
```bash
Bash("while [ $(ls .claude/agent_complete/*.done 2>/dev/null | wc -l) -lt {N} ]; do sleep 10; done && echo 'all done'", timeout: 600000)
```

**NEVER use:**
- `AgentOutputTool` / `TaskOutput` - adds 50-100k tokens per agent
- Repeated `Glob()` calls in a loop - fills context
- `Bash("ls ...")` for status checks - output fills context
