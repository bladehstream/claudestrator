# Orchestrator Initialization Flow

## Overview

This document defines the exact interaction flow when the orchestrator starts a new session. It provides the concrete prompts and decision points for both skill discovery and project requirements gathering.

---

## Session Start Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION INITIALIZATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SKILL DISCOVERY (automatic, then prompt if needed)          │
│     ├── Try default locations silently                          │
│     ├── If skills found → report and continue                   │
│     └── If no skills → prompt user for directory                │
│                                                                  │
│  2. PROJECT DETECTION                                           │
│     ├── Check for existing journal → resume                     │
│     ├── Check for PRD.md → parse requirements                   │
│     └── Neither found → conduct interview                       │
│                                                                  │
│  3. CONFIRM AND BEGIN                                           │
│     └── Summarize setup, confirm with user, start execution     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Skill Discovery

### Automatic Discovery (Silent)

On session start, orchestrator attempts to find skills automatically:

```
SEARCH ORDER:
1. Project-local: ./skills/ or ./.claude/skills/
2. User global: ~/.claude/skills/
3. Bundled: [orchestrator install location]/skills/
```

### If Skills Found

```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📚 Skill Library Loaded

Directory: ~/.claude/skills/
Skills found: 12

By category:
  • implementation: html5_canvas, game_feel, react_components
  • design: game_designer, api_designer
  • quality: qa_agent, security_reviewer, user_persona
  • support: svg_asset_gen, documentation, refactoring

Ready for task matching.
─────────────────────────────────────────────────────
```

Then proceed to Phase 2.

### If No Skills Found

```
ORCHESTRATOR PROMPT:
─────────────────────────────────────────────────────
⚠️  No skills found in default locations.

I searched:
  • ./skills/
  • ./.claude/skills/
  • ~/.claude/skills/

To use the orchestrator, I need a directory containing skill
definition files (.md files with YAML frontmatter).

OPTIONS:
1. Provide a path to your skills directory
2. Use bundled skills from claudestrator repo
3. Continue without skills (limited functionality)

Where are your skills located?
─────────────────────────────────────────────────────
```

User provides path → scan that directory → report results.

### User Override

User can specify custom directory at any time:

```
USER: "Use skills from /home/user/my-custom-skills"

ORCHESTRATOR:
─────────────────────────────────────────────────────
📚 Scanning custom skill directory...

Directory: /home/user/my-custom-skills/
Skills found: 8
[... list skills ...]

Using this directory for skill matching.
─────────────────────────────────────────────────────
```

---

## Phase 2: Project Detection

### Check 1: Existing Journal

```
IF ./.claude/journal/index.md EXISTS:

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📋 Existing Project Found

Project: [name from index.md]
Status: [X/Y tasks completed]
Last active: [date from index.md]

Current state:
  • Completed: task-001, task-002, task-003
  • In progress: task-004 (Implement user authentication)
  • Pending: task-005, task-006

Would you like to:
1. Resume from where we left off
2. Start fresh (archive current journal)
3. Review the journal first

How should we proceed?
─────────────────────────────────────────────────────
```

### Check 2: PRD Exists

```
IF ./PRD.md OR ./specs/*.md EXISTS (and no journal):

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📄 Project Requirements Found

File: ./PRD.md

Let me review the requirements...

[Orchestrator reads and summarizes the PRD]

SUMMARY:
─────────────────────────────────────────────────────
Project: [extracted name]
Type: [extracted type]
Key Features:
  1. [feature 1]
  2. [feature 2]
  3. [feature 3]

Technical Stack: [extracted constraints]
─────────────────────────────────────────────────────

Does this accurately capture your requirements?
If yes, I'll decompose this into tasks and begin.
If not, what should I adjust?
─────────────────────────────────────────────────────
```

### Check 3: New Project (Interview)

```
IF no journal AND no PRD:

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
🆕 New Project Setup

I don't see an existing journal or PRD file.
Let me gather some information about your project.

─────────────────────────────────────────────────────

QUESTION 1 of 4: Project Overview

What are you building?
(Brief description - e.g., "A task management API" or
"A 2D puzzle game")

─────────────────────────────────────────────────────
```

**User responds**

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
QUESTION 2 of 4: Key Features

What are the main features or requirements?
(List the core functionality - e.g., "User auth, CRUD for
tasks, due date reminders, team sharing")

─────────────────────────────────────────────────────
```

**User responds**

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
QUESTION 3 of 4: Technical Constraints

Any technical requirements or constraints?
(Language, framework, dependencies, platforms, etc.)

If none, just say "no constraints" or "your choice"

─────────────────────────────────────────────────────
```

**User responds**

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
QUESTION 4 of 4: Success Criteria

What does "done" look like?
(How will we know the project is complete?)

─────────────────────────────────────────────────────
```

**User responds**

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
📋 Project Summary

Based on your responses:

PROJECT: [interpreted name]
TYPE: [game/webapp/api/cli/library/etc.]

FEATURES:
  1. [feature 1]
  2. [feature 2]
  3. [feature 3]
  ...

TECHNICAL:
  • Language: [language]
  • Framework: [framework or "none specified"]
  • Constraints: [any constraints]

SUCCESS CRITERIA:
  • [criterion 1]
  • [criterion 2]

─────────────────────────────────────────────────────

Does this look correct?

Options:
1. Yes, proceed with planning
2. Let me clarify something
3. Save as PRD.md for future reference, then proceed

─────────────────────────────────────────────────────
```

---

## Phase 3: Task Decomposition

Once requirements are confirmed:

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
🔨 Decomposing into Tasks

Analyzing requirements and creating task breakdown...

TASKS IDENTIFIED:
─────────────────────────────────────────────────────
ID   | Name                      | Complexity | Deps
-----|---------------------------|------------|------
001  | Set up project structure  | easy       | -
002  | Design data models        | normal     | -
003  | Implement user model      | normal     | 001
004  | Implement auth middleware | normal     | 003
005  | Implement core API        | normal     | 003,004
006  | Add validation            | normal     | 005
007  | Write tests               | normal     | 005
008  | QA verification           | normal     | all

Total: 8 tasks
Estimated complexity: Normal (mostly Sonnet agents)

─────────────────────────────────────────────────────

Ready to begin execution?

Options:
1. Yes, start with task 001
2. Modify tasks first
3. Show me more detail on the tasks

─────────────────────────────────────────────────────
```

---

## Phase 4: Execution Confirmation

```
ORCHESTRATOR:
─────────────────────────────────────────────────────
✅ Setup Complete

CONFIGURATION:
  • Skills: 12 loaded from ~/.claude/skills/
  • Project: [project name]
  • Tasks: 8 tasks planned
  • Journal: ./.claude/journal/

EXECUTION PLAN:
  Starting with: task-001 (Set up project structure)
  Model: Haiku (easy complexity)
  Skills: documentation

I'll work through tasks sequentially, updating the
journal as I go. You can check progress anytime by
asking "show status" or reviewing the journal.

─────────────────────────────────────────────────────

Beginning task 001...
─────────────────────────────────────────────────────
```

---

## Quick Commands During Session

| Command | Action |
|---------|--------|
| "show status" | Display current task and overall progress |
| "show journal" | Summarize journal contents |
| "pause" | Stop after current task completes |
| "skip to task X" | Jump to specific task |
| "use skills from [path]" | Change skill directory |
| "show loaded skills" | List available skills |
| "add task: [description]" | Add new task to queue |

---

## Configuration Persistence

After first run, settings are saved to `.claude/orchestrator_config.md`:

```yaml
---
skill_directory: ~/.claude/skills/
default_model: sonnet
journal_location: ./.claude/journal/
auto_save_prd: true
---
```

Subsequent sessions read this config and skip prompts if valid.

---

## Summary: What Happens on First Run

1. **Skill Discovery**
   - Automatically searches default locations
   - Reports what was found
   - Prompts only if nothing found

2. **Project Requirements**
   - Checks for existing journal (resume?)
   - Checks for PRD.md (parse it)
   - If neither: conducts 4-question interview

3. **Confirmation**
   - Summarizes understanding
   - Shows task breakdown
   - Gets user approval before starting

4. **Execution**
   - Creates journal
   - Begins first task
   - Reports progress throughout

---

*Flow Version: 1.0*
