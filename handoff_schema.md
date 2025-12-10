# Structured Handoff Schema

## Overview

Handoff notes are the primary mechanism for knowledge transfer between agents. This schema replaces freeform prose with structured data that preserves semantic meaning and enables programmatic extraction.

**Problem**: "Naive summarization turns multi-step reasoning into vague soup."

**Solution**: Enforce schema for all agent handoffs, enabling:
- Automatic extraction of patterns and gotchas
- Reliable context gathering for subsequent agents
- Knowledge graph population
- Audit trail of what was learned

---

## Handoff Schema Definition

### YAML Format (in task files)

```yaml
## Handoff

outcome: completed | partial | failed | blocked

files_created:
  - path: src/auth/jwt.ts
    purpose: JWT token generation and validation
    lines: 1-150

files_modified:
  - path: src/config/database.ts
    lines: 45-67
    change_type: add | modify | delete | refactor
    description: Added connection pool configuration

patterns_discovered:
  - id: pattern-XXX  # Auto-generated if not provided
    pattern: Use AuthContext.getCurrentUser() for user state
    location: src/context/AuthContext.tsx
    applies_to: [auth, user-state, react-context]

gotchas:
  - id: gotcha-XXX  # Auto-generated if not provided
    issue: API rate limit is 100/min, not 1000/min as documented
    discovered_in: External payment API integration
    mitigation: Added retry logic with exponential backoff
    severity: high | medium | low

dependencies_for_next:
  - file: src/auth/jwt.ts
    reason: Contains token validation logic needed for protected routes
  - file: src/types/auth.ts
    reason: Type definitions for auth payloads

open_questions:
  - question: Should refresh tokens be stored in httpOnly cookies or localStorage?
    context: Security vs UX tradeoff
    recommendation: httpOnly cookies for better security
    blocking: false

suggested_next_steps:
  - step: Implement protected route middleware
    priority: high
    depends_on: [jwt.ts, AuthContext.tsx]
  - step: Add token refresh logic
    priority: medium
    depends_on: []

blockers:
  - blocker: Missing API credentials for payment service
    impact: Cannot complete payment integration
    suggested_resolution: Request credentials from user
    blocking_tasks: [task-005, task-006]
```

---

## Field Specifications

### outcome (required)
| Value | Meaning |
|-------|---------|
| `completed` | All acceptance criteria met |
| `partial` | Some criteria met, work can continue |
| `failed` | Could not complete, needs intervention |
| `blocked` | External dependency prevents completion |

### files_created (required if any)
```yaml
files_created:
  - path: string          # Relative path from project root
    purpose: string       # What this file does (1 sentence)
    lines: string         # Line range "start-end" or "all"
```

### files_modified (required if any)
```yaml
files_modified:
  - path: string          # Relative path from project root
    lines: string         # Line range affected
    change_type: enum     # add | modify | delete | refactor
    description: string   # What changed and why
```

### patterns_discovered (recommended)
```yaml
patterns_discovered:
  - id: string            # Optional, auto-generated if omitted
    pattern: string       # The pattern in one sentence
    location: string      # Where it's used/defined
    applies_to: [string]  # Tags for when to use this pattern
```

### gotchas (recommended)
```yaml
gotchas:
  - id: string            # Optional, auto-generated if omitted
    issue: string         # The gotcha in one sentence
    discovered_in: string # Where/how it was found
    mitigation: string    # How to avoid/handle it
    severity: enum        # high | medium | low
```

### dependencies_for_next (recommended)
```yaml
dependencies_for_next:
  - file: string          # Path the next agent should read
    reason: string        # Why it's needed
```

### open_questions (optional)
```yaml
open_questions:
  - question: string      # The unresolved question
    context: string       # Why it matters
    recommendation: string # Agent's suggested answer
    blocking: boolean     # Does this block next tasks?
```

### suggested_next_steps (recommended)
```yaml
suggested_next_steps:
  - step: string          # What should happen next
    priority: enum        # high | medium | low
    depends_on: [string]  # Files/components this depends on
```

### blockers (required if outcome is blocked/partial)
```yaml
blockers:
  - blocker: string       # What's blocking
    impact: string        # What can't be done
    suggested_resolution: string
    blocking_tasks: [string]  # Task IDs affected
```

---

## Processing Handoffs

### Orchestrator Processing

```
AFTER agent completes:
    READ task file
    PARSE handoff section as YAML

    # Update operational state
    FOR file IN handoff.files_created + handoff.files_modified:
        UPDATE journal.context_map with file info

    # Update knowledge graph
    FOR pattern IN handoff.patterns_discovered:
        CREATE pattern node in knowledge_graph
        LINK to current task node

    FOR gotcha IN handoff.gotchas:
        CREATE gotcha node in knowledge_graph
        LINK to current task node
        IF gotcha.severity == "high":
            ADD to orchestrator_memory.learned_context.gotchas

    # Handle blockers
    FOR blocker IN handoff.blockers:
        ADD to journal.active_blockers
        UPDATE blocked task statuses

    # Prepare for next agent
    context_for_next = {
        files_to_read: handoff.dependencies_for_next,
        patterns: handoff.patterns_discovered,
        gotchas: handoff.gotchas.filter(severity in ["high", "medium"]),
        open_questions: handoff.open_questions.filter(blocking == true)
    }
```

### Context Injection for Next Agent

```
WHEN spawning next agent that depends on completed task:
    EXTRACT from predecessor's handoff:
        - dependencies_for_next → agent reads these files
        - patterns_discovered → included in "patterns to follow"
        - gotchas → included in "warnings"
        - suggested_next_steps → informs task breakdown

    FORMAT as structured context:
        ## From Task [ID]: [Name]

        ### Files to Review
        | File | Reason |
        |------|--------|
        {{#each dependencies_for_next}}
        | {{file}} | {{reason}} |
        {{/each}}

        ### Patterns to Follow
        {{#each patterns_discovered}}
        - **{{pattern}}** (see: {{location}})
        {{/each}}

        ### Warnings
        {{#each gotchas where severity != "low"}}
        - ⚠️ {{issue}}: {{mitigation}}
        {{/each}}
```

---

## Updated Task File Template

```markdown
# Task [ID]: [Name]

## Metadata
[... existing metadata ...]

## Objective
[... existing objective ...]

## Acceptance Criteria
[... existing criteria ...]

## Context Provided
[... existing context ...]

---

## Execution Log
[... existing execution log format ...]

---

## Handoff

```yaml
outcome: [completed | partial | failed | blocked]

files_created:
  - path: [path]
    purpose: [purpose]
    lines: [range]

files_modified:
  - path: [path]
    lines: [range]
    change_type: [type]
    description: [description]

patterns_discovered:
  - pattern: [pattern description]
    location: [where]
    applies_to: [tags]

gotchas:
  - issue: [issue]
    discovered_in: [context]
    mitigation: [how to avoid]
    severity: [high | medium | low]

dependencies_for_next:
  - file: [path]
    reason: [why needed]

suggested_next_steps:
  - step: [what to do]
    priority: [high | medium | low]
    depends_on: [dependencies]
```

---

*Task completed: [timestamp]*
```

---

## Validation Rules

### Required Fields
- `outcome` - Always required
- `files_created` OR `files_modified` - At least one if any files changed
- `blockers` - Required if outcome is `blocked` or `partial`

### Conditional Requirements
| Condition | Required Fields |
|-----------|-----------------|
| outcome == completed | files_created/modified (if any) |
| outcome == partial | blockers, suggested_next_steps |
| outcome == failed | blockers with suggested_resolution |
| outcome == blocked | blockers with blocking_tasks |

### Format Validation
- All paths must be relative to project root
- Line ranges must be "N-M" or "all"
- Tags in applies_to must be lowercase, hyphenated
- severity must be high/medium/low
- priority must be high/medium/low

---

## Migration from Freeform Handoffs

For existing task files with freeform handoff notes:

```
1. PARSE freeform text for:
   - File mentions (paths) → files_created/modified
   - "Watch out for" / "Be careful" → gotchas
   - "Pattern" / "Always use" → patterns_discovered
   - "Next" / "Then" / "Should" → suggested_next_steps
   - "Question" / "Unclear" → open_questions

2. PROMPT agent to structure if ambiguous:
   "Please structure this handoff note:
    [freeform text]

    Into this format:
    [schema template]"

3. VALIDATE against schema

4. UPDATE task file with structured handoff
```

---

## Benefits

1. **Semantic Preservation**: Structured data doesn't lose meaning in summarization
2. **Automatic Knowledge Extraction**: Patterns/gotchas auto-populate knowledge graph
3. **Reliable Context Transfer**: Next agent gets exactly what it needs
4. **Queryable History**: Can search for all tasks that discovered patterns about "auth"
5. **Measurable Completeness**: Easy to verify all required fields present

---

*Handoff Schema Version: 1.0*
