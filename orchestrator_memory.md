# Orchestrator Memory System

## Overview

The orchestrator maintains a **global project memory** that persists across sessions. This is distinct from task-level journals - it captures orchestrator-level state, decisions, and learned context.

---

## Memory Architecture

```
project/.claude/
├── orchestrator_state.md      # PRIMARY: Global orchestrator memory
├── journal/
│   ├── index.md               # Task registry and progress
│   └── task-*.md              # Task-level execution logs
└── config.md                  # User preferences and settings
```

### Separation of Concerns

| File | Scope | Contents |
|------|-------|----------|
| `orchestrator_state.md` | Orchestrator-level | Session history, decisions, learned context, notes |
| `journal/index.md` | Project-level | Task registry, dependencies, context map |
| `journal/task-*.md` | Task-level | Execution logs, agent outputs |
| `config.md` | Configuration | Skill directory, preferences |

---

## Orchestrator State File Format

```markdown
# Orchestrator State

## Session Info
| Field | Value |
|-------|-------|
| Project | [project name] |
| Initialized | [first session date] |
| Last Active | [last session date] |
| Total Sessions | [count] |
| Current Phase | [planning/implementation/testing/complete] |

## Project Understanding

### What We're Building
[High-level description captured from user]

### Success Criteria
- [Criterion 1]
- [Criterion 2]

### Technical Constraints
- [Constraint 1]
- [Constraint 2]

## Key Decisions

Architectural and design decisions made during orchestration:

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| [date] | [what was decided] | [why] | [what it affects] |

## Learned Context

Things discovered during execution that inform future work:

### Code Patterns
- [Pattern observed]: [where and why]

### Project Conventions
- [Convention]: [description]

### Gotchas & Warnings
- [Issue]: [how to avoid]

## Orchestrator Notes

Observations and context not captured elsewhere:

- [date]: [note]
- [date]: [note]

## Blockers & Risks

| Item | Status | Mitigation |
|------|--------|------------|
| [blocker/risk] | [active/resolved] | [approach] |

## Session Log

| Session | Date | Duration | Tasks Completed | Notes |
|---------|------|----------|-----------------|-------|
| 1 | [date] | [time] | [task IDs] | [brief note] |
| 2 | [date] | [time] | [task IDs] | [brief note] |

## Resume Context

**For next session, remember:**
- [Important context point 1]
- [Important context point 2]
- [Current focus area]
- [Next recommended action]

---
*Last saved: [timestamp]*
```

---

## Lifecycle Commands

### `/orchestrate` - Initialize or Resume

When user runs `/orchestrate` or starts orchestrator mode:

```
1. CHECK for existing state
   IF .claude/orchestrator_state.md EXISTS:
       LOAD state
       DISPLAY resume summary
       ASK: "Resume from where we left off?"
   ELSE:
       RUN initialization flow (interview, skill discovery)
       CREATE orchestrator_state.md
       CREATE journal structure

2. LOAD configuration
   READ .claude/config.md if exists
   APPLY skill directory, preferences

3. LOAD task state
   READ journal/index.md
   IDENTIFY current phase and next task

4. REPORT ready state
   "Orchestrator active. Project: X. Progress: Y/Z tasks."
```

### `/checkpoint` - Save Current State

Explicit save without exiting:

```
1. UPDATE orchestrator_state.md
   - Current phase
   - Any new decisions
   - Learned context from this session
   - Session duration

2. UPDATE journal/index.md
   - Task statuses
   - Context map additions

3. CONFIRM to user
   "Checkpoint saved. You can safely pause or continue."
```

### `/status` - Show Current State

Display without modifying:

```
1. READ orchestrator_state.md
2. READ journal/index.md
3. DISPLAY summary:
   - Project name and phase
   - Progress (X/Y tasks)
   - Current/next task
   - Active blockers
   - Session duration
```

### `/deorchestrate` - Clean Exit

Proper shutdown with full save:

```
1. COMPLETE current operation (if any)
   - If agent running, wait for completion
   - Process agent result

2. SAVE full state
   - Update orchestrator_state.md
   - Update journal/index.md
   - Write "Resume Context" section

3. GENERATE exit summary
   "Session complete.
    Duration: X minutes
    Tasks completed: [list]
    Next recommended: [task/action]

    State saved. Run /orchestrate to resume."

4. CONFIRM safe to exit
```

---

## Auto-Save Triggers

State is automatically saved when:

| Trigger | What's Saved |
|---------|--------------|
| Task completion | Journal index, task file |
| Key decision made | Decision log in orchestrator_state |
| User provides context | Learned context section |
| Agent returns result | Context map updates |
| Every 10 minutes | Full checkpoint |
| Before spawning complex agent | Full checkpoint |

---

## State Loading Priority

On session start, load in this order:

```
1. orchestrator_state.md  → Orchestrator memory
2. config.md              → Configuration
3. journal/index.md       → Task state
4. Skill directory        → Available skills

IF any file missing:
    - orchestrator_state.md missing → Run full initialization
    - config.md missing → Use defaults
    - journal/index.md missing → Create empty, start fresh
    - Skills missing → Prompt user
```

---

## Resume Context Format

The "Resume Context" section is critical for session continuity:

```markdown
## Resume Context

**For next session, remember:**

### Immediate Context
- Currently working on: [task or "between tasks"]
- Last action taken: [what happened]
- Waiting for: [user input / nothing / specific info]

### Important Background
- [Key context point that affects next steps]
- [Recent decision that matters]
- [User preference expressed this session]

### Recommended Next Steps
1. [First thing to do]
2. [Second thing to do]

### Open Questions
- [Question needing user input]
- [Uncertainty to resolve]
```

---

## Implementation Notes

### What Orchestrator Writes

```
✅ .claude/orchestrator_state.md  (own memory)
✅ .claude/journal/index.md       (task registry)
✅ .claude/journal/task-*.md      (creates, agents fill)
✅ .claude/config.md              (configuration)

❌ Project source files           (agents only)
❌ Project assets                 (agents only)
❌ Project documentation          (agents only)
```

### Memory vs Journal

| Orchestrator State | Journal |
|-------------------|---------|
| Why decisions were made | What was done |
| Patterns observed | Files modified |
| User preferences | Execution logs |
| Session history | Task details |
| Resume context | Agent outputs |

---

## Slash Command Reference

| Command | Action |
|---------|--------|
| `/orchestrate` | Initialize or resume orchestrator mode |
| `/checkpoint` | Save current state without exiting |
| `/status` | Display current state summary |
| `/deorchestrate` | Clean exit with full save |
| `/skills` | Show loaded skills |
| `/tasks` | Show task list and status |
| `/decision [text]` | Log a key decision |
| `/note [text]` | Add orchestrator note |

---

*Memory System Version: 1.0*
