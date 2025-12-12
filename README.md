# Claudestrator

A multi-agent orchestration framework for Claude Code that enables complex, multi-step project development through intelligent task decomposition, skill-based agent construction, and persistent state management.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Orchestrator Role](#orchestrator-role)
- [Commands](#commands)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Available Skills](#available-skills)
- [How It Works](#how-it-works)
- [Model Selection](#model-selection)
- [Documentation](#documentation)
- [v2 Improvements](#new-in-v2-research-based-improvements)
- [Contributing](#contributing)
- [License](#license)

## Overview

Claudestrator transforms Claude Code from a single assistant into a coordinated team of specialized agents. Instead of handling all implementation details directly, it:

- **Decomposes** projects into discrete, trackable tasks
- **Matches** each task to appropriate skills from a library
- **Constructs** specialized agents with relevant expertise
- **Tracks** progress through a persistent journal system
- **Learns** from execution feedback to improve strategies
- **Coordinates** verification and iteration cycles

## Key Features

| Feature | Description |
|---------|-------------|
| **Strict Role Separation** | Orchestrator manages; agents implement. Never mixed. |
| **Dynamic Skill Discovery** | Skills auto-loaded from directory - just drop in new .md files |
| **Category Deduplication** | One skill per category - no redundant expertise |
| **Knowledge Graph** | Tag-based retrieval of project knowledge and learnings |
| **Computed Context** | Fresh, relevant context computed per-agent (not accumulated) |
| **Hot/Cold State** | Working memory (hot) separate from archival memory (cold) |
| **Structured Handoffs** | YAML schema preserves semantics between agents |
| **Strategy Evolution** | Orchestrator learns from execution feedback |
| **Prompt Caching** | Stable prefix structure for cache optimization |
| **Dynamic Model Selection** | Easy→Haiku, Normal→Sonnet, Complex→Opus |
| **Git Integration** | Auto-commits after each task; prompts to init if missing |
| **Iteration Support** | Iterate on feedback, extend with new features, or archive and restart |
| **PRD Versioning** | Automatic PRD history for audit trail across iterations |
| **Autonomy Levels** | Supervised, Trust Agents, or Full Autonomy with safety guardrails |
| **Async Issue Reporting** | Report issues in separate session; orchestrator polls and creates tasks |
| **Skill Gap Analysis** | Analyze PRD requirements against available skills; warn before orchestration |
| **Dry-Run Mode** | Preview task decomposition, estimates, and dependency graph before executing |
| **Performance Metrics** | Track token usage, costs, success rates by model/skill; view with `/progress metrics` |
| **Dependency Visualization** | ASCII dependency graph in `/progress tasks` showing critical path and parallelization |
| **Learning Analytics** | Track learning over time with `/analytics`; measures success trends, skill effectiveness, error patterns |

## Architecture

### Memory System (v2)

```
project/.claude/
├── session_state.md          # HOT: Working memory, read/write constantly
├── orchestrator_memory.md    # COLD: Long-term memory, append-only
├── knowledge_graph.json      # Tag-based index for retrieval
├── strategies.md             # Evolved strategies from feedback
├── memories/                 # Episodic memory entries
│   └── YYYY-MM-DD-topic.md
├── journal/
│   ├── index.md              # Task registry
│   └── task-*.md             # Task execution logs
├── analytics/                # Learning analytics data
│   ├── sessions/             # Archived session metrics
│   ├── trends.json           # Cross-session trends
│   ├── skill_rankings.json   # Skill effectiveness
│   └── error_patterns.json   # Error analysis
└── config.md                 # User preferences
```

### Key Architectural Principles

| Principle | Implementation |
|-----------|----------------|
| **Context as Compiled View** | Context computed fresh per-call, not accumulated |
| **Tiered Memory** | Hot (session) + Cold (archival) + Knowledge Graph |
| **Retrieval Beats Pinning** | Query knowledge graph by tags, don't load everything |
| **Schema-Driven Handoffs** | Structured YAML preserves meaning across agents |
| **Offload Heavy State** | Agents write to files, orchestrator reads summaries |
| **Evolving Strategies** | Learn from execution feedback, not static prompts |

## Orchestrator Role

> **The orchestrator is a PROJECT MANAGER, not an IMPLEMENTER.**

| Orchestrator DOES | Orchestrator DOES NOT |
|-------------------|----------------------|
| Plan & decompose work | Write code |
| Track progress | Edit project files |
| Match skills to tasks | Run build/test commands |
| Spawn agents | Create assets |
| Review results | Implement features |
| Coordinate iteration | Fix bugs directly |

All implementation work is delegated to agents via the Task tool. See [Orchestrator Constraints](orchestrator_constraints.md) for detailed rules.

## Commands

Claudestrator uses a **dual terminal workflow** for maximum efficiency:

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

### Pre-Orchestration (Terminal 2)

Run these **before** starting orchestration in Terminal 1:

| Command | Model | Action |
|---------|-------|--------|
| `/prdgen` | Sonnet | Generate PRD with skill gap analysis |
| `/audit-skills` | Sonnet | Generate skill library health report |
| `/skill-enhance [id]` | Opus | Research and propose updates to a skill |
| `/ingest-skill <source>` | (main) | Import external skills |

### Orchestration (Terminal 1)

| Command | Model | Action |
|---------|-------|--------|
| `/orchestrate` | (main) + dynamic | Initialize or resume orchestrator |
| `/orchestrate --dry-run` | (main) | Preview tasks, estimates, and dependencies |
| `/progress` | (main) | Show project overview |
| `/progress tasks` | (main) | Show task list with dependency graph |
| `/progress agents` | (main) | List running and recent agents |
| `/progress metrics` | (main) | Show performance metrics and token usage |
| `/progress <agent-id>` | (main) | Show agent's last output |
| `/analytics` | (main) | Full learning analytics report |
| `/analytics trends` | (main) | Success rate trends over time |
| `/analytics skills` | (main) | Skill effectiveness rankings |
| `/analytics errors` | (main) | Error pattern analysis |
| `/skills` | (main) | Show loaded skills |
| `/checkpoint` | (main) | Save state (continue working) |
| `/deorchestrate` | (main) | Clean exit with full save |

### Support Tasks (Terminal 2, while orchestrator runs)

| Command | Model | Action |
|---------|-------|--------|
| `/issue` | Sonnet | Report bug/enhancement |
| `/issue reject <id> <reason>` | (main) | Mark issue as won't fix |
| `/issues` | (main) | View issue queue |
| `/refresh issues` | (main) | Poll issue queue now |
| `/refresh skills` | (main) | Reload skill directory |
| `/refresh prd` | (main) | Queue restart after run completes |
| `/refresh cancel` | (main) | Cancel queued restart |
| `/abort` | (main) | Emergency stop (requires confirm) |

> **Model notes:** "(main)" runs in your current context. Sonnet/Opus spawn dedicated agents. `/orchestrate` spawns sub-agents dynamically: Easy→Haiku, Normal→Sonnet, Complex→Opus.

See [User Guide: Command Reference](docs/user_guide.md#command-reference) for detailed examples and options.

## Quick Start

### One-Line Install (Recommended)

**Project-local installation** (default, current directory):
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash
```

**Global installation** (available in all projects):
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash -s -- --global
```

The installer will:
- **Preview all changes with diffs** before making any modifications
- Clone the repository
- Set up slash commands (symlinks)
- Copy skills (new only, never overwrites)
- Configure CLAUDE.md
- Install settings.json with `/init` protection hook
- **Never overwrite existing files** (shows diffs for conflicts)
- Create backups before modifying CLAUDE.md

> **⚠️ Important:** After installation, do NOT run `/init` - it will overwrite your Claudestrator configuration. The installer adds a SessionStart hook that warns you about this.

**Dry run** (preview changes without installing):
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash -s -- --dry-run
```

To inspect the script before running:
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh -o install.sh
less install.sh
bash install.sh
```

To uninstall:
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash -s -- --uninstall
```

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

#### Option A: Project-Local Installation (Default)

```bash
# 1. Clone into your project
cd /path/to/your/project
git clone https://github.com/bladehstream/claudestrator.git .claudestrator

# 2. Set up .claude directory structure
mkdir -p .claude/commands .claude/skills .claude/journal

# 3. Install slash commands
for cmd in .claudestrator/commands/*.md; do
  ln -sf "../.claudestrator/commands/$(basename $cmd)" .claude/commands/
done

# 4. Install skills (copy to allow customization)
cp -r .claudestrator/skills/* .claude/skills/

# 5. Create project CLAUDE.md
cat > .claude/CLAUDE.md << 'EOF'
## Claudestrator

When I say "/orchestrate", read and follow the protocol at:
.claudestrator/orchestrator_protocol_v3.md

Skill directory: .claude/skills/
PRD templates: .claudestrator/prd_generator/templates/
State files: .claude/ (session_state.md, orchestrator_memory.md, etc.)
EOF
```

#### Option B: Global Installation (All Projects)

```bash
# 1. Clone the repository
git clone https://github.com/bladehstream/claudestrator.git ~/.claude/claudestrator

# 2. Install slash commands (symlink to personal commands directory)
mkdir -p ~/.claude/commands
for cmd in ~/.claude/claudestrator/commands/*.md; do
  ln -sf "$cmd" ~/.claude/commands/
done

# 3. Install skills
mkdir -p ~/.claude/skills
cp -r ~/.claude/claudestrator/skills/* ~/.claude/skills/

# 4. Add orchestrator to your CLAUDE.md (or create one)
echo '
## Claudestrator

When I say "/orchestrate", read and follow the protocol at:
~/.claude/claudestrator/orchestrator_protocol_v3.md

Skill directory: ~/.claude/skills/
PRD templates: ~/.claude/claudestrator/prd_generator/templates/
' >> ~/.claude/CLAUDE.md
```

</details>

### After Installation

**Dual Terminal Workflow:**

```
TERMINAL 2 (Setup)              TERMINAL 1 (Orchestration)
──────────────────              ─────────────────────────
1. /prdgen                      (wait for setup)
   → Review skill gap analysis
   → Address critical gaps

2. /audit-skills (optional)
   /ingest-skill <url>

3. /clear                       4. /orchestrate
                                   → Tasks execute
                                   → Auto-commits

(Support while running)
/issue                          /progress agents
/refresh prd                    /deorchestrate
```

**Step-by-step:**

1. **Terminal 2: Generate a PRD** (required):
   ```
   /prdgen
   ```
   - Interactive interview creates `PRD.md`
   - Review the skill gap analysis at the end
   - Address critical gaps with `/ingest-skill` if needed

2. **Terminal 2: Clear context**:
   ```
   /clear
   ```

3. **Terminal 1: Start orchestration**:
   ```
   /orchestrate
   ```
   - Checks for git repository (prompts to init if missing)
   - Shows skill gap warning if applicable
   - Decomposes work into tasks
   - Executes using specialized agents
   - Auto-commits after each task

4. **Terminal 2: Support tasks** (while orchestrator runs):
   ```
   /issue                    # Report bugs as you find them
   /refresh prd              # Queue restart if PRD changes
   /ingest-skill <url>       # Add skills, then /refresh skills
   ```

### Verifying Installation

After setup, run `/help` in Claude Code. You should see:
- `/orchestrate` - Initialize or resume orchestrator mode
- `/prdgen` - Generate PRD through interview
- `/audit-skills` - Skill library health report
- Plus other Claudestrator commands

## Directory Structure

```
claudestrator/
├── orchestrator_protocol_v3.md    # Core protocol definition
├── orchestrator_constraints.md    # Role boundaries
├── skill_loader.md                # Dynamic skill discovery
│
├── # Memory & State (v2)
├── state_management.md            # Hot/cold state separation
├── knowledge_graph.md             # Tag-based retrieval system
├── computed_context.md            # Dynamic context computation
├── handoff_schema.md              # Structured handoff format
├── strategy_evolution.md          # Adaptive learning system
├── prompt_caching.md              # Cache-optimized prompt structure
│
├── prd_generator/                 # Standalone PRD generation system
│   ├── prd_protocol.md            # Interview methodology
│   ├── prd_constraints.md         # Agent boundaries
│   └── templates/                 # PRD templates by project type
│       ├── web_application.md
│       ├── cli_tool.md
│       ├── api_service.md
│       ├── game.md
│       ├── mobile_app.md
│       ├── library.md
│       └── minimal.md
│
├── skills/                        # Default skill directory
│   ├── skill_manifest.md          # Optional reference index
│   ├── skill_template.md          # Template for new skills
│   ├── implementation/            # Code-writing skills
│   ├── design/                    # Planning/architecture skills
│   ├── quality/                   # QA/review skills
│   ├── support/                   # Supporting skills
│   ├── maintenance/               # Skill maintenance skills
│   ├── security/                  # Security implementation skills
│   ├── domain/                    # Domain-specific expertise
│   └── orchestrator/              # Orchestrator self-use skills
│
├── docs/
│   └── user_guide.md              # Comprehensive usage guide
│
├── templates/
│   ├── session_state.md           # Hot state template
│   ├── orchestrator_memory.md     # Cold state template
│   ├── knowledge_graph.json       # Knowledge graph template
│   ├── strategies.md              # Strategy file template
│   ├── memory_entry.md            # Episodic memory template
│   ├── journal_index.md           # Project state template
│   ├── task_entry.md              # Task file template (with YAML handoff)
│   └── agent_prompt.md            # Cache-optimized prompt template
│
└── commands/                      # Slash command definitions
```

## Available Skills

**36 skills** across 8 categories: Implementation, Design, Quality, Support, Maintenance, Security, Domain, and Orchestrator.

Browse skills by category: [`skills/`](skills/)

| Category | Skills | Examples |
|----------|--------|----------|
| Implementation | 7 | `html5_canvas`, `data_visualization`, `mcp_builder` |
| Design | 6 | `api_designer`, `database_designer`, `frontend_design` |
| Quality | 4 | `qa_agent`, `security_reviewer`, `webapp_testing` |
| Support | 11 | `documentation`, `prd_generator`, `xlsx`, `pdf` |
| Maintenance | 3 | `skill_auditor`, `skill_enhancer`, `skill_creator` |
| Security | 2 | `authentication`, `software_security` |
| Domain | 1 | `financial_app` |
| Orchestrator | 1 | `agent_construction` |

See [User Guide: Available Skills](docs/user_guide.md#available-skills) for full descriptions.

## How It Works

### 1. Initialization
- Check for git repository; prompt to initialize if missing
- Load skills from directory
- Enable auto-commits if git is available

### 2. Discovery
Claude loads your PRD. If no PRD exists, it prompts you to run `/prdgen` first to keep orchestration context clean.

### 3. Planning
Requirements are decomposed into tasks with:
- Clear objectives
- Acceptance criteria
- Complexity assessment
- Dependencies

### 4. Execution
For each task:
1. Match relevant skills from the library (one per category)
2. Select model based on complexity
3. **Compute** context (query knowledge graph, filter by relevance)
4. Construct agent prompt (cache-optimized structure)
5. Spawn specialized agent
6. Process structured handoff
7. Update knowledge graph and strategies
8. **Auto-commit** changes (if git enabled)

### 5. Verification
QA agent validates all acceptance criteria. Issues become new tasks for iteration.

### 6. Iteration & Extension (Post-Completion)

When a run completes, `/orchestrate` offers three options:

| Option | Use Case | What Happens |
|--------|----------|--------------|
| **Iterate** | Improve existing features | Gather feedback → create improvement tasks → execute |
| **Extend** | Add new features | Add requirements → decompose → execute |
| **Archive** | Start fresh | Archive current run → begin new project |

**Iteration workflow:**
```
1. Review run summary (files, features, decisions)
2. Select improvement categories (performance, UX, bugs, etc.)
3. Describe specific issues
4. New tasks created with "Improves: task-XXX" links
5. PRD updated with iteration notes
6. Execute iteration tasks
```

**Extension workflow:**
```
1. View current project state
2. Choose: /prdgen for large features OR inline for small additions
3. PRD versioned and updated
4. New tasks created with integration analysis
5. Execute extension tasks
```

**PRD versioning:** Each iteration/extension archives the current PRD to `PRD-history/` before updating.

## Model Selection

| Complexity | Model | Max Skills | Max Context Items | Use For |
|------------|-------|------------|-------------------|---------|
| Easy | Haiku | 3 | 5 code refs | Constants, searches, simple edits |
| Normal | Sonnet | 7 | 10 code refs | Features, fixes, single components |
| Complex | Opus | 15 | 20 code refs | Architecture, algorithms, multi-system |

## Documentation

### Core
- [Protocol](orchestrator_protocol_v3.md) - Full protocol specification
- [Orchestrator Constraints](orchestrator_constraints.md) - Role boundaries and rules
- [Initialization Flow](initialization_flow.md) - First-run interaction scripts

### Memory & State (v2)
- [State Management](state_management.md) - Hot/cold state separation
- [Knowledge Graph](knowledge_graph.md) - Tag-based retrieval system
- [Computed Context](computed_context.md) - Dynamic context computation
- [Handoff Schema](handoff_schema.md) - Structured handoff format
- [Strategy Evolution](strategy_evolution.md) - Adaptive learning system
- [Prompt Caching](prompt_caching.md) - Cache-optimized prompt structure

### Skills & Commands
- [Skill Loader](skill_loader.md) - Dynamic skill discovery specification
- [Skill Reference](skills/skill_manifest.md) - Bundled skills reference
- [Slash Commands](commands/) - Session management commands

### Guides
- [User Guide](docs/user_guide.md) - Comprehensive usage documentation

## New in v2: Research-Based Improvements

### Knowledge Graph

Tag-based retrieval of project knowledge. Query by keywords instead of loading everything:

```json
{
  "nodes": [
    {"id": "task-001", "type": "task", "tags": ["auth", "jwt"], "summary": "..."},
    {"id": "gotcha-001", "type": "gotcha", "tags": ["api", "rate-limit"], "summary": "..."}
  ],
  "tag_index": {"auth": ["task-001"], "api": ["gotcha-001"]}
}
```

See [Knowledge Graph](knowledge_graph.md) for full specification.

### Hot/Cold State Separation

- **Hot (session_state.md)**: Working memory, scratchpad, current task focus. Read/write constantly.
- **Cold (orchestrator_memory.md)**: Project understanding, decisions, patterns. Read at start, append-only.

See [State Management](state_management.md) for lifecycle details.

### Structured Handoffs

YAML schema replaces freeform handoff notes:

```yaml
outcome: completed
patterns_discovered:
  - pattern: "Use AuthContext for user state"
    applies_to: [auth, react-context]
gotchas:
  - issue: "API rate limit is 100/min"
    severity: high
```

See [Handoff Schema](handoff_schema.md) for full specification.

### Computed Context

Context is computed fresh per-agent call:
1. Extract task keywords
2. Query knowledge graph by tags
3. Filter context map by relevance
4. Apply complexity-based limits

See [Computed Context](computed_context.md) for algorithm details.

### Strategy Evolution

Orchestrator learns from execution feedback:

```markdown
### Pairing Rules
| When Using | Also Include | Reason | Learned From |
|------------|--------------|--------|--------------|
| html5_canvas | security_reviewer | Missed XSS vulnerability | task-015 |
```

See [Strategy Evolution](strategy_evolution.md) for feedback processing.

## Contributing

Contributions welcome! Areas of interest:
- New skill definitions for different domains
- Protocol improvements
- Memory system enhancements
- Integration examples

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with Claude Code*
*Memory Architecture v2 based on research from Anthropic, Google Cloud ADK, and A-MEM*
