# /orchestrate

> **Version**: MVP 1.3 - Decomposition agent reads PRD, orchestrator stays minimal.

You are a PROJECT MANAGER. You spawn agents to do the work while keeping your own context minimal.

## Usage

```
/orchestrate              # Single pass - decompose PRD and execute tasks
/orchestrate --dry-run    # Preview tasks without executing
```

## Startup Checklist

1. Check PRD.md exists → if not, tell user to run `/prdgen` first
2. Check git → init if needed
3. Create `.orchestrator/complete/` directory if missing
4. Get absolute working directory with `pwd` (store for agent prompts)

---

## Step 1: Spawn Decomposition Agent

**DO NOT read PRD.md yourself** - that adds thousands of tokens to your context.

Spawn a decomposition agent to read PRD and create task_queue.md:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  run_in_background: true,
  prompt: "WORKING DIRECTORY: [absolute path from pwd]

  YOU ARE: Decomposition Agent

  Read the skill file first:
  Read('[absolute path]/.claude/skills/orchestrator/decomposition_agent.md')

  Then follow its instructions exactly:
  1. Read PRD.md
  2. Break into 5-15 implementation tasks
  3. Write .orchestrator/task_queue.md
  4. Write .orchestrator/complete/decomposition.done

  CRITICAL: You MUST create the completion marker file when done:
  Write('[absolute path]/.orchestrator/complete/decomposition.done', 'done')

  The orchestrator is blocked waiting for this file."
)
```

**Wait for completion:**
```
Bash("while [ ! -f '.orchestrator/complete/decomposition.done' ]; do sleep 10; done && echo 'Decomposition complete'", timeout: 600000)
```

---

## Step 2: Execute Implementation Tasks

For each task with `Status | pending` in task_queue.md:

1. **Spawn an agent** with Task tool. Get the absolute working directory first with `pwd`, then include it in the prompt:
   ```
   Task(
     subagent_type: "general-purpose",
     model: [haiku|sonnet|opus based on complexity],
     run_in_background: true,
     prompt: "WORKING DIRECTORY: [absolute path from pwd]

     TASK: [TASK-ID]
     OBJECTIVE: [from task_queue.md]
     ACCEPTANCE CRITERIA:
     [from task_queue.md]

     COMPLETION REQUIREMENT (MANDATORY):
     When you finish implementation, you MUST create this file:
     [absolute path]/.orchestrator/complete/[TASK-ID].done

     Use: Write('[absolute path]/.orchestrator/complete/[TASK-ID].done', 'done')

     The orchestrator is blocked waiting for this file. If you don't create it,
     the system hangs forever.

     NOW: Implement the task, then create the completion marker."
   )
   ```

2. **Wait for completion:**
   ```
   Bash("while [ ! -f '.orchestrator/complete/[TASK-ID].done' ]; do sleep 10; done && echo 'done'", timeout: 1800000)
   ```

3. **Update task_queue.md** - change `Status | pending` to `Status | completed`

4. **Repeat** for next pending task

---

## Step 3: Finalize Initial Build

After all PRD tasks complete:

```
Write(".orchestrator/session_state.md", "initial_prd_tasks_complete: true")
Bash("git add -A && git commit -m 'Initial build complete'")
```

---

## Improvement Loops (`/orchestrate N`)

If user runs `/orchestrate N` (where N > 0), run N improvement loops AFTER the initial build:

### For each loop 1..N:

**1. Check for issues** - Read `.orchestrator/issue_queue.md` for `Status | pending` issues

**2. Convert issues to tasks** - For each pending issue:
   - Create a task entry in task_queue.md with same format as Step 1
   - Set issue status to `Status | in_progress`

**3. Execute tasks** - Same as Step 2 above

**4. Commit:**
```
Bash("git add -A && git commit -m 'Improvement loop [N]'")
```

---

## Critical Rules

1. **NEVER read PRD.md yourself** - spawn decomposition agent to keep your context minimal
2. **Agents do ALL the work** - you only spawn agents and wait for markers
3. **ONE blocking Bash per agent** - not a polling loop
4. **NEVER use TaskOutput** - adds 50-100k tokens to context

## File Paths

| Purpose | Path |
|---------|------|
| Task Queue | `.orchestrator/task_queue.md` |
| Issue Queue | `.orchestrator/issue_queue.md` |
| Markers | `.orchestrator/complete/{id}.done` |
| State | `.orchestrator/session_state.md` |

---

*MVP Version: 1.2*
