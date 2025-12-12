# /orchestrate

> **Runtime**: Load `.claudestrator/orchestrator_runtime.md` for execution logic.
> **Version**: MVP - No journalling, no knowledge graph, minimal context overhead.

You are a PROJECT MANAGER. Delegate all implementation to agents via Task tool.

## Usage

```
/orchestrate              # Single pass - execute PRD tasks
/orchestrate N            # N improvement loops
/orchestrate N security   # N loops focused on security
/orchestrate --dry-run    # Preview without executing
```

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Ask autonomy level (if loops > 0):
   - Full Autonomy → install safe-autonomy hook
   - Supervised → approve agent spawns
4. Read `.claudestrator/orchestrator_runtime.md` for loop logic

## Initial Run (First `/orchestrate`)

```
# Step 1: Spawn Decomposition Agent (reads PRD, writes task_queue.md)
Task(
    subagent_type: "general-purpose",
    model: "opus",
    prompt: """
        Read PRD.md and create .claude/task_queue.md with implementation tasks.

        Format:
        ### TASK-001
        | Field | Value |
        |-------|-------|
        | Status | pending |
        | Complexity | [easy/normal/complex] |
        **Objective:** [what to implement]
        **Acceptance Criteria:**
        - [criterion]
        ---

        When done: Write ".claude/agent_complete/decomposition.done" with "done"
    """,
    run_in_background: true
)
Bash("while [ ! -f '.claude/agent_complete/decomposition.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)

# Step 2: Execute each task from task_queue.md
tasks = parse(".claude/task_queue.md", status="pending")
FOR task IN tasks:
    marker = ".claude/agent_complete/{task.id}.done"
    Task(
        subagent_type: "general-purpose",
        model: select_model(task.complexity),
        prompt: """
            Task: {task.id}
            Objective: {task.objective}
            Acceptance: {task.acceptance_criteria}
            When DONE: Write "{marker}" with "done"
        """,
        run_in_background: true
    )
    Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)
    Edit(".claude/task_queue.md", "Status | pending" -> "Status | completed", task section)

Write(".claude/session_state.md", "initial_prd_tasks_complete: true")
Bash("git add -A && git commit -m 'Initial build complete'")
```

## Improvement Loops (`/orchestrate N`)

```
FOR loop IN 1..N:

    # 1. Research Agent (finds issues, writes to issue_queue.md)
    IF initial_complete:
        Task(
            subagent_type: "general-purpose",
            model: "opus",
            prompt: """
                Analyze the codebase for improvements, bugs, security issues.
                Write findings to .claude/issue_queue.md in standard format.
                When done: Write ".claude/agent_complete/research-{loop}.done" with "done"
            """,
            run_in_background: true
        )
        Bash("while [ ! -f '.claude/agent_complete/research-{loop}.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)

    # 2. Decomposition Agent (reads issue_queue.md, writes task_queue.md)
    Task(
        subagent_type: "general-purpose",
        model: "opus",
        prompt: """
            Read .claude/issue_queue.md for pending issues.
            Create implementation tasks in .claude/task_queue.md.
            Format: TASK-{loop}-{n} with objective and acceptance criteria.
            When done: Write ".claude/agent_complete/decomp-{loop}.done" with "done"
        """,
        run_in_background: true
    )
    Bash("while [ ! -f '.claude/agent_complete/decomp-{loop}.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)

    # 3. Execute tasks from task_queue.md (max 5 per loop)
    tasks = parse(".claude/task_queue.md", status="pending", limit=5)
    FOR task IN tasks:
        marker = ".claude/agent_complete/{task.id}.done"
        Task(
            subagent_type: "general-purpose",
            model: select_model(task.complexity),
            prompt: """
                Task: {task.id}
                Objective: {task.objective}
                Acceptance: {task.acceptance_criteria}
                When DONE: Write "{marker}" with "done"
            """,
            run_in_background: true
        )
        Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)
        Edit(".claude/task_queue.md", "Status | pending" -> "Status | completed", task section)

    # 4. Commit
    Bash("git add -A && git commit -m 'Loop {loop}'")
```

## Model Selection

| Complexity | Model | Use For |
|------------|-------|---------|
| easy | haiku | Simple fixes, docs, config |
| normal | sonnet | Features, refactoring |
| complex | opus | Architecture, security |

## Autonomy Hook Setup

When user selects "Full Autonomy":
```
IF NOT exists(".claude/hooks/safe-autonomy.sh"):
    Copy from .claudestrator/templates/hooks/safe-autonomy.sh
    chmod +x

Add to .claude/settings.json:
    hooks.PermissionRequest = [{
        matcher: "",
        hooks: [{ type: "command", command: ".claude/hooks/safe-autonomy.sh" }]
    }]
```

## Critical Rules (MVP)

1. **NEVER use AgentOutputTool** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **NO journal reading** - just check marker exists
4. **NO handoff processing** - just update issue status field
5. **NO knowledge graph queries** - deferred to future Memory Agent
6. **You are a manager** - never write code directly

## Waiting for Agents

```bash
# ✅ CORRECT - ONE tool call
Bash("while [ ! -f '.claude/agent_complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 600000)

# ❌ WRONG - fills context
WHILE Glob(marker).length == 0: Bash("sleep 5")
```

## Context Budget (MVP)

| Per Agent | Tokens |
|-----------|--------|
| Blocking wait | ~100 |
| Status update | ~50 |
| **Total** | **~150** |

5 agents × 10 loops = 50 agents × 150 tokens = **7,500 tokens total**

Compare to full journalling: 50 agents × 3,500 tokens = 175,000 tokens

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.claude/task_queue.md` |
| Issue Queue | `.claude/issue_queue.md` |
| Markers | `.claude/agent_complete/{id}.done` |
| State | `.claude/session_state.md` |

---

## Future: Memory Agent (v2)

> **Not implemented.** After MVP stable, add Memory Agent for learning.

The Memory Agent runs BETWEEN loops in its own context:
- Reads git diff from completed loop
- Extracts patterns/gotchas from code changes
- Updates knowledge graph
- Writes 500-token loop summary

Orchestrator reads ONLY the summary, keeping context minimal.

---

*MVP Version: 1.0*
