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
│  1. GIT STATUS CHECK                                            │
│     ├── Check if .git exists                                    │
│     ├── If no git → prompt user to initialize                   │
│     └── If git exists → note for auto-commits                   │
│                                                                  │
│  2. SKILL DISCOVERY (automatic, then prompt if needed)          │
│     ├── Try default locations silently                          │
│     ├── If skills found → report and continue                   │
│     └── If no skills → prompt user for directory                │
│                                                                  │
│  3. PROJECT DETECTION                                           │
│     ├── Check for existing journal → resume                     │
│     ├── Check for PRD.md → parse requirements                   │
│     └── Neither found → prompt for /prdgen                      │
│                                                                  │
│  4. CONFIRM AND BEGIN                                           │
│     └── Summarize setup, confirm with user, start execution     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Git Status Check

### Check for Git Repository

```
IF .git directory EXISTS:
    GIT_ENABLED = true

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
✓ Git repository detected
  Auto-commit after each task: enabled
─────────────────────────────────────────────────────
```

### If No Git Repository

```
IF .git directory DOES NOT EXIST:

ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
⚠️  No Git Repository Detected

Version control is recommended for tracking changes
made by agents. Without git, changes cannot be
easily reviewed or rolled back.

Would you like to initialize git?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Yes, initialize git
    Run 'git init' and enable auto-commits

  ○ No, continue without git
    Changes won't be tracked or committed
─────────────────────────────────────────────────────
```

**If user selects "Yes":**
```
RUN: git init
RUN: git add -A
RUN: git commit -m "Initial commit before orchestration"

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
✓ Git initialized
  Initial commit created
  Auto-commit after each task: enabled
─────────────────────────────────────────────────────
```

**If user selects "No":**
```
GIT_ENABLED = false

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
⚠️  Continuing without git
  Auto-commits disabled
  Consider initializing git later for change tracking
─────────────────────────────────────────────────────
```

---

## Phase 0.5: Autonomy Selection

After git check, prompt user for their preferred autonomy level.

### Autonomy Prompt

```
ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
🔐 Autonomy Level

How much control do you want during orchestration?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Supervised (Recommended)
    Approve each tool operation individually

  ○ Trust Agents
    Approve once per agent, then agent runs freely

  ○ Full Autonomy
    Auto-approve safe operations, block dangerous ones
─────────────────────────────────────────────────────
```

### Autonomy Level Behaviors

| Level | Behavior |
|-------|----------|
| **Supervised** | Default Claude Code behavior - prompts for each operation |
| **Trust Agents** | Single approval per Task spawn, agent runs autonomously |
| **Full Autonomy** | Safe-autonomy hook auto-approves most operations |

### Full Autonomy Safety Guardrails

When "Full Autonomy" is selected, the `safe-autonomy.sh` hook provides guardrails:

**Auto-Approved:**
- Read, Glob, Grep (most files)
- Edit (within project directory)
- Git commands (except force push to main)
- Package managers (npm, pip, cargo, etc.)
- Build/test commands
- Task tool (agent spawns)

**Auto-Denied:**
- `sudo`, `su` (privilege escalation)
- `rm -rf /` or recursive delete outside project
- `curl | bash` (code injection)
- Editing system files (/etc, ~/.bashrc)
- Reading sensitive files (.env, ~/.ssh, ~/.aws)
- `chmod 777`, `dd`, `mkfs`

**Passthrough (asks user):**
- Unrecognized commands
- Network operations not in allowlist

### Hook Verification

```
IF autonomy_level == "Full Autonomy":
    IF .claude/hooks/safe-autonomy.sh EXISTS AND EXECUTABLE:
        ORCHESTRATOR OUTPUT:
        ─────────────────────────────────────────────────────
        ✓ Full Autonomy enabled
          Safe-autonomy hook active
          Dangerous operations will be blocked
        ─────────────────────────────────────────────────────
    ELSE:
        ORCHESTRATOR OUTPUT:
        ─────────────────────────────────────────────────────
        ⚠️ Safe-autonomy hook not found

        Full Autonomy requires the safe-autonomy.sh hook.
        Run the installer or manually install:
          cp .claudestrator/templates/hooks/safe-autonomy.sh .claude/hooks/
          chmod +x .claude/hooks/safe-autonomy.sh

        Falling back to Supervised mode.
        ─────────────────────────────────────────────────────
        SET autonomy_level = "Supervised"
```

### Store Autonomy Selection

```
WRITE to session_state.md:
    autonomy_level: [selected level]
    autonomy_set_at: [timestamp]
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

## Phase 2: Project Detection (Enhanced State Detection)

### Check 1: Existing Journal

The orchestrator detects multiple states and offers appropriate options:

#### State A: Tasks In Progress

```
IF ./.claude/journal/index.md EXISTS AND
   any task has status == 'in_progress' OR pending with met dependencies:

ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📋 Resuming Project

Project: [name from index.md]
Run: [run_number] ([run_type])
Progress: [X/Y] tasks completed

Current state:
  • Completed: task-001, task-002, task-003
  • In progress: task-004 (Implement user authentication)
  • Pending: task-005, task-006

Resuming from task-004...
─────────────────────────────────────────────────────
```

#### State B: Project Complete (All Tasks Done)

```
IF ./.claude/journal/index.md EXISTS AND
   all tasks have status == 'completed' AND
   index.phase == 'complete':

ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
✅ Project Complete

Run [N] finished with all [X] tasks completed.

Project: [name]
Completed: [date]
Files created: [count]

What would you like to do?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Iterate
    Review outputs, gather feedback, create improvement tasks

  ○ Extend
    Add new requirements to the project

  ○ Archive
    Mark this run complete and start fresh
─────────────────────────────────────────────────────
```

**If user selects "Iterate":**
```
→ Enter Phase 6.1: Iteration Mode
→ See "Iteration Flow" section below
```

**If user selects "Extend":**
```
→ Enter Phase 6.2: Extension Mode
→ See "Extension Flow" section below
```

**If user selects "Archive":**
```
→ Archive current run to journal/archive/run-{N}/
→ Archive PRD to PRD-history/
→ Proceed to Phase 2, Check 2 (PRD Detection)
```

#### State C: Deorchestrated (Paused Session)

```
IF ./.claude/journal/index.md EXISTS AND
   (index.phase == 'paused' OR index.deorchestrated == true):

ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
📋 Previous Session Found

Project: [name]
Last active: [last_updated date]
Progress: [X/Y] tasks completed
Run: [N] ([run_type])
Phase: [phase] (paused via /deorchestrate)

Resume from where you left off?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Yes, resume (Recommended)
    Continue from task [next_task]

  ○ No, start fresh
    Archive current progress and begin new run
─────────────────────────────────────────────────────
```

**If user selects "Yes, resume":**
```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
✓ Resuming session

Reloading context from journal...
  • Loaded [X] completed task summaries
  • Loaded [Y] key decisions
  • Loaded context map with [Z] entries

Continuing with task-[next]...
─────────────────────────────────────────────────────
```

#### State D: Failed/Blocked State

```
IF ./.claude/journal/index.md EXISTS AND
   (active_blockers exist OR multiple tasks have status == 'failed'):

ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
⚠️ Previous Run Had Issues

Project: [name]
Run: [N]

Blockers:
  • [blocker 1]
  • [blocker 2]

Failed tasks:
  • task-[X]: [name] - [failure reason]
  • task-[Y]: [name] - [failure reason]

How would you like to proceed?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Review and retry
    Examine failures, attempt recovery

  ○ Skip and continue
    Mark blockers as skipped, proceed with remaining tasks

  ○ Reset and start fresh
    Archive current state, begin new run
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

## Phase 6: Iteration Flow

Entered when user selects "Iterate" from a completed project state.

### 6.1 Summary Generation

```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📊 Run [N] Summary

Completed: [X] tasks
Duration: [start_date] → [end_date]

Files Created:
  • src/components/Dashboard.tsx
  • src/services/api.ts
  • [...]

Key Features Implemented:
  • [feature 1 from PRD]
  • [feature 2 from PRD]

Architecture Decisions:
  • [decision 1 from journal]
  • [decision 2 from journal]

Known Limitations:
  • [from QA feedback]
─────────────────────────────────────────────────────
```

### 6.2 Feedback Collection

```
ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
What aspects need improvement?
─────────────────────────────────────────────────────

OPTIONS (multi-select):
  ☐ Performance issues
    Speed, memory, responsiveness

  ☐ UX/UI improvements
    Layout, interactions, accessibility

  ☐ Bug fixes
    Issues found during testing

  ☐ Feature enhancements
    Improvements to existing features

  ☐ Code quality
    Refactoring, patterns, maintainability
─────────────────────────────────────────────────────
```

For each selection, follow up with freeform:
```
ORCHESTRATOR PROMPT:
─────────────────────────────────────────────────────
Describe the [selected category] issues:

(Enter details about what needs to change)
─────────────────────────────────────────────────────
```

### 6.3 Task Generation

```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📝 Iteration Tasks

Based on your feedback, I've created:

ID   | Name                      | Complexity | Improves
-----|---------------------------|------------|----------
009  | Optimize API response time| normal     | task-005
010  | Add loading indicators    | easy       | task-003
011  | Fix date parsing bug      | easy       | task-004
012  | Refactor auth middleware  | normal     | task-006

Run: 2 (iteration)
PRD: Updated with iteration notes

Ready to begin iteration?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Yes, start iteration (Recommended)
    Begin with task 009

  ○ Modify tasks first
    Add, remove, or change tasks

  ○ Cancel
    Return to main menu
─────────────────────────────────────────────────────
```

---

## Phase 6.2: Extension Flow

Entered when user selects "Extend" from a completed project state.

### Extension Context

```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📋 Current Project State

Project: [name]
Completed: [X] tasks across [Y] runs
PRD Version: v[N]

Current Features:
  • [feature 1]
  • [feature 2]
  • [feature 3]

Architecture:
  • [key architectural pattern]
  • [tech stack summary]
─────────────────────────────────────────────────────
```

### Extension Options

```
ORCHESTRATOR PROMPT (using AskUserQuestion):
─────────────────────────────────────────────────────
How would you like to add new requirements?
─────────────────────────────────────────────────────

OPTIONS:
  ○ Run /prdgen (Recommended for large features)
    Generate full PRD for extension, then merge

  ○ Describe inline (For smaller additions)
    Add requirements directly in this session
─────────────────────────────────────────────────────
```

**If inline description:**
```
ORCHESTRATOR PROMPT:
─────────────────────────────────────────────────────
Describe the new features you want to add:

(List requirements, constraints, and success criteria)
─────────────────────────────────────────────────────
```

### Extension Task Generation

```
ORCHESTRATOR OUTPUT:
─────────────────────────────────────────────────────
📝 Extension Tasks

Analyzing new requirements against existing codebase...

Integration points identified:
  • [existing file] → needs modification for [new feature]
  • [existing component] → will be extended

New tasks:

ID   | Name                      | Complexity | Type
-----|---------------------------|------------|------
013  | Design export API         | normal     | design
014  | Implement CSV exporter    | normal     | implementation
015  | Add export UI controls    | normal     | feature
016  | Integration testing       | normal     | testing

Run: 3 (extension)
PRD: Updated with extension requirements

Ready to begin extension?
─────────────────────────────────────────────────────
```

---

## Summary: What Happens on First Run

1. **Git Check**
   - Checks for .git repository
   - Prompts to initialize if missing
   - Enables auto-commits if present

2. **Skill Discovery**
   - Automatically searches default locations
   - Reports what was found
   - Prompts only if nothing found

3. **Project Requirements**
   - Checks for existing journal (detects state)
   - Checks for PRD.md (parse it)
   - If no PRD: prompts for /prdgen

4. **Confirmation**
   - Summarizes understanding
   - Shows task breakdown
   - Gets user approval before starting

5. **Execution**
   - Creates journal
   - Begins first task
   - Reports progress throughout
   - Auto-commits after each task

## Summary: What Happens on Subsequent Runs

1. **State Detection**
   - In progress → Resume automatically
   - Complete → Offer iterate/extend/archive
   - Paused → Offer resume
   - Failed → Offer retry/skip/reset

2. **Context Reload**
   - Load journal summaries
   - Query knowledge graph
   - Rebuild context map

3. **Continue Execution**
   - Resume from next pending task
   - Or execute new iteration/extension tasks

---

*Flow Version: 2.1*
*Updated: December 2025*
*Added: Phase 6 Iteration/Extension flows, Enhanced state detection, Autonomy selection*
