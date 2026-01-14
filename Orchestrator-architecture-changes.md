# Claudestrator Complexity Reduction Plan

## Problem Statement

The Claudestrator workflow has grown to:
- **orchestrate.md**: 1,552 lines, 170+ critical path branches
- **decomposition_agent.md**: 1,310 lines, 4 mutually-exclusive mode branches
- **11+ completion marker variants** with inconsistent naming
- **7 anti-cheat checks** in test verification assuming adversarial agents

LLM compliance with this pseudo-code is fragile because:
1. Long prompts get skimmed - details buried in 1000+ lines get missed
2. Branching logic (`if mode X, else if mode Y`) is easy to misinterpret
3. Ordering requirements (`do X before Y`) get violated by eager LLMs
4. Negative constraints (`NEVER do X`) are harder to follow than positive ones

---

## 5 Proposals for Complexity Reduction

### Proposal 1: Prompt Modularization (Break Up Monoliths)

**Current state:** Single massive files that agents must parse entirely.

**Proposed change:** Split into phase-specific modules:

```
orchestrate.md (1,552 lines) →
  ├── orchestrate-dispatcher.md (200 lines) - thin control loop
  ├── phases/startup.md (100 lines)
  ├── phases/critical-loop.md (150 lines)
  ├── phases/decomposition.md (100 lines)
  ├── phases/execution.md (200 lines)
  └── phases/verification.md (150 lines)

decomposition_agent.md (1,310 lines) →
  ├── decomposition-core.md (200 lines) - common logic
  ├── modes/initial.md (150 lines) - Branch A
  ├── modes/improvement.md (150 lines) - Branch B
  ├── modes/critical.md (100 lines) - Branch C
  └── modes/external-spec.md (200 lines) - Branch D
```

**Benefits:**
- Each agent reads ONLY what it needs (smaller context)
- Easier to maintain individual pieces
- Can test modes in isolation

**Risks:**
- More files to coordinate
- Risk of drift between modules
- Requires dispatcher logic

**Effort:** Medium (restructuring, no logic changes)

---

### Proposal 2: Bash Control Flow (Deterministic Orchestration)

**Current state:** LLM must follow pseudo-code branching and ordering.

**Proposed change:** Move control flow to bash, leave creativity to LLM:

```bash
#!/bin/bash
# orchestrate.sh - Deterministic control flow

# Step 1: Startup (programmatic, not LLM)
check_git_init
create_directories
detect_source_type

# Step 2: Critical scan (programmatic)
CRITICAL_COUNT=$(grep -c "Priority | critical" .orchestrator/issue_queue.md 2>/dev/null || echo 0)

# Step 3: Branch deterministically
if [ "$CRITICAL_COUNT" -gt 0 ]; then
  # Spawn Claude with minimal, focused prompt
  claude-code --prompt "$(cat prompts/process-critical-issues.md)"
else
  # Different prompt for normal flow
  claude-code --prompt "$(cat prompts/execute-pending-tasks.md)"
fi

# Step 4: Wait for completion (bash controls)
wait_for_marker ".orchestrator/complete/phase.done"

# Step 5: Next phase...
```

**Benefits:**
- Deterministic flow control (bash can't skip steps)
- LLM prompts become smaller and focused
- Easier to debug (bash has clear execution path)
- Ordering enforced by script, not LLM compliance

**Risks:**
- Requires external orchestration (not pure Claude Code)
- Two systems to maintain (bash + prompts)
- Less portable across environments

**Effort:** High (architectural change)

---

### Proposal 3: Unified Task Schema (Eliminate Mode Branches)

**Current state:** Agents have modes (initial, improvement_loop, critical_only, external_spec).

**Proposed change:** Tasks are self-contained; agents don't need to know "what mode":

```yaml
# Every task carries its full context
task:
  id: TASK-001
  type: backend
  source: PRD.md | issue_queue.md | external_spec
  priority: critical | normal

  # Everything the agent needs, no mode inference
  inputs:
    - file: src/auth/login.ts
    - requirement: "JWT token generation"
    - related_issue: ISSUE-20260114-001  # if from issue queue

  outputs:
    - file: src/auth/login.ts
    - test: tests/auth/login.test.ts

  verification:
    command: npm test -- --grep "login"
    expected_exit: 0

  # Retry tracking embedded in task
  retry_count: 0
  max_retries: 3
```

**Benefits:**
- Eliminates mode branches in decomposition agent
- Tasks are self-documenting
- Easier debugging (inspect task, not reconstruct mode)
- Agents become stateless executors

**Risks:**
- Larger task entries
- Decomposition must be smarter upfront
- Schema design complexity

**Effort:** Medium-High (data model change)

---

### Proposal 4: Feature Pruning (Remove Low-Value Complexity)

**Current state:** Many features with unclear ROI:

| Feature | Lines | Usage | Recommendation |
|---------|-------|-------|----------------|
| Query quotas (`--research 2 security 3 UI`) | ~50 | Low | Remove |
| Auto-retry mechanism (Step 6) | ~80 | Low | Remove |
| Concurrency control (MAX_CONCURRENT=10) | ~60 | Low | Sequential for MVP |
| External spec mode (Branch D) | ~200 | Medium | Keep but simplify |
| Runaway agent cleanup (Step 2c-1) | ~30 | High | Keep |

**Proposed MVP flow:**

```
1. Read PRD.md or task_queue.md
2. Create tasks (decomposition)
3. Execute tasks sequentially (no concurrency)
4. Run tests
5. Generate report
Done.
```

**Remove for MVP:**
- Research agent with quotas
- Auto-retry mechanism
- Concurrency control
- Critical issue loop (handle failures manually)

**Benefits:**
- ~400 lines removed from orchestrate.md
- Dramatically simpler mental model
- More reliable (fewer edge cases)

**Risks:**
- Less powerful for large projects
- May need to add features back later
- Sunk cost of existing complexity

**Effort:** Low-Medium (deletion is easier than creation)

---

### Proposal 5: Trust-Based Verification (Simplify Anti-Cheat)

**Current state:** Test verification has 7 anti-cheat checks assuming adversarial agents:
- No `:memory:`
- No `app.request()` bypass
- No `jsdom` faking
- No `Mock*` classes
- Hash validation of evidence
- Process boundary verification
- Confidence-tagged reporting

**Proposed change:** Trust creation agents more, simplify verification to:

```markdown
## Test Verification (Simplified)

1. Run the tests: `npm test`
2. Capture exit code and output
3. If exit code != 0: Report failures
4. If exit code == 0: Report success

That's it. No grep-based cheat detection.
```

**Why this works:**
- If test creation agent cheats, tests will fail in production
- Anti-cheat detection is probabilistic anyway (LLM can miss patterns)
- Real verification happens when code ships

**Add lightweight sanity checks only:**
- Tests actually exist (files present)
- Tests actually ran (output contains test framework output)
- Tests didn't skip everything (`0 tests` is suspicious)

**Benefits:**
- test_verification_agent.md drops from 416 lines to ~100
- Faster verification (no grep pattern scanning)
- Less cognitive load on verifier LLM

**Risks:**
- Cheating tests could slip through
- Relies on production validation catching issues
- Less confidence in pre-merge quality

**Effort:** Low (simplification/deletion)

---

## Revised Execution Plan

**Selected Proposals:**
- Proposal 1: Prompt Modularization
- Proposal 3: Unified Task Schema
- New: Modular Research Tool (loaded on demand)

**Strategy:** Reduce LLM cognitive load by breaking monolithic prompts into focused modules and making tasks self-contained. Research tool becomes optional/modular.

---

### Phase 1: Prompt Modularization (Proposal 1)

**Goal:** Break monolithic prompts into focused, mode-specific modules.

#### 1.1 Split orchestrate.md (1,552 lines)

```
claudestrator/commands/
  ├── orchestrate.md              # 300 lines - core dispatcher + phase routing
  └── orchestrate-phases/
      ├── startup.md              # 100 lines - pre-flight, directory init
      ├── critical-loop.md        # 150 lines - critical issue detection/resolution
      ├── decomposition.md        # 100 lines - spawn decomposition agent
      ├── execution.md            # 200 lines - task execution loop
      ├── verification.md         # 150 lines - test verification phase
      └── analysis.md             # 100 lines - report generation
```

**How it works:**
- Main orchestrate.md contains phase routing logic
- Each phase file is `Read()` only when that phase is active
- Reduces context from 1,552 → ~300 lines per phase

#### 1.2 Split decomposition_agent.md (1,310 lines)

```
claudestrator/.claude/prompts/
  ├── decomposition_agent.md      # 200 lines - core schema, common rules
  └── decomposition-modes/
      ├── initial.md              # 150 lines - Branch A (PRD → tasks)
      ├── improvement.md          # 150 lines - Branch B (issues → tasks)
      ├── critical.md             # 100 lines - Branch C (critical only)
      └── external-spec.md        # 200 lines - Branch D (JSON spec)
```

**How it works:**
- Core file defines task format, required fields, completion marker
- Mode files are concatenated by orchestrator based on MODE parameter
- Agent reads core + one mode file = ~350 lines instead of 1,310

#### 1.3 Split test_creation_agent.md and test_verification_agent.md

```
claudestrator/.claude/prompts/
  ├── test_creation_agent.md      # 150 lines - core test writing rules
  └── test-creation-modes/
      ├── unit.md                 # Framework-specific unit test patterns
      ├── integration.md          # API/DB integration patterns
      └── e2e.md                  # Browser/Playwright patterns

  ├── test_verification_agent.md  # 150 lines - core verification rules
  └── test-verification-modes/
      ├── standard.md             # Run tests, report results
      └── adversarial.md          # Anti-cheat checks (optional)
```

**Files to create:**
- `claudestrator/commands/orchestrate-phases/*.md` (6 files)
- `claudestrator/.claude/prompts/decomposition-modes/*.md` (4 files)
- `claudestrator/.claude/prompts/test-creation-modes/*.md` (3 files)
- `claudestrator/.claude/prompts/test-verification-modes/*.md` (2 files)

**Files to modify:**
- `claudestrator/commands/orchestrate.md` - Slim down, add phase routing
- `claudestrator/.claude/prompts/decomposition_agent.md` - Extract modes
- `claudestrator/.claude/prompts/test_creation_agent.md` - Extract modes
- `claudestrator/.claude/prompts/test_verification_agent.md` - Extract modes

**Effort:** 6-8 hours

---

### Phase 2: Unified Task Schema (Proposal 3)

**Goal:** Tasks carry all context; agents don't need to infer mode.

#### 2.1 Define Standard Task Schema

```yaml
# task_queue.md entry format (all tasks use this)
task:
  id: TASK-001
  status: pending | in_progress | completed | failed
  category: backend | frontend | fullstack | test_creation | test_verification
  complexity: easy | normal | complex

  # Source tracking (no mode inference needed)
  source:
    type: prd | issue | external_spec
    file: PRD.md | .orchestrator/issue_queue.md | projectspec/*.json
    reference: null | ISSUE-20260114-001 | UNIT-001

  # Self-contained context
  objective: "Implement user authentication endpoint"

  acceptance_criteria:
    - "POST /auth/login accepts email and password"
    - "Returns JWT token on success"
    - "Returns 401 on invalid credentials"

  inputs:
    files:
      - src/auth/login.ts
    requirements:
      - "Use bcrypt for password hashing"

  outputs:
    files:
      - src/auth/login.ts
    tests:
      - tests/auth/login.test.ts

  verification:
    build_command: npm run build
    test_command: npm test -- --grep "auth"
    expected_exit: 0

  dependencies:
    - TASK-T01  # Must complete before this task runs

  # Retry tracking (embedded, not reconstructed from issue)
  retry:
    count: 0
    max: 3
    failure_signature: null
```

#### 2.2 Update Decomposition Agent

- Remove mode branch logic
- All modes produce same task schema
- Source tracking embedded in task, not inferred

#### 2.3 Update Implementation Agents

- Read task schema directly
- No need to parse MODE or reconstruct context
- Inputs/outputs/verification all explicit

**Files to modify:**
- `claudestrator/.claude/prompts/decomposition_agent.md` - Use new schema
- `claudestrator/.claude/prompts/backend_agent.md` - Read new schema
- `claudestrator/.claude/prompts/frontend_agent.md` - Read new schema
- `claudestrator/.claude/prompts/test_creation_agent.md` - Read new schema
- `claudestrator/commands/orchestrate.md` - Update task parsing

**Effort:** 4-6 hours

---

### Phase 3: Modular Research Tool

**Goal:** Research agent and quota logic loaded only when `--research` flag is used.

#### 3.1 Extract Research Logic from orchestrate.md

**Current state:** Research agent spawning and quota parsing embedded in main orchestrate.md (~150 lines).

**Proposed change:**
```
claudestrator/commands/
  ├── orchestrate.md              # Core flow (no research logic)
  └── orchestrate-modules/
      └── research.md             # Research agent + quota parsing
```

**orchestrate.md stub:**
```markdown
## Step 4.2: Research Agent (Optional)

If `--research` flag present:
1. Read('.claudestrator/commands/orchestrate-modules/research.md')
2. Follow research agent instructions
3. Return to main flow

If no `--research` flag: Skip to Step 4.3
```

#### 3.2 Research Module Contents

```markdown
# Research Module (orchestrate-modules/research.md)

## Quota Parsing
[Move quota parsing logic here - ~50 lines]

## Research Agent Spawn
[Move agent spawn template here - ~100 lines]

## Wait and Process
[Move completion handling here - ~30 lines]
```

**Benefits:**
- orchestrate.md shrinks by ~150 lines
- Research logic only loaded when needed
- Easier to modify research behavior without touching core flow

**Files to create:**
- `claudestrator/commands/orchestrate-modules/research.md`

**Files to modify:**
- `claudestrator/commands/orchestrate.md` - Remove research logic, add module reference

**Effort:** 2-3 hours

---

## Summary: Execution Order

| Phase | What | Lines Before | Lines After | Effort |
|-------|------|--------------|-------------|--------|
| 1 | Prompt Modularization | 3,278 (combined) | ~300 per context | 6-8 hrs |
| 2 | Unified Task Schema | 4 mode branches | 1 universal schema | 4-6 hrs |
| 3 | Modular Research Tool | 150 lines in core | 0 lines (on demand) | 2-3 hrs |

**Total reduction:**
- orchestrate.md: 1,552 → ~450 lines (core) + modules
- decomposition_agent.md: 1,310 → ~350 lines per mode
- Research logic: 150 → 0 lines in core (loaded on demand)

---

## Files Summary

**Phase 1 - Create:**
- `claudestrator/commands/orchestrate-phases/startup.md`
- `claudestrator/commands/orchestrate-phases/critical-loop.md`
- `claudestrator/commands/orchestrate-phases/decomposition.md`
- `claudestrator/commands/orchestrate-phases/execution.md`
- `claudestrator/commands/orchestrate-phases/verification.md`
- `claudestrator/commands/orchestrate-phases/analysis.md`
- `claudestrator/.claude/prompts/decomposition-modes/initial.md`
- `claudestrator/.claude/prompts/decomposition-modes/improvement.md`
- `claudestrator/.claude/prompts/decomposition-modes/critical.md`
- `claudestrator/.claude/prompts/decomposition-modes/external-spec.md`
- `claudestrator/.claude/prompts/test-creation-modes/unit.md`
- `claudestrator/.claude/prompts/test-creation-modes/integration.md`
- `claudestrator/.claude/prompts/test-creation-modes/e2e.md`
- `claudestrator/.claude/prompts/test-verification-modes/standard.md`
- `claudestrator/.claude/prompts/test-verification-modes/adversarial.md`

**Phase 1 - Modify:**
- `claudestrator/commands/orchestrate.md`
- `claudestrator/.claude/prompts/decomposition_agent.md`
- `claudestrator/.claude/prompts/test_creation_agent.md`
- `claudestrator/.claude/prompts/test_verification_agent.md`

**Phase 2 - Modify:**
- `claudestrator/.claude/prompts/decomposition_agent.md` - New schema
- `claudestrator/.claude/prompts/backend_agent.md` - Read new schema
- `claudestrator/.claude/prompts/frontend_agent.md` - Read new schema
- `claudestrator/.claude/prompts/test_creation_agent.md` - Read new schema
- `claudestrator/commands/orchestrate.md` - Parse new schema

**Phase 3 - Create:**
- `claudestrator/commands/orchestrate-modules/research.md`

**Phase 3 - Modify:**
- `claudestrator/commands/orchestrate.md` - Remove research, add module stub

---

## Verification

**After Phase 1:**
- Run `/orchestrate` with each mode (initial, improvement, critical, external_spec)
- Verify correct phase modules are loaded
- Compare task_queue.md output to previous runs

**After Phase 2:**
- Inspect generated task_queue.md for new schema format
- Run implementation agent on a task
- Verify agent reads all fields correctly

**After Phase 3:**
- Run `/orchestrate` without `--research` - verify no research logic loaded
- Run `/orchestrate --research` - verify research module loads and works
- Run `/orchestrate --research 2 security` - verify quota parsing works
