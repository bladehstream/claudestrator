# /claudestrator-help - Show Claudestrator Command Reference

Display comprehensive help for all Claudestrator commands.

## Usage

```
/claudestrator-help              Show all commands with descriptions
/claudestrator-help <command>    Show detailed help for a specific command
```

---

## When Called

Display the following command reference. If a specific command is requested via `$ARGUMENTS`, show only that command's detailed section.

---

## Command Reference Output

```
═══════════════════════════════════════════════════════════
CLAUDESTRATOR COMMAND REFERENCE
═══════════════════════════════════════════════════════════

⚠️  Do NOT run /init - it overwrites Claudestrator configuration

───────────────────────────────────────────────────────────
WORKFLOW: Use two terminals
───────────────────────────────────────────────────────────

  TERMINAL 1 (Orchestrator)     TERMINAL 2 (Support)
  ─────────────────────────     ────────────────────
  /orchestrate                  /prdgen (before T1)
  /status                       /issue
  /tasks                        /issues
  /skills                       /ingest-skill
  /checkpoint                   /refresh
  /deorchestrate                /abort

───────────────────────────────────────────────────────────
GETTING STARTED
───────────────────────────────────────────────────────────

  /prdgen                 Generate PRD via interactive interview
                          Creates PRD.md with requirements
                          Shows skill gap analysis at end
                          Run in Terminal 2 BEFORE /orchestrate

  /orchestrate            Start or resume orchestration
                          Decomposes PRD into tasks
                          Spawns agents to implement
                          Auto-commits after each task

  /orchestrate --dry-run  Preview without executing
                          Shows task list and dependencies
                          Estimates tokens and costs
                          Identifies skill gaps

───────────────────────────────────────────────────────────
MONITORING (Terminal 1)
───────────────────────────────────────────────────────────

  /status                 Show project overview
                          Phase, progress, current task

  /status agents          List running and recent agents
                          Shows agent IDs for inspection

  /status <agent-id>      Show specific agent's last output
                          Useful for debugging stuck agents

  /status metrics         Show performance metrics
                          Token usage, costs, success rates
                          Breakdown by model and skill

  /tasks                  Show task list with status
                          Dependency graph visualization
                          Critical path analysis

  /skills                 Show loaded skills by category
                          Skill match statistics

───────────────────────────────────────────────────────────
STATE MANAGEMENT
───────────────────────────────────────────────────────────

  /checkpoint             Save state without exiting
                          Creates restore point
                          Use before risky operations

  /deorchestrate          Clean exit with full save
                          Archives completed work
                          Safe to resume later

───────────────────────────────────────────────────────────
ISSUE TRACKING (Terminal 2)
───────────────────────────────────────────────────────────

  /issue                  Report bug or enhancement
                          Interactive interview
                          Writes to issue queue
                          Orchestrator polls automatically

  /issue reject <id> <reason>
                          Mark issue as won't fix
                          Moves to rejected section

  /issues                 View issue queue
                          Shows pending and in-progress

───────────────────────────────────────────────────────────
REFRESH SIGNALS (Terminal 2)
───────────────────────────────────────────────────────────

  /refresh issues         Poll issue queue now
                          Don't wait for next auto-poll

  /refresh skills         Reload skill directory
                          After adding new skills

  /refresh prd            Queue restart after run completes
                          Use when PRD changes significantly

  /refresh cancel         Cancel queued restart

───────────────────────────────────────────────────────────
SKILL MANAGEMENT
───────────────────────────────────────────────────────────

  /audit-skills           Generate skill library health report
                          Finds outdated, conflicting, or
                          missing skills

  /ingest-skill <source>  Import external skill
                          From URL, file, or paste
                          Security review included

  /skill-enhance [id]     Research and improve a skill
                          Web search for latest practices
                          Proposes updates for approval

───────────────────────────────────────────────────────────
EMERGENCY
───────────────────────────────────────────────────────────

  /abort                  Emergency stop
                          Requires confirmation
                          Use when agents are stuck or
                          producing incorrect output

═══════════════════════════════════════════════════════════
Documentation: https://github.com/bladehstream/claudestrator
═══════════════════════════════════════════════════════════
```

---

## If Specific Command Requested

If `$ARGUMENTS` contains a command name (e.g., "orchestrate", "prdgen", "status"):

1. Read the corresponding command file: `.claude/commands/<command>.md` or `.claudestrator/commands/<command>.md`
2. Display the full content of that command file
3. If command not found, show: "Command not found. Run /claudestrator-help to see all commands."
