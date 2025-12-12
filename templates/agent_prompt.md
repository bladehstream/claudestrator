# Agent Prompt Template (MVP)

> **Version**: MVP - Minimal prompt, no journalling overhead.
> **Future**: Full template with handoffs will be used when Memory Agent is implemented.

---

## MVP Agent Prompt

```markdown
# Agent Task

You are executing a single task for a larger project.

## Task: {{task_id}}

### Objective
{{task.objective}}

### Acceptance Criteria
{{#each task.acceptance_criteria}}
- [ ] {{this}}
{{/each}}

## Rules

1. **Focus**: Complete ONLY this task, nothing more
2. **Quality**: Meet all acceptance criteria before finishing
3. **Confidence**: If unsure about approach, WebSearch for official docs first

## Working Directory

Project root. Key locations:
- PRD: `./PRD.md`
- Source: `./src/` (or project-specific)

## When Done

**Write the completion marker:**
```
Write(".claude/agent_complete/{{task_id}}.done", "done")
```

This is the LAST thing you do. The orchestrator waits for this file.
```

---

## Template Variables

| Variable | Description |
|----------|-------------|
| `{{task_id}}` | Task identifier (e.g., "001", "auth-setup") |
| `{{task.objective}}` | Single sentence describing the task |
| `{{task.acceptance_criteria}}` | Array of criteria to meet |

---

## What's NOT in MVP

The following are deferred to v2 (Memory Agent):

- **Execution Log**: Agents don't write logs
- **Handoff YAML**: No structured handoff
- **Computed Context**: No patterns/gotchas injection
- **Skills Section**: Not loading skill files
- **Prior Work**: No dependency context

These add ~2-3k tokens per agent prompt. MVP keeps prompts under 500 tokens.

---

## Future: Full Template (v2)

When Memory Agent is implemented, restore:

1. **Handoff Schema** - Agents write structured YAML with patterns/gotchas
2. **Computed Context** - Inject relevant patterns from knowledge graph
3. **Execution Log** - Track actions for debugging
4. **Skills** - Load relevant skill files

The Memory Agent will:
- Process handoffs AFTER agents complete
- Update knowledge graph
- Prepare computed context for next loop

Orchestrator never reads raw handoffs - only Memory Agent summaries.

---

*MVP Template Version: 1.0*
