# Orchestrator Runtime (Slim)

> **Full reference**: See `orchestrator_protocol_v3.md` for detailed documentation.
> **This file**: ~2k tokens - load this, not the full protocol.

## Initial Run (`/orchestrate` - first time)

Decompose PRD into tasks, execute them. No research agent.

```
tasks = decompose_prd_into_tasks()
FOR task IN tasks:
    execute_task(task)
    # Poll: WHILE Glob(marker).length == 0: Bash("sleep 5")

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
        spawn_research_agent(loop, focus_areas)
        WHILE Glob(research_marker).length == 0: Bash("sleep 5")
    ELSE:
        # Still building - execute remaining PRD tasks
        continue_prd_tasks()

    # 2. Execute issues (max 5 per loop)
    FOR issue IN read_pending_issues().slice(0, 5):
        marker = ".claude/agent_complete/{issue.id}.done"
        Task(..., run_in_background: true)

        # Poll SILENTLY - no ls output
        WHILE Glob(marker).length == 0:
            Bash("sleep 5")

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

1. **NEVER use AgentOutputTool** - causes context bloat
2. **Poll via Glob** for completion markers
3. **Read only handoff section** from journals (~500 tokens)
4. **Spawn agents with run_in_background: true**
5. **Don't read full protocol** - use this runtime doc only
