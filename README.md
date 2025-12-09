# Claudestrator

A multi-agent orchestration framework for Claude Code that enables complex, multi-step project development through intelligent task decomposition, skill-based agent construction, and persistent state management.

## Overview

Claudestrator transforms Claude Code from a single assistant into a coordinated team of specialized agents. Instead of handling all implementation details directly, it:

- **Decomposes** projects into discrete, trackable tasks
- **Matches** each task to appropriate skills from a library
- **Constructs** specialized agents with relevant expertise
- **Tracks** progress through a persistent journal system
- **Coordinates** verification and iteration cycles

## Key Features

| Feature | Description |
|---------|-------------|
| **Skill-Based Matching** | Tasks matched to skills via domain, keywords, and complexity |
| **Dynamic Model Selection** | Easy→Haiku, Normal→Sonnet, Complex→Opus |
| **Persistent Journal** | Tracks decisions, reasoning, and context across sessions |
| **Agent Factory** | Dynamically constructs agent prompts from skills + context |

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
   - Track progress in a journal

## Directory Structure

```
claudestrator/
├── orchestrator_protocol_v3.md    # Core protocol definition
├── docs/
│   └── user_guide.md              # Comprehensive usage guide
├── skills/
│   ├── skill_manifest.md          # Index of all skills
│   ├── skill_template.md          # Template for new skills
│   ├── agent_model_selection.md   # Model selection criteria
│   ├── implementation/            # Code-writing skills
│   ├── design/                    # Planning/architecture skills
│   ├── quality/                   # QA/review skills
│   └── support/                   # Supporting skills
└── templates/
    ├── journal_index.md           # Project state template
    ├── task_entry.md              # Task file template
    └── agent_prompt.md            # Agent prompt template
```

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
3. Gather context from prior tasks
4. Construct and spawn specialized agent
5. Update journal with results

### 4. Verification
QA agent validates all acceptance criteria. Issues become new tasks for iteration.

## The Journal System

Journals solve context loss between agent invocations:

```
project/.claude/journal/
├── index.md          # Project state, task registry, context map
├── task-001-*.md     # Detailed execution log
├── task-002-*.md     # Reasoning and handoff notes
└── ...
```

Each task file captures:
- What was done and why
- Files modified with locations
- Errors encountered and resolutions
- Notes for subsequent agents

## Creating Custom Skills

1. Copy `skills/skill_template.md`
2. Fill in metadata (domain, keywords, complexity)
3. Define patterns, standards, and examples
4. Register in `skill_manifest.md`

## Model Selection

| Complexity | Model | Max Skills | Use For |
|------------|-------|------------|---------|
| Easy | Haiku | 1 | Constants, searches, simple edits |
| Normal | Sonnet | 2 | Features, fixes, single components |
| Complex | Opus | 3 | Architecture, algorithms, multi-system |

## Documentation

- [User Guide](docs/user_guide.md) - Comprehensive usage documentation
- [Protocol](orchestrator_protocol_v3.md) - Full protocol specification
- [Skill Manifest](skills/skill_manifest.md) - Available skills reference

## Contributing

Contributions welcome! Areas of interest:
- New skill definitions for different domains
- Protocol improvements
- Journal format enhancements
- Integration examples

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with Claude Code*
