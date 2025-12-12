# /orchestrate (Slim Runtime)

> Load `.claudestrator/orchestrator_runtime.md` - NOT the full protocol.

## Usage
```
/orchestrate           # Single pass
/orchestrate N         # N improvement loops
/orchestrate N focus   # N loops focused on: security, performance, ux, etc.
```

## Startup

1. Check PRD.md exists
2. Check/init git
3. Ask autonomy level (if loops > 0)
4. Load skills manifest (not full skills)

## Main Loop

```python
for loop in range(1, total_loops + 1):
    # Research phase (spawns research agent)
    if loop == 1 or no_pending_issues():
        research_agent(loop, total_loops, focus)
        poll_completion(".claude/agent_complete/research-{loop}.done")

    # Get issues to work on
    issues = parse_issue_queue(limit=5)

    # Execute each issue
    for issue in issues:
        marker = f".claude/agent_complete/{issue.id}.done"

        Task(
            subagent_type="general-purpose",
            model=select_model(issue.complexity),
            prompt=f"""
                Task: {issue.summary}
                Details: {issue.details}
                Criteria: {issue.acceptance_criteria}

                When done:
                1. Write journal to .claude/journal/task-{issue.id}.md
                2. Write "{marker}" with content "done"
            """,
            run_in_background=True
        )

        # Poll for marker (NOT AgentOutputTool!)
        while not glob(marker):
            bash("sleep 5")

        # Read outcome
        handoff = read_journal_handoff(issue.id)
        mark_issue_complete(issue.id, handoff.outcome)

    # End of loop
    if git_enabled:
        bash("git add -A && git commit -m 'Loop {loop} complete'")

    save_snapshot(loop)
```

## Model Selection

- `easy` → haiku
- `normal` → sonnet
- `complex` → opus

## DO NOT

- Read `orchestrator_protocol_v3.md` (68k tokens!)
- Use `AgentOutputTool` (context bloat)
- Read full skill files (use manifest)
- Store agent outputs in variables
