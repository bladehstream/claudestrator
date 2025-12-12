# Command Reference

Complete reference for all Claudestrator slash commands.

---

## Pre-Orchestration (Terminal 2)

Run these **before** starting orchestration in Terminal 1:

| Command | Model | Description |
|---------|-------|-------------|
| `/prdgen` | Opus | Generate PRD through interactive interview. Creates `PRD.md` with requirements, acceptance criteria, and skill gap analysis. |
| `/audit-skills` | Sonnet | Generate skill library health report. Identifies outdated, missing, or redundant skills. |
| `/skill-enhance [id]` | Opus | Research and propose updates to a specific skill. Uses web search for latest best practices. |
| `/ingest-skill <source>` | (main) | Import external skills from URL or file path. Validates format and adds to skill directory. |

---

## Orchestration (Terminal 1)

Main orchestration commands:

| Command | Model | Description |
|---------|-------|-------------|
| `/orchestrate` | (main) + dynamic | Start orchestration. Spawns Decomposition Agent → reads PRD → creates task queue → spawns Implementation Agents. |
| `/orchestrate N` | (main) + dynamic | Run N improvement loops. Each loop: Research Agent → Decomposition Agent → Implementation Agents. |
| `/orchestrate N <focus>` | (main) + dynamic | Run N loops focused on specific area: `security`, `performance`, `UI`, `bugs`, `testing`, `documentation`. |
| `/orchestrate --dry-run` | (main) | Preview task decomposition, estimates, and dependency graph without executing. |
| `/progress` | (main) | Show project overview: current loop, tasks completed, active agents. |
| `/progress tasks` | (main) | Show task list with status and dependency information. |
| `/progress agents` | (main) | List running and recently completed agents. |
| `/checkpoint` | (main) | Save current state without exiting. Safe pause point. |
| `/deorchestrate` | (main) | Clean exit with full state save. |

---

## Support Tasks (Terminal 2, while orchestrator runs)

Run these in a separate terminal while orchestration is active:

| Command | Model | Description |
|---------|-------|-------------|
| `/issue` | Sonnet | Report a bug or enhancement. Added to issue queue for next loop. |
| `/issue reject <id> <reason>` | (main) | Mark issue as won't fix with explanation. |
| `/issues` | (main) | View current issue queue with status. |
| `/refresh issues` | (main) | Force poll issue queue immediately. |
| `/refresh skills` | (main) | Reload skill directory after adding new skills. |
| `/refresh prd` | (main) | Queue restart after current run completes. Use when PRD has changed. |
| `/refresh cancel` | (main) | Cancel queued restart. |
| `/abort` | (main) | Emergency stop. Requires confirmation. Saves state before exit. |

---

## Utility Commands

| Command | Model | Description |
|---------|-------|-------------|
| `/skills` | (main) | Show loaded skills by category. |
| `/claudestrator-help` | (main) | Show Claudestrator help and command summary. |

---

## Model Selection

Commands that spawn agents use dynamic model selection:

| Complexity | Model | Use For |
|------------|-------|---------|
| easy | Haiku | Simple fixes, config changes, documentation |
| normal | Sonnet | Features, refactoring, single components |
| complex | Opus | Architecture, security, multi-system changes |

**Note:** "(main)" means the command runs in your current Claude Code session. Named models (Sonnet, Opus) spawn dedicated sub-agents.

---

## Agent Types

| Agent | Spawned By | Reads | Writes |
|-------|------------|-------|--------|
| Decomposition | `/orchestrate` | PRD.md or issue_queue.md | task_queue.md |
| Research | `/orchestrate N` | Codebase, web | issue_queue.md |
| Implementation | Orchestrator | Task from queue | Source code |

---

*See [User Guide](user_guide.md) for detailed examples and workflows.*
