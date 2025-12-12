# Orchestrator Runtime (MVP)

> **Version**: MVP - Minimal viable orchestration, no learning/journalling overhead.
> **Future**: Journalling and learning will be handled by a dedicated Memory Agent between loops.

## Initial Run (`/orchestrate`)

**Step 1: Spawn Decomposition Agent** (reads PRD, writes task_queue.md)

```
# Load the decomposition skill for the agent prompt
decomp_skill = Read(".claudestrator/skills/orchestrator/decomposition_agent.md")

Task(
    subagent_type: "general-purpose",
    model: "opus",
    prompt: """
        {decomp_skill}

        ---

        ## Your Task

        Read PRD.md and create .claude/task_queue.md with implementation tasks.
        Follow the process defined in the skill above.

        Source document: PRD.md
        Output file: .claude/task_queue.md
        Completion marker: .claude/agent_complete/decomposition.done
    """,
    run_in_background: true
)
Bash("while [ ! -f '.claude/agent_complete/decomposition.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
```

**Step 2: Execute Tasks** (orchestrator reads task_queue.md, spawns agents)

```
tasks = parse(".claude/task_queue.md", status="pending")
FOR task IN tasks:
    marker = ".claude/agent_complete/{task.id}.done"

    Task(
        prompt: <agent_prompt with task.objective and task.acceptance_criteria>,
        run_in_background: true
    )

    Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
    Edit(".claude/task_queue.md", "Status | pending" -> "Status | completed", task section)

Write(".claude/session_state.md", "initial_prd_tasks_complete: true")
```

## Improvement Loops (`/orchestrate N`)

```
FOR loop IN 1..N:
    # 1. Research Agent (finds issues, writes to issue_queue.md)
    IF initial_complete:
        Task(
            prompt: "Analyze codebase for improvements. Write issues to .claude/issue_queue.md.
                     When done: Write '.claude/agent_complete/research-{loop}.done' with 'done'",
            model: "opus",
            run_in_background: true
        )
        Bash("while [ ! -f '.claude/agent_complete/research-{loop}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

    # 2. Decomposition Agent (reads issue_queue.md, writes task_queue.md)
    decomp_skill = Read(".claudestrator/skills/orchestrator/decomposition_agent.md")

    Task(
        prompt: "{decomp_skill}\n\n---\n\n## Your Task\n\nSource: .claude/issue_queue.md\nOutput: .claude/task_queue.md\nMarker: .claude/agent_complete/decomp-{loop}.done",
        model: "opus",
        run_in_background: true
    )
    Bash("while [ ! -f '.claude/agent_complete/decomp-{loop}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

    # 3. Execute tasks from task_queue.md (max 5)
    tasks = parse(".claude/task_queue.md", status="pending", limit=5)
    FOR task IN tasks:
        marker = ".claude/agent_complete/{task.id}.done"
        Task(..., run_in_background: true)
        Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
        Edit(".claude/task_queue.md", "Status | pending" -> "Status | completed", task section)

    # 4. Commit
    Bash("git add -A && git commit -m 'Loop {loop}'")
```

## Agent Prompt (Minimal)

```
You are executing: {task.id} - {task.summary}

## Acceptance Criteria
{task.acceptance_criteria}

## Instructions
1. Implement the requirement
2. When DONE: Write ".claude/agent_complete/{task.id}.done" with content "done"

## Confidence Check
If LOW confidence on implementation approach: WebSearch for official docs first.
```

**No journal writing required.** Agents just implement and write the completion marker.

## Model Selection

| Complexity | Model |
|------------|-------|
| easy | haiku |
| normal | sonnet |
| complex | opus |

## File Paths (Minimal)

| Purpose | Path |
|---------|------|
| Task Queue | `.claude/task_queue.md` |
| Issue Queue | `.claude/issue_queue.md` |
| Completion | `.claude/agent_complete/{id}.done` |
| State | `.claude/session_state.md` |

## CRITICAL RULES

1. **NEVER use AgentOutputTool** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **NO journal reading** - just check marker exists
4. **NO handoff processing** - just update issue status field
5. **NO knowledge graph** - deferred to future Memory Agent

## Waiting for Agents

```bash
# ✅ CORRECT - ONE tool call
Bash("while [ ! -f '.claude/agent_complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# ❌ WRONG - fills context
WHILE Glob(marker).length == 0: Bash("sleep 5")
```

## Context Budget (MVP)

| Operation | Tokens |
|-----------|--------|
| Wait for agent | ~100 |
| Update issue status | ~50 |
| Git commit | ~100 |
| **Total per agent** | **~250** |

Compare to full journalling: ~3-5k tokens per agent.

---

## Future: Memory Agent Architecture

> **Not implemented in MVP.** This is the target architecture for v2.

After MVP is stable, add a dedicated Memory Agent that runs BETWEEN loops:

```
# Orchestrator (stays minimal)
FOR loop IN 1..N:
    execute_agents()
    Bash("git add -A && git commit")

    # Spawn Memory Agent at end of loop
    spawn_memory_agent(loop)
    wait_for_memory_agent()

# Memory Agent (separate context)
- Read all .claude/agent_complete/*.done markers
- Read corresponding source file changes (git diff)
- Extract patterns, gotchas from code changes
- Update .claude/knowledge_graph.json
- Write .claude/loop_summary.md (~500 tokens)
- Orchestrator reads ONLY loop_summary.md next loop
```

**Benefits:**
- Learning happens in isolated context (Memory Agent)
- Orchestrator stays minimal (~250 tokens/agent)
- Knowledge accumulates without bloating orchestrator
- Memory Agent can use Opus for sophisticated pattern extraction

---

*MVP Runtime Version: 1.0*
