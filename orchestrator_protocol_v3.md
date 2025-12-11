# Orchestrator Protocol v3

## Overview

The Orchestrator Protocol defines how a primary Claude agent coordinates complex, multi-step projects by:
1. Loading requirements from PRD
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

### 1.0 Git Status Check

> **See**: [initialization_flow.md](initialization_flow.md) for detailed prompts.

```
IF .git directory EXISTS:
    GIT_ENABLED = true
    Report: "✓ Git repository detected - auto-commits enabled"
ELSE:
    PROMPT user (using AskUserQuestion):
        "No git repository detected. Initialize git?"
        Options: "Yes, initialize" | "No, continue without"

    IF user selects "Yes":
        RUN: git init
        RUN: git add -A
        RUN: git commit -m "Initial commit before orchestration"
        GIT_ENABLED = true
    ELSE:
        GIT_ENABLED = false
        WARN: "Continuing without git - changes won't be tracked"
```

### 1.0.5 Autonomy Selection

> **See**: [initialization_flow.md](initialization_flow.md) for detailed prompts and safety guardrails.

```
PROMPT user (using AskUserQuestion):
    "How much control do you want during orchestration?"
    Options:
        - "Supervised (Recommended)" - Approve each operation
        - "Trust Agents" - Approve once per agent spawn
        - "Full Autonomy" - Auto-approve with safety guardrails

SET AUTONOMY_LEVEL = user_selection

IF AUTONOMY_LEVEL == "Full Autonomy":
    IF .claude/hooks/safe-autonomy.sh EXISTS AND EXECUTABLE:
        Report: "✓ Full Autonomy enabled - safe-autonomy hook active"
    ELSE:
        WARN: "Safe-autonomy hook not found - falling back to Supervised"
        SET AUTONOMY_LEVEL = "Supervised"

STORE in session_state.md:
    autonomy_level: {AUTONOMY_LEVEL}
```

**Autonomy Levels:**

| Level | Behavior |
|-------|----------|
| Supervised | Default - approve each tool operation |
| Trust Agents | Approve per agent spawn, agent runs freely |
| Full Autonomy | Hook auto-approves safe ops, blocks dangerous ones |

**Full Autonomy Safety Guardrails (via safe-autonomy.sh hook):**
- Auto-approve: Read, Edit (in project), git, npm, build commands, Task spawns
- Auto-deny: sudo, rm -rf outside project, curl|bash, system files, .env
- Passthrough: Unknown commands (user prompted)

### 1.1 Check for Existing Journal (Enhanced State Detection)

```
IF project/.claude/journal/index.md EXISTS:
    Read index.md
    DETERMINE project_state:

    CASE 1: Tasks in progress
        IF any task has status == 'in_progress' OR
           any task has status == 'pending' AND dependencies met:
            → Resume execution from current position
            REPORT: "Resuming from task {active_task}..."

    CASE 2: Project complete (all tasks completed)
        IF all tasks have status == 'completed' AND
           index.phase == 'complete':
            → Offer iteration options (using AskUserQuestion)
            PROMPT:
                "✅ Project Complete

                All {X} tasks from the previous run are complete.

                What would you like to do?

                1. Iterate - Review outputs, gather feedback, create improvement tasks
                2. Extend - Add new requirements to the project
                3. Archive - Mark this run complete and start fresh
                "

            IF user selects "Iterate":
                → Enter Phase 6: Iteration
            IF user selects "Extend":
                → Enter Phase 6.2: Extension
            IF user selects "Archive":
                → Archive current run, proceed to Phase 1.2

    CASE 3: Deorchestrated (clean exit, work paused)
        IF index.phase == 'paused' OR
           index.deorchestrated == true:
            → Offer resume options
            PROMPT:
                "📋 Previous Session Found

                Project: {project_name}
                Last active: {last_updated}
                Progress: {X/Y} tasks completed
                Phase: {phase} (paused)

                Resume from where you left off?"

            IF user confirms:
                → Reload context from journal
                → Resume execution

    CASE 4: Failed/blocked state
        IF active_blockers exist OR
           multiple tasks have status == 'failed':
            → Report blockers, offer options
            PROMPT:
                "⚠️ Previous Run Had Issues

                Blockers: {blocker_list}
                Failed tasks: {failed_task_list}

                Options:
                1. Review and retry failed tasks
                2. Skip blockers and continue
                3. Reset and start fresh
                "

ELSE:
    Create journal structure
    Proceed to requirements discovery
```

See [initialization_flow.md](initialization_flow.md) for detailed user prompts.

### 1.2 Requirements Discovery

```
IF project/PRD.md OR project/specs/*.md EXISTS:
    Parse requirements from file(s)
    Summarize understanding to user
    Request confirmation or clarification
ELSE:
    STOP orchestration
    INFORM user:
        "No PRD found. To keep orchestration context clean, please:

        1. Run /prdgen to generate requirements
        2. Run /clear to reset context
        3. Run /orchestrate to begin execution

        This ensures maximum context capacity for project work."
    EXIT
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

> **See**: [skill_loader.md](skill_loader.md) for full matching specification including category deduplication.

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

    # Step 4: Sort by score
    candidates.sortBy(score, DESC)

    # Step 5: Deduplicate by category (NEW in v3.1)
    # Only one skill per category - highest scorer wins
    selected = deduplicateByCategory(candidates)

    # Step 6: Apply max_skills limit
    max_skills = CASE complexity
        WHEN 'easy' THEN 3
        WHEN 'normal' THEN 7
        WHEN 'complex' THEN 15

    RETURN selected.take(max_skills)
```

**Category Deduplication**: Each skill has a `category` field (e.g., `rendering`, `testing`, `security`). Only the highest-scoring skill from each category is selected. This prevents redundant skills (e.g., three different testing skills) while ensuring diversity.

### 3.3 Select Model

```
FUNCTION selectModel(task):
    CASE task.complexity
        WHEN 'easy' THEN 'haiku'
        WHEN 'normal' THEN 'sonnet'
        WHEN 'complex' THEN 'opus'
```

Reference: `orchestrator/skills/agent_model_selection.md`

### 3.4 Gather Context (Computed)

> **See**: [computed_context.md](computed_context.md) for full algorithm specification.

Context is **computed fresh** for each agent call, not accumulated:

```
FUNCTION gatherContext(task):
    # Step 1: Extract task signals
    signals = extractTaskSignals(task)
        → keywords, domains, file mentions

    # Step 2: Query knowledge graph
    knowledge = queryRelevantKnowledge(signals)
        → patterns, gotchas, decisions, related tasks

    # Step 3: Extract dependency context (structured handoffs)
    dependencies = extractDependencyContext(task)
        → summaries, files_to_read, inherited patterns/gotchas

    # Step 4: Filter context map by relevance
    code_refs = filterContextMap(signals, journal.context_map)
        → scored by keyword match, top N by complexity

    # Step 5: Apply limits by complexity
    context = applyContextLimits(computed, task.complexity)
        → Easy: 5 refs, Normal: 10 refs, Complex: 20 refs

    RETURN context
```

Key differences from v1:
- Query knowledge graph by tags, don't load everything
- Parse structured YAML handoffs, not freeform text
- Score and filter context map by relevance
- Enforce limits based on model capacity

### 3.5 Construct Agent Prompt (Cache-Optimized)

> **See**: [prompt_caching.md](prompt_caching.md) for caching strategy.

Prompts are structured for optimal cache utilization:
- **Stable Prefix**: Identity, rules, format, skills (~70% of prompt)
- **Variable Suffix**: Task details, computed context (~30% of prompt)

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

> **Apply**: [skills/orchestrator/agent_construction.md](skills/orchestrator/agent_construction.md) for model selection, skill composition, and context budgeting.

```
# Generate unique agent ID
agent_id = "agent-" + generateShortId()

# Spawn the agent
Task(
    subagent_type: "general-purpose",
    model: selectModel(task),
    prompt: constructPrompt(task, skills, context, model),
    description: task.name
)

# Track agent in session state for /status monitoring
session_state.running_agents.append({
    id: agent_id,
    task_id: task.id,
    task_name: task.name,
    model: selectModel(task),
    skills: matched_skills.map(s => s.id),
    started_at: NOW()
})

WRITE session_state.md
```

**Parallel Agent Spawning:**

When multiple tasks have no interdependencies, spawn them in a single message:

```
independent_tasks = pending_tasks.filter(
    t => t.dependencies.all(d => d.status == 'completed')
)

# Spawn up to MAX_PARALLEL agents in one message
FOR task IN independent_tasks.slice(0, MAX_PARALLEL):
    # Each Task() call in same message runs concurrently
    Task(...)
    session_state.running_agents.append(...)

# All agents run concurrently, orchestrator waits for all to complete
```

**Checking Agent Status (for /status command):**

```
FUNCTION getAgentStatus(agent_id):
    result = AgentOutputTool(agent_id, block=false)
    RETURN {
        status: result.status,  # running | completed | error
        output: result.output.slice(-500)  # Last 500 chars
    }
```

### 3.7 Process Agent Result

> **See**: [handoff_schema.md](handoff_schema.md) for structured handoff format.
> **See**: [strategy_evolution.md](strategy_evolution.md) for feedback processing.

```
AFTER agent completes:
    # Move agent from running to completed in session state
    agent = session_state.running_agents.find(a => a.task_id == task.id)
    session_state.running_agents.remove(agent)
    session_state.completed_agents.append({
        ...agent,
        completed_at: NOW(),
        duration: NOW() - agent.started_at,
        outcome: handoff.outcome,
        final_output: result.slice(-500)  # Store last 500 chars for /status
    })
    WRITE session_state.md

    # Read updated task file
    result = READ task.file_path

    # Parse structured handoff (YAML)
    handoff = PARSE_YAML(result.handoff)

    # Update journal index
    IF handoff.outcome == 'completed':
        journal.index.tasks[task.id].status = 'completed'
        FOR file IN handoff.files_created + handoff.files_modified:
            journal.index.context_map.UPDATE_OR_ADD(file)
    ELSE IF handoff.outcome == 'failed':
        journal.index.tasks[task.id].status = 'failed'
        journal.index.active_blockers.append(handoff.blockers)

    # Update knowledge graph
    FOR pattern IN handoff.patterns_discovered:
        knowledge_graph.addNode({type: "pattern", ...pattern})
    FOR gotcha IN handoff.gotchas:
        knowledge_graph.addNode({type: "gotcha", ...gotcha})

    # Collect feedback for strategy evolution
    feedback = collectExecutionFeedback(task, handoff)
    IF feedback.signals.any():
        updateStrategies(feedback)

    # Update TodoWrite
    TodoWrite: mark task complete or failed

    # Auto-commit if git enabled
    IF GIT_ENABLED AND handoff.outcome == 'completed':
        git add -A
        git commit -m "task-{task.id}: {task.name}

        Completed by {model} agent with skills: {skills_used}

        Files changed:
        {handoff.files_modified}
        {handoff.files_created}

        🤖 Generated with Claudestrator"

    # Check for iteration needed
    IF handoff.outcome == 'partial' AND iterations < 3:
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
    Move journal/ to journal/archive/run-{run_number}/
    Keep index.md as historical record
    Increment run_number in index
```

---

## Phase 6: Iteration

Phase 6 handles post-completion workflows: iterating on feedback or extending with new requirements.

### 6.1 Iteration Mode (Feedback-Driven Improvement)

Entered when user selects "Iterate" from completed project state.

```
ITERATION WORKFLOW:

1. GENERATE SUMMARY
    Compile outputs from previous run:
        - Files created/modified
        - Key features implemented
        - Architecture decisions made
        - Known limitations (from QA feedback)

    PRESENT to user:
        "📊 Previous Run Summary

        Completed tasks: {task_list}
        Files created: {file_list}
        Key features: {feature_summary}

        What would you like to improve or change?"

2. GATHER FEEDBACK
    Using AskUserQuestion + freeform input:

    PROMPT:
        "What aspects need improvement?"
        Options:
          - Performance issues
          - UX/UI improvements
          - Bug fixes noticed during testing
          - Feature enhancements
          - Code quality/refactoring
          - Other (freeform)

    Allow multi-select + freeform details for each selection.

3. DECOMPOSE FEEDBACK INTO TASKS
    For each feedback item:
        - Analyze scope and complexity
        - Create improvement task(s)
        - Link to original tasks (predecessor reference)
        - Estimate complexity

4. VERSION PRD (if substantial changes)
    IF feedback requires significant changes:
        ARCHIVE current PRD:
            cp PRD.md PRD-history/v{N}-{date}.md

        APPEND iteration notes to PRD:
            ## Iteration {N+1} - {date}
            ### Feedback
            {user_feedback}
            ### New Requirements
            {decomposed_requirements}

5. UPDATE JOURNAL
    Create new task entries for improvement items:
        - ID continues from previous run (e.g., 010, 011...)
        - Type: "iteration" or original type
        - Predecessor: link to original task being improved
        - Mark as iteration_run: {N+1}

    Update index.md:
        - Phase: implementation (reset)
        - Iteration: {N+1}
        - Previous runs: append summary

6. EXECUTE ITERATION TASKS
    Return to Phase 3 (Task Execution) with new tasks
```

### 6.2 Extension Mode (New Requirements)

Entered when user selects "Extend" from completed project state.

```
EXTENSION WORKFLOW:

1. PRESENT CONTEXT
    PROMPT:
        "📋 Current Project State

        Project: {name}
        Completed: {X} tasks in {Y} runs
        Current features: {feature_summary}

        What would you like to add?"

2. GATHER NEW REQUIREMENTS
    Options:
        a. Run /prdgen to generate full extension PRD
        b. Describe extension inline (for smaller additions)

    IF inline description:
        - Capture requirements
        - Validate against existing architecture
        - Flag potential conflicts

3. VERSION PRD
    ARCHIVE current PRD:
        cp PRD.md PRD-history/v{N}-{date}.md

    IF full /prdgen:
        Merge new PRD with existing
    ELSE:
        APPEND to PRD:
            ## Extension {N+1} - {date}
            ### New Requirements
            {requirements}

4. DECOMPOSE AND PLAN
    - Analyze new requirements against existing codebase
    - Identify integration points
    - Create tasks for new features
    - Add integration/testing tasks

5. UPDATE JOURNAL
    - Increment run number
    - Add new tasks to registry
    - Mark as extension_run: true

6. EXECUTE
    Return to Phase 3 (Task Execution)
```

### 6.3 Archive and Reset

Entered when user selects "Archive" from completed project state.

```
ARCHIVE WORKFLOW:

1. ARCHIVE CURRENT RUN
    CREATE: journal/archive/run-{N}-{date}/
    MOVE: All task-*.md files to archive
    COPY: index.md to archive (snapshot)

2. ARCHIVE PRD VERSION
    cp PRD.md PRD-history/v{N}-final.md

3. UPDATE INDEX
    RESET index.md:
        - Phase: ready
        - Run number: {N+1}
        - Tasks: cleared (or keep as historical reference)
        - Previous runs: append summary

4. PROMPT FOR NEXT ACTION
    "Run {N} archived.

    Options:
    1. Start fresh with new /prdgen
    2. Exit orchestration"
```

### 6.4 PRD History Structure

```
project/
├── PRD.md                      # Current/active PRD
├── PRD-history/                # Version history
│   ├── v1-initial.md           # Original PRD
│   ├── v2-iteration-1.md       # After first iteration
│   ├── v3-extension-1.md       # After extension
│   └── v4-final.md             # Archived version
```

### 6.5 Journal Iteration Tracking

Updated journal index fields for iteration support:

```markdown
## Orchestration Runs

| Run | Type | Date | Tasks | Outcome |
|-----|------|------|-------|---------|
| 1 | initial | 2024-12-01 | 001-008 | complete |
| 2 | iteration | 2024-12-05 | 009-012 | complete |
| 3 | extension | 2024-12-10 | 013-018 | in_progress |

## Current Run

| Field | Value |
|-------|-------|
| Run Number | 3 |
| Run Type | extension |
| PRD Version | v3 |
| Started | 2024-12-10 |
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
│   ├── session_state.md            # HOT: Working memory
│   ├── orchestrator_memory.md      # COLD: Long-term memory
│   ├── knowledge_graph.json        # Tag-based retrieval index
│   ├── strategies.md               # Evolved strategies
│   ├── config.md                   # User preferences
│   ├── memories/                   # Episodic memory entries
│   │   └── YYYY-MM-DD-topic.md
│   └── journal/
│       ├── index.md                # Project state + task registry
│       ├── task-001-name.md        # Individual task logs (YAML handoffs)
│       ├── task-002-name.md
│       └── archive/                # Completed sessions
│
orchestrator/
├── orchestrator_protocol_v3.md     # This file
├── orchestrator_constraints.md     # Role boundaries
├── # Memory & State (v2)
├── state_management.md             # Hot/cold separation
├── knowledge_graph.md              # Tag-based retrieval
├── computed_context.md             # Dynamic context computation
├── handoff_schema.md               # Structured handoff format
├── strategy_evolution.md           # Adaptive learning
├── prompt_caching.md               # Cache optimization
├── skills/
│   ├── skill_manifest.md           # Skill index
│   ├── skill_template.md           # Template for new skills
│   ├── implementation/             # Code-writing skills
│   ├── design/                     # Design skills
│   ├── quality/                    # QA/review skills
│   ├── support/                    # Supporting skills
│   ├── maintenance/                # Skill maintenance skills
│   ├── security/                   # Security implementation skills
│   ├── domain/                     # Domain-specific expertise
│   └── orchestrator/               # Orchestrator self-use skills
│       └── agent_construction.md   # Model selection, skill composition
├── templates/
│   ├── session_state.md            # Hot state template
│   ├── orchestrator_memory.md      # Cold state template
│   ├── knowledge_graph.json        # Knowledge graph template
│   ├── strategies.md               # Strategy file template
│   ├── memory_entry.md             # Episodic memory template
│   ├── journal_index.md            # Journal index template
│   ├── task_entry.md               # Task file template (YAML handoff)
│   └── agent_prompt.md             # Cache-optimized prompt template
└── docs/
    └── user_guide.md               # How to use this system
```

---

## Quick Reference

### Orchestrator Checklist

- [ ] Git status checked (initialize or note GIT_ENABLED)
- [ ] Journal exists or created
- [ ] PRD loaded (required)
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
  - [ ] Git commit (if GIT_ENABLED)
- [ ] QA executed
- [ ] Results reported

### Model Selection Quick Reference

| Complexity | Model | Max Skills | Max Context |
|------------|-------|------------|-------------|
| Easy | Haiku | 3 | 5 code refs |
| Normal | Sonnet | 7 | 10 code refs |
| Complex | Opus | 15 | 20 code refs |

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

## Related Documentation

### Memory & State (v2)
- [State Management](state_management.md) - Hot/cold state separation
- [Knowledge Graph](knowledge_graph.md) - Tag-based retrieval system
- [Computed Context](computed_context.md) - Dynamic context computation
- [Handoff Schema](handoff_schema.md) - Structured handoff format
- [Strategy Evolution](strategy_evolution.md) - Adaptive learning system
- [Prompt Caching](prompt_caching.md) - Cache-optimized prompt structure

### Core
- [Orchestrator Constraints](orchestrator_constraints.md) - Role boundaries
- [Skill Loader](skill_loader.md) - Dynamic skill discovery
- [Initialization Flow](initialization_flow.md) - First-run scripts

---

*Protocol Version: 3.3*
*Updated: December 2024*
*Added: Phase 6 Iteration Support, Enhanced State Detection, Autonomy Levels*
*Memory Architecture v2 based on research from Anthropic, Google Cloud ADK, and A-MEM*
