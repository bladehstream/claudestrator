# /init - Claudestrator Initialization

This project uses **Claudestrator**, a multi-agent orchestration framework.

## You're Already Set Up!

Claudestrator has pre-configured this project. The standard `/init` workflow is replaced with our orchestration system.

## Quick Start

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Create your PRD (Product Requirements Document)           │
│          Run: /prdgen                                               │
│                                                                     │
│  STEP 2: Start orchestration                                        │
│          Run: /orchestrate                                          │
│                                                                     │
│  STEP 3: Report issues as you find them                            │
│          Run: /issue                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/prdgen` | Generate PRD via interactive interview |
| `/orchestrate` | Start multi-agent task execution |
| `/orchestrate --dry-run` | Preview tasks and cost estimates |
| `/progress` | Show project status and metrics |
| `/issue` | Report a bug or enhancement |
| `/claudestrator-help` | Full command reference |

## Dual Terminal Workflow

For best results, use two terminals:

**Terminal 1 (Orchestrator)**
- `/orchestrate` - Runs the main orchestration loop
- `/progress` - Check status

**Terminal 2 (Support)**
- `/prdgen` - Create PRD before starting
- `/issue` - Report bugs during development
- `/ingest-skill` - Add new skills

## Next Step

Run `/prdgen` to create your Product Requirements Document.
