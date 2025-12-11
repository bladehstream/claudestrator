# /tasks - Show Task List

Display all tasks with their current status and dependency graph.

## Usage

```
/tasks                  Show task list with dependency graph
/tasks --list           Show task list only (no graph)
/tasks --graph          Show dependency graph only
```

## Display Format

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

## Dependency Graph Rendering

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

## Graph Examples

### Simple Linear

```
[001]✓ ──► [002]◐ ──► [003]○ ──► [004]○
```

### Fork and Join

```
         ┌──► [002]✓ ──┐
[001]✓ ──┤             ├──► [004]○
         └──► [003]◐ ──┘
```

### Complex Dependencies

```
[001]✓ ─┬──► [003]✓ ──┬──► [006]○ ──┐
        │             │             │
[002]✓ ─┼──► [004]◐ ──┤             ├──► [008]○
        │             │             │
        └──► [005]○ ──┴──► [007]○ ──┘
```

### With Blocked Task

```
[001]✓ ──► [002]✗ ──► [003]○
           BLOCKED: Waiting for external API key
```

## Task Details

To see details on a specific task, user can ask:
"Show me task 004" or "What's the status of the auth task?"

Then display from `journal/task-004-*.md`:
- Full objective
- Acceptance criteria with status
- Execution log summary
- Any blockers or notes

---

*Command Version: 1.1*
*Added: Dependency graph visualization, critical path analysis*
