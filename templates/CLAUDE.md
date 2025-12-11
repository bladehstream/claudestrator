# Project Instructions

> ⚠️ **DO NOT run `/init`** - it will overwrite this configuration file.

## Claudestrator

Multi-agent orchestration framework for complex, multi-step projects.

### Quick Start

1. **Terminal 2:** Run `/prdgen` to generate a PRD (Product Requirements Document)
2. **Terminal 1:** Run `/orchestrate` to begin orchestration
3. **Terminal 2:** Use `/issue` to report bugs as you find them

### Dual Terminal Workflow

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

### Commands

Run `/claudestrator-help` for full command reference.

**Getting Started:**
- `/prdgen` - Generate PRD via interactive interview
- `/orchestrate` - Start or resume orchestration
- `/orchestrate --dry-run` - Preview tasks and cost estimates

**Monitoring:**
- `/progress` - Show project overview
- `/progress tasks` - Task list with dependency graph
- `/progress metrics` - Token usage, costs, success rates
- `/skills` - Loaded skills by category

**Issue Tracking:**
- `/issue` - Report bug or enhancement
- `/issues` - View issue queue

**Skill Management:**
- `/audit-skills` - Skill library health report
- `/ingest-skill <source>` - Import external skill

### Resources

- **Protocol:** Read `.claudestrator/orchestrator_protocol_v3.md` when orchestrating
- **Skills:** `.claude/skills/`
- **State:** `.claude/` (session_state.md, orchestrator_memory.md, journal/)

### Documentation

https://github.com/bladehstream/claudestrator
