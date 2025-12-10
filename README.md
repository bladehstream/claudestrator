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
| **Knowledge Graph** | Tag-based retrieval of project knowledge and learnings |
| **Computed Context** | Fresh, relevant context computed per-agent (not accumulated) |
| **Hot/Cold State** | Working memory (hot) separate from archival memory (cold) |
| **Structured Handoffs** | YAML schema preserves semantics between agents |
| **Strategy Evolution** | Orchestrator learns from execution feedback |
| **Prompt Caching** | Stable prefix structure for cache optimization |
| **Dynamic Model Selection** | Easy→Haiku, Normal→Sonnet, Complex→Opus |

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

## Session Management

| Command | Action |
|---------|--------|
| `/orchestrate` | Initialize or resume orchestrator mode |
| `/checkpoint` | Save current state (can continue working) |
| `/status` | Show project and task status |
| `/tasks` | Show task list with progress |
| `/skills` | Show loaded skills |
| `/deorchestrate` | Clean exit with full state save |

## Quick Start

1. **Copy to your Claude skills directory:**
   ```bash
   cp -r skills/* ~/.claude/skills/
   ```

2. **Start a project with Claude Code:**
   ```
   "I want to build [your project description]"
   ```

3. **Claude (as orchestrator) will:**
   - Interview you or read your PRD
   - Decompose work into tasks
   - Execute using specialized agents
   - Track progress and learnings
   - Evolve strategies based on feedback

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
├── skills/                        # Default skill directory
│   ├── skill_manifest.md          # Optional reference index
│   ├── skill_template.md          # Template for new skills
│   ├── agent_model_selection.md   # Model selection criteria
│   ├── implementation/            # Code-writing skills
│   ├── design/                    # Planning/architecture skills
│   ├── quality/                   # QA/review skills
│   └── support/                   # Supporting skills
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
├── commands/                      # Slash command definitions
└── docs/
    └── user_guide.md              # Comprehensive usage guide
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

## Available Skills

### Implementation
- `html5_canvas` - HTML5 Canvas games and 2D graphics
- `game_feel` - Polish, "juice", and game effects

### Design
- `game_designer` - Game mechanics, progression, balance
- `api_designer` - REST/GraphQL API design

### Quality
- `qa_agent` - Testing and verification
- `user_persona` - UX review and accessibility
- `security_reviewer` - Security audits

### Support
- `svg_asset_gen` - SVG graphics creation
- `refactoring` - Code restructuring
- `documentation` - Technical writing

## How It Works

### 1. Discovery
Claude checks for a PRD or interviews you about your project requirements.

### 2. Planning
Requirements are decomposed into tasks with:
- Clear objectives
- Acceptance criteria
- Complexity assessment
- Dependencies

### 3. Execution
For each task:
1. Match relevant skills from the library
2. Select model based on complexity
3. **Compute** context (query knowledge graph, filter by relevance)
4. Construct agent prompt (cache-optimized structure)
5. Spawn specialized agent
6. Process structured handoff
7. Update knowledge graph and strategies

### 4. Verification
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
