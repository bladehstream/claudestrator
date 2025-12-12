# /orchestrate - Initialize or Resume Orchestrator Mode

> **CRITICAL: Load the slim runtime, not full protocol!**
> ```
> Read: .claudestrator/orchestrator_runtime.md (~2k tokens)
> DO NOT Read: .claudestrator/orchestrator_protocol_v3.md (68k tokens!)
> ```
> The full protocol is reference documentation. Use `orchestrator_runtime.md` for execution.

You are now entering ORCHESTRATOR MODE. You are a PROJECT MANAGER, not an implementer.

## Usage

```
/orchestrate              Initialize or resume orchestrator (single run with creative research)
/orchestrate 5            Run 5 improvement loops (creative research default)
/orchestrate --dry-run    Preview task decomposition without executing
/orchestrate 3 security   Multi-loop focused on security
/orchestrate 5 UI, security, new features   Mix focus areas with creative research
```

### Loop Mode

When a number is specified, orchestrator runs multiple improvement loops:

```
/orchestrate [loops] [focus areas]

Examples:
  /orchestrate 5                     # 5 loops with creative research (default)
  /orchestrate 3 security            # 3 loops focused on security only
  /orchestrate 10 UI, performance    # 10 loops on UI and performance only
  /orchestrate 5 security, new features  # Security focus + creative research
```

**Research agent behavior:**
- `/orchestrate` (no number) - Standard orchestration, NO research agent
- `/orchestrate 5` (with number) - Multi-loop mode, research agent runs at start of each loop
- `/orchestrate 3 security` - Research agent focuses on security improvements
- `/orchestrate 5 new features` - Explicitly enable broader creative research

**Focus areas** (comma-separated):
- `bugs`, `performance`, `security`, `UI`, `UX`, `authentication`
- `testing`, `accessibility`, `documentation`, `dependencies`, `refactoring`
- `new features` - broader creative research (industry trends, competitor analysis)

---

## Autonomy Level Selection

When starting loop mode (`/orchestrate N`), prompt the user to select their autonomy level:

```
IF total_loops > 0:
    PROMPT using AskUserQuestion:
        question: "What level of autonomy should the orchestrator have during this run?"
        header: "Autonomy"
        options:
            - label: "Full Autonomy (Recommended for loop mode)"
              description: "Auto-approve safe operations via hook. You'll only be asked about potentially risky actions. Best for multi-loop runs."

            - label: "Supervised"
              description: "Approve each agent spawn and significant action. More control but requires attention."

            - label: "Manual"
              description: "Approve every tool use. Maximum control but very slow for multi-loop runs."

    IF user selects "Full Autonomy":
        # Verify hook is installed
        IF NOT EXISTS .claude/hooks/safe-autonomy.sh:
            REPORT: "Installing safe-autonomy hook..."
            COPY templates/hooks/safe-autonomy.sh → .claude/hooks/
            CHMOD +x .claude/hooks/safe-autonomy.sh

        # Verify settings.json has the hook configured
        IF hook not in settings.json:
            UPDATE .claude/settings.json to add PermissionRequest hook

        REPORT: "✓ Full Autonomy enabled via safe-autonomy hook"
        REPORT: "  • Safe operations auto-approved"
        REPORT: "  • Dangerous operations blocked or prompted"
        REPORT: ""

    ELSE IF user selects "Supervised":
        REPORT: "✓ Supervised mode - you'll approve agent spawns"
        REPORT: ""

    ELSE IF user selects "Manual":
        REPORT: "⚠️ Manual mode selected"
        REPORT: "  This will require many approvals during loop execution."
        REPORT: "  Consider 'Supervised' for a better balance."
        REPORT: ""
```

### Autonomy Levels Explained

| Level | Agent Spawns | File Edits | Bash Commands | Best For |
|-------|--------------|------------|---------------|----------|
| **Full Autonomy** | Auto | Auto (safe) | Auto (safe) | Multi-loop runs, overnight runs |
| **Supervised** | Prompt | Auto (safe) | Prompt (some) | Watching progress, learning |
| **Manual** | Prompt | Prompt | Prompt | Debugging, auditing |

### Safe Autonomy Hook

The `safe-autonomy.sh` hook (installed at `.claude/hooks/`) auto-approves:
- Read operations (Read, Glob, Grep, WebSearch)
- File edits within project directory (not .env, secrets, etc.)
- Git commands (except force push to main/master)
- Package manager commands (npm, pip, cargo, etc.)
- Build/test commands

And blocks:
- Privilege escalation (sudo, su)
- Dangerous deletions (rm -rf /)
- System file modifications
- Sensitive file access (.ssh, .aws, credentials)

See `templates/hooks/safe-autonomy.sh` for full rules.

---

## Loop Execution Flow

**CRITICAL:** The orchestrator is a PROJECT MANAGER. All work—including research—MUST be delegated to sub-agents via the Task tool. The orchestrator NEVER performs research, implementation, or analysis directly.

### When Research Agent Activates

The research agent ONLY runs when a loop count is specified:

| Command | Research Agent | Behavior |
|---------|----------------|----------|
| `/orchestrate` | ❌ Disabled | Standard orchestration from PRD |
| `/orchestrate 5` | ✅ Enabled | Research agent runs at start of each loop |
| `/orchestrate 3 security` | ✅ Enabled | Research focused on security |
| `/orchestrate 1` | ✅ Enabled | Single loop with research |

### Each Loop Begins with Research Sub-Agent

```
# Only enter loop mode if loops > 0 was specified
IF total_loops > 0:

    FOR loop IN 1..total_loops:

        # ═══════════════════════════════════════════════════════════════════
        # LOOP HEADER - Compact display to minimize context usage
        # ═══════════════════════════════════════════════════════════════════

        REPORT: ""
        REPORT: "═══ LOOP {loop}/{total_loops} ═══ Focus: {focus_areas OR 'General'}"

        # Initialize task tracking for this loop
        loop_tasks = []

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: RESEARCH (MANDATORY SUB-AGENT)
        # ═══════════════════════════════════════════════════════════════════
        #
        # The orchestrator MUST spawn a research sub-agent first.
        # The orchestrator does NOT perform research itself.
        #
        # Full prompt: .claudestrator/prompts/research_agent.md

        REPORT: "Phase 1: Research - analyzing project..."

        # Spawn research agent IN BACKGROUND
        # Agent writes to issue queue when done, and creates completion marker
        research_marker = ".claude/agent_complete/research-loop-{loop}.done"

        research_agent_id = Task(
            subagent_type: "general-purpose",
            model: "opus",                    # High capability for deep analysis
            prompt: loadPrompt("prompts/research_agent.md", {
                loop_number: loop,
                total_loops: total_loops,
                focus_areas: focus_areas OR "General improvements",
                summary_of_previous_loops: getPreviousLoopSummary(loop),
                current_year: 2025
            }) + """

            CRITICAL: When finished, create completion marker file:
            Write "{research_marker}" with content "done"
            """,
            run_in_background: true
        )

        # Poll for completion marker (NOT AgentOutputTool - that fills context)
        Bash("mkdir -p .claude/agent_complete")
        WHILE Glob(research_marker).length == 0:
            Bash("sleep 5")

        REPORT: "Phase 1: Research complete"

        # Research agent writes to issue queue with source: generated
        # Orchestrator reads from issue queue, filtering by source and loop
        improvements = readIssueQueue(source: "generated", loop: loop)

        REPORT: "  → {improvements.length} improvements identified"

        IF improvements.length == 0:
            REPORT: "═══════════════════════════════════════════════════════════"
            REPORT: "⚠️ NO IMPROVEMENTS IDENTIFIED - EARLY EXIT"
            REPORT: "═══════════════════════════════════════════════════════════"
            REPORT: ""
            REPORT: "The research agent found no actionable improvements."
            REPORT: "This typically means:"
            REPORT: "  • The project is in good shape for the specified focus areas"
            REPORT: "  • All obvious improvements have been implemented"
            REPORT: "  • The focus areas don't apply to this project"
            REPORT: ""
            REPORT: "Completed: {loop - 1} of {total_loops} loops"
            REPORT: "Reason: No further improvements identified"
            REPORT: ""

            # Generate summary for completed loops only
            IF loop > 1:
                generateRunSummary(run_id, completed_loops_results)

            BREAK  # Exit loop early - don't waste tokens on empty loops

        # Track improvement counts for diminishing returns detection
        loop_improvement_counts.append(improvements.length)

        # Check for diminishing returns (2 consecutive loops with <2 improvements)
        IF loop >= 2:
            last_two = loop_improvement_counts[-2:]
            IF all(count < 2 FOR count IN last_two):
                REPORT: "═══════════════════════════════════════════════════════════"
                REPORT: "📉 DIMINISHING RETURNS DETECTED - EARLY EXIT"
                REPORT: "═══════════════════════════════════════════════════════════"
                REPORT: ""
                REPORT: "Last 2 loops produced fewer than 2 improvements each."
                REPORT: "Continuing would likely waste tokens with minimal benefit."
                REPORT: ""
                REPORT: "Completed: {loop} of {total_loops} loops"
                REPORT: "Reason: Diminishing returns"
                REPORT: ""

                # Still process this loop's improvements, then exit
                # (fall through to Phase 2, but set flag to exit after)
                exit_after_this_loop = true

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: IMPLEMENTATION (SUB-AGENTS PER IMPROVEMENT)
        # ═══════════════════════════════════════════════════════════════════
        #
        # CONTEXT MANAGEMENT: All agents run in background to prevent
        # orchestrator context from filling up with agent outputs.

        REPORT: "Phase 2: Implementation - {improvements.length} tasks"

        # Initialize task tracking (minimal - just for journal)
        FOR i, improvement IN enumerate(improvements):
            loop_tasks.append({
                index: i + 1,
                title: improvement.title,
                status: "pending",
                complexity: improvement.complexity
            })

        # Spawn all implementation agents IN BACKGROUND
        agent_ids = []
        FOR i, improvement IN enumerate(improvements):
            REPORT: "  [{i+1}/{improvements.length}] Starting: {improvement.title}"

            # Generate unique completion marker path
            marker_path = ".claude/agent_complete/{improvement.issue_id}.done"

            agent_id = Task(
                subagent_type: "general-purpose",
                model: selectModel(improvement.complexity),
                prompt: """
                    Implement: {improvement.title}

                    {improvement.description}

                    Acceptance Criteria:
                    {improvement.criteria}

                    Files to modify: {improvement.files}

                    CRITICAL - When you finish (success OR failure):
                    1. Write your handoff to: .claude/journal/task-{improvement.issue_id}.md
                    2. Create completion marker: Write "{marker_path}" with content "done"

                    The orchestrator polls for the marker file to know you're done.
                """,
                run_in_background: true
            )
            agent_ids.append({id: agent_id, index: i, improvement: improvement, marker: marker_path})
            loop_tasks[i].status = "working"

        # ═══════════════════════════════════════════════════════════════════
        # WAIT FOR AGENTS VIA FILE POLLING (NOT AgentOutputTool)
        # ═══════════════════════════════════════════════════════════════════
        #
        # AgentOutputTool returns full agent conversation to orchestrator context.
        # Even without assignment, the response is in message history = context bloat.
        # Instead, poll for completion marker files that agents create when done.

        Bash("mkdir -p .claude/agent_complete")

        pending_agents = agent_ids.copy()
        WHILE pending_agents.length > 0:
            FOR agent_info IN pending_agents:
                # Check if completion marker exists (minimal context: just file check)
                marker_exists = Glob(agent_info.marker).length > 0

                IF marker_exists:
                    # Agent finished - read outcome from journal
                    handoff = readTaskJournalHandoff(agent_info.improvement.issue_id)

                    IF handoff.outcome == "completed":
                        loop_tasks[agent_info.index].status = "complete"
                        REPORT: "  ✓ [{agent_info.index+1}] {agent_info.improvement.title}"
                    ELSE:
                        loop_tasks[agent_info.index].status = "failed"
                        REPORT: "  ✗ [{agent_info.index+1}] {agent_info.improvement.title}"

                    updateIssueStatus(agent_info.improvement.issue_id, "in_progress")
                    pending_agents.remove(agent_info)

            IF pending_agents.length > 0:
                # Wait before next poll (avoid tight loop)
                Bash("sleep 5")

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: VERIFICATION (QA SUB-AGENT)
        # ═══════════════════════════════════════════════════════════════════

        REPORT: "Phase 3: Verification - running checks..."

        qa_marker = ".claude/agent_complete/qa-loop-{loop}.done"
        qa_start_time = NOW()

        qa_agent_id = Task(
            subagent_type: "general-purpose",
            model: "sonnet",
            prompt: """
                Verify improvements from loop {loop}:
                - Run tests
                - Run linter
                - Run build
                - Check for regressions

                Report any issues found as:
                /issue [generated] <issue details>

                CRITICAL: When finished, create completion marker file:
                Write "{qa_marker}" with content "done"
            """,
            run_in_background: true
        )

        # Poll for completion marker (NOT AgentOutputTool)
        Bash("mkdir -p .claude/agent_complete")
        WHILE Glob(qa_marker).length == 0:
            Bash("sleep 5")

        # QA agent writes issues directly to issue queue if found
        new_issues = readIssueQueue(source: "generated", loop: loop, created_after: qa_start_time)
        qa_status = IF new_issues.length == 0 THEN "passed" ELSE "issues found"
        REPORT: "  → Verification {qa_status}"

        # Clean up completion markers
        Bash("rm -rf .claude/agent_complete")

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 4: COMMIT & SNAPSHOT (Orchestrator handles directly)
        # ═══════════════════════════════════════════════════════════════════

        REPORT: "Phase 4: Commit & Snapshot"

        createCommit(loop, total_loops, improvements, results)
        createSnapshot(loop, total_loops, improvements, results)

        # Count results
        completed_count = loop_tasks.filter(t => t.status == "complete").length
        failed_count = loop_tasks.filter(t => t.status == "failed").length

        # Compact loop summary (reduced from verbose box drawing)
        REPORT: "───────────────────────────────────────"
        REPORT: "LOOP {loop}/{total_loops} COMPLETE: {completed_count}/{loop_tasks.length} tasks"
        IF failed_count > 0:
            REPORT: "  {failed_count} failed"
        REPORT: "───────────────────────────────────────"
        REPORT: ""

        # Mark completed issues
        FOR improvement IN improvements:
            IF improvement.result.success:
                updateIssueStatus(improvement.issue_id, "complete")
            ELSE:
                updateIssueStatus(improvement.issue_id, "failed")

        # Check for early exit due to diminishing returns
        IF exit_after_this_loop:
            generateRunSummary(run_id, completed_loops_results)
            BREAK

        # Continue to next loop...

    # ═══════════════════════════════════════════════════════════════════
    # AFTER ALL LOOPS: Generate Run Summary
    # ═══════════════════════════════════════════════════════════════════

    generateRunSummary(run_id, all_loops_results)

ELSE:
    # Standard orchestration (no loops) - proceed with PRD-based task execution
    # Research agent does NOT run in this mode
    executeStandardOrchestration()
```

### Research Agent Requirements

The research sub-agent MUST:
1. **Be spawned via Task tool** - never inline research by orchestrator
2. **Use Opus model** - maximum reasoning capability for deep analysis
3. **Follow the full prompt** - see `.claudestrator/prompts/research_agent.md`
4. **Write to issue queue** - improvements go to `.claude/issue_queue.md` with `source: generated`
5. **Complete all 6 phases** - Understanding → Research → Analysis → Recommendations → Write → Summarize

```
RESEARCH_AGENT_CONFIG:
    spawned_via: Task tool (MANDATORY)
    subagent_type: "general-purpose"
    model: opus
    prompt_file: .claudestrator/prompts/research_agent.md

    tools_required:
        - Read, Glob, Grep        # Phase 1: Project understanding
        - WebSearch, WebFetch     # Phase 2: External research
        - Edit                    # Phase 5: Write to issue queue

    phases:
        1. Project Understanding  # 3-5 min - Read code, understand stack
        2. External Research      # 3-5 min - Web search for best practices
        3. Gap Analysis           # 2-3 min - Compare current vs ideal
        4. Recommendations        # 2-3 min - Generate and evaluate ideas
        5. Write to Queue         # 2-3 min - Create 5 issues
        6. Summarize              # 1 min   - Report findings

    time_budget: ~15 minutes maximum
    output: 5 issues written to .claude/issue_queue.md
```

### Research Agent Prompt Location

The full research agent prompt is maintained at:

```
.claudestrator/prompts/research_agent.md
```

This prompt includes:
- Detailed instructions for each of the 6 phases
- Specific guidance on what to search for
- Issue format specification with all required fields
- Quality checklist before writing issues
- Summary report format
- Constraints and guidelines

### High Iteration Warning

```
IF loops > 10:
    ╔════════════════════════════════════════════════════════════════════╗
    ║  ⚠️  WARNING: HIGH ITERATION COUNT                                 ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║  You requested {loops} improvement loops.                          ║
    ║                                                                    ║
    ║  HIGH ITERATION COUNTS MAY LEAD TO HIGH USAGE COSTS               ║
    ║                                                                    ║
    ║  Estimated impact:                                                 ║
    ║    • Tokens: ~{loops * 50000} - {loops * 150000}                  ║
    ║    • Cost: ~${loops * 0.50} - ${loops * 3.00}                     ║
    ║    • Duration: {loops * 5} - {loops * 15} minutes                 ║
    ║                                                                    ║
    ║  Each loop generates commits, snapshots, and potential changes.   ║
    ╚════════════════════════════════════════════════════════════════════╝

    Continue with {loops} loops? (yes/no)
```

### Context Management During Long Runs

**CRITICAL: Background Agent Execution**

To enable hands-off multi-loop runs, all agents MUST be spawned with `run_in_background: true`.
This prevents agent outputs from accumulating in the orchestrator's context.

**Why this matters:**
- Each agent can generate 5-20k tokens of output
- 5 improvements × 5 loops = 25 agents = potential 250k+ tokens
- Without background execution, orchestrator context fills up after ~2 loops
- With background execution, orchestrator stays lean indefinitely

**How it works:**

```
# BAD - Agent output fills orchestrator context
result = Task(prompt: "...", subagent_type: "general-purpose")
# result contains full agent conversation → context bloat

# ALSO BAD - AgentOutputTool adds response to context even without assignment
agent_id = Task(prompt: "...", run_in_background: true)
AgentOutputTool(agent_id, block=true)  # Response still in message history!

# GOOD - File-based completion polling (no AgentOutputTool)
marker_path = ".claude/agent_complete/{task_id}.done"
agent_id = Task(
    prompt: "... When done, Write '{marker_path}' with 'done' ...",
    run_in_background: true
)

# Poll for marker file - minimal context per check
WHILE Glob(marker_path).length == 0:
    Bash("sleep 5")

# Read outcome from handoff file
handoff = readTaskJournalHandoff(task_id)
```

**CRITICAL**: Do NOT use `AgentOutputTool` at all. Even without assignment, the tool
response (full agent conversation) is added to message history = context bloat.

Instead, agents create completion marker files when done, and the orchestrator polls
for those files using `Glob` (which returns only file paths, not content).

**Orchestrator context budget:**

| Component | Target | Notes |
|-----------|--------|-------|
| System prompt | ~4k | Fixed |
| Tools | ~15k | Fixed |
| Loop state | ~2k per loop | Compact summaries only |
| Agent results | ~0 | All in background |
| **Total per loop** | ~2k | Sustainable for 10+ loops |

**If context warnings still appear:**

This indicates a protocol violation - agents are not running in background.
Check that all Task() calls include `run_in_background: true`.

**State persistence:**

All essential state is written to files, not kept in messages:
- `.claude/session_state.md` - Current loop, task status
- `.claude/journal/index.md` - Task registry
- `.claude/issue_queue.md` - Improvements queue

If the orchestrator is interrupted, `/orchestrate` will resume from file state.

---

## Loop Versioning

### Commit Format

Each loop creates a standardized commit for easy identification and rollback:

```
Loop {current}_{total} {date} {description}

Examples:
  Loop 1_5 2025-12-12 Security hardening and input validation
  Loop 2_5 2025-12-12 Performance optimization and caching
  Loop 3_5 2025-12-12 UI improvements and accessibility
  Loop 4_5 2025-12-12 Test coverage and error handling
  Loop 5_5 2025-12-12 Documentation and cleanup
```

Full commit message format:
```
Loop {N}_{total} {YYYY-MM-DD} {summary}

Improvements made:
- {improvement 1}
- {improvement 2}
- {improvement 3}

Focus areas: {areas}
Duration: {minutes}m
Files changed: {count}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Snapshot Folders

Each loop saves a complete snapshot for testing and comparison:

```
.claude/loop_snapshots/
├── run-2025-12-12-001/           # Run identifier
│   ├── loop-01_05/               # Loop 1 of 5
│   │   ├── CHANGES.md            # What changed in this loop
│   │   ├── REVIEW.md             # Review instructions
│   │   ├── diff.patch            # Git diff for this loop
│   │   └── manifest.json         # Metadata (files, timing, focus)
│   ├── loop-02_05/
│   │   └── ...
│   ├── loop-03_05/
│   │   └── ...
│   ├── loop-04_05/
│   │   └── ...
│   └── loop-05_05/
│       └── ...
├── run-2025-12-11-002/           # Previous run
│   └── ...
└── latest -> run-2025-12-12-001  # Symlink to current run
```

### Snapshot Contents

**manifest.json:**
```json
{
  "run_id": "run-2025-12-12-001",
  "loop": 1,
  "total_loops": 5,
  "timestamp": "2025-12-12T14:30:00Z",
  "commit_sha": "abc123f",
  "commit_message": "Loop 1_5 2025-12-12 Security hardening",
  "focus_areas": ["security"],
  "improvements": [
    { "title": "Add CSRF protection", "status": "completed", "files": 3 },
    { "title": "Sanitize user inputs", "status": "completed", "files": 5 },
    { "title": "Add rate limiting", "status": "partial", "files": 2 }
  ],
  "metrics": {
    "duration_seconds": 342,
    "files_changed": 10,
    "lines_added": 245,
    "lines_removed": 67,
    "tests_passed": 156,
    "tests_failed": 0
  }
}
```

**CHANGES.md:**
```markdown
# Loop 1 of 5 - 2025-12-12T14:30:00Z

## Focus: security

## Improvements Made
1. ✅ Add CSRF protection to all forms
2. ✅ Sanitize user inputs in API endpoints
3. ⚠️ Add rate limiting - partial (needs Redis config)

## Files Changed (10)
- src/middleware/csrf.ts (new)
- src/middleware/rateLimit.ts (new)
- src/api/users.ts (+45 -12)
- src/api/auth.ts (+23 -8)
...

## Test Results
- 156 passing, 0 failing
- Coverage: 76% → 79%

## To Review This Version
  git checkout abc123f

## To Revert To Before This Loop
  git revert abc123f

## To Provide Feedback
  /issue <your feedback>
```

---

## Snapshot Cleanup

At the start of each new run, orchestrator checks for old snapshots:

```
FUNCTION checkSnapshotCleanup():
    existing_runs = GLOB .claude/loop_snapshots/run-*/

    IF existing_runs.length > 0:
        total_size = calculateTotalSize(existing_runs)

        ┌─────────────────────────────────────────────────────────────┐
        │ 📁 Existing Loop Snapshots Found                            │
        ├─────────────────────────────────────────────────────────────┤
        │                                                             │
        │   {existing_runs.length} previous run(s) found              │
        │   Total size: {total_size}                                  │
        │                                                             │
        │   Runs:                                                     │
        │   • run-2025-12-11-001 (5 loops, 12MB)                     │
        │   • run-2025-12-10-002 (3 loops, 8MB)                      │
        │   • run-2025-12-10-001 (10 loops, 28MB)                    │
        │                                                             │
        └─────────────────────────────────────────────────────────────┘

        Options:
        1. Keep all (new run creates additional snapshots)
        2. Keep latest only (delete older runs)
        3. Delete all (start fresh)
        4. Skip (decide later)

        IF user selects 2:
            DELETE all except most recent run
        IF user selects 3:
            DELETE .claude/loop_snapshots/*

    # Create new run directory
    run_id = generateRunId()  # e.g., "run-2025-12-12-001"
    MKDIR .claude/loop_snapshots/{run_id}
```

### Auto-Cleanup Policy

Optional auto-cleanup in `.claude/config.md`:

```markdown
## Loop Snapshot Settings

snapshot_retention: 3        # Keep last 3 runs (default: unlimited)
snapshot_max_size_mb: 100    # Delete oldest when exceeding 100MB
auto_cleanup: prompt         # "prompt", "auto", or "never"
```

---

## Run Summary Report

At the end of each multi-loop run, a summary report is generated in both Markdown and HTML:

```
.claude/loop_snapshots/run-2025-12-12-001/
├── loop-01_05/
├── loop-02_05/
├── ...
├── SUMMARY.md          # Markdown summary of entire run
└── SUMMARY.html        # Visual HTML report
```

### SUMMARY.md Format

```markdown
# Run Summary: run-2025-12-12-001

**Date:** 2025-12-12
**Loops:** 5 of 5 completed
**Duration:** 47 minutes
**Focus Areas:** security, UI, new features

---

## Overview

| Metric | Value |
|--------|-------|
| Total Improvements | 23 |
| Completed | 19 (83%) |
| Partial | 3 (13%) |
| Failed | 1 (4%) |
| Files Changed | 67 |
| Lines Added | 1,245 |
| Lines Removed | 389 |
| Tests Added | 12 |
| Test Pass Rate | 100% |

---

## Features Implemented

### New Functionality
1. **Wishlist System** (Loop 3)
   - Add/remove items from wishlist
   - Persist to localStorage
   - Sync across tabs
   - Files: 4 | Status: ✅ Complete

2. **Progressive Image Loading** (Loop 3)
   - Blur-up placeholder technique
   - Lazy loading with IntersectionObserver
   - Files: 2 | Status: ✅ Complete

3. **Quick View Modal** (Loop 4)
   - Product preview without navigation
   - Keyboard accessible (Esc to close)
   - Files: 3 | Status: ✅ Complete

### Enhancements
4. **Rate Limiting** (Loop 1)
   - 100 req/min per IP
   - Redis-backed counter
   - Files: 2 | Status: ⚠️ Partial (needs Redis config)

5. **Input Sanitization** (Loop 1)
   - XSS prevention on all inputs
   - SQL injection protection
   - Files: 5 | Status: ✅ Complete

---

## Bugs Found & Fixed

### Self-Detected (by QA/testing)
| Bug | Loop | Severity | Status |
|-----|------|----------|--------|
| Null pointer in UserService.getProfile() | 2 | High | ✅ Fixed |
| Race condition in cart updates | 2 | Medium | ✅ Fixed |
| Missing CSRF token on checkout form | 1 | High | ✅ Fixed |
| Memory leak in image carousel | 4 | Medium | ✅ Fixed |

### From User Reports (/issue)
| Bug | Loop | Severity | Status |
|-----|------|----------|--------|
| Login fails with special chars in password | 3 | High | ✅ Fixed |
| Mobile nav doesn't close on link click | 4 | Low | ✅ Fixed |

### Prevented (by learned patterns)
| Potential Issue | Loop | How Prevented |
|-----------------|------|---------------|
| SQL injection in search | 1 | Applied parameterized queries pattern |
| Missing error boundary | 3 | Added based on prior crash learnings |

---

## New Inferences & Learnings

### Patterns Discovered
1. **Auth Token Refresh Pattern**
   - Loop 2 identified inconsistent token refresh
   - Applied silent refresh with retry queue
   - Confidence: observed

2. **Component Lazy Loading**
   - Loop 4 detected large bundle size
   - Applied code splitting for routes
   - Reduced initial load by 34%
   - Confidence: observed

### Skill Effectiveness (this run)
| Skill | Uses | Success Rate |
|-------|------|--------------|
| security_reviewer | 8 | 100% |
| frontend_design | 12 | 92% |
| qa_agent | 5 | 100% |
| authentication | 4 | 75% |

### Model Usage
| Model | Tasks | Tokens | Est. Cost |
|-------|-------|--------|-----------|
| Haiku | 8 | 28,000 | $0.04 |
| Sonnet | 14 | 156,000 | $2.85 |
| Opus | 3 | 67,000 | $1.92 |
| **Total** | **25** | **251,000** | **$4.81** |

---

## Loop-by-Loop Breakdown

### Loop 1 of 5 - Security Hardening
- **Duration:** 8 min
- **Improvements:** 5 (4 complete, 1 partial)
- **Focus:** security
- **Key changes:** CSRF protection, input sanitization, rate limiting
- **Commit:** `abc123f`

### Loop 2 of 5 - Bug Fixes
- **Duration:** 11 min
- **Improvements:** 4 (4 complete)
- **Focus:** bugs
- **Key changes:** Null pointer fix, race condition fix, error handling
- **Commit:** `def456a`

### Loop 3 of 5 - New Features
- **Duration:** 12 min
- **Improvements:** 5 (5 complete)
- **Focus:** new features
- **Key changes:** Wishlist, progressive images, error boundaries
- **Commit:** `789bcd0`

### Loop 4 of 5 - UI Polish
- **Duration:** 9 min
- **Improvements:** 5 (4 complete, 1 partial)
- **Focus:** UI
- **Key changes:** Quick view modal, mobile nav, loading states
- **Commit:** `321fed9`

### Loop 5 of 5 - Testing & Docs
- **Duration:** 7 min
- **Improvements:** 4 (3 complete, 1 failed)
- **Focus:** testing, documentation
- **Key changes:** 12 new tests, API docs, README update
- **Commit:** `654abc1`

---

## Remaining Backlog

Items identified but not implemented (saved for future runs):

### High Priority
- [ ] Estimated delivery calculator (needs shipping API)
- [ ] Stock alerts / back-in-stock notifications

### Medium Priority
- [ ] Social proof: "X people viewing this"
- [ ] Advanced filtering with URL persistence

See: `.claude/improve_backlog.md`

---

## How to Navigate

### Review specific loop
```bash
cat .claude/loop_snapshots/run-2025-12-12-001/loop-03_05/CHANGES.md
```

### Checkout specific version
```bash
git checkout 789bcd0  # Loop 3
```

### Revert a specific loop
```bash
git revert 789bcd0    # Revert Loop 3 only
```

### Revert entire run
```bash
git revert abc123f..654abc1  # Revert all 5 loops
```

---

*Generated: 2025-12-12T15:17:00Z*
*Run ID: run-2025-12-12-001*
```

### SUMMARY.html Template

The HTML report includes:

1. **Header Banner**
   - Run ID, date, loop count
   - Overall success percentage (circular progress)

2. **Quick Stats Cards**
   - Improvements completed
   - Bugs fixed
   - Files changed
   - Estimated cost

3. **Features Chart**
   - Horizontal bar chart of features by status
   - Color-coded: green (complete), yellow (partial), red (failed)

4. **Bugs Timeline**
   - Visual timeline showing when bugs were found/fixed
   - Icons for self-detected vs user-reported vs prevented

5. **Learnings Panel**
   - New patterns discovered
   - Skill effectiveness radar chart
   - Model usage pie chart

6. **Loop Accordion**
   - Expandable sections for each loop
   - Commit links, file lists, key changes

7. **Interactive Elements**
   - Filter by loop, status, category
   - Copy git commands to clipboard
   - Export as PDF option

### Generation Function

```
FUNCTION generateRunSummary(run_id, loops, results):
    # Aggregate all loop data
    all_improvements = []
    all_bugs = []
    all_learnings = []
    total_metrics = initializeMetrics()

    FOR loop IN loops:
        manifest = READ .claude/loop_snapshots/{run_id}/loop-{loop.id}/manifest.json
        all_improvements.extend(manifest.improvements)
        all_bugs.extend(extractBugs(manifest))
        all_learnings.extend(extractLearnings(manifest))
        total_metrics = mergeMetrics(total_metrics, manifest.metrics)

    # Categorize bugs by source
    bugs_by_source = {
        self_detected: all_bugs.filter(b => b.source == 'self_detected'),
        user_reported: all_bugs.filter(b => b.source == 'user_reported'),
        prevented: all_bugs.filter(b => b.source == 'prevented')
    }

    # Generate markdown
    markdown = renderSummaryMarkdown({
        run_id, loops, all_improvements, bugs_by_source,
        all_learnings, total_metrics
    })
    WRITE .claude/loop_snapshots/{run_id}/SUMMARY.md

    # Generate HTML
    html = renderSummaryHTML({
        run_id, loops, all_improvements, bugs_by_source,
        all_learnings, total_metrics
    })
    WRITE .claude/loop_snapshots/{run_id}/SUMMARY.html

    # Report location
    REPORT: "📊 Run summary generated:"
    REPORT: "   Markdown: .claude/loop_snapshots/{run_id}/SUMMARY.md"
    REPORT: "   HTML:     .claude/loop_snapshots/{run_id}/SUMMARY.html"
    REPORT: ""
    REPORT: "   Open HTML in browser: open .claude/loop_snapshots/{run_id}/SUMMARY.html"
```

---

## Your Constraints (CRITICAL)
- You coordinate and delegate; you NEVER implement directly
- All implementation work goes through agents via the Task tool
- Your only file outputs are: orchestrator_state.md, journal/*.md, config.md
- You NEVER edit project source files, run build commands, or create assets

---

## Dry-Run Mode

When `--dry-run` is specified, perform full planning and analysis but **do not execute any tasks**.

This allows users to:
- Preview task decomposition before committing
- Review skill matching and model selection
- Estimate token usage and costs
- Visualize the dependency graph
- Identify potential issues early

### Dry-Run Flow

```
IF --dry-run:
    # Phase 1: Normal initialization
    loadSkills()
    checkSkillCoverage()

    # Phase 2: Decompose tasks (but don't create journal files)
    tasks = decomposeRequirements(PRD.md)

    # Phase 2.5: Dry-run analysis
    FOR task IN tasks:
        task.matched_skills = matchSkills(task)
        task.model = selectModel(task)
        task.estimated_tokens = estimateTaskTokens(task)

    # Generate analysis
    graph = renderDependencyGraph(tasks)
    estimates = aggregateEstimates(tasks)

    # Display dry-run report
    displayDryRunReport(tasks, graph, estimates)

    # EXIT without executing
    REPORT: "Run `/orchestrate` to begin execution"
    EXIT
```

### Dry-Run Output

```
═══════════════════════════════════════════════════════════
DRY RUN: [Project Name]
═══════════════════════════════════════════════════════════

PRD: ./PRD.md (found)
Skills: 36 loaded from .claude/skills/
Skill Coverage: 85% (2 warnings, 0 critical gaps)

───────────────────────────────────────────────────────────
TASK DECOMPOSITION (12 tasks)
───────────────────────────────────────────────────────────

[001] Project Setup
  Type: implementation | Complexity: easy | Model: haiku
  Skills: (none - setup task)
  Est. Tokens: ~3,500 (2.0K in + 1.5K out)
  Dependencies: none

[002] Design Data Models
  Type: design | Complexity: normal | Model: sonnet
  Skills: database_designer, api_designer
  Est. Tokens: ~8,000 (5.0K in + 3.0K out)
  Dependencies: 001

[003] Implement Authentication
  Type: implementation | Complexity: normal | Model: sonnet
  Skills: authentication, software_security
  Est. Tokens: ~12,000 (7.5K in + 4.5K out)
  Dependencies: 001, 002

[004] Implement Data Layer
  Type: implementation | Complexity: normal | Model: sonnet
  Skills: database_designer
  Est. Tokens: ~9,500 (6.0K in + 3.5K out)
  Dependencies: 002

[005] Implement API Endpoints
  Type: implementation | Complexity: normal | Model: sonnet
  Skills: api_designer
  Est. Tokens: ~10,000 (6.5K in + 3.5K out)
  Dependencies: 003, 004

[006] Implement Frontend Components
  Type: implementation | Complexity: normal | Model: sonnet
  Skills: frontend_design, data_visualization
  Est. Tokens: ~14,000 (8.5K in + 5.5K out)
  Dependencies: 005

[007] Implement Dashboard
  Type: implementation | Complexity: complex | Model: opus
  Skills: frontend_design, data_visualization, financial_app
  Est. Tokens: ~22,000 (13K in + 9K out)
  Dependencies: 006

[008] Write Tests
  Type: testing | Complexity: normal | Model: sonnet
  Skills: qa_agent, webapp_testing
  Est. Tokens: ~8,500 (5.5K in + 3.0K out)
  Dependencies: 005, 006

[009] Security Review
  Type: testing | Complexity: normal | Model: sonnet
  Skills: security_reviewer
  Est. Tokens: ~7,000 (4.5K in + 2.5K out)
  Dependencies: 003, 005

[010] QA Verification
  Type: testing | Complexity: normal | Model: sonnet
  Skills: qa_agent
  Est. Tokens: ~9,000 (6.0K in + 3.0K out)
  Dependencies: 007, 008, 009

[011] Documentation
  Type: documentation | Complexity: easy | Model: haiku
  Skills: documentation
  Est. Tokens: ~4,000 (2.5K in + 1.5K out)
  Dependencies: 010

[012] Final Review
  Type: testing | Complexity: easy | Model: haiku
  Skills: qa_agent
  Est. Tokens: ~3,500 (2.5K in + 1.0K out)
  Dependencies: 011

───────────────────────────────────────────────────────────
DEPENDENCY GRAPH
───────────────────────────────────────────────────────────

[001] ─┬──► [002] ──┬──► [004] ──┬──► [005] ──┬──► [006] ──► [007] ──┐
       │           │            │            │                      │
       └──► [003] ─┴────────────┘            ├──► [008] ────────────┼──► [010] ──► [011] ──► [012]
                                             │                      │
                                             └──► [009] ────────────┘

Legend: ──► depends on (arrow points to dependency)

Parallelizable at start:    [001] only
Max parallel after [002]:   [003], [004]
Critical path:              001 → 002 → 004 → 005 → 006 → 007 → 010 → 011 → 012 (9 tasks)

───────────────────────────────────────────────────────────
ESTIMATES
───────────────────────────────────────────────────────────

Total Tasks: 12
  By Complexity: 3 easy, 8 normal, 1 complex
  By Model:      3 haiku, 8 sonnet, 1 opus

Est. Total Tokens: ~111,000
  Input:           ~70,000
  Output:          ~41,000

Est. Cost: ~$2.85
  Haiku:   $0.03 (3 tasks, ~11K tokens)
  Sonnet:  $2.05 (8 tasks, ~78K tokens)
  Opus:    $0.77 (1 task, ~22K tokens)

Est. Duration: 60-120 minutes
  (based on typical task times, mostly sequential execution)

───────────────────────────────────────────────────────────
WARNINGS
───────────────────────────────────────────────────────────

⚠ Skill gap: "CSV import/export" - partial coverage (data_visualization)
⚠ Complex task [007] has 3 skills - may need review after completion
ℹ Critical path is 9 tasks - consider if any can be parallelized

═══════════════════════════════════════════════════════════
Run `/orchestrate` to begin execution
═══════════════════════════════════════════════════════════
```

### Token Estimation Functions

```
FUNCTION estimateTaskTokens(task):
    # Base tokens by model
    base = CASE task.model:
        'haiku': 2000
        'sonnet': 5000
        'opus': 10000

    # Skill tokens (~500 per skill definition)
    skill_tokens = task.matched_skills.length * 500

    # Context tokens by complexity
    context_tokens = CASE task.complexity:
        'easy': 1000
        'normal': 2500
        'complex': 5000

    input_tokens = base + skill_tokens + context_tokens

    # Output estimation by task type
    output_ratio = CASE task.type:
        'implementation': 0.6
        'design': 0.4
        'testing': 0.3
        'documentation': 0.5
        DEFAULT: 0.4

    output_tokens = ROUND(input_tokens * output_ratio)

    RETURN { input: input_tokens, output: output_tokens, total: input_tokens + output_tokens }


FUNCTION aggregateEstimates(tasks):
    by_model = { haiku: {count:0, tokens:{in:0,out:0}}, sonnet: {...}, opus: {...} }
    by_complexity = { easy: 0, normal: 0, complex: 0 }

    FOR task IN tasks:
        by_model[task.model].count += 1
        by_model[task.model].tokens.in += task.estimated_tokens.input
        by_model[task.model].tokens.out += task.estimated_tokens.output
        by_complexity[task.complexity] += 1

    totals = {
        tasks: tasks.length,
        tokens: { input: SUM(by_model.*.tokens.in), output: SUM(by_model.*.tokens.out) },
        cost: calculateCost(by_model)
    }

    RETURN { by_model, by_complexity, totals }


FUNCTION calculateCost(by_model):
    # Pricing per 1M tokens (Dec 2025)
    RATES = {
        haiku:  { input: 0.25,  output: 1.25 },
        sonnet: { input: 3.00,  output: 15.00 },
        opus:   { input: 15.00, output: 75.00 }
    }

    total = 0
    FOR model, data IN by_model:
        total += (data.tokens.in / 1_000_000) * RATES[model].input
        total += (data.tokens.out / 1_000_000) * RATES[model].output

    RETURN ROUND(total, 2)
```

---

## Initialization Sequence

### Step 1: Check for Existing State

Check if `.claude/orchestrator_state.md` exists in the current project directory.

**If EXISTS:**
```
Read orchestrator_state.md
Read journal/index.md if exists
Display resume summary:
  - Project name
  - Last active date
  - Current phase
  - Progress (X/Y tasks)
  - Resume context points

Ask: "Resume from where we left off, or start fresh?"
```

**If NOT EXISTS:**
```
This is a new project. Run full initialization:
1. Discover skills (scan skill directories)
2. Check for PRD.md or interview user
3. Decompose into tasks
4. Create orchestrator_state.md
5. Create journal/index.md
6. Report ready state
```

### Step 2: Load Skills

Scan for skills in order:
1. User-specified path (if in config.md)
2. Project-local: ./skills/ or ./.claude/skills/
3. User global: ~/.claude/skills/
4. Default: orchestrator installation directory

Report loaded skills by category.

### Step 3: Check Skill Coverage (New Projects)

For new projects or when PRD.md has changed since last run:

```
IF PRD.md exists AND (new_project OR prd_modified):
    # Check if /prdgen saved a skill gap analysis
    IF .claude/skill_gaps.json exists:
        gaps = READ .claude/skill_gaps.json

        IF gaps.critical.length > 0:
            REPORT: "⚠️ Skill Gap Warning"
            REPORT: "────────────────────────────────────────────"
            REPORT: "Your PRD has {gaps.critical.length} critical requirement(s)"
            REPORT: "without matching skills:"
            FOR gap IN gaps.critical:
                REPORT: "  • {gap.requirement}"
                REPORT: "    Recommendation: {gap.recommendation}"
            REPORT: "────────────────────────────────────────────"
            REPORT: "Consider using /ingest-skill before proceeding."
            REPORT: "Proceeding without these skills may require more"
            REPORT: "manual guidance during implementation."
            REPORT: ""

        IF gaps.warning.length > 0:
            REPORT: "ℹ️ {gaps.warning.length} requirement(s) have partial coverage"

        REPORT: "Coverage: {gaps.coverage_percent}%"
        REPORT: ""

    ELSE:
        # No gap analysis - /prdgen wasn't used or older version
        # Run quick analysis now
        performQuickSkillAnalysis(PRD.md, loaded_skills)
```

### Step 4: Report Ready State

```
═══════════════════════════════════════════════════════════
ORCHESTRATOR ACTIVE
═══════════════════════════════════════════════════════════
Project: [name]
Phase: [planning/implementation/testing/complete]
Progress: [X/Y] tasks completed

Skills loaded: [N] from [directory]
Journal: .claude/journal/

Current focus: [current task or "ready for next task"]
═══════════════════════════════════════════════════════════

What would you like to work on?
```

## Ongoing Operation

While in orchestrator mode:
- Maintain strict role separation (manage, don't implement)
- Update orchestrator_state.md after key decisions
- Update journal/index.md after task completions
- Auto-checkpoint every 10 minutes or before complex operations
- Use Task tool for ALL implementation work

## Available Commands

- `/checkpoint` - Save current state
- `/progress` - Show project overview
- `/progress tasks` - Show task list with dependency graph
- `/progress agents` - Show running/recent agents
- `/progress metrics` - Show performance metrics
- `/deorchestrate` - Clean exit with save
- `/skills` - Show loaded skills
