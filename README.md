# Claudestrator

Multi-agent orchestration framework for Claude Code. Transforms complex projects into coordinated agent pipelines.

```
PRD.md ──▶ DECOMPOSE ──▶ task_queue.md ──▶ IMPLEMENT ──▶ Code
```

---

## Dual Terminal Workflow

```
┌─────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
│ TERMINAL 1: Orchestrator                │  │ TERMINAL 2: Support                     │
│─────────────────────────────────────────│  │─────────────────────────────────────────│
│                                         │  │ SETUP (before T1):                      │
│ /orchestrate         Start/resume       │  │   /prdgen            Generate PRD       │
│ /orchestrate N       N improvement loops│  │   /audit-skills      Skill health       │
│ /orchestrate N security  Focused loops  │  │   /ingest-skill <url> Add skills        │
│ /orchestrate --dry-run   Preview only   │  │                                         │
│                                         │  │ WHILE RUNNING:                          │
│ /progress            Project overview   │  │   /issue             Report bug         │
│ /progress tasks      Task list          │  │   /issues            View queue         │
│ /progress agents     Agent status       │  │   /refresh prd       Queue restart      │
│                                         │  │   /refresh skills    Reload skills      │
│ /checkpoint          Save state         │  │   /abort             Emergency stop     │
│ /deorchestrate       Clean exit         │  │                                         │
│                                         │  │ UTILITY:                                │
│                                         │  │   /skills            List skills        │
│                                         │  │   /claudestrator-help                   │
└─────────────────────────────────────────┘  └─────────────────────────────────────────┘
```

See [Command Reference](docs/command_reference.md) for detailed descriptions.

---

## Quick Start

**Install:**
```bash
curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash
```

**Run:**
```
Terminal 2: /prdgen          # Create PRD first
Terminal 2: /clear           # Clear context
Terminal 1: /orchestrate     # Start orchestration
Terminal 2: /issue           # Report bugs while running
```

See [User Guide](docs/user_guide.md) for detailed setup and usage.

---

## Architecture (MVP)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR                                   │
│                         (reads task_queue.md ONLY)                          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│ DECOMPOSITION │        │   RESEARCH    │        │IMPLEMENTATION │
│    AGENT      │        │    AGENT      │        │   AGENTS      │
│               │        │               │        │               │
│ Reads:        │        │ Reads:        │        │ Reads:        │
│  PRD.md       │        │  Codebase     │        │  Task         │
│  issue_queue  │        │  Web/Docs     │        │               │
│               │        │               │        │ Writes:       │
│ Writes:       │        │ Writes:       │        │  Code         │
│  task_queue   │        │  issue_queue  │        │  .done marker │
└───────────────┘        └───────────────┘        └───────────────┘
```

**Key principle:** Orchestrator never reads PRD or issue_queue directly. Heavy documents processed by agents in isolated contexts.

See [Architecture Guide](docs/architecture.md) for full details.

---

## File Structure

```
project/
├── PRD.md                          # Your requirements (created by /prdgen)
├── .claude/
│   ├── task_queue.md               # Tasks for orchestrator
│   ├── issue_queue.md              # Issues from research/user
│   ├── session_state.md            # Orchestration state
│   └── agent_complete/*.done       # Completion markers
└── .claudestrator/                 # Framework (git clone)
    ├── orchestrator_runtime.md     # Runtime protocol
    ├── commands/                   # Slash commands
    └── skills/                     # Skill library
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Command Reference](docs/command_reference.md) | All slash commands with options |
| [User Guide](docs/user_guide.md) | Detailed setup, workflows, troubleshooting |
| [Architecture Guide](docs/architecture.md) | Agent pipeline, context management |
| [Skill Library](skills/) | Available skills by category |

---

## Model Selection

| Complexity | Model | Use For |
|------------|-------|---------|
| easy | Haiku | Simple fixes, docs, config |
| normal | Sonnet | Features, refactoring |
| complex | Opus | Architecture, security |

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with Claude Code*
