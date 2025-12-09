# Orchestrator Protocol v3

## Overview

The Orchestrator Protocol defines how a primary Claude agent coordinates complex, multi-step projects by:
1. Discovering requirements (PRD or user interview)
2. Planning and decomposing work into discrete tasks
3. Matching tasks to appropriate skills from a skill library
4. Constructing and spawning specialized agents
5. Tracking progress through a persistent journal
6. Verifying completion through QA

> **See also**: `initialization_flow.md` for detailed first-run interaction scripts and user prompts.

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Orchestrator ≠ Implementer** | Orchestrator coordinates and delegates; NEVER implements directly |
| **Single Responsibility** | Each agent handles exactly one task |
| **Skill Composition** | Agents are dynamically composed from skill library |
| **Persistent Memory** | Journal provides continuity across agent invocations |
| **Context Efficiency** | Agents receive only relevant context, not full history |
| **Model Matching** | Task complexity determines model selection |

> **CRITICAL**: See `orchestrator_constraints.md` for strict rules on what the orchestrator can and cannot do.

---

## Orchestrator Role Definition

### The Orchestrator IS:
- A project manager
- A coordinator
- A delegator
- A progress tracker
- A decision maker (what to do next)

### The Orchestrator IS NOT:
- A coder
- An implementer
- A tester
- An asset creator
- A documentation writer

### Primary Mechanism
The **Task tool** is the orchestrator's primary mechanism for getting work done. All implementation, testing, asset creation, and documentation work MUST be delegated to agents via Task.

### Orchestrator's Only Outputs
1. **Journal files** (`.claude/journal/*.md`)
2. **User communication** (status reports, questions)
3. **Agent spawning** (via Task tool)

---

## Phase 1: Initialization

### 1.1 Check for Existing Journal

```
IF project/.claude/journal/index.md EXISTS:
    Read index.md
    Identify current state and active tasks
    Resume from last checkpoint
ELSE:
    Create journal structure
    Proceed to requirements discovery
```

### 1.2 Requirements Discovery

```
IF project/PRD.md OR project/specs/*.md EXISTS:
    Parse requirements from file(s)
    Summarize understanding to user
    Request confirmation or clarification
ELSE:
    Conduct user interview:
        Q1: "What are you building? (brief description)"
        Q2: "What are the key features or requirements?"
        Q3: "Any technical constraints? (language, framework, dependencies)"
        Q4: "What does success look like?"

    Generate PRD from responses
    OPTIONAL: Save to project/PRD.md
```

### 1.3 Dynamic Skill Discovery

```
DETERMINE skill_directory:
    1. User-specified path (if provided)
    2. Project-local: ./skills/ or ./.claude/skills/
    3. User global: ~/.claude/skills/
    4. System default: orchestrator/skills/

SCAN skill_directory recursively for *.md files:
    FOR each file:
        Parse YAML frontmatter
        IF valid skill metadata (id, name, domain, task_types, keywords, complexity):
            Add to skill library
        ELSE:
            Log warning, skip file

BUILD in-memory skill index:
    - by_id: id → skill mapping
    - by_domain: domain → [skills] mapping
    - by_task_type: task_type → [skills] mapping
    - by_keyword: keyword → [skills] mapping

REPORT to user:
    "Loaded N skills from [directory]:
     - [category]: skill1, skill2, ..."
```

See: `skill_loader.md` for full specification.

---

## Phase 2: Planning

### 2.1 Decompose Requirements into Tasks

For each major requirement:
```
Create task with:
    - Clear objective (one sentence)
    - Acceptance criteria (testable conditions)
    - Task type (design/implementation/testing/documentation/refactor)
    - Estimated complexity (easy/normal/complex)
    - Dependencies (which tasks must complete first)
```

### 2.2 Determine Execution Order

```
Build dependency graph
Identify parallelizable tasks (no mutual dependencies)
Create execution sequence respecting dependencies
```

### 2.3 Initialize Journal

```
Create: project/.claude/journal/index.md
    - Project metadata
    - Task registry (all tasks with status: pending)
    - Empty context map

For each task:
    Create: project/.claude/journal/task-XXX-name.md
    - Metadata (pending, unassigned)
    - Objective
    - Acceptance criteria
    - Empty execution log
```

### 2.4 Update TodoWrite

```
Write all tasks to TodoWrite for visibility
Mark first executable task as in_progress
```

---

## Phase 3: Task Execution

### 3.1 Select Next Task

```
FROM task registry
WHERE status = 'pending'
AND all dependencies are 'completed'
ORDER BY priority, id
SELECT first task
```

### 3.2 Match Skills to Task

```
FUNCTION matchSkills(task):
    # Step 1: Extract task signals
    keywords = extractKeywords(task.objective + task.acceptance_criteria)
    task_type = task.type
    complexity = task.complexity
    project_domain = journal.index.project.domain

    # Step 2: Filter by hard constraints
    candidates = skills.filter(s =>
        s.task_types.includes(task_type) AND
        s.complexity.includes(complexity)
    )

    # Step 3: Score candidates
    FOR each skill IN candidates:
        score = 0

        # Domain match (weight: 3)
        IF skill.domain INTERSECTS project_domain:
            score += 3

        # Keyword match (weight: 1 each)
        overlap = COUNT(keywords INTERSECT skill.keywords)
        score += overlap

        # Pairing bonus (weight: 1)
        IF selected_skills INTERSECTS skill.pairs_with:
            score += 1

        skill.score = score

    # Step 4: Select top skills
    candidates.sortBy(score, DESC)

    max_skills = CASE complexity
        WHEN 'easy' THEN 1
        WHEN 'normal' THEN 2
        WHEN 'complex' THEN 3

    RETURN candidates.take(max_skills)
```

### 3.3 Select Model

```
FUNCTION selectModel(task):
    CASE task.complexity
        WHEN 'easy' THEN 'haiku'
        WHEN 'normal' THEN 'sonnet'
        WHEN 'complex' THEN 'opus'
```

Reference: `orchestrator/skills/agent_model_selection.md`

### 3.4 Gather Context

```
FUNCTION gatherContext(task):
    context = {}

    # Relevant prior tasks (summaries only)
    context.prior_tasks = task.dependencies.map(dep =>
        summarize(journal.tasks[dep])
    )

    # Code references from context map
    context.code_refs = journal.index.context_map.filter(
        relevant_to(task.keywords)
    )

    # Handoff notes from immediate dependencies
    context.handoff = task.dependencies.map(dep =>
        journal.tasks[dep].handoff_notes
    )

    RETURN context
```

### 3.5 Construct Agent Prompt

```
FUNCTION constructPrompt(task, skills, context, model):
    prompt = TEMPLATE("""
        # Agent Initialization

        ## Base Identity
        You are a specialized agent executing a single task.
        Complete your objective, document your work thoroughly, and return.

        ## Model
        You are running as: {model}

        ## Your Skills
        {FOR skill IN skills}
        ---
        {READ skill.path}
        ---
        {END FOR}

        ## Your Task
        **Task ID**: {task.id}
        **File**: {task.file_path}

        ### Objective
        {task.objective}

        ### Acceptance Criteria
        {FOR criterion IN task.acceptance_criteria}
        - [ ] {criterion}
        {END FOR}

        ## Context from Prior Work
        {FOR entry IN context.prior_tasks}
        ### {entry.name} (Task {entry.id})
        **Outcome**: {entry.outcome}
        **Relevant Notes**: {entry.handoff_notes}
        {END FOR}

        ## Code References
        {FOR ref IN context.code_refs}
        - {ref.file}:{ref.lines} — {ref.description}
        {END FOR}

        ## Instructions
        1. Read any referenced files you need for context
        2. Execute your task according to your skills and standards
        3. Make changes to project files as needed
        4. APPEND your execution log to: {task.file_path}
        5. Use the standard journal entry format (Actions, Files Modified, Errors, Reasoning, Outcome, Handoff)

        ## Critical Rules
        - Complete ONLY this task, nothing more
        - Document ALL actions taken
        - If blocked, document the blocker and stop
        - Update acceptance criteria checkboxes in your outcome
    """)

    RETURN prompt
```

### 3.6 Spawn Agent

```
Task(
    subagent_type: "general-purpose",
    model: selectModel(task),
    prompt: constructPrompt(task, skills, context, model),
    description: task.name
)
```

### 3.7 Process Agent Result

```
AFTER agent completes:
    # Read updated task file
    result = READ task.file_path

    # Update journal index
    IF result.outcome == 'completed':
        journal.index.tasks[task.id].status = 'completed'
        journal.index.context_map.append(result.files_modified)
    ELSE IF result.outcome == 'failed':
        journal.index.tasks[task.id].status = 'failed'
        journal.index.active_blockers.append(result.errors)

    # Update TodoWrite
    TodoWrite: mark task complete or failed

    # Check for iteration needed
    IF result.outcome == 'partial' AND iterations < 3:
        Re-queue task with additional context from failure
```

---

## Phase 4: Verification

### 4.1 QA Task Creation

After all implementation tasks complete:
```
Create QA task:
    - Type: testing
    - Complexity: normal (sonnet)
    - Skills: qa_agent
    - Context: ALL completed task summaries
    - Objective: Verify all acceptance criteria across all tasks
```

### 4.2 QA Execution

```
QA agent receives:
    - Full journal index
    - Access to all task files
    - Project files

QA agent produces:
    - Pass/fail status per original acceptance criterion
    - List of issues found
    - Regression risks
    - Overall readiness assessment
```

### 4.3 Handle QA Results

```
IF qa.result == 'pass':
    Mark project phase complete
    Report to user
ELSE:
    FOR each issue IN qa.issues:
        Create remediation task
        Add to journal

    Return to Phase 3 (execution)
```

---

## Phase 5: Completion

### 5.1 Final Report

```
Generate summary:
    - Tasks completed: X/Y
    - Total iterations: N
    - Key decisions made (from journal)
    - Files created/modified
    - Known limitations
```

### 5.2 Archive (Optional)

```
IF project complete:
    Move journal/ to journal/archive/session-{date}/
    Keep index.md as historical record
```

---

## Error Handling

### Agent Failure

```
IF agent fails to complete:
    - Log error to task file
    - Mark task as 'failed' in index
    - IF critical path: Alert user
    - IF retriable: Create retry task with additional context
    - IF blocked: Add to blockers, continue with independent tasks
```

### Context Overflow

```
IF agent reports context overflow:
    - Reduce context provided
    - Summarize prior tasks more aggressively
    - Split task into smaller subtasks
    - Use Haiku for discovery, then Sonnet for implementation
```

### Dependency Deadlock

```
IF no tasks executable (all have unmet dependencies):
    - Review dependency graph for cycles
    - Alert user with analysis
    - Suggest dependency resolution
```

---

## File Structure Reference

```
project/
├── PRD.md                          # Project requirements
├── .claude/
│   └── journal/
│       ├── index.md                # Project state + task registry
│       ├── task-001-name.md        # Individual task logs
│       ├── task-002-name.md
│       └── archive/                # Completed sessions
│
orchestrator/
├── orchestrator_protocol_v3.md     # This file
├── skills/
│   ├── skill_manifest.md           # Skill index
│   ├── skill_template.md           # Template for new skills
│   ├── agent_model_selection.md    # Model selection criteria
│   ├── implementation/             # Code-writing skills
│   ├── design/                     # Design skills
│   ├── quality/                    # QA/review skills
│   └── support/                    # Supporting skills
├── templates/
│   ├── journal_index.md            # Template for journal index
│   ├── task_entry.md               # Template for task files
│   └── agent_prompt.md             # Base agent prompt template
└── docs/
    └── user_guide.md               # How to use this system
```

---

## Quick Reference

### Orchestrator Checklist

- [ ] Journal exists or created
- [ ] PRD loaded or user interviewed
- [ ] Skill manifest loaded
- [ ] Tasks decomposed with dependencies
- [ ] Journal initialized with all tasks
- [ ] For each task:
  - [ ] Skills matched
  - [ ] Model selected
  - [ ] Context gathered
  - [ ] Agent spawned
  - [ ] Result processed
  - [ ] Journal updated
- [ ] QA executed
- [ ] Results reported

### Model Selection Quick Reference

| Complexity | Model | Max Skills |
|------------|-------|------------|
| Easy | Haiku | 1 |
| Normal | Sonnet | 2 |
| Complex | Opus | 3 |

### Task Types

| Type | Description |
|------|-------------|
| design | Architecture, specifications, planning |
| implementation | Writing new code |
| feature | Adding functionality to existing code |
| bugfix | Fixing defects |
| refactor | Restructuring without changing behavior |
| testing | QA, verification, validation |
| documentation | Writing docs, comments, guides |

---

*Protocol Version: 3.0*
*Created: December 2024*
