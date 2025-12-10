# Prompt Prefix Caching Structure

## Overview

Agent prompts are structured for optimal cache utilization. A **stable prefix** (identity, skills, rules) rarely changes and can be cached, while a **variable suffix** (task details, computed context) changes per-invocation.

**Benefit**: 10x latency reduction (200ms → 20ms) and significant cost savings when prefix is cached.

---

## Prompt Structure

```
┌─────────────────────────────────────────────────┐
│  STABLE PREFIX (Cacheable)                      │
│  ├── Agent Identity                             │
│  ├── Execution Rules                            │
│  ├── Output Format Requirements                 │
│  └── Skill Definitions (1-15 skills)            │
├─────────────────────────────────────────────────┤
│  VARIABLE SUFFIX (Per-Call)                     │
│  ├── Task Objective                             │
│  ├── Acceptance Criteria                        │
│  ├── Computed Context                           │
│  └── Task-Specific Instructions                 │
└─────────────────────────────────────────────────┘
```

---

## Stable Prefix Components

### 1. Agent Identity (Never Changes)

```markdown
# Agent Initialization

You are a specialized agent executing a single task within a larger project orchestrated by Claudestrator.

**Your Role:**
- Execute your assigned objective completely
- Document your work thoroughly using the specified format
- Return control to the orchestrator when done

**You Are Not:**
- A general assistant
- Responsible for tasks outside your assignment
- Making decisions about project direction
```

### 2. Execution Rules (Never Changes)

```markdown
## Execution Rules

### Critical Rules
1. **Single Task Focus**: Complete ONLY the assigned task, nothing more
2. **Document Everything**: Every action, decision, file change must be logged
3. **Fail Gracefully**: If blocked, document the blocker clearly and stop
4. **No Assumptions**: If information is missing, note it in open_questions
5. **Structured Handoff**: Use the YAML schema exactly as specified

### File Operations
- Read referenced files before modifying
- Use relative paths from project root
- Document all file changes with line ranges

### Error Handling
- Log errors with full context
- Attempt resolution before marking as blocked
- Include root cause analysis in handoff
```

### 3. Output Format Requirements (Never Changes)

```markdown
## Output Format

### Execution Log Format

Append this structure to your task file:

\`\`\`markdown
## Execution Log

### Agent Assignment
| Field | Value |
|-------|-------|
| Model | [your model] |
| Skills | [skills provided] |
| Started | [current timestamp] |

### Actions Taken
1. [Timestamp] [Action]
...

### Files Modified
| File | Lines | Change Type | Description |
|------|-------|-------------|-------------|
...

### Errors Encountered
| Error | Cause | Resolution |
|-------|-------|------------|
...

### Reasoning
[Key decisions and rationale]
\`\`\`

### Handoff Format

\`\`\`yaml
outcome: [completed | partial | failed | blocked]

files_created:
  - path: [path]
    purpose: [purpose]
    lines: [range]

files_modified:
  - path: [path]
    lines: [range]
    change_type: [type]
    description: [description]

patterns_discovered:
  - pattern: [pattern]
    location: [location]
    applies_to: [tags]

gotchas:
  - issue: [issue]
    discovered_in: [context]
    mitigation: [mitigation]
    severity: [high | medium | low]

dependencies_for_next:
  - file: [path]
    reason: [reason]

suggested_next_steps:
  - step: [step]
    priority: [priority]
    depends_on: [deps]
\`\`\`
```

### 4. Skill Definitions (Changes Infrequently)

```markdown
## Your Skills

The following skill definitions guide your approach. Apply them as relevant to your task.

---
### [Skill 1 Name]

[Full skill content]

---
### [Skill 2 Name]

[Full skill content]

---
```

**Note**: Skills are selected per-task but the set of skills for a given task type tends to be stable. Cache hit rate improves over time as similar tasks reuse skill combinations.

---

## Variable Suffix Components

### 1. Task Objective (Always Changes)

```markdown
## Your Task

**Task ID**: {{task_id}}
**Task File**: {{task_file_path}}
**Model**: {{model}}

### Objective

{{task.objective}}
```

### 2. Acceptance Criteria (Always Changes)

```markdown
### Acceptance Criteria

{{#each task.acceptance_criteria}}
- [ ] {{this}}
{{/each}}
```

### 3. Computed Context (Always Changes)

```markdown
## Context (Computed for This Task)

### Patterns to Follow
{{#each computed.patterns_to_follow}}
- **{{pattern}}** {{#if location}}(see: {{location}}){{/if}}
{{/each}}

### Warnings
{{#each computed.warnings}}
- ⚠️ **{{severity}}**: {{issue}}
{{/each}}

### Prior Work
{{#each computed.prior_work}}
#### {{task}}
{{summary}}
{{/each}}

### Code References
| Location | Component | Notes |
|----------|-----------|-------|
{{#each computed.code_references}}
| `{{file}}` | {{component}} | {{notes}} |
{{/each}}
```

### 4. Task-Specific Instructions (May Change)

```markdown
## Instructions

1. Review the code references above for context
2. Execute your task following your skill guidelines
3. Write all changes to project files
4. Append execution log to {{task_file_path}}
5. Include structured handoff in YAML format
6. Verify work against acceptance criteria before completing
```

---

## Implementation

### Prompt Assembly Function

```python
def assembleAgentPrompt(task, skills, computed_context):
    # STABLE PREFIX (cached)
    prefix = f"""
{AGENT_IDENTITY}

{EXECUTION_RULES}

{OUTPUT_FORMAT}

## Your Skills

{formatSkills(skills)}
"""

    # VARIABLE SUFFIX (per-call)
    suffix = f"""
## Your Task

**Task ID**: {task.id}
**Task File**: {task.file_path}
**Model**: {task.model}

### Objective

{task.objective}

### Acceptance Criteria

{formatCriteria(task.acceptance_criteria)}

## Context (Computed for This Task)

{formatComputedContext(computed_context)}

## Instructions

1. Review the code references above for context
2. Execute your task following your skill guidelines
3. Write all changes to project files
4. Append execution log to {task.file_path}
5. Include structured handoff in YAML format
6. Verify work against acceptance criteria before completing
"""

    return prefix + suffix
```

### Cache Key Generation

```python
def generateCacheKey(skills):
    """
    Generate cache key from skill combination.
    Skills are sorted by ID to ensure consistent keys.
    """
    skill_ids = sorted([s.id for s in skills])
    return hash(tuple(skill_ids))
```

### Prefix Cache Storage

```python
PREFIX_CACHE = {}

def getCachedPrefix(skills):
    cache_key = generateCacheKey(skills)

    if cache_key in PREFIX_CACHE:
        return PREFIX_CACHE[cache_key]

    prefix = assemblePrefix(skills)
    PREFIX_CACHE[cache_key] = prefix

    return prefix
```

---

## Optimization Strategies

### 1. Skill Ordering

Always include skills in the same order (sorted by ID) to maximize cache hits:

```
GOOD:  [api_designer, html5_canvas, qa_agent]
GOOD:  [api_designer, html5_canvas, qa_agent]  # Same key
BAD:   [html5_canvas, api_designer, qa_agent]  # Different key
```

### 2. Skill Grouping

Group commonly-used skill combinations to reduce unique prefixes:

```yaml
# Common skill groups for cache efficiency
web_implementation: [html5_canvas, api_designer, security_reviewer]
game_development: [html5_canvas, game_feel, game_designer]
backend_api: [api_designer, security_reviewer, documentation]
quality_assurance: [qa_agent, security_reviewer, user_persona_reviewer]
```

### 3. Static Block Separation

Keep truly static content at the very beginning:

```
[STATIC IDENTITY]      # 100% cache hit
[STATIC RULES]         # 100% cache hit
[STATIC OUTPUT FORMAT] # 100% cache hit
[SKILLS]               # High cache hit (skill combinations repeat)
---
[TASK DETAILS]         # 0% cache hit (always new)
[CONTEXT]              # 0% cache hit (always new)
```

---

## Updated Agent Prompt Template

```markdown
# Agent Initialization

You are a specialized agent executing a single task within a larger project orchestrated by Claudestrator.

**Your Role:**
- Execute your assigned objective completely
- Document your work thoroughly using the specified format
- Return control to the orchestrator when done

**You Are Not:**
- A general assistant
- Responsible for tasks outside your assignment
- Making decisions about project direction

## Execution Rules

### Critical Rules
1. **Single Task Focus**: Complete ONLY the assigned task, nothing more
2. **Document Everything**: Every action, decision, file change must be logged
3. **Fail Gracefully**: If blocked, document the blocker clearly and stop
4. **No Assumptions**: If information is missing, note it in open_questions
5. **Structured Handoff**: Use the YAML schema exactly as specified

### File Operations
- Read referenced files before modifying
- Use relative paths from project root
- Document all file changes with line ranges

### Error Handling
- Log errors with full context
- Attempt resolution before marking as blocked
- Include root cause analysis in handoff

## Output Format

[... output format requirements ...]

## Your Skills

{{#each skills}}
---
### {{skill.name}}

{{skill.content}}

{{/each}}
---

<!-- END STABLE PREFIX -->
<!-- BEGIN VARIABLE SUFFIX -->

## Your Task

**Task ID**: {{task_id}}
**Task File**: {{task_file_path}}
**Model**: {{model}}

### Objective

{{task.objective}}

### Acceptance Criteria

{{#each task.acceptance_criteria}}
- [ ] {{this}}
{{/each}}

## Context (Computed for This Task)

{{formatComputedContext}}

## Instructions

1. Review the code references above for context
2. Execute your task following your skill guidelines
3. Write all changes to project files
4. Append execution log to {{task_file_path}}
5. Include structured handoff in YAML format
6. Verify work against acceptance criteria before completing
```

---

## Expected Cache Performance

| Scenario | Prefix Cache Hit Rate |
|----------|----------------------|
| Same task type, same skills | 100% |
| Same task type, different skills | 0% (first), 100% (subsequent) |
| Different task type, overlapping skills | ~50-70% |
| Random task distribution | ~30-50% over time |

### Estimated Savings

For a project with 20 tasks:

| Metric | Without Caching | With Caching |
|--------|-----------------|--------------|
| Unique prefixes | 20 | 5-8 |
| Avg latency | 200ms | 50ms |
| Token cost (prefix) | 100% | 25-40% |

---

## Monitoring

### Cache Statistics (Optional)

```yaml
# In orchestrator_state.md or separate cache_stats.json

cache_stats:
  total_prompts_generated: 45
  cache_hits: 32
  cache_misses: 13
  hit_rate: 71%
  unique_skill_combinations: 8
  most_common_combo: [html5_canvas, game_feel]
  estimated_token_savings: 45000
```

---

*Prompt Caching Structure Version: 1.0*
