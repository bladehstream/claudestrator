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

**Recommended workflow:**

```
1. /prdgen                    # Generate project requirements (required)
2. /clear                     # Clear context window
3. /audit-skills              # Check skill library health
4. /ingest-skill <source>     # Import any missing skills (if needed)
5. /clear                     # Clear context before orchestration
6. /orchestrate               # Start with clean context
```

**Step-by-step:**

1. **Generate a PRD** (required):
   ```
   /prdgen
   ```
   Interactive interview that creates `PRD.md`. Uses clickable options for structured choices (template selection, platform choices, etc.).

2. **Clear context** after PRD generation:
   ```
   /clear
   ```

3. **Audit and enhance skills** (recommended):
   ```
   /audit-skills              # Check for issues, missing coverage
   /ingest-skill <url>        # Import any needed skills
   ```

4. **Clear context** before orchestration:
   ```
   /clear
   ```

5. **Start orchestration**:
   ```
   /orchestrate
   ```

6. **Claude (as orchestrator) will:**
   - Check for git repository (prompt to initialize if missing)
   - Load your PRD (stops if not found, prompts for `/prdgen`)
   - Decompose the work into tasks
   - Initialize a journal to track progress
   - Begin executing tasks using specialized agents
   - **Auto-commit** after each task completes (if git enabled)

7. **Git integration:**
   - If `.git` exists, orchestrator enables auto-commits
   - If not, you'll be prompted: "Initialize git?"
   - Each completed task creates a commit with task details
   - This allows easy review and rollback of agent changes

### Resuming Work

If you start a new conversation on an existing project:
```
"Continue working on the project in /path/to/project"
```

Claude will read the journal and resume from where work left off.

---

## Autonomy Levels

When you run `/orchestrate`, you'll be asked to choose an autonomy level:

| Level | Behavior | Best For |
|-------|----------|----------|
| **Supervised** | Approve each tool operation | Learning, sensitive projects |
| **Trust Agents** | Approve once per agent spawn | Balanced control |
| **Full Autonomy** | Auto-approve with safety guardrails | Experienced users, long runs |

### Supervised Mode (Default)

Standard Claude Code behavior - you approve each operation:
- Every file edit
- Every bash command
- Every agent spawn

Good for: First-time users, sensitive codebases, when you want full visibility.

### Trust Agents Mode

You approve when an agent is spawned (Task tool), but the agent runs without further prompts:
- Approve agent spawn once
- Agent executes all its operations freely
- Useful for trusting the skill matching system

Good for: Users comfortable with the skill system, medium-length runs.

### Full Autonomy Mode

The `safe-autonomy.sh` hook auto-approves most operations with safety guardrails:

**Auto-Approved:**
- File read/search operations (Read, Glob, Grep)
- File edits within project directory
- Git commands (except force push to main/master)
- Package managers (npm, pip, cargo, etc.)
- Build and test commands
- Agent spawns (Task tool)

**Auto-Denied (blocked):**
- `sudo`, `su` (privilege escalation)
- `rm -rf /` or recursive delete outside project
- `curl | bash` (code injection)
- Editing system files (/etc, ~/.bashrc, etc.)
- Reading sensitive files (.env, ~/.ssh, ~/.aws)
- Destructive disk operations (dd, mkfs)

**Passthrough (asks you):**
- Unrecognized commands
- Network operations not in allowlist

Good for: Experienced users, long orchestration runs, trusted codebases.

### Hook Installation

The safe-autonomy hook is installed automatically by the installer:
```
.claude/hooks/safe-autonomy.sh
```

If you need to reinstall it manually:
```bash
cp .claudestrator/templates/hooks/safe-autonomy.sh .claude/hooks/
chmod +x .claude/hooks/safe-autonomy.sh
```

### Customizing the Hook

You can edit `.claude/hooks/safe-autonomy.sh` to adjust:
- Which commands are auto-approved
- Which domains are allowed for web fetches
- Additional safety rules

---

## System Components

### Directory Structure

```
orchestrator/                    # The orchestrator system
├── orchestrator_protocol_v3.md  # Core protocol definition
├── initialization_flow.md       # First-run interaction scripts
├── skills/                      # Skill library
│   ├── skill_manifest.md        # Index of all skills
│   ├── skill_template.md        # Template for new skills
│   ├── implementation/          # Code-writing skills
│   ├── design/                  # Design/planning skills
│   ├── quality/                 # QA/review skills
│   ├── support/                 # Supporting skills
│   ├── security/                # Security skills
│   ├── domain/                  # Domain-specific skills
│   └── orchestrator/            # Self-use skills (agent_construction)
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
| `skill_loader.md` | Dynamic skill discovery specification |
| `skills/*.md` | Skill files (auto-discovered from frontmatter) |
| `journal/index.md` | Project state, task list, context map |
| `journal/task-*.md` | Detailed log for each task |

---

## Dynamic Skill Loading

Skills are discovered automatically - no static manifest required.

### How It Works

1. **On session start**, orchestrator scans the skill directory
2. **Parses YAML frontmatter** from each `.md` file
3. **Builds runtime index** searchable by domain, keywords, task types
4. **Reports loaded skills** to user

### Skill Directory Priority

```
1. User-specified: "Use skills from /path/to/skills"
2. Project-local: ./skills/ or ./.claude/skills/
3. User global: ~/.claude/skills/
4. Default: orchestrator/skills/
```

### Adding New Skills

Simply drop a properly formatted skill file into the directory:

```bash
# Copy template
cp skills/skill_template.md skills/implementation/my_new_skill.md

# Edit with your skill definition
# Ensure frontmatter has: name, id, domain, task_types, keywords, complexity

# Done - available next session
```

### Required Frontmatter

```yaml
---
name: My Skill Name
id: my_skill_id
domain: [web, backend]
task_types: [implementation, feature]
keywords: [keyword1, keyword2, keyword3]
complexity: [normal, complex]
pairs_with: [related_skill]  # optional
---
```

---

## How It Works

### Phase 1: Discovery

When you start orchestration, Claude will:

1. **Check git status** - Prompt to initialize if missing (enables auto-commits)
2. **Check for existing journal** - Resume if found
3. **Load PRD.md** - Parse requirements from your PRD

**If no PRD exists:** The orchestrator will stop and instruct you to:
```
1. Run /prdgen to generate requirements
2. Run /clear to reset context
3. Run /orchestrate again
```

This keeps the orchestration context clean and focused on execution rather than requirements gathering.

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
   | Easy | Haiku | 3 |
   | Normal | Sonnet | 7 |
   | Complex | Opus | 15 |

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

### Phase 5: Iteration & Extension

When all tasks complete, running `/orchestrate` again offers three options:

| Option | When to Use |
|--------|-------------|
| **Iterate** | You've tested the output and want improvements |
| **Extend** | You want to add new features |
| **Archive** | You're done and want to start fresh |

#### Iteration Mode

Iterate when you want to improve existing functionality:

```
1. Orchestrator shows run summary (files created, features built)
2. You select improvement categories:
   - Performance issues
   - UX/UI improvements
   - Bug fixes
   - Feature enhancements
   - Code quality
3. You describe specific issues for each category
4. New tasks are created with links to original tasks
5. PRD is updated with iteration notes
6. Tasks execute as normal
```

#### Extension Mode

Extend when you want to add new features:

```
1. Orchestrator shows current project state
2. You choose how to add requirements:
   - /prdgen for large features (separate interview)
   - Inline description for small additions
3. PRD is archived and updated with new requirements
4. Tasks are created with integration analysis
5. Tasks execute as normal
```

#### PRD Versioning

Each iteration or extension automatically archives the current PRD:

```
project/
├── PRD.md                      # Current/active PRD
└── PRD-history/
    ├── v1-initial.md           # Original PRD
    ├── v2-iteration-1.md       # After first iteration
    └── v3-extension-1.md       # After extension
```

This provides an audit trail of how requirements evolved.

---

## Agent Monitoring

During orchestration, sub-agents execute tasks in the background. You can monitor their progress without interrupting execution.

### Checking Agent Status

| Command | Description |
|---------|-------------|
| `/status` | Overview including running agent count |
| `/status agents` | List all running and recently completed agents |
| `/status <agent-id>` | View last output from a specific agent |

### Example: Listing Agents

```
/status agents

═══════════════════════════════════════════════════════════
AGENT STATUS
═══════════════════════════════════════════════════════════

RUNNING (2)
  agent-abc123  Task 004: Implement auth middleware    2m 34s
  agent-def456  Task 007: Write unit tests             45s

COMPLETED THIS SESSION (3)
  agent-xyz789  Task 003: Design data models      ✓    3m 12s
  agent-uvw321  Task 002: Set up project          ✓    1m 45s
  agent-rst654  Task 001: Initialize structure    ✓    0m 38s

═══════════════════════════════════════════════════════════
Usage: /status <agent-id> to see last agent output
═══════════════════════════════════════════════════════════
```

### Example: Agent Details

```
/status agent-abc123

═══════════════════════════════════════════════════════════
AGENT: agent-abc123
═══════════════════════════════════════════════════════════

Task:     004 - Implement auth middleware
Model:    sonnet
Skills:   authentication, security
Started:  2m 34s ago
Status:   running

LAST OUTPUT (12s ago)
───────────────────────────────────────────────────────────
Created src/middleware/auth.ts with JWT validation.
Now implementing refresh token logic...

Reading src/config/auth.config.ts for token expiry settings.
───────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════
```

### How It Works

- Orchestrator tracks agents in `session_state.md`
- Running agents can be polled for latest output via `AgentOutputTool`
- Completed agents store their final output for later inspection
- Agent IDs persist for the session, allowing lookup after completion

### Tips

- Use `/status agents` to see "what's happening right now"
- Use `/status <agent-id>` when an agent seems to be taking long
- Agent output is truncated to ~500 characters for readability
- Full task details are always in `journal/task-*.md`

---

## Issue Reporting

Report bugs, enhancements, and other issues asynchronously - even while the orchestrator is running tasks in another session.

### Why Async Issues?

- **Decoupled workflow** - Report issues without interrupting orchestration
- **Standardized format** - Issue Reporter interviews you to capture consistent details
- **Priority handling** - Critical issues jump the queue automatically
- **Duplicate detection** - Avoid creating redundant tasks

### Commands

| Command | Purpose |
|---------|---------|
| `/issue` | Report a new issue (spawns Issue Reporter) |
| `/issues` | View issue queue status |
| `/issues <issue-id>` | View specific issue details |
| `/reject <id> <reason>` | Mark issue as won't fix |

### Reporting an Issue

```
/issue

Issue Reporter:
    "What type of issue are you reporting?

    1. Bug - Something isn't working correctly
    2. Performance - Slowness or resource issues
    3. Enhancement - New feature request
    4. UX - User experience improvement
    5. Security - Security concern
    6. Refactor - Code quality issue"
```

The Issue Reporter will interview you based on the issue type, gathering:
- Reproduction steps (for bugs)
- Performance metrics (for performance issues)
- Acceptance criteria (for enhancements)
- Security impact (for security issues)

### Quick Issue

Start with context:
```
/issue Dashboard is slow when loading transactions
```

The Issue Reporter uses your description as a starting point and asks targeted follow-up questions.

### Issue Priority

| Priority | Behavior |
|----------|----------|
| `critical` | Interrupts queue - becomes next task immediately |
| `high` | Inserted at top of pending tasks |
| `medium` | Normal queue position by submission time |
| `low` | End of queue, after all other pending |

### How Issues Become Tasks

1. You run `/issue` and complete the interview
2. Issue is written to `.claude/issue_queue.md`
3. Orchestrator polls the queue:
   - Every 10 minutes during active orchestration
   - After each agent completes a task
   - When `/orchestrate` is started
4. Pending issues are converted to tasks with appropriate priority
5. Issue status updates as the task progresses

### Viewing the Queue

```
/issues

═══════════════════════════════════════════════════════════
ISSUE QUEUE
═══════════════════════════════════════════════════════════

SUMMARY
  Pending:     2
  Accepted:    1  (tasks created)
  In Progress: 1
  Completed:   3

PENDING ISSUES (2)
  ISSUE-20241211-002  high    performance  Dashboard slow with 100+ items
  ISSUE-20241211-001  medium  enhancement  Add CSV export headers

ACCEPTED (awaiting execution)
  ISSUE-20241210-001  medium  bug          → task-012

IN PROGRESS
  ISSUE-20241209-001  high    bug          → task-011 (agent-abc123)

═══════════════════════════════════════════════════════════
```

### Rejecting Issues

Mark an issue as "won't fix":
```
/reject ISSUE-20241211-001 "Out of scope for v1"
```

Only pending or accepted issues can be rejected.

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

1. **Generate a PRD first** (required)
   - Use `/prdgen` for interactive generation
   - Provides clear reference throughout execution
   - Can be refined before orchestration begins
   - Run `/clear` after PRD generation

2. **Audit skills before orchestration**
   - Run `/audit-skills` to check library health
   - Use `/ingest-skill` to import missing capabilities
   - Run `/clear` before starting orchestration

3. **Be specific about constraints**
   - Language/framework preferences
   - Performance requirements
   - Integration needs

### For During Development

1. **Let the orchestrator work**
   - Don't micromanage tasks
   - Trust the skill matching
   - Review journal if curious

2. **Monitor agent progress** with `/status`:
   ```
   /status              # Overview - shows running agent count
   /status agents       # List all running and recent agents
   /status agent-abc123 # See last output from specific agent
   ```

3. **Provide feedback when asked**
   - Clarify ambiguous requirements
   - Make design decisions when needed
   - Report issues you discover

4. **Check the journal** if something seems wrong
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
| Haiku | Simple changes, searches, constants | 3 |
| Sonnet | Features, fixes, standard implementation | 7 |
| Opus | Architecture, algorithms, complex decisions | 15 |

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

*User Guide Version: 1.3*
*Last Updated: December 2024*
