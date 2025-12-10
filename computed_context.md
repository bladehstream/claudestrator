# Computed Context System

## Overview

Context is **computed fresh for each agent call**, not accumulated blindly. Every LLM invocation receives a minimal, relevant projection of the durable state.

**Principle**: "The prompt is not the agent. The state—how actions are stored, transformed, filtered, reused—is the entire difference between a toy demo and something that handles real work."

---

## Core Concept

### Before: Accumulated Context

```
Agent receives:
- Full journal index
- All completed task summaries
- Complete context map
- All learned patterns
→ Context bloat, signal dilution
```

### After: Computed Context

```
Agent receives:
- Task-specific slice of knowledge graph
- Relevant patterns matching task keywords
- Only dependencies' handoffs, not full history
- Filtered context map by component relevance
→ Minimal, focused context
```

---

## Context Computation Pipeline

### Phase 1: Extract Task Signals

```
FUNCTION extractTaskSignals(task):
    signals = {
        keywords: [],
        domains: [],
        files_mentioned: [],
        task_types: []
    }

    # Parse objective and criteria
    text = task.objective + " " + task.acceptance_criteria.join(" ")

    # Extract keywords (nouns, technical terms)
    signals.keywords = EXTRACT_KEYWORDS(text)
        .FILTER(word => NOT_STOPWORD(word))
        .MAP(word => word.toLowerCase())

    # Identify domains from keywords
    DOMAIN_MAPPING = {
        "api": ["endpoint", "rest", "graphql", "route", "request"],
        "auth": ["login", "token", "jwt", "session", "password"],
        "database": ["query", "schema", "migration", "model", "record"],
        "ui": ["component", "button", "form", "page", "style"],
        "testing": ["test", "spec", "mock", "assert", "coverage"]
    }

    FOR domain, triggers IN DOMAIN_MAPPING:
        IF signals.keywords INTERSECTS triggers:
            signals.domains.APPEND(domain)

    # Extract file references from objective
    signals.files_mentioned = EXTRACT_PATHS(text)

    # Task type from metadata
    signals.task_types = [task.type]

    RETURN signals
```

### Phase 2: Query Knowledge Graph

```
FUNCTION queryRelevantKnowledge(signals, limit=15):
    results = {
        patterns: [],
        gotchas: [],
        decisions: [],
        related_tasks: []
    }

    # Primary query: keywords
    keyword_matches = knowledge_graph.queryByTags(signals.keywords, limit=20)

    # Secondary query: domains
    domain_matches = knowledge_graph.queryByTags(signals.domains, limit=10)

    # Merge and deduplicate
    all_matches = DEDUPE(keyword_matches + domain_matches)

    # Categorize by type
    FOR node IN all_matches:
        SWITCH node.type:
            CASE "pattern":
                results.patterns.APPEND({
                    pattern: node.summary,
                    location: node.file,
                    relevance: node.score
                })
            CASE "gotcha":
                results.gotchas.APPEND({
                    issue: node.summary,
                    severity: node.severity || "medium",
                    relevance: node.score
                })
            CASE "decision":
                results.decisions.APPEND({
                    decision: node.summary,
                    rationale: node.rationale,
                    relevance: node.score
                })
            CASE "task":
                results.related_tasks.APPEND(node.id)

    # Limit by relevance
    results.patterns = results.patterns.SORT_BY(relevance, DESC).TAKE(5)
    results.gotchas = results.gotchas.SORT_BY(relevance, DESC).TAKE(3)
    results.decisions = results.decisions.SORT_BY(relevance, DESC).TAKE(3)
    results.related_tasks = results.related_tasks.TAKE(5)

    RETURN results
```

### Phase 3: Extract Dependency Context

```
FUNCTION extractDependencyContext(task):
    context = []

    FOR dep_id IN task.dependencies:
        dep_task = journal.tasks[dep_id]

        IF dep_task.status != "completed":
            CONTINUE  # Skip incomplete dependencies

        # Parse structured handoff
        handoff = PARSE_YAML(dep_task.handoff)

        context.APPEND({
            task_id: dep_id,
            task_name: dep_task.name,
            summary: dep_task.outcome.summary,

            # From structured handoff
            files_to_read: handoff.dependencies_for_next,
            patterns: handoff.patterns_discovered,
            gotchas: handoff.gotchas.FILTER(g => g.severity != "low"),
            open_questions: handoff.open_questions.FILTER(q => q.blocking)
        })

    RETURN context
```

### Phase 4: Filter Context Map

```
FUNCTION filterContextMap(signals, full_map):
    filtered = []

    FOR entry IN full_map:
        relevance_score = 0

        # Score by keyword match in component/file name
        FOR keyword IN signals.keywords:
            IF entry.component.LOWER().CONTAINS(keyword):
                relevance_score += 2
            IF entry.location.LOWER().CONTAINS(keyword):
                relevance_score += 1

        # Score by domain match
        FOR domain IN signals.domains:
            IF entry.notes.LOWER().CONTAINS(domain):
                relevance_score += 1

        # Score by file mention
        FOR file IN signals.files_mentioned:
            IF entry.location.CONTAINS(file):
                relevance_score += 3

        IF relevance_score > 0:
            filtered.APPEND({
                ...entry,
                relevance: relevance_score
            })

    # Return top entries
    RETURN filtered.SORT_BY(relevance, DESC).TAKE(10)
```

### Phase 5: Compute Final Context

```
FUNCTION computeContext(task):
    # Step 1: Extract signals
    signals = extractTaskSignals(task)

    # Step 2: Query knowledge graph
    knowledge = queryRelevantKnowledge(signals)

    # Step 3: Get dependency context
    dependencies = extractDependencyContext(task)

    # Step 4: Filter context map
    code_refs = filterContextMap(signals, journal.context_map)

    # Step 5: Assemble computed context
    computed = {
        # From knowledge graph (patterns, gotchas, decisions)
        patterns_to_follow: knowledge.patterns,
        warnings: knowledge.gotchas,
        relevant_decisions: knowledge.decisions,

        # From dependencies (handoffs)
        prior_work: dependencies.MAP(d => ({
            task: d.task_name,
            summary: d.summary,
            files_created: d.files_to_read
        })),
        inherited_patterns: dependencies.FLATMAP(d => d.patterns),
        inherited_warnings: dependencies.FLATMAP(d => d.gotchas),
        blocking_questions: dependencies.FLATMAP(d => d.open_questions),

        # From context map
        code_references: code_refs.MAP(r => ({
            file: r.location,
            component: r.component,
            notes: r.notes
        })),

        # Metadata for debugging
        _computed: {
            signals: signals,
            knowledge_nodes_matched: knowledge.patterns.length +
                                    knowledge.gotchas.length +
                                    knowledge.decisions.length,
            dependency_count: dependencies.length,
            context_map_filtered: code_refs.length
        }
    }

    RETURN computed
```

---

## Context Injection Format

### Agent Prompt Context Section

```markdown
## Context (Computed)

### Patterns to Follow
{{#if patterns_to_follow}}
{{#each patterns_to_follow}}
- **{{pattern}}** {{#if location}}(see: {{location}}){{/if}}
{{/each}}
{{else}}
No specific patterns identified for this task.
{{/if}}

### Warnings
{{#if warnings}}
{{#each warnings}}
- ⚠️ **{{severity}}**: {{issue}}
{{/each}}
{{else}}
No known gotchas for this task area.
{{/if}}

### Relevant Decisions
{{#if relevant_decisions}}
{{#each relevant_decisions}}
- {{decision}}
{{/each}}
{{/if}}

### Prior Work
{{#each prior_work}}
#### {{task}}
{{summary}}

**Files Created:**
{{#each files_created}}
- `{{file}}`: {{reason}}
{{/each}}
{{/each}}

### Code References
{{#if code_references}}
| Location | Component | Notes |
|----------|-----------|-------|
{{#each code_references}}
| `{{file}}` | {{component}} | {{notes}} |
{{/each}}
{{else}}
Explore the codebase as needed. No specific references pre-identified.
{{/if}}

### Open Questions (Blocking)
{{#if blocking_questions}}
⚠️ The following questions need resolution:
{{#each blocking_questions}}
- **{{question}}**
  - Context: {{context}}
  - Recommendation: {{recommendation}}
{{/each}}
{{/if}}
```

---

## Context Limits

### By Complexity Level

| Complexity | Max Patterns | Max Gotchas | Max Code Refs | Max Prior Tasks |
|------------|--------------|-------------|---------------|-----------------|
| Easy (Haiku) | 3 | 2 | 5 | 2 |
| Normal (Sonnet) | 5 | 3 | 10 | 4 |
| Complex (Opus) | 10 | 5 | 20 | 8 |

### Enforcement

```
FUNCTION applyContextLimits(computed, complexity):
    limits = CONTEXT_LIMITS[complexity]

    computed.patterns_to_follow = computed.patterns_to_follow.TAKE(limits.max_patterns)
    computed.warnings = computed.warnings.TAKE(limits.max_gotchas)
    computed.code_references = computed.code_references.TAKE(limits.max_code_refs)
    computed.prior_work = computed.prior_work.TAKE(limits.max_prior_tasks)

    RETURN computed
```

---

## Debugging Context Computation

### Context Debug Output

Enable with `DEBUG_CONTEXT=true` in orchestrator config:

```markdown
## Context Debug

### Signals Extracted
- Keywords: [list]
- Domains: [list]
- Files Mentioned: [list]

### Knowledge Graph Query
- Nodes matched: N
- Patterns found: N
- Gotchas found: N
- Decisions found: N

### Dependencies Processed
- Task IDs: [list]
- Patterns inherited: N
- Warnings inherited: N

### Context Map Filtering
- Total entries: N
- Entries after filter: N
- Top relevance score: N
```

---

## Integration Points

### In Protocol (Phase 3.4)

Replace current `gatherContext`:

```
# OLD
context = {
    prior_tasks: task.dependencies.map(summarize),
    code_refs: journal.context_map.filter(relevant)
}

# NEW
context = computeContext(task)
context = applyContextLimits(context, task.complexity)
```

### In Agent Prompt Template

Replace flat context section with computed context format.

### In Post-Execution

```
AFTER agent completes:
    # Extract from structured handoff
    handoff = PARSE_YAML(task.handoff)

    # Update knowledge graph with discovered patterns/gotchas
    FOR pattern IN handoff.patterns_discovered:
        knowledge_graph.addNode({
            type: "pattern",
            tags: pattern.applies_to,
            summary: pattern.pattern,
            file: pattern.location
        })

    # Context map grows based on files created/modified
    FOR file IN handoff.files_created + handoff.files_modified:
        journal.context_map.UPDATE_OR_ADD({
            component: INFER_COMPONENT(file.path),
            location: file.path + ":" + file.lines,
            notes: file.purpose || file.description
        })
```

---

## Benefits

1. **Token Efficiency**: Agent receives ~500-2000 tokens of context vs 5000+ with blind accumulation
2. **Signal Clarity**: Only relevant patterns/gotchas, not entire history
3. **Debuggability**: Can inspect exactly what context was computed and why
4. **Scalability**: Context size doesn't grow linearly with project size
5. **Relevance**: Keyword-based filtering surfaces what matters for this specific task

---

*Computed Context System Version: 1.0*
