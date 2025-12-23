# Task [ID]: [Name]

## Metadata (TABLE format - REQUIRED)

| Field | Value |
|-------|-------|
| Priority | [must_have / nice_to_have / critical / high / medium / low] |
| Status | pending |
| Category | [frontend / backend / testing / fullstack / devops / etc.] |
| Depends On | [task IDs or []] |

---

## Prose Section (BOLD format - REQUIRED)

**Description:** [REQUIRED - Clear description of what needs to be accomplished]

### For TEST tasks only:

**Steps:**
1. [REQUIRED - First test step]
2. [Second test step]
3. [Additional steps as needed]

**Expected Result:** [REQUIRED - Expected outcome of the test]

---

## Extended Fields (optional, for detailed tracking)

| Field | Value |
|-------|-------|
| Model | - |
| Complexity | [easy / normal / complex] |
| Skills | - |
| Created | [YYYY-MM-DD HH:MM] |
| Started | - |
| Completed | - |
| Blocks | [task IDs or "none"] |

## Acceptance Criteria

- [ ] [Criterion 1 - specific, testable condition]
- [ ] [Criterion 2 - specific, testable condition]
- [ ] [Criterion 3 - specific, testable condition]

## Context Provided

| Type | Reference | Purpose |
|------|-----------|---------|
| File | [path:lines] | [why agent needs this] |
| Task | [task-XXX summary] | [relevant decision/outcome] |
| Pattern | [pattern from knowledge graph] | [how to apply] |
| Gotcha | [warning from prior task] | [what to avoid] |

---

## Execution Log

*Populated by agent during execution*

### Agent Assignment

| Field | Value |
|-------|-------|
| Model | [haiku / sonnet / opus] |
| Skills | [skill IDs used] |
| Started | [timestamp] |

### Actions Taken

1. [Timestamp] [Action description]
2. [Timestamp] [Action description]
3. [Timestamp] [Action description]

### Files Modified

| File | Lines | Change Type | Description |
|------|-------|-------------|-------------|
| [path] | [range] | [add/modify/delete/refactor] | [what changed] |

### Errors Encountered

| Error | Cause | Resolution |
|-------|-------|------------|
| [error description] | [root cause] | [how fixed] |

### Reasoning

[Key decisions made during execution and why. Helps future agents understand intent.]

---

## Outcome

### Result

[completed / partial / failed / blocked]

### Summary

[1-2 sentence description of what was accomplished]

### Acceptance Criteria Status

- [x] [Criterion 1]
- [x] [Criterion 2]
- [ ] [Criterion 3 - why not met]

---

## Handoff

```yaml
outcome: [completed | partial | failed | blocked]

files_created:
  - path: [relative/path/to/file]
    purpose: [what this file does]
    lines: [1-N or "all"]

files_modified:
  - path: [relative/path/to/file]
    lines: [start-end]
    change_type: [add | modify | delete | refactor]
    description: [what changed and why]

patterns_discovered:
  - pattern: [the pattern in one sentence]
    location: [where it's used/defined]
    applies_to: [tag1, tag2, tag3]

gotchas:
  - issue: [the gotcha in one sentence]
    discovered_in: [where/how found]
    mitigation: [how to avoid/handle]
    severity: [high | medium | low]

dependencies_for_next:
  - file: [path next agent should read]
    reason: [why it's needed]

open_questions:
  - question: [unresolved question]
    context: [why it matters]
    recommendation: [suggested answer]
    blocking: [true | false]

suggested_next_steps:
  - step: [what should happen next]
    priority: [high | medium | low]
    depends_on: [file1, file2]

blockers:  # Required if outcome is blocked or partial
  - blocker: [what's blocking]
    impact: [what can't be done]
    suggested_resolution: [how to resolve]
    blocking_tasks: [task-XXX, task-YYY]
```

---

*Task completed: [timestamp]*
