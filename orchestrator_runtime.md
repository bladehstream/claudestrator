# Orchestrator Runtime (MVP)

> **Version**: MVP 1.1 - Explicit prompt construction, no variable interpolation.

## Key Principle: Full Prompt Content

**CRITICAL**: When spawning agents, the prompt must contain the FULL text of any skill files - not variable references like `{decomp_skill}`. Claude does not automatically interpolate variables in strings.

**Correct approach:**
1. Read the skill file with Read tool
2. Include the entire content in the Task prompt parameter

---

## Initial Run (`/orchestrate`)

### Step 1: Spawn Decomposition Agent

1. Read the skill file:
   ```
   Read(".claudestrator/skills/orchestrator/decomposition_agent.md")
   ```

2. Call Task tool with prompt containing:
   - The FULL content of the skill file
   - Plus these task-specific instructions:
   ```
   ---

   ## Your Task

   Read PRD.md and create .orchestrator/task_queue.md with implementation tasks.
   Follow the process defined in the skill above.

   Source document: PRD.md
   Output file: .orchestrator/task_queue.md
   Completion marker: .orchestrator/complete/decomposition.done

   CRITICAL: You MUST use the Write tool to create the completion marker when done:
   Write(".orchestrator/complete/decomposition.done", "done")
   ```

   Task parameters:
   - model: "opus"
   - run_in_background: true

3. Wait for completion:
   ```
   Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
   ```

### Step 2: Execute Tasks

For each pending task in `.orchestrator/task_queue.md`:

1. Spawn agent:
   ```
   Task(
     model: [haiku|sonnet|opus based on complexity],
     run_in_background: true,
     prompt: "Task: [TASK-ID]
              Objective: [from task_queue.md]
              Acceptance Criteria: [from task_queue.md]

              CRITICAL: When finished, create the completion marker:
              Write('.orchestrator/complete/[TASK-ID].done', 'done')"
   )
   ```

2. Wait:
   ```
   Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
   ```

3. Update task status to "completed" in task_queue.md

4. After all tasks:
   ```
   Write(".orchestrator/session_state.md", "initial_prd_tasks_complete: true")
   Bash("git add -A && git commit -m 'Initial build complete'")
   ```

---

## Improvement Loops (`/orchestrate N`)

For each loop 1..N:

### 1. Research Agent (if initial complete)

```
Task(
  model: "opus",  # Research requires deep analysis
  run_in_background: true,
  prompt: "Analyze codebase for improvements. Write to .orchestrator/issue_queue.md.
           When done: Write('.orchestrator/complete/research-[LOOP].done', 'done')"
)
Bash("while [ ! -f '.orchestrator/complete/research-[LOOP].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
```

### 2. Decomposition Agent

Same as Initial Step 1, but:
- Source: `.orchestrator/issue_queue.md`
- Marker: `.orchestrator/complete/decomp-[LOOP].done`

### 3. Execute Tasks (max 5)

Same as Initial Step 2, limit 5 per loop.

### 4. Commit

```
Bash("git add -A && git commit -m 'Loop [LOOP]'")
```

---

## Model Selection

| Complexity | Model |
|------------|-------|
| easy | haiku |
| normal | sonnet |
| complex | opus |

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Completion | `.orchestrator/complete/{id}.done` |
| State | `.orchestrator/session_state.md` |

## CRITICAL RULES

1. **NEVER use TaskOutput** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **Full skill content in prompts** - no variable references
4. **Manager only** - never write code directly

## Waiting Pattern

```bash
# CORRECT - single blocking call
Bash("while [ ! -f '.orchestrator/complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# WRONG - fills context
while not exists: Bash("sleep 5")
```

---

*MVP Runtime Version: 1.1*
