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

### Dual Terminal Workflow

Claudestrator is designed for a **dual terminal workflow**:

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ TERMINAL 1: Orchestrator        │  │ TERMINAL 2: Support Tasks       │
│─────────────────────────────────│  │─────────────────────────────────│
│ /orchestrate                    │  │ /prdgen        (before T1)      │
│   ├─► Executing tasks...        │  │ /issue         (report bugs)    │
│   ├─► Auto-polling issues       │  │ /issues        (view queue)     │
│   └─► Auto-committing           │  │ /refresh prd   (queue restart)  │
│                                 │  │ /ingest-skill  (add skills)     │
│ /progress agents                │  │ /abort         (emergency stop) │
│ /deorchestrate                  │  │                                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

### Starting a New Project

**Step-by-step:**

1. **Terminal 2: Generate a PRD** (required):
   ```
   /prdgen
   ```
   - Interactive interview creates `PRD.md`
   - Review the **skill gap analysis** at the end
   - Address critical gaps with `/ingest-skill` if needed

2. **Terminal 2: Clear context**:
   ```
   /clear
   ```

3. **Terminal 2: Audit skills** (optional):
   ```
   /audit-skills              # Check for issues
   /ingest-skill <url>        # Import any needed skills
   ```

4. **Terminal 1: Start orchestration**:
   ```
   /orchestrate
   ```
   - Checks for git repository (prompts to init if missing)
   - Shows skill gap warning if applicable
   - Decomposes work into tasks
   - Executes using specialized agents
   - Auto-commits after each task

5. **Terminal 2: Support tasks** (while orchestrator runs):
   ```
   /issue                    # Report bugs as you find them
   /refresh prd              # Queue restart if PRD changes
   /ingest-skill <url>       # Add skills, then /refresh skills
   ```

**Git integration:**
- If `.git` exists, orchestrator enables auto-commits
- If not, you'll be prompted: "Initialize git?"
- Each completed task creates a commit with task details

### Resuming Work

If you start a new conversation on an existing project:
```
"Continue working on the project in /path/to/project"
```

Claude will read the journal and resume from where work left off.

---

## Skill Gap Analysis

After generating a PRD with `/prdgen`, the system automatically analyzes your requirements against available skills to identify coverage gaps.

### What It Does

1. Extracts requirements from your PRD (tech stack, features, domain expertise)
2. Matches each requirement against the skill library
3. Reports coverage and identifies gaps
4. Saves analysis to `.claude/skill_gaps.json`

### Coverage Levels

| Level | Score | Meaning |
|-------|-------|---------|
| **Covered** | High match | Skill library has strong expertise |
| **Partial** | Medium match | Basic support, may need guidance |
| **Gap** | Low/no match | No specialized skill available |

### Gap Severity

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| `critical` | Core feature without coverage | Consider adding skill first |
| `warning` | Secondary feature, partial coverage | Can proceed, note in tasks |

### Example Output

After `/prdgen` completes:

```
SKILL COVERAGE ANALYSIS
───────────────────────────────────────────────────────────

REQUIREMENTS DETECTED:
  • React frontend with charts
  • User authentication (JWT)
  • PostgreSQL database
  • CSV import/export

SKILL COVERAGE:
  ✓ frontend_design         → React frontend
  ✓ data_visualization      → Charts
  ✓ authentication          → User authentication
  ✓ database_designer       → PostgreSQL

GAPS IDENTIFIED:
  ⚠ CSV import/export       → Warning (partial)
                              data_visualization has basic CSV support

COVERAGE: 90% (4/4.5 requirements)

───────────────────────────────────────────────────────────
```

### Orchestrator Integration

When you run `/orchestrate`, it checks for the saved gap analysis:

```
⚠️ Skill Gap Warning
────────────────────────────────────────────
Your PRD has 2 critical requirement(s) without matching skills:
  • Kubernetes deployment
    Recommendation: Use /ingest-skill to import k8s expertise
  • GraphQL API
    Recommendation: Use /ingest-skill to import GraphQL skill
────────────────────────────────────────────
Coverage: 60%
```

### Addressing Gaps

1. **Use `/ingest-skill`** to import skills from URLs or local files
2. **Create a custom skill** in `skills/` directory (see skill template)
3. **Proceed anyway** - agents will use general knowledge (may be slower, less optimal)

Gaps are warnings, not blockers. The orchestrator will attempt all tasks regardless of skill coverage.

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

### Phase 5: Loop Mode (Iteration & Improvement)

For iterative improvement, use **loop mode** instead of running `/orchestrate` multiple times manually:

```
/orchestrate 5                    # Run 5 improvement loops
/orchestrate 3 security           # 3 loops focused on security
/orchestrate 5 UI, performance    # 5 loops on UI and performance
```

#### How Loop Mode Works

Each loop follows this pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LOOP N of M                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  1. RESEARCH    → Research agent analyzes project, identifies 5 fixes  │
│  2. IMPLEMENT   → Implementation agents execute each improvement       │
│  3. VERIFY      → QA agent verifies no regressions                     │
│  4. COMMIT      → Auto-commit: "Loop 1_5 2025-12-12 <summary>"        │
│  5. SNAPSHOT    → Save CHANGES.md, diff.patch to snapshot folder      │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Loop Progress Display

During loop execution, you'll see compact progress updates for each phase:

```
═══ LOOP 1/3 ═══ Focus: security, performance

Phase 1: Research - analyzing project...
  → 5 improvements identified

Phase 2: Implementation - 5 tasks
  [1/5] Starting: Add CSRF protection to forms
  [2/5] Starting: Implement rate limiting
  [3/5] Starting: Add input validation
  [4/5] Starting: Optimize database queries
  [5/5] Starting: Add caching layer
  ✓ [1] Add CSRF protection to forms
  ✓ [2] Implement rate limiting
  ✓ [3] Add input validation
  ✓ [4] Optimize database queries
  ✗ [5] Add caching layer

Phase 3: Verification - running checks...
  → Verification passed

Phase 4: Commit & Snapshot
───────────────────────────────────────
LOOP 1/3 COMPLETE: 4/5 tasks
  1 failed
───────────────────────────────────────
```

**Status icons:**
- `✓` Complete - task finished successfully
- `✗` Failed - task encountered an error

**Why compact output?**

The orchestrator uses minimal output to preserve context for long runs. Detailed task
logs are written to journal files, not displayed inline. This allows 10+ loops without
context overflow.

#### Research Agent

The research agent (Opus model) runs at the start of each loop:
- Analyzes current project state
- Searches web for best practices and industry standards
- Identifies 5 specific improvements
- Writes improvements to issue queue with `source: generated`

#### Focus Areas

Optionally focus improvements on specific areas:

| Focus | What It Targets |
|-------|-----------------|
| `bugs` | Broken functionality, error handling |
| `performance` | Speed, memory, bundle size |
| `security` | Vulnerabilities, auth issues |
| `UI` | Visual design, layout, styling |
| `UX` | User flows, interactions |
| `testing` | Coverage gaps, flaky tests |
| `documentation` | Comments, README, API docs |
| `new features` | Creative research for novel enhancements |

#### Loop Snapshots

Each loop saves a snapshot for review:

```
.claude/loop_snapshots/
├── run-2025-12-12-001/
│   ├── loop-01_05/
│   │   ├── CHANGES.md      # What changed
│   │   ├── REVIEW.md       # Review instructions
│   │   ├── diff.patch      # Git diff
│   │   └── manifest.json   # Metadata
│   ├── loop-02_05/
│   └── ...
├── SUMMARY.md              # Full run summary
└── SUMMARY.html            # Visual dashboard
```

#### Early Exit

Loop mode exits early to save tokens when:
- No improvements found (project in good shape)
- Diminishing returns (2 consecutive loops with <2 improvements)

#### Commit Format

Loop commits follow a standard format for easy navigation:

```
Loop 1_5 2025-12-12 Security hardening and input validation
Loop 2_5 2025-12-12 Performance optimization and caching
Loop 3_5 2025-12-12 UI improvements and accessibility
```

To revert a specific loop: `git revert <commit-sha>`

---

## Agent Monitoring

During orchestration, sub-agents execute tasks in the background. You can monitor their progress without interrupting execution.

### Checking Agent Status

| Command | Description |
|---------|-------------|
| `/progress` | Overview including running agent count |
| `/progress tasks` | Show task list with dependency graph |
| `/progress agents` | List all running and recently completed agents |
| `/progress <agent-id>` | View last output from a specific agent |

### Example: Listing Agents

```
/progress agents

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
Usage: /progress <agent-id> to see last agent output
═══════════════════════════════════════════════════════════
```

### Example: Agent Details

```
/progress agent-abc123

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

- Use `/progress agents` to see "what's happening right now"
- Use `/progress <agent-id>` when an agent seems to be taking long
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
| `/issue reject <id> <reason>` | Mark issue as won't fix |
| `/issues` | View issue queue status |
| `/issues <issue-id>` | View specific issue details |

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
/issue reject ISSUE-20241211-001 "Out of scope for v1"
```

Only pending or accepted issues can be rejected.

---

## Dual Terminal Workflow

Run the orchestrator in one terminal while using another for support tasks.

### Terminal Layout

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ TERMINAL 1: Orchestrator        │  │ TERMINAL 2: Support Tasks       │
│─────────────────────────────────│  │─────────────────────────────────│
│ /orchestrate                    │  │ /issue "bug in login"           │
│   ├─► Task 004 executing...     │  │ /refresh issues                 │
│   ├─► [detects refresh signal]  │  │                                 │
│   ├─► Polling issue queue...    │  │ /ingest-skill <url>             │
│   └─► Created task from issue   │  │ /refresh skills                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

### The /refresh Command

Signal the orchestrator to reload resources or queue lifecycle changes:

| Command | Timing | Action |
|---------|--------|--------|
| `/refresh issues` | Immediate | Poll issue queue now |
| `/refresh skills` | Immediate | Reload skill directory |
| `/refresh prd` | **Queued** | Restart with new PRD after current run completes |
| `/refresh cancel` | Immediate | Cancel a queued PRD restart |

**Important:** `/refresh` requires an argument. Running `/refresh` alone does nothing.

### Why PRD Changes Are Queued

PRD changes mid-run cause architectural conflicts:
- Existing tasks were planned against the old PRD
- New tasks would be planned against the new PRD
- Dependencies between old and new tasks may not align

Instead, `/refresh prd`:
1. Flags the orchestrator to restart after the current run
2. Current run completes normally (all tasks finish)
3. Orchestrator archives the completed run
4. Analyzes differences between old and new PRD
5. Creates tasks only for the changes
6. Begins new run automatically

### Example: Urgent Bug Report

```
Terminal 2:
  /issue "Production login failing for all users"
  [Issue Reporter interviews, sets priority: critical]

  /refresh issues
  "Refresh signal sent: issues"

Terminal 1:
  [Task 005 completes]
  "🔄 Refresh signal: polling issue queue"
  "⚠️  Critical issue detected: Production login failing for all users"
  "Creating urgent task 012"
  [Task 012 becomes next task]
```

### Example: PRD Update

```
Terminal 2:
  [edits PRD.md with new requirements]
  /refresh prd

  "PRD restart queued.
   Current run will complete (3 tasks remaining), then restart."

Terminal 1:
  "📋 PRD restart queued - current run will complete first"
  [Task 006 completes]
  [Task 007 completes]
  [Task 008 completes]
  "🔄 PRD restart was queued - initiating restart sequence..."
  "📋 PRD Changes Detected:
     - added: New user roles feature
     - modified: Authentication flow
     - removed: Legacy login support"
  "✅ Restart complete - 5 tasks created from PRD changes"
```

### What Each Terminal Does

| Terminal 1 (Orchestrator) | Terminal 2 (Support) |
|---------------------------|----------------------|
| `/orchestrate` | `/issue`, `/issue reject` |
| `/progress`, `/progress agents` | `/issues` |
| `/checkpoint` | `/refresh issues\|skills\|prd\|cancel` |
| `/deorchestrate` | `/abort` |
| `/progress tasks`, `/skills` | `/ingest-skill`, `/audit-skills` |

### Emergency Stop: /abort

If you discover a fundamental flaw and want to stop immediately:

```
/abort                    # Shows confirmation prompt
/abort confirm            # Executes abort
```

**What /abort does:**
- Stops any running agents
- Purges all pending tasks
- Archives completed tasks for reference
- Marks current run as aborted

**When to use /abort vs other commands:**

| Scenario | Command |
|----------|---------|
| Fundamental design flaw | `/abort` |
| Want to update PRD for next run | `/refresh prd` |
| Want to pause and resume later | `/deorchestrate` |
| Single task is failing | Let it fail (orchestrator handles it) |

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
   - Review the **skill gap analysis** at the end
   - Address critical gaps with `/ingest-skill` before proceeding
   - Run `/clear` after PRD generation

2. **Review skill coverage**
   - `/prdgen` shows skill coverage automatically
   - `/orchestrate` will also warn about gaps
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

2. **Monitor agent progress** with `/progress`:
   ```
   /progress              # Overview - shows running agent count
   /progress tasks        # Task list with dependency graph
   /progress agents       # List all running and recent agents
   /progress agent-abc123 # See last output from specific agent
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

### "Context low" warnings during loop mode

**Cause**: This warning should NOT appear if the orchestrator is following protocol correctly.
All agents must run with `run_in_background: true` to keep their outputs isolated from the
orchestrator's context.

**Example warning:**
```
● Agent "ISSUE-009 Accessibility WCAG" completed.
  ⎿  Context low · Run /compact to compact & continue
```

**If you see this warning:**

This indicates the orchestrator protocol has a context leak. Common causes:

1. **AgentOutputTool result stored**: The `AgentOutputTool` returns the **full agent
   conversation**, not just status. If the result is assigned to a variable
   (`result = AgentOutputTool(...)`), the entire conversation fills orchestrator context.

2. **Missing background flag**: Agents not spawned with `run_in_background: true`.

**Correct pattern:**
```
# Spawn agent in background
agent_id = Task(..., run_in_background: true)

# Wait for completion - DO NOT store the result
AgentOutputTool(agent_id, block=true)  # No assignment!

# Read outcome from file instead
handoff = Read(".claude/journal/task-{id}.md") -> parse HANDOFF section
```

**How it should work:**
- Agents run in background (`run_in_background: true`)
- `AgentOutputTool` called to wait, but result is **NOT stored**
- Agent writes outcome to task journal file
- Orchestrator reads only the handoff section from file
- Orchestrator context stays lean (~2k tokens per loop)

**Expected context usage:**

| Loops | Context Used | Notes |
|-------|--------------|-------|
| 1-3 | ~25k | Well within limits |
| 4-7 | ~35k | Still comfortable |
| 8-10 | ~45k | No issues |
| 10+ | ~55k+ | Sustainable with background agents |

**If state is lost:**
1. Check `.claude/session_state.md` for loop progress
2. Check `.claude/journal/index.md` for task states
3. Run `/orchestrate` to resume - it detects and continues the run

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

## Command Reference

Detailed documentation for all Claudestrator commands.

### PRD Generation (`/prdgen`)

Standalone agent that interviews you and generates `PRD.md`.

**Usage:**
```
/prdgen                      # Start interactive interview
/prdgen --template cli       # Pre-select template
/prdgen --output ./docs/PRD.md  # Custom output path
```

**Available Templates:**
| Template | Best For |
|----------|----------|
| `web` | SaaS, dashboards, CRUD apps |
| `cli` | Command-line utilities |
| `api` | REST/GraphQL backends |
| `game` | Browser/mobile games |
| `mobile` | iOS/Android applications |
| `library` | Packages, SDKs, libraries |
| `minimal` | Quick projects, prototypes |

**Features:**
- Web access for researching competitors
- Skill gap analysis after generation
- Saves gap analysis to `.claude/skill_gaps.json`

### Skill Ingestion (`/ingest-skill`)

Import external skills from multiple sources.

**Usage:**
```bash
# Single skill from GitHub
/ingest-skill https://github.com/user/repo/blob/main/skills/my-skill.md

# Multiple skills
/ingest-skill ./local-skill.md https://raw.githubusercontent.com/user/repo/main/skill.md

# Directory with helper scripts
/ingest-skill https://github.com/user/repo/tree/main/skills/complex-skill/
```

**Features:**
- Auto-detects metadata (category, keywords, complexity) with user approval
- Security analysis on helper scripts (detects obfuscation, suspicious patterns)
- Parses and merges existing frontmatter
- Double confirmation before overwriting existing skills
- Handles skills with helper scripts (`.js`, `.py`, etc.)
- Prompts before running `npm install` for dependencies

### Skill Maintenance (`/audit-skills`, `/skill-enhance`)

**`/audit-skills`** - Analyzes skill library health:
```
/audit-skills                # Generate health report
```
- Identifies issues (missing fields, outdated references)
- Reports coverage gaps against common task types
- Suggests improvements

**`/skill-enhance [id]`** - Research and update a skill:
```
/skill-enhance frontend_design   # Research and propose updates
```
- Web research for best practices
- Proposes changes with human approval
- Never auto-commits changes

### Issue Reporting (`/issue`, `/issues`)

**`/issue`** - Report or reject issues:
```
/issue                           # Start interactive reporting
/issue <brief description>       # Start with context
/issue reject <id> <reason>      # Mark issue as won't fix
```

**`/issues`** - View issue queue:
```
/issues                  # Full queue summary
/issues pending          # Only pending issues
/issues <issue-id>       # Details of specific issue
```

**Issue Types:** bug, performance, enhancement, ux, security, refactor

**Priority Levels:**
| Priority | Orchestrator Behavior |
|----------|----------------------|
| `critical` | Interrupts queue - becomes next task |
| `high` | Top of pending tasks |
| `medium` | Normal queue order |
| `low` | End of queue |

### Refresh Commands (`/refresh`)

Signal the orchestrator to reload resources.

```
/refresh issues      # Poll issue queue immediately
/refresh skills      # Reload skill directory
/refresh prd         # Queue restart after current run completes
/refresh cancel      # Cancel queued restart
```

**Important:** `/refresh` requires an argument. Running `/refresh` alone shows usage help.

**Important:** `/refresh prd` is queued, not immediate. The orchestrator:
1. Completes all tasks in the current run
2. Archives the completed run
3. Analyzes PRD differences
4. Creates tasks only for changes
5. Starts new run automatically

### Emergency Stop (`/abort`)

Stop orchestration immediately.

```
/abort               # Shows confirmation prompt
/abort confirm       # Executes abort
```

**What `/abort` does:**
- Stops any running agents
- Purges all pending tasks
- Archives completed work for reference
- Marks current run as aborted

**Safeguards:**
- Requires explicit `/abort confirm` to execute
- Shows count of tasks that will be purged
- Archives completed work before purging

### Progress Commands (`/progress`)

```
/progress              # Project overview
/progress tasks        # Show task list with dependency graph
/progress agents       # List running and recent agents
/progress <agent-id>   # Last output from specific agent
/progress metrics      # Performance metrics and token usage
```

The dependency graph shows:
- Task status icons: ✓ done, ◐ active, ○ pending, ✗ blocked
- Dependency arrows showing execution order
- Critical path analysis
- Parallelization opportunities

### Dry-Run Mode (`/orchestrate --dry-run`)

Preview task decomposition without executing:

```
/orchestrate --dry-run
```

Shows:
- Complete task list with types, complexity, and models
- Skill matching per task
- Token estimates (input/output) per task
- Dependency graph visualization
- Total cost estimates by model
- Warnings about skill gaps or complex tasks

### Loop Mode (`/orchestrate N`)

Run multiple improvement loops with research agent:

```
/orchestrate 5                    # 5 loops with research
/orchestrate 3 security           # 3 loops focused on security
/orchestrate 5 UI, new features   # Mix focus with creative research
```

**Key differences from standard `/orchestrate`:**

| Command | Research Agent | Behavior |
|---------|----------------|----------|
| `/orchestrate` | ❌ No | Standard PRD-based execution |
| `/orchestrate 5` | ✅ Yes | Research agent at each loop start |

**Autonomy prompt:** When starting loop mode, you'll be asked to select:
- **Full Autonomy** (recommended) - Auto-approve safe operations
- **Supervised** - Approve agent spawns
- **Manual** - Approve everything

**High iteration warning:** Loops >10 show cost estimate and require confirmation.

### Analytics Commands

| Command | Purpose |
|---------|---------|
| `/progress metrics` | Current session stats (tokens, costs, success rates) |
| `/analytics` | Cross-session trends and learning analysis |
| `/dashboard` | Generate visual HTML dashboard |

**When to use which:**
- Use `/progress metrics` during a run to see current session stats
- Use `/analytics` after runs to see trends across sessions
- Use `/dashboard` to generate a shareable visual report

### Other Commands

| Command | Description |
|---------|-------------|
| `/orchestrate` | Initialize or resume orchestrator (standard mode) |
| `/orchestrate N` | Run N improvement loops with research agent |
| `/checkpoint` | Save current state (continue working) |
| `/skills` | Show loaded skills |
| `/deorchestrate` | Clean exit with full save |

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

*User Guide Version: 1.6*
*Last Updated: December 2025*
*Added: Dry-run mode, performance metrics, dependency visualization*
