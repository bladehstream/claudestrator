# Claudestrator

A multi-agent orchestration framework for Claude Code that enables complex, multi-step project development through intelligent task decomposition, skill-based agent construction, and persistent state management.

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

Claudestrator commands are split into two phases to optimize context window usage.

### Phase 1: Pre-Orchestration Commands

Run these commands **before** starting orchestration. They handle project setup and skill management. After completing these, run `/clear` to start orchestration with a clean context.

| Command | Model | Action |
|---------|-------|--------|
| `/prdgen` | Sonnet | Generate PRD through interactive interview |
| `/audit-skills` | Sonnet | Generate skill library health report |
| `/skill-enhance [id]` | Opus | Research and propose updates to a skill |
| `/ingest-skill <source>` | (main) | Import external skills from URLs or local paths |

> **Model transparency:** Commands spawn agents using the specified model. "(main)" means the command runs in your current context without spawning a sub-agent.

**Recommended workflow:**
```
/prdgen                    # Generate project requirements
/clear                     # Clear context window
/audit-skills              # Verify skill library health
/ingest-skill <url>        # Import any needed skills
/clear                     # Clear context before orchestration
/orchestrate               # Start with clean context
```

> **Why clear between phases?** PRD generation, skill auditing, and skill ingestion consume context with their interview/analysis history. Clearing before `/orchestrate` ensures maximum context capacity for actual project work.

### Phase 2: Orchestration Commands

Run these commands **during** active orchestration to manage the session.

| Command | Model | Action |
|---------|-------|--------|
| `/orchestrate` | (main) + dynamic | Initialize or resume orchestrator mode |
| `/checkpoint` | (main) | Save current state (can continue working) |
| `/status` | (main) | Show project and task status |
| `/tasks` | (main) | Show task list with progress |
| `/skills` | (main) | Show loaded skills |
| `/deorchestrate` | (main) | Clean exit with full state save |

> **Dynamic model selection:** `/orchestrate` runs in your main context but spawns sub-agents with models selected by task complexity: Easy→Haiku, Normal→Sonnet, Complex→Opus.

### Command Details

#### PRD Generation (`/prdgen`)

Standalone agent that interviews you and generates `PRD.md`. Supports 7 project templates:
- Web application, CLI tool, API service, Game, Mobile app, Library, Minimal

Has web access for researching competitors and validating requirements.

#### Skill Ingestion (`/ingest-skill`)

Import external skills from multiple sources:

```bash
# Single skill from GitHub
/ingest-skill https://github.com/user/repo/blob/main/skills/my-skill.md

# Multiple skills
/ingest-skill ./local-skill.md https://raw.githubusercontent.com/user/repo/main/skill.md

# Directory with helper scripts
/ingest-skill https://github.com/user/repo/tree/main/skills/complex-skill/
```

Features:
- Auto-detects metadata (category, keywords, complexity) with user approval
- Security analysis on helper scripts (detects obfuscation, suspicious patterns)
- Parses and merges existing frontmatter
- Double confirmation before overwriting existing skills
- Handles skills with helper scripts (`.js`, `.py`, etc.)
- Prompts before running `npm install` for dependencies

#### Skill Maintenance (`/audit-skills`, `/skill-enhance`)

- `/audit-skills` - Analyzes skill library health, identifies issues, suggests improvements
- `/skill-enhance [id]` - Researches web for updates, proposes changes with human approval

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

1. **Start Claude Code** in your project directory

2. **Generate a PRD** (required):
   ```
   /prdgen
   ```
   Interactive interview that creates `PRD.md`. Uses clickable options for structured choices.

3. **Clear context** after PRD generation:
   ```
   /clear
   ```

4. **Audit and enhance skills** (recommended):
   ```
   /audit-skills              # Check for issues
   /ingest-skill <url>        # Import any needed skills
   ```

5. **Clear context** before orchestration:
   ```
   /clear
   ```

6. **Start orchestration**:
   ```
   /orchestrate
   ```

7. **Claude (as orchestrator) will:**
   - Check for git repository (prompt to initialize if missing)
   - Load your PRD (stops if not found, prompts for `/prdgen`)
   - Decompose work into tasks
   - Execute using specialized agents
   - Auto-commit after each task completion
   - Track progress in `.claude/journal/`
   - Learn and adapt from feedback

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

## Available Skills (36 total)

### Implementation
| Skill | Description |
|-------|-------------|
| `html5_canvas` | HTML5 Canvas games and 2D graphics |
| `game_feel` | Polish, "juice", and game effects |
| `data_visualization` | Charts, graphs, D3.js, Chart.js, dashboards |
| `algorithmic_art` | Generative art and creative coding |
| `mcp_builder` | Model Context Protocol server development |
| `slack_gif_creator` | Slack-compatible GIF generation |
| `web_artifacts_builder` | Interactive web artifact creation |

### Design
| Skill | Description |
|-------|-------------|
| `game_designer` | Game mechanics, progression, balance |
| `api_designer` | REST/GraphQL API design |
| `database_designer` | Schema design, indexing, migrations |
| `frontend_design` | UI/UX, CSS, responsive design |
| `canvas_design` | HTML5 Canvas design patterns |
| `theme_factory` | Theme and styling system generation |

### Quality
| Skill | Description |
|-------|-------------|
| `qa_agent` | Testing and verification |
| `user_persona_reviewer` | UX review and accessibility |
| `security_reviewer` | Post-implementation security audits |
| `webapp_testing` | Playwright, E2E testing, browser automation |

### Support
| Skill | Description |
|-------|-------------|
| `svg_asset_generator` | SVG graphics creation |
| `refactoring` | Code restructuring |
| `documentation` | Technical writing |
| `prd_generator` | Interactive requirements elicitation |
| `brand_guidelines` | Brand identity documentation |
| `doc_coauthoring` | Collaborative document writing |
| `docx` | Microsoft Word document generation |
| `internal_comms` | Internal communication drafting |
| `pdf` | PDF document handling |
| `pptx` | PowerPoint presentation generation |
| `xlsx` | Excel spreadsheet generation |

### Maintenance
| Skill | Description |
|-------|-------------|
| `skill_auditor` | Skill library health auditing |
| `skill_enhancer` | Web research and skill updates |
| `skill_creator` | Creating new Claudestrator skills |

### Security
| Skill | Description |
|-------|-------------|
| `authentication` | OAuth2, JWT, sessions, password security |
| `software_security` | Secure coding, OWASP, injection prevention |

### Domain
| Skill | Description |
|-------|-------------|
| `financial_app` | Personal finance, budgeting, transactions |

### Orchestrator
| Skill | Description |
|-------|-------------|
| `agent_construction` | Model selection, skill composition, context budgeting (self-use) |

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
