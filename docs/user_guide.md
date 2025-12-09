# Orchestrator System User Guide

## Introduction

The Orchestrator System is a framework for managing complex, multi-step projects using Claude Code. Instead of handling all implementation details directly, the system:

1. **Decomposes** projects into discrete tasks
2. **Matches** each task to appropriate skills from a library
3. **Constructs** specialized agents dynamically
4. **Tracks** progress through a persistent journal
5. **Coordinates** verification and iteration

This approach keeps the primary agent (orchestrator) focused on coordination while delegating implementation to purpose-built agents with relevant expertise.

---

## Quick Start

### Starting a New Project

1. **Tell Claude what you want to build:**
   ```
   "I want to build a REST API for a todo list application"
   ```

2. **Claude (as orchestrator) will:**
   - Ask clarifying questions or read your PRD if one exists
   - Decompose the work into tasks
   - Initialize a journal to track progress
   - Begin executing tasks using specialized agents

3. **You can optionally provide a PRD:**
   Create `PRD.md` in your project directory with requirements, and Claude will use it instead of interviewing you.

### Resuming Work

If you start a new conversation on an existing project:
```
"Continue working on the project in /path/to/project"
```

Claude will read the journal and resume from where work left off.

---

## System Components

### Directory Structure

```
orchestrator/                    # The orchestrator system
├── orchestrator_protocol_v3.md  # Core protocol definition
├── skills/                      # Skill library
│   ├── skill_manifest.md        # Index of all skills
│   ├── skill_template.md        # Template for new skills
│   ├── agent_model_selection.md # Model selection criteria
│   ├── implementation/          # Code-writing skills
│   ├── design/                  # Design/planning skills
│   ├── quality/                 # QA/review skills
│   └── support/                 # Supporting skills
├── templates/                   # Document templates
│   ├── journal_index.md         # Journal index template
│   ├── task_entry.md            # Task file template
│   └── agent_prompt.md          # Agent prompt template
└── docs/
    └── user_guide.md            # This file

your-project/                    # Your project directory
├── PRD.md                       # (Optional) Project requirements
├── .claude/
│   └── journal/                 # Project journal (auto-created)
│       ├── index.md             # Current state and task registry
│       ├── task-001-*.md        # Individual task logs
│       └── task-002-*.md
└── [your project files]
```

### Key Files

| File | Purpose |
|------|---------|
| `orchestrator_protocol_v3.md` | The complete protocol Claude follows |
| `skill_manifest.md` | Index of available skills for matching |
| `journal/index.md` | Project state, task list, context map |
| `journal/task-*.md` | Detailed log for each task |

---

## How It Works

### Phase 1: Discovery

When you start a project, Claude will:

1. **Check for existing journal** - Resume if found
2. **Look for PRD.md** - Use requirements if found
3. **Interview you** - Ask about what you're building if no PRD

Example interview:
```
Q: What are you building?
A: A task management API

Q: What are the key features?
A: CRUD operations for tasks, user authentication, due dates

Q: Any technical constraints?
A: Node.js, Express, MongoDB

Q: What does success look like?
A: Working API with tests that I can deploy to Heroku
```

### Phase 2: Planning

Claude decomposes your requirements into tasks:

```markdown
| ID | Name | Complexity | Dependencies |
|----|------|------------|--------------|
| 001 | Set up project structure | easy | none |
| 002 | Design API endpoints | normal | none |
| 003 | Implement user model | normal | 001 |
| 004 | Implement auth middleware | normal | 003 |
| 005 | Implement task CRUD | normal | 003, 004 |
| 006 | Add validation | normal | 005 |
| 007 | Write tests | normal | 005 |
| 008 | QA verification | normal | all |
```

### Phase 3: Execution

For each task, Claude:

1. **Matches skills** from the library based on:
   - Task type (design, implementation, testing)
   - Keywords in the objective
   - Project domain
   - Complexity level

2. **Selects model** based on complexity:
   | Complexity | Model | Max Skills |
   |------------|-------|------------|
   | Easy | Haiku | 1 |
   | Normal | Sonnet | 2 |
   | Complex | Opus | 3 |

3. **Constructs agent prompt** combining:
   - Base agent instructions
   - Selected skill definitions
   - Task objective and criteria
   - Context from prior tasks
   - Relevant code references

4. **Spawns the agent** to execute the task

5. **Updates journal** with results

### Phase 4: Verification

After implementation tasks complete:
- QA agent verifies all acceptance criteria
- Issues found become new tasks
- Iteration continues until all criteria pass

---

## The Journal System

### Why Journals?

Journals solve the problem of context loss between agent invocations:
- Each agent execution is stateless
- Journals persist decisions, reasoning, and file locations
- New agents can read relevant history
- Orchestrator stays lightweight

### Journal Index (`journal/index.md`)

The index tracks:
- **Project metadata** - Name, type, domain, stack
- **Current state** - Phase, active task, progress
- **Task registry** - All tasks with status
- **Key decisions** - Architecture choices made
- **Context map** - Where important code lives

### Task Files (`journal/task-*.md`)

Each task file contains:
- **Metadata** - Status, model, complexity, dependencies
- **Objective** - What needs to be done
- **Acceptance criteria** - How to verify completion
- **Execution log** - Actions taken, files modified
- **Reasoning** - Why decisions were made
- **Handoff notes** - What the next agent needs to know

### Reading the Journal

You can inspect the journal anytime:
```bash
cat project/.claude/journal/index.md      # See overall state
cat project/.claude/journal/task-003-*.md # See specific task
```

---

## Available Skills

### Implementation Skills

| Skill | Use For |
|-------|---------|
| `html5_canvas` | HTML5 Canvas games, 2D graphics |
| `game_feel` | Polish, "juice", game effects |

### Design Skills

| Skill | Use For |
|-------|---------|
| `game_designer` | Game mechanics, progression, balance |
| `api_designer` | REST API design, endpoints |

### Quality Skills

| Skill | Use For |
|-------|---------|
| `qa_agent` | Testing, verification |
| `user_persona` | UX review, accessibility |
| `security_reviewer` | Security audits |

### Support Skills

| Skill | Use For |
|-------|---------|
| `svg_asset_gen` | Creating SVG graphics |
| `refactoring` | Code restructuring |
| `documentation` | Writing docs, READMEs |

---

## Creating Custom Skills

### 1. Copy the Template

```bash
cp orchestrator/skills/skill_template.md \
   orchestrator/skills/implementation/my_skill.md
```

### 2. Fill in Metadata

```yaml
---
name: My Custom Skill
id: my_skill
version: 1.0
domain: [web, backend]
task_types: [implementation, feature]
keywords: [keyword1, keyword2, keyword3]
complexity: [normal, complex]
pairs_with: [related_skill]
---
```

### 3. Define the Skill

Write:
- Role description
- Core competencies
- Code patterns with examples
- Quality standards
- Anti-patterns to avoid

### 4. Register in Manifest

Add entry to `skill_manifest.md`:
- Add to Quick Reference table
- Add detailed entry in Skill Details section

---

## Best Practices

### For Project Setup

1. **Write a PRD** for complex projects
   - Saves interview time
   - Provides reference throughout
   - Can be refined as you go

2. **Be specific about constraints**
   - Language/framework preferences
   - Performance requirements
   - Integration needs

### For During Development

1. **Let the orchestrator work**
   - Don't micromanage tasks
   - Trust the skill matching
   - Review journal if curious

2. **Provide feedback when asked**
   - Clarify ambiguous requirements
   - Make design decisions when needed
   - Report issues you discover

3. **Check the journal** if something seems wrong
   - Task files show detailed reasoning
   - Context map shows where code lives

### For Iteration

1. **Report bugs clearly**
   - What you expected
   - What happened
   - How to reproduce

2. **Request changes explicitly**
   - "Change X to do Y"
   - Claude will create appropriate tasks

---

## Troubleshooting

### "Context window exceeded"

**Cause**: Agent task file got too large or too much context passed.

**Solutions**:
- Let orchestrator use smaller context chunks
- Break tasks into smaller pieces
- Archive completed phases

### "Agent didn't complete the task"

**Cause**: Task was too complex or unclear.

**Solutions**:
- Check task file for reasoning/blockers
- Clarify requirements
- Break into smaller tasks

### "Wrong skill was matched"

**Cause**: Keywords didn't match well.

**Solutions**:
- Update skill manifest keywords
- Be more specific in task objective
- Manually suggest skills if needed

### "Journal got corrupted"

**Cause**: Partial write or conflict.

**Solutions**:
- Check git history if versioned
- Recreate from task files
- Worst case: restart journal (tasks are independent)

---

## Customization

### Adding Domain-Specific Skills

If you work in a specific domain (e.g., React, Django, Unity):

1. Create skill files with domain patterns
2. Add to manifest with appropriate keywords
3. Claude will match them to relevant tasks

### Modifying the Protocol

The protocol in `orchestrator_protocol_v3.md` can be adjusted:
- Change complexity thresholds
- Adjust skill matching weights
- Modify journal format

### Integrating with CI/CD

Journal files are plain markdown:
- Can be committed to git
- Can trigger automation on task completion
- Can generate reports from structured data

---

## Example Workflow

### Building a Simple Game

```
User: I want to build a simple snake game in HTML5

Claude: I'll help you build a snake game. Let me gather some details:
        - Canvas size preference?
        - Any specific features (walls, power-ups)?
        - Visual style preference?

User: 800x600, basic walls mode, retro pixel style

Claude: Creating project journal and decomposing into tasks...

        Tasks created:
        1. Set up HTML5 canvas boilerplate [easy]
        2. Design game mechanics [normal]
        3. Create SVG sprites [easy]
        4. Implement snake movement [normal]
        5. Implement food spawning [normal]
        6. Add collision detection [normal]
        7. Implement scoring [easy]
        8. Add game states [normal]
        9. Polish with effects [normal]
        10. QA verification [normal]

        Starting task 1...
        [Spawns agent with html5_canvas skill]

        Task 1 complete. Starting task 2...
        [Spawns agent with game_designer skill]

        ... continues until complete ...

        QA complete. Game is ready!
```

---

## Reference

### Model Selection Criteria

| Model | When to Use | Max Skills |
|-------|-------------|------------|
| Haiku | Simple changes, searches, constants | 1 |
| Sonnet | Features, fixes, standard implementation | 2 |
| Opus | Architecture, algorithms, complex decisions | 3 |

### Task Types

| Type | Description |
|------|-------------|
| design | Planning, specifications, architecture |
| implementation | Writing new code |
| feature | Adding to existing code |
| bugfix | Fixing defects |
| refactor | Restructuring code |
| testing | QA, verification |
| documentation | Writing docs |

### Task States

| State | Meaning |
|-------|---------|
| pending | Not started |
| in_progress | Currently executing |
| completed | Successfully finished |
| failed | Could not complete |
| blocked | Waiting on external factor |

---

## Getting Help

- Review `orchestrator_protocol_v3.md` for detailed protocol
- Check `skill_manifest.md` for available skills
- Inspect journal files for debugging
- Ask Claude to explain its reasoning

---

*User Guide Version: 1.0*
*Last Updated: December 2024*
