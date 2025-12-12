# Orchestrator Runtime (Slim)

> **Full reference**: See `orchestrator_protocol_v3.md` for detailed documentation.
> **This file**: ~2k tokens - load this, not the full protocol.

## Core Loop

```
FOR loop IN 1..total_loops:
    # 1. Research (first loop only or if no pending issues)
    IF loop == 1 OR issue_queue_empty:
        spawn_research_agent(loop)
        wait_for_completion()

    # 2. Process issue queue
    issues = read_pending_issues()

    # 3. Execute each issue
    FOR issue IN issues.slice(0, 5):
        marker = ".claude/agent_complete/{issue.id}.done"

        Task(
            subagent_type: "general-purpose",
            model: select_model(issue.complexity),
            prompt: build_prompt(issue),
            run_in_background: true
        )

        # Poll for completion (NOT AgentOutputTool)
        WHILE NOT file_exists(marker):
            sleep(5)

        # Read result from journal
        handoff = read_handoff(issue.id)
        update_issue_status(issue, handoff)

    # 4. Commit if git enabled
    IF git_enabled:
        git add -A && git commit

    # 5. Save snapshot
    save_loop_snapshot(loop)
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
