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

**Run (Standard - PRD-based):**
```
Terminal 2: /prdgen          # Create PRD first
Terminal 2: /clear           # Clear context
Terminal 1: /orchestrate     # Start orchestration
Terminal 2: /issue           # Report bugs while running
```

**Run (Alternative - External Spec Files):**
```
# Place your spec files in projectspec/
#   - spec-final.json        (feature definitions)
#   - test-plan-output.json  (test cases)

Terminal 1: /orchestrate --source external_spec
# Orchestrator prompts for file paths and generates tasks from JSON specs
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

**IMPORTANT**: The `.claude/` and `.orchestrator/` folders have distinct purposes:

| Folder | Purpose | Safe to Delete? |
|--------|---------|-----------------|
| `.claude/` | **Orchestrator code** - commands, prompts, skills | ✅ Yes - reinstall from GitHub |
| `.orchestrator/` | **Runtime state** - queues, reports, history | ❌ No - loses run history |

```
project/
├── PRD.md                              # Your requirements (created by /prdgen)
│
├── .claude/                            # ORCHESTRATOR CODE (reinstallable)
│   ├── commands/                       #   Slash command definitions
│   ├── prompts/                        #   Agent prompt files
│   │   └── implementation/             #   Implementation agent prompts
│   ├── skills/                         #   Skill library (if installed)
│   └── hooks/                          #   Safety hooks (if configured)
│
├── .orchestrator/                      # RUNTIME STATE (preserve this!)
│   ├── task_queue.md                   #   Current tasks
│   ├── issue_queue.md                  #   Issues from research/user
│   ├── session_state.md                #   Current session state
│   ├── complete/                       #   Completion markers (.done, .failed)
│   ├── reports/                        #   Task execution reports (JSON)
│   ├── research/                       #   Research artifacts (screenshots, etc.)
│   ├── history.csv                     #   Cumulative run history
│   ├── analytics.json                  #   Aggregated analytics
│   └── analytics.html                  #   Human-readable dashboard
│
└── .claudestrator/                     # Framework source (git clone)
    ├── commands/                       #   Command implementations (authoritative)
    │   └── orchestrate.md              #   Main orchestration logic
    ├── prompts/                        #   Agent prompt files
    └── orchestrator_runtime.md         #   Reference docs only (deprecated)
```

**To upgrade Claudestrator** without losing state:
```bash
rm -rf .claude           # Remove old code
# Reinstall from GitHub - .orchestrator/ state preserved
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
