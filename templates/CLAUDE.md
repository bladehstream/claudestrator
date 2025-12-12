# 🎭 CLAUDESTRATOR

> **Multi-Agent Orchestration Framework**

This project is powered by Claudestrator. Standard Claude Code `/init` has been replaced with orchestration commands.

## Quick Start

```
/prdgen      →  Create your PRD (Product Requirements Document)
/orchestrate →  Start multi-agent task execution
/issue       →  Report bugs as you find them
```

## Dual Terminal Workflow

For best results, use two terminals:

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ TERMINAL 1: Orchestrator        │  │ TERMINAL 2: Support Tasks       │
│─────────────────────────────────│  │─────────────────────────────────│
│ /orchestrate                    │  │ /prdgen        (before T1)      │
│   ├─► Executing tasks...        │  │ /issue         (report bugs)    │
│   ├─► Auto-polling issues       │  │ /issues        (view queue)     │
│   └─► Auto-committing           │  │ /refresh prd   (queue restart)  │
│                                 │  │ /ingest-skill  (add skills)     │
│ /progress                       │  │ /abort         (emergency stop) │
│ /deorchestrate                  │  │                                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

## Commands Reference

Run `/claudestrator-help` for full documentation.

| Command | Description |
|---------|-------------|
| `/prdgen` | Generate PRD via interactive interview |
| `/orchestrate` | Start or resume orchestration |
| `/orchestrate --dry-run` | Preview tasks and cost estimates |
| `/progress` | Show project status and metrics |
| `/issue` | Report bug or enhancement |
| `/issues` | View issue queue |
| `/skills` | List loaded skills by category |
| `/audit-skills` | Skill library health report |
| `/ingest-skill <url>` | Import external skill |

## Resources

- **Runtime:** `.claudestrator/orchestrator_runtime.md`
- **Commands:** `.claudestrator/commands/orchestrate.md`
- **Skills:** `.claude/skills/`
- **State:** `.claude/` (task_queue.md, session_state.md)
- **Docs:** https://github.com/bladehstream/claudestrator
