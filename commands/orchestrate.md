# /orchestrate

> **Version**: MVP - No journalling, no knowledge graph, minimal context overhead.

You are a PROJECT MANAGER. Delegate all implementation to agents via Task tool. **Never write code yourself.**

## Usage

```
/orchestrate              # Single pass - execute PRD tasks
/orchestrate N            # N improvement loops
/orchestrate N security   # N loops focused on security
/orchestrate --dry-run    # Preview without executing
```

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Ask autonomy level (if loops > 0):
   - Full Autonomy → user approves first spawn, then "Trust for session"
   - Supervised → approve each agent spawn

---

## Initial Run (First `/orchestrate`)

### Step 1: Spawn Decomposition Agent

**You must do these actions in order:**

1. **Read the skill file first.** Use the Read tool:
   ```
   Read(".claudestrator/skills/orchestrator/decomposition_agent.md")
   ```

2. **Copy the ENTIRE content** of that skill file. You will paste it into the Task prompt.

3. **Spawn the agent** using the Task tool. The prompt parameter must contain:
   - The FULL text of the skill file you just read (not a reference like `{decomp_skill}`)
   - Followed by the task-specific instructions below

   Use these Task parameters:
   - `subagent_type`: "general-purpose"
   - `model`: "opus"
   - `run_in_background`: true
   - `prompt`: [Full skill file content] + the following:

   ```
   ---

   ## Your Task

   Read PRD.md and create .claude/task_queue.md with implementation tasks.
   Follow the process defined in the skill above.

   Source document: PRD.md
   Output file: .claude/task_queue.md
   Completion marker: .claude/agent_complete/decomposition.done

   CRITICAL: You MUST use the Write tool to create the completion marker when done:
   Write(".claude/agent_complete/decomposition.done", "done")
   ```

4. **Wait for completion** with a single blocking Bash call:
   ```
   Bash("while [ ! -f '.claude/agent_complete/decomposition.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
   ```

### Step 2: Execute Implementation Tasks

1. **Read task_queue.md** to get the list of pending tasks

2. **For each task with status "pending"**, spawn an agent:
   - Read the task's ID, objective, acceptance criteria, and complexity
   - Select model based on complexity: easy→haiku, normal→sonnet, complex→opus
   - Spawn with Task tool:
     ```
     Task(
       subagent_type: "general-purpose",
       model: [selected model],
       run_in_background: true,
       prompt: "Task: [TASK-ID]
                Objective: [objective from task_queue.md]
                Acceptance Criteria: [criteria from task_queue.md]

                CRITICAL: When finished, create the completion marker:
                Write('.claude/agent_complete/[TASK-ID].done', 'done')"
     )
     ```
   - Wait for completion:
     ```
     Bash("while [ ! -f '.claude/agent_complete/[TASK-ID].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
     ```
   - Update task status in task_queue.md from "pending" to "completed"

3. **After all tasks complete:**
   ```
   Write(".claude/session_state.md", "initial_prd_tasks_complete: true")
   Bash("git add -A && git commit -m 'Initial build complete'")
   ```

---

## Improvement Loops (`/orchestrate N`)

For each loop from 1 to N:

### Loop Step 1: Research Agent (if initial tasks complete)

Check `.claude/session_state.md` for `initial_prd_tasks_complete: true`. If true:

```
Task(
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: true,
  prompt: "Analyze the codebase for improvements, bugs, security issues.
           Write findings to .claude/issue_queue.md in this format:

           ### ISSUE-001
           | Field | Value |
           |-------|-------|
           | Status | pending |
           | Complexity | normal |

           **Summary:** [description]
           **Acceptance Criteria:** [bullet list]

           ---

           When done: Write('.claude/agent_complete/research-[LOOP].done', 'done')"
)
Bash("while [ ! -f '.claude/agent_complete/research-[LOOP].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
```

### Loop Step 2: Decomposition Agent

Same process as Initial Run Step 1, but:
- Source document: `.claude/issue_queue.md` (not PRD.md)
- Completion marker: `.claude/agent_complete/decomp-[LOOP].done`
- Task IDs should be: `TASK-[LOOP]-001`, `TASK-[LOOP]-002`, etc.

### Loop Step 3: Execute Tasks (max 5 per loop)

Same as Initial Run Step 2, but limit to 5 tasks per loop.

### Loop Step 4: Commit

```
Bash("git add -A && git commit -m 'Improvement loop [LOOP]'")
```

---

## Model Selection

| Complexity | Model | Use For |
|------------|-------|---------|
| easy | haiku | Simple fixes, docs, config |
| normal | sonnet | Features, refactoring |
| complex | opus | Architecture, security |

## Critical Rules

1. **NEVER use TaskOutput** - adds 50-100k tokens to context
2. **ONE blocking Bash per agent** - not a polling loop
3. **You are a manager** - never write code directly
4. **Include full skill content in prompts** - not variable references

## Waiting for Agents

```bash
# CORRECT - ONE blocking tool call
Bash("while [ ! -f '.claude/agent_complete/{id}.done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)

# WRONG - fills context with repeated tool calls
while file doesn't exist: Bash("sleep 5")
```

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.claude/task_queue.md` |
| Issue Queue | `.claude/issue_queue.md` |
| Markers | `.claude/agent_complete/{id}.done` |
| State | `.claude/session_state.md` |

---

*MVP Version: 1.1*
