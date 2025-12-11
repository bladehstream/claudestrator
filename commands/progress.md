# /progress - Show Orchestration Progress

Display orchestrator progress, tasks, agents, and metrics.

## Usage

```
/progress              Show orchestrator overview
/progress tasks        Show task list with dependency graph
/progress agents       List all running and recent agents
/progress metrics      Show performance metrics and token usage
/progress <agent-id>   Show last output from a specific agent
```

---

## /progress (No Arguments)

Read and display information from:
- `.claude/session_state.md`
- `.claude/journal/index.md`

```
═══════════════════════════════════════════════════════════
ORCHESTRATOR PROGRESS
═══════════════════════════════════════════════════════════

PROJECT
  Name: [project name]
  Phase: [planning/implementation/testing/complete]
  Started: [date]
  Last checkpoint: [timestamp]

PROGRESS
  Tasks: [completed]/[total] ([percentage]%)
  ████████████░░░░░░░░ [visual progress bar]

CURRENT STATE
  Active task: [task ID and name, or "none"]
  Next task: [task ID and name]
  Blockers: [count, or "none"]
  Running agents: [count, or "none"]
  ⏳ PRD restart queued (X tasks remaining)    ← If /refresh prd was called

RECENT ACTIVITY
  - [Last few actions/completions]

SESSION
  Duration: [time since /orchestrate]
  Checkpoints: [count]
  Autonomy: [supervised/trust-agents/full-autonomy]

SKILLS
  Loaded: [count] from [directory]

═══════════════════════════════════════════════════════════
Commands: /progress tasks | /progress agents | /progress metrics
═══════════════════════════════════════════════════════════
```

---

## /progress tasks

Display all tasks with their current status and dependency graph.

Read from `.claude/journal/index.md` and display:

```
═══════════════════════════════════════════════════════════
TASK REGISTRY
═══════════════════════════════════════════════════════════

COMPLETED ✓
  [001] Set up project structure
  [002] Design data models
  [003] Implement user model

IN PROGRESS ◐
  [004] Implement auth middleware
        Agent: sonnet | Skills: authentication, security
        Started: 5 minutes ago

PENDING ○
  [005] Implement core API          (depends on: 003, 004)
  [006] Add validation              (depends on: 005)
  [007] Write tests                 (depends on: 005)
  [008] QA verification             (depends on: 006, 007)

BLOCKED ✗
  [none]

───────────────────────────────────────────────────────────
DEPENDENCY GRAPH
───────────────────────────────────────────────────────────

[001]✓ ─┬──► [003]✓ ──┬──► [005]○ ──► [006]○ ──┬──► [008]○
        │             │                        │
[002]✓ ─┴──► [004]◐ ──┘              [007]○ ──┘

Legend: ✓ done | ◐ active | ○ pending | ✗ blocked
        ──► depends on (arrow points to dependency)

───────────────────────────────────────────────────────────
ANALYSIS
───────────────────────────────────────────────────────────

Parallelizable now:     [004] (in progress)
Ready after [004]:      [005]
Critical path:          001 → 003 → 005 → 006 → 008 (5 tasks)
Estimated remaining:    5 tasks

═══════════════════════════════════════════════════════════
Progress: 3/8 (37.5%)
═══════════════════════════════════════════════════════════
```

### Dependency Graph Rendering

```
FUNCTION renderDependencyGraph(tasks):
    # 1. Build adjacency lists
    FOR task IN tasks:
        FOR dep IN task.dependencies:
            edges[dep].add(task.id)  # dep -> task

    # 2. Find roots (no dependencies)
    roots = tasks.filter(t => t.dependencies.length == 0)

    # 3. Assign levels via BFS
    levels = {}
    queue = roots.map(r => {id: r.id, level: 0})
    WHILE queue not empty:
        node = queue.dequeue()
        levels[node.id] = max(levels[node.id] OR 0, node.level)
        FOR child IN edges[node.id]:
            queue.enqueue({id: child, level: node.level + 1})

    # 4. Group tasks by level
    level_groups = groupBy(tasks, t => levels[t.id])

    # 5. Render ASCII
    output = []
    FOR level, tasks IN level_groups:
        row = renderLevelRow(tasks, edges)
        output.append(row)

    # 6. Add legend
    output.append("")
    output.append("Legend: ✓ done | ◐ active | ○ pending | ✗ blocked")
    output.append("        ──► depends on (arrow points to dependency)")

    RETURN output.join("\n")


FUNCTION getStatusIcon(task):
    CASE task.status:
        'completed': '✓'
        'in_progress': '◐'
        'pending': '○'
        'blocked': '✗'
        'failed': '✗'


FUNCTION findCriticalPath(tasks):
    # Longest path through dependency graph
    # Use dynamic programming on topologically sorted tasks

    topo = topologicalSort(tasks)
    dist = {}  # distance to each node
    prev = {}  # previous node in longest path

    FOR task IN topo:
        dist[task.id] = 0
        FOR dep IN task.dependencies:
            IF dist[dep] + 1 > dist[task.id]:
                dist[task.id] = dist[dep] + 1
                prev[task.id] = dep

    # Find endpoint with max distance
    endpoint = maxBy(tasks, t => dist[t.id])

    # Trace back to build path
    path = [endpoint.id]
    current = endpoint.id
    WHILE prev[current]:
        path.unshift(prev[current])
        current = prev[current]

    RETURN path


FUNCTION findParallelizable(tasks):
    # Tasks that can run now (dependencies met, status pending)
    ready = tasks.filter(t =>
        t.status == 'pending' AND
        t.dependencies.every(d => getTask(d).status == 'completed')
    )
    RETURN ready
```

### Graph Examples

**Simple Linear:**
```
[001]✓ ──► [002]◐ ──► [003]○ ──► [004]○
```

**Fork and Join:**
```
         ┌──► [002]✓ ──┐
[001]✓ ──┤             ├──► [004]○
         └──► [003]◐ ──┘
```

**Complex Dependencies:**
```
[001]✓ ─┬──► [003]✓ ──┬──► [006]○ ──┐
        │             │             │
[002]✓ ─┼──► [004]◐ ──┤             ├──► [008]○
        │             │             │
        └──► [005]○ ──┴──► [007]○ ──┘
```

---

## /progress agents

List all running and recently completed agents from the current session.

Read from `.claude/session_state.md` (running_agents section).

```
═══════════════════════════════════════════════════════════
AGENT STATUS
═══════════════════════════════════════════════════════════

RUNNING (2)
  agent-abc123  Task 004: Implement auth middleware    2m 34s
  agent-def456  Task 007: Write unit tests             45s

COMPLETED THIS SESSION (3)
  agent-xyz789  Task 003: Design data models      ✓    3m 12s
  agent-uvw321  Task 002: Set up project          ✓    1m 45s
  agent-rst654  Task 001: Initialize structure    ✓    0m 38s

═══════════════════════════════════════════════════════════
Usage: /progress <agent-id> to see last agent output
═══════════════════════════════════════════════════════════
```

**Implementation:**
1. Read `session_state.md` for `running_agents` and `completed_agents` arrays
2. For running agents, use `AgentOutputTool(agentId, block=false)` to check status
3. Display agent ID, task reference, and elapsed time

---

## /progress <agent-id>

Show detailed status and last output from a specific agent.

```
═══════════════════════════════════════════════════════════
AGENT: agent-abc123
═══════════════════════════════════════════════════════════

Task:     004 - Implement auth middleware
Model:    sonnet
Skills:   authentication, security
Started:  2m 34s ago
Status:   running

LAST OUTPUT (12s ago)
───────────────────────────────────────────────────────────
Created src/middleware/auth.ts with JWT validation.
Now implementing refresh token logic...

Reading src/config/auth.config.ts for token expiry settings.
───────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════
```

**Implementation:**
1. Look up agent-id in `session_state.md`
2. Call `AgentOutputTool(agentId, block=false)` to get latest output
3. Truncate output to last ~500 characters if longer
4. Display agent metadata and output

**For completed agents:**
```
═══════════════════════════════════════════════════════════
AGENT: agent-xyz789 (completed)
═══════════════════════════════════════════════════════════

Task:      003 - Design data models
Model:     sonnet
Skills:    database_designer
Duration:  3m 12s
Outcome:   completed

FINAL OUTPUT
───────────────────────────────────────────────────────────
✓ Created src/models/User.ts
✓ Created src/models/Transaction.ts
✓ Created src/models/Category.ts
✓ Updated src/types/index.ts with exports

All acceptance criteria met. Models follow TypeScript
strict mode with full type coverage.
───────────────────────────────────────────────────────────

See: .claude/journal/task-003-design-data-models.md
═══════════════════════════════════════════════════════════
```

---

## /progress metrics

Show performance metrics, token usage, and cost estimates.

Read from `.claude/metrics.json`.

```
═══════════════════════════════════════════════════════════
PERFORMANCE METRICS
═══════════════════════════════════════════════════════════

SESSION
  ID:       2025-12-11-001
  Started:  2h 15m ago
  Project:  Personal Finance Dashboard

───────────────────────────────────────────────────────────
BY MODEL
───────────────────────────────────────────────────────────

  Model    Tasks  Success  Avg Time   Tokens (in/out)
  ───────────────────────────────────────────────────────
  Haiku      5    100%      42s        15K / 10K
  Sonnet    10     90%      85s        80K / 40K
  Opus       0      -        -          -

───────────────────────────────────────────────────────────
BY SKILL (top 5 by usage)
───────────────────────────────────────────────────────────

  Skill               Used  Success Rate
  ───────────────────────────────────────────────────────
  frontend_design       4     100% (4/4)
  authentication        2      50% (1/2)
  data_visualization    2     100% (2/2)
  database_designer     2     100% (2/2)
  qa_agent              1     100% (1/1)

───────────────────────────────────────────────────────────
BY TASK TYPE
───────────────────────────────────────────────────────────

  Type            Count  Success  Avg Time
  ───────────────────────────────────────────────────────
  implementation     8     88%     1m 12s
  design             3    100%       48s
  testing            2    100%     2m 05s
  documentation      2    100%       35s

───────────────────────────────────────────────────────────
TOTALS
───────────────────────────────────────────────────────────

  Tasks Completed:    14/15 (93%)
  Tasks Retried:      1 (1 retry total)
  Total Duration:     2h 15m

  Tokens Used:        145,000
    Input:            95,000
    Output:           50,000

  Estimated Cost:     ~$2.47
    Haiku:            $0.04
    Sonnet:           $1.93
    Opus:             $0.50

═══════════════════════════════════════════════════════════
```

**Implementation:**
1. Read `.claude/metrics.json`
2. Format aggregates into tables
3. Calculate derived values (avg time, success rate)
4. Sort skills by usage count

**If No Metrics:**
```
═══════════════════════════════════════════════════════════
NO METRICS AVAILABLE
═══════════════════════════════════════════════════════════

No performance metrics recorded yet.
Metrics are collected after tasks complete.

Run /orchestrate to begin and metrics will accumulate.

═══════════════════════════════════════════════════════════
```

---

## Error States

### If No State Exists

```
═══════════════════════════════════════════════════════════
NO ORCHESTRATOR STATE FOUND
═══════════════════════════════════════════════════════════

No orchestrator state exists for this project.
Run /orchestrate to initialize.

═══════════════════════════════════════════════════════════
```

### If Agent Not Found

```
═══════════════════════════════════════════════════════════
AGENT NOT FOUND
═══════════════════════════════════════════════════════════

No agent with ID "agent-invalid" found in this session.

Run /progress agents to see available agents.

═══════════════════════════════════════════════════════════
```

---

*Command Version: 2.0*
*Merged from /status and /tasks commands*
*Avoids conflict with Claude Code built-in /status command*
