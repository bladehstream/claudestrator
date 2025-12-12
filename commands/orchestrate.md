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

## Main Loop (MVP)

```
FOR loop IN 1..total_loops:

    # 1. Research phase (only after initial PRD complete)
    IF initial_complete AND (loop == 1 OR no_pending_issues):
        marker = ".claude/agent_complete/research-{loop}.done"
        Task(
            prompt: <research_agent_prompt>,
            model: "opus",
            run_in_background: true
        )
        Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)

    # 2. Get pending issues (max 5 per loop)
    issues = parse(".claude/issue_queue.md", status="pending", limit=5)

    # 3. Execute each issue
    FOR issue IN issues:
        marker = ".claude/agent_complete/{issue.id}.done"

        Task(
            subagent_type: "general-purpose",
            model: select_model(issue.complexity),
            prompt: """
                Task: {issue.id} - {issue.summary}
                Details: {issue.details}
                Acceptance: {issue.acceptance_criteria}

                When DONE: Write "{marker}" with content "done"
            """,
            run_in_background: true
        )

        # SINGLE blocking wait
        Bash("while [ ! -f '{marker}' ]; do sleep 10; done && echo 'done'", timeout: 600000)

        # Update issue status (single field, no handoff reading)
        Edit(".claude/issue_queue.md", "Status | pending" -> "Status | completed", issue.id section)

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
| Issues | `.claude/issue_queue.md` |
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
