# Knowledge Graph System

## Overview

The knowledge graph provides **tag-based retrieval** of project knowledge, enabling the orchestrator to find relevant context without reading every file. This follows the A-MEM principle: "Flat logs are unsearchable. Effective memory requires evolution and linkage."

---

## Architecture

```
project/.orchestrator/
├── knowledge_graph.json      # Tag-based index for retrieval
├── memories/                 # Episodic memory entries
│   ├── YYYY-MM-DD-topic.md   # Individual insights/decisions
│   └── ...
├── session_state.md          # Hot: Working memory
├── orchestrator_memory.md    # Cold: Long-term memory
└── journal/                  # Task execution logs
```

---

## Knowledge Graph Schema

### File: `.orchestrator/knowledge_graph.json`

```json
{
  "version": 1,
  "last_updated": "2024-12-10T14:30:00Z",
  "nodes": [
    {
      "id": "task-001",
      "type": "task",
      "tags": ["auth", "api", "jwt"],
      "summary": "Implemented JWT authentication flow",
      "file": "journal/task-001-auth.md",
      "created": "2024-12-10",
      "connections": ["decision-001"]
    },
    {
      "id": "decision-001",
      "type": "decision",
      "tags": ["database", "architecture", "postgresql"],
      "summary": "Chose PostgreSQL over SQLite for concurrent write support",
      "file": "memories/2024-12-10-database-choice.md",
      "created": "2024-12-10",
      "connections": ["task-001", "task-005"]
    },
    {
      "id": "pattern-001",
      "type": "pattern",
      "tags": ["error-handling", "api", "convention"],
      "summary": "All API errors use ErrorResponse class with code, message, details",
      "file": null,
      "created": "2024-12-10",
      "connections": []
    },
    {
      "id": "gotcha-001",
      "type": "gotcha",
      "tags": ["rate-limit", "api", "external"],
      "summary": "External payment API rate limit is 100/min, not 1000/min as documented",
      "file": "memories/2024-12-10-payment-rate-limit.md",
      "created": "2024-12-10",
      "connections": ["task-003"]
    }
  ],
  "tag_index": {
    "auth": ["task-001"],
    "api": ["task-001", "pattern-001", "gotcha-001"],
    "database": ["decision-001"],
    "architecture": ["decision-001"],
    "postgresql": ["decision-001"],
    "error-handling": ["pattern-001"],
    "rate-limit": ["gotcha-001"]
  }
}
```

### Node Types

| Type | Purpose | Typical Source |
|------|---------|----------------|
| `task` | Completed work with learnings | Journal task files |
| `decision` | Architectural/design choices | Orchestrator decisions |
| `pattern` | Code conventions observed | Agent handoff notes |
| `gotcha` | Warnings and edge cases | Agent error logs |
| `insight` | General learnings | Session consolidation |

### Node Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (type-NNN or date-based) |
| `type` | Yes | Node type from table above |
| `tags` | Yes | Array of lowercase keywords for retrieval |
| `summary` | Yes | One-sentence description (max 100 chars) |
| `file` | No | Path to detailed content (null if inline) |
| `created` | Yes | ISO date string |
| `connections` | No | Related node IDs (for graph traversal) |

---

## Operations

### Query by Tags

```
FUNCTION queryByTags(tags: string[], limit: number = 10): Node[]
    matching_ids = SET()

    FOR tag IN tags:
        IF tag IN knowledge_graph.tag_index:
            matching_ids.ADD_ALL(tag_index[tag])

    # Score by relevance (number of matching tags)
    scored = []
    FOR id IN matching_ids:
        node = knowledge_graph.nodes[id]
        score = COUNT(tags INTERSECT node.tags)
        scored.APPEND({node, score})

    scored.SORT_BY(score, DESC)
    RETURN scored.TAKE(limit).MAP(s => s.node)
```

### Add Node

```
FUNCTION addNode(node: Node): void
    # Validate required fields
    REQUIRE node.id, node.type, node.tags, node.summary, node.created

    # Add to nodes array
    knowledge_graph.nodes.APPEND(node)

    # Update tag index
    FOR tag IN node.tags:
        IF tag NOT IN tag_index:
            tag_index[tag] = []
        tag_index[tag].APPEND(node.id)

    # Update timestamp
    knowledge_graph.last_updated = NOW()

    # Write to disk
    SAVE knowledge_graph.json
```

### Update Node

```
FUNCTION updateNode(id: string, updates: Partial<Node>): void
    node = knowledge_graph.nodes.FIND(n => n.id == id)
    REQUIRE node EXISTS

    # If tags changed, update tag index
    IF updates.tags:
        # Remove from old tags
        FOR tag IN node.tags:
            tag_index[tag].REMOVE(id)
        # Add to new tags
        FOR tag IN updates.tags:
            IF tag NOT IN tag_index:
                tag_index[tag] = []
            tag_index[tag].APPEND(id)

    # Apply updates
    node.MERGE(updates)

    SAVE knowledge_graph.json
```

### Get Connected Nodes

```
FUNCTION getConnected(id: string, depth: number = 1): Node[]
    visited = SET()
    queue = [id]
    result = []

    FOR level IN 1..depth:
        next_queue = []
        FOR current_id IN queue:
            IF current_id IN visited:
                CONTINUE
            visited.ADD(current_id)

            node = knowledge_graph.nodes.FIND(n => n.id == current_id)
            IF node AND level > 0:  # Don't include starting node
                result.APPEND(node)

            FOR connected_id IN node.connections:
                next_queue.APPEND(connected_id)

        queue = next_queue

    RETURN result
```

---

## Integration with Orchestrator

### On Task Completion

```
AFTER agent completes task:
    # Extract knowledge from task result
    task_result = READ task file

    # Create task node
    task_node = {
        id: task.id,
        type: "task",
        tags: EXTRACT_KEYWORDS(task.objective + task.handoff_notes),
        summary: task_result.summary,
        file: task.file_path,
        created: NOW(),
        connections: task.dependencies
    }
    knowledge_graph.addNode(task_node)

    # Extract patterns from handoff notes
    FOR pattern IN task_result.patterns_discovered:
        pattern_node = {
            id: "pattern-" + GENERATE_ID(),
            type: "pattern",
            tags: EXTRACT_KEYWORDS(pattern),
            summary: pattern,
            file: null,
            created: NOW(),
            connections: [task.id]
        }
        knowledge_graph.addNode(pattern_node)

    # Extract gotchas from errors
    FOR gotcha IN task_result.gotchas:
        gotcha_node = {
            id: "gotcha-" + GENERATE_ID(),
            type: "gotcha",
            tags: EXTRACT_KEYWORDS(gotcha),
            summary: gotcha,
            file: null,
            created: NOW(),
            connections: [task.id]
        }
        knowledge_graph.addNode(gotcha_node)
```

### On Key Decision

```
WHEN orchestrator makes significant decision:
    decision_node = {
        id: "decision-" + GENERATE_ID(),
        type: "decision",
        tags: EXTRACT_KEYWORDS(decision.description),
        summary: decision.description,
        file: CREATE_MEMORY_FILE(decision),  # If detailed
        created: NOW(),
        connections: [current_task.id] IF current_task ELSE []
    }
    knowledge_graph.addNode(decision_node)
```

### Context Gathering (Enhanced)

```
FUNCTION gatherContext(task):
    context = {}

    # Step 1: Extract task keywords
    keywords = EXTRACT_KEYWORDS(task.objective + task.acceptance_criteria)

    # Step 2: Query knowledge graph
    relevant_nodes = knowledge_graph.queryByTags(keywords, limit=10)

    # Step 3: Categorize by type
    context.decisions = relevant_nodes.FILTER(n => n.type == "decision")
    context.patterns = relevant_nodes.FILTER(n => n.type == "pattern")
    context.gotchas = relevant_nodes.FILTER(n => n.type == "gotcha")
    context.related_tasks = relevant_nodes.FILTER(n => n.type == "task")

    # Step 4: Load summaries only (not full files)
    # Full files loaded only if agent requests

    # Step 5: Add dependency context (from journal, as before)
    context.prior_tasks = task.dependencies.MAP(dep =>
        summarize(journal.tasks[dep])
    )

    RETURN context
```

---

## Memory File Format

### File: `.orchestrator/memories/YYYY-MM-DD-topic.md`

```markdown
---
id: decision-001
type: decision
date: 2024-12-10
tags: [database, architecture, postgresql, sqlite]
---

# Decision: Database Selection

## Context
We need a database for the user management system. Expected load: 100 concurrent users, 10k records.

## Options Considered
1. **SQLite** - Simple, no setup, single file
2. **PostgreSQL** - Full ACID, concurrent writes, scalable

## Decision
Chose PostgreSQL.

## Rationale
- SQLite's single-writer lock would bottleneck concurrent user registrations
- PostgreSQL's connection pooling handles our concurrency needs
- Easier to scale horizontally if needed later

## Implications
- Need Docker setup for local dev
- Added `pg` dependency to package.json
- Connection string in `.env.DATABASE_URL`

## Related
- Task 001: User auth implementation
- Task 005: Database migrations
```

---

## Initialization

### On First `/orchestrate`

```
IF NOT EXISTS .orchestrator/knowledge_graph.json:
    CREATE {
        version: 1,
        last_updated: NOW(),
        nodes: [],
        tag_index: {}
    }

IF NOT EXISTS .orchestrator/memories/:
    CREATE DIRECTORY
```

### Migration from Existing Projects

```
IF EXISTS .orchestrator/journal/index.md AND NOT EXISTS knowledge_graph.json:
    # Import existing tasks as nodes
    FOR task IN journal.tasks WHERE status == 'completed':
        READ task file
        CREATE task node from handoff notes

    # Import existing decisions
    FOR decision IN orchestrator_state.key_decisions:
        CREATE decision node

    # Import learned context
    FOR pattern IN orchestrator_state.learned_context.patterns:
        CREATE pattern node
    FOR gotcha IN orchestrator_state.learned_context.gotchas:
        CREATE gotcha node
```

---

## Template: knowledge_graph.json

```json
{
  "version": 1,
  "last_updated": "",
  "nodes": [],
  "tag_index": {}
}
```

---

## Benefits

1. **Token Efficiency**: Query returns summaries, not full content
2. **Relevance Filtering**: Only retrieve what matches task keywords
3. **Cross-Session Learning**: Patterns and gotchas persist across sessions
4. **Debuggability**: Can inspect exactly what knowledge exists
5. **Evolution**: Nodes can be updated as understanding improves

---

*Knowledge Graph System Version: 1.0*
