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

---

## Pre-Requisite: Verification Workflow Bug Fixes

> **Priority: HIGH** - These bugs must be fixed BEFORE starting the complexity reduction phases.
> Without these fixes, the verification system is unreliable and will produce false positives.

### Bug 1: Missing TASK-V## Tasks in Non-External-Spec Modes

**Status:** OPEN
**Discovered:** 2026-01-14
**Severity:** HIGH

**Problem:**
The Decomposition Agent only creates TASK-V## verification tasks in `external_spec` mode (BRANCH D). The other modes—`initial`, `improvement_loop`, and `critical_only`—do not create verification tasks.

**Impact:**
- Tests are created (TASK-T##)
- Implementation completes (TASK-###)
- **Verification step is skipped** (no TASK-V## in queue)
- QA (TASK-99999) runs without independent test verification

**Root Cause:**
Section D.4b in `decomposition_agent.md` defines TASK-V## creation, but this logic only exists in BRANCH D (external_spec mode). BRANCH A, B, and C lack equivalent logic.

**Fix Required:**
1. Add Phase 2C-b (Create VERIFY Tasks) to decomposition_agent.md
2. Apply to all modes: initial, improvement_loop, critical_only
3. TASK-V## depends on TASK-T## + related BUILD tasks
4. Uses `test_verification` category

**Files to Modify:**
- `.claude/prompts/decomposition_agent.md` - Add TASK-V## creation to all branches

---

### Bug 2: Environmental Failures Treated as Acceptable Skips ("Cheating")

**Status:** OPEN
**Discovered:** 2026-01-14
**Severity:** HIGH

**Problem:**
Verification agents mark suites as PASS when significant portions of tests are skipped due to environmental issues:

```
│ Integration │ 50     │ 0      │ 26      │ 100% (of runnable) │
Known Issues (Environmental, not bugs):
- Ollama not running → 3 E2E + 6 integration tests blocked
- startServer export issue → 15 integration tests skipped
```

**Why This Is Cheating:**
1. "100% (of runnable)" hides that 34% of tests didn't run
2. Environmental issues like "Ollama not running" should BLOCK, not skip
3. "Known Issues" are dismissed rather than flagged as blocking problems

**Root Cause:**
In `test_verification_agent.md` Phase 5:
- FAIL requires "All tests skipped" (skipped == total)
- BLOCKED requires "All tests skipped due to environment issues"
- Neither handles "significant portion skipped due to environment"

Agent can technically PASS with: 50 pass, 26 skipped, 0 failed → PASS (wrong!)

**Fix Required:**
1. Add skip rate threshold: >10% skipped = FAIL
2. Add environmental pattern detection (ECONNREFUSED, Ollama, EADDRINUSE, etc.)
3. Any environmental issue = BLOCKED (not acceptable skip)
4. Ban "100% (of runnable)" phrasing - report actual rates
5. Categorize skips: EXPECTED vs ENVIRONMENTAL vs CODE_ISSUE

**Files to Modify:**
- `.claude/prompts/test_verification_agent.md` - Stricter verdict rules

---

### Proposal 5 Status Update

**Original Proposal:** Trust-Based Verification (simplify anti-cheat)

**Status:** ❌ REJECTED

**Rationale:**
Real-world testing proves agents DO cheat (inadvertently or not):
- Tests "pass" with 34% skip rate
- Environmental failures dismissed as "not bugs"
- "100% (of runnable)" is statistical manipulation

**Decision:**
Strengthen verification first. Consider simplification only after the system works correctly and we have confidence in test quality.

---

### Execution Order

| Order | Task | Status |
|-------|------|--------|
| 0a | Fix TASK-V## creation (Bug 1) | ⏳ PENDING |
| 0b | Fix environmental skip cheating (Bug 2) | ⏳ PENDING |
| 0c | Fix port conflicts / orphan cleanup (Bug 3) | ⏳ PENDING |
| 1 | Phase 1: Prompt Modularization | ⏳ BLOCKED by 0a, 0b, 0c |
| 2 | Phase 2: Unified Task Schema | ⏳ BLOCKED by Phase 1 |
| 3 | Phase 3: Modular Research Tool | ⏳ BLOCKED by Phase 1 |

**Note:** Bug fixes are numbered 0a/0b to indicate they must be completed before Phase 1 begins.

---

### Bug 3: Port Conflicts and Orphaned Test Processes

**Status:** OPEN
**Discovered:** 2026-01-14
**Severity:** MEDIUM

**Problem:**
Tests fail with `EADDRINUSE` due to:
1. Inconsistent port allocation patterns across test files
2. Orphaned server processes from previous test runs
3. No global cleanup infrastructure

**Current Port Patterns (Inconsistent):**

| Test File | Pattern | Issue |
|-----------|---------|-------|
| E2E tests | `BASE_PORT (3100) + counter` | Counter resets per file, causes collisions |
| Integration (realtime) | `3100 + Math.random() * 100` | Random can collide |
| Performance | `30000 + hash(TASK_ID)` | Better, but not universal |

**Current Cleanup Patterns:**
- `afterAll` with `server.close()` - can hang if server stuck
- No timeout protection on graceful shutdown
- No global teardown to catch orphans
- No force-kill fallback

**Impact:**
- 1 error (port conflict) in latest test run
- Flaky tests depending on run order
- Orphaned processes accumulate between runs

---

#### Solution A: Deterministic Port Allocation + Server Registry

**Principle:** Unique ports per test file, centralized tracking, aggressive cleanup.

**1. Port Allocator Utility**

```typescript
// tests/utils/port-allocator.ts
const RESERVED_PORTS = new Set<number>();
const PORT_BASE = 10000;
const PORT_RANGE = 50000;

export function allocatePort(testId: string): number {
  // Deterministic hash based on test ID
  const hash = testId.split('').reduce((acc, char) => {
    return ((acc << 5) - acc) + char.charCodeAt(0);
  }, 0);

  let port = PORT_BASE + (Math.abs(hash) % PORT_RANGE);

  // Find next available if collision
  while (RESERVED_PORTS.has(port)) {
    port = PORT_BASE + ((port - PORT_BASE + 1) % PORT_RANGE);
  }

  RESERVED_PORTS.add(port);
  return port;
}

export function releasePort(port: number): void {
  RESERVED_PORTS.delete(port);
}
```

**2. Server Registry with Timeout-Protected Cleanup**

```typescript
// tests/utils/test-server-registry.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface TrackedServer {
  server: any;
  port: number;
  testId: string;
  startedAt: number;
}

const activeServers: Map<number, TrackedServer> = new Map();

export async function registerServer(
  server: any,
  port: number,
  testId: string
): Promise<void> {
  // Kill anything already on this port
  await forceKillPort(port);
  activeServers.set(port, { server, port, testId, startedAt: Date.now() });
}

export async function shutdownServer(port: number): Promise<void> {
  const tracked = activeServers.get(port);
  if (!tracked) return;

  try {
    // Graceful shutdown with 5s timeout
    await Promise.race([
      new Promise<void>((resolve) => tracked.server.close(() => resolve())),
      new Promise<void>((_, reject) =>
        setTimeout(() => reject(new Error('shutdown timeout')), 5000)
      )
    ]);
  } catch {
    // Force kill if graceful fails
    await forceKillPort(port);
  }

  activeServers.delete(port);
}

export async function shutdownAllServers(): Promise<void> {
  const ports = Array.from(activeServers.keys());
  await Promise.all(ports.map(shutdownServer));
}

async function forceKillPort(port: number): Promise<void> {
  try {
    await execAsync(`lsof -ti:${port} | xargs kill -9 2>/dev/null || true`);
  } catch {
    // Ignore errors - port may already be free
  }
}
```

**3. Global Setup/Teardown**

```typescript
// tests/utils/global-setup.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export default async function globalSetup(): Promise<void> {
  console.log('[GLOBAL SETUP] Cleaning orphaned test servers...');

  // Kill any processes in our test port range
  try {
    await execAsync(
      'lsof -ti:10000-60000 2>/dev/null | xargs kill -9 2>/dev/null || true'
    );
  } catch {
    // Ignore - no orphans to kill
  }

  console.log('[GLOBAL SETUP] Port range 10000-60000 cleared');
}
```

```typescript
// tests/utils/global-teardown.ts
import { shutdownAllServers } from './test-server-registry.js';

export default async function globalTeardown(): Promise<void> {
  console.log('[GLOBAL TEARDOWN] Shutting down all test servers...');
  await shutdownAllServers();
  console.log('[GLOBAL TEARDOWN] Complete');
}
```

**4. Vitest Config Update**

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globalSetup: './tests/utils/global-setup.ts',
    globalTeardown: './tests/utils/global-teardown.ts',
    // Run test files sequentially to avoid port races
    fileParallelism: false,
    // But tests within a file can run in parallel
    sequence: { concurrent: true }
  }
});
```

**Pros:**
- Deterministic: same test always gets same port
- Debuggable: port maps to test ID
- Aggressive cleanup prevents orphans

**Cons:**
- Hash collisions require fallback logic
- Global teardown required
- Port range must be coordinated

---

#### Solution B: OS-Assigned Ephemeral Ports (Port 0)

**Principle:** Let the OS assign available ports, eliminating collision entirely.

**1. Server Factory with Dynamic Port**

```typescript
// tests/utils/create-test-server.ts
import { createServer } from 'http';
import { AddressInfo } from 'net';

export interface TestServerHandle {
  server: ReturnType<typeof createServer>;
  port: number;
  url: string;
  shutdown: () => Promise<void>;
}

export async function createTestServer(
  app: any,
  testId: string
): Promise<TestServerHandle> {
  const server = createServer(app.fetch);

  // Listen on port 0 = OS assigns available port
  await new Promise<void>((resolve, reject) => {
    server.listen(0, '127.0.0.1', () => resolve());
    server.on('error', reject);
  });

  const { port } = server.address() as AddressInfo;
  const url = `http://127.0.0.1:${port}`;

  console.log(`[${testId}] Server started on dynamic port ${port}`);

  const shutdown = async () => {
    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => {
        server.closeAllConnections();
        resolve();
      }, 5000);

      server.close(() => {
        clearTimeout(timeout);
        resolve();
      });
    });
    console.log(`[${testId}] Server on port ${port} stopped`);
  };

  return { server, port, url, shutdown };
}
```

**2. Usage in Tests**

```typescript
// tests/integration/some-test.test.ts
import { createTestServer, type TestServerHandle } from '../utils/create-test-server.js';
import { createServer as createAppServer } from '../../src/api/server.js';

describe('Some Integration Test', () => {
  let testServer: TestServerHandle;

  beforeAll(async () => {
    const { app } = createAppServer({ databaseUrl: dbPath });
    testServer = await createTestServer(app, 'INT-008');

    // testServer.url is now available with the dynamic port
    const response = await fetch(`${testServer.url}/health`);
    expect(response.ok).toBe(true);
  });

  afterAll(async () => {
    await testServer.shutdown();
  });

  it('should do something', async () => {
    const response = await fetch(`${testServer.url}/api/endpoint`);
    // ...
  });
});
```

**3. Defense-in-Depth Cleanup (5 Layers)**

Since ephemeral ports mean we can't use `lsof -ti:PORT`, we track PIDs instead:

**Layer 1: PID Registry (Normal Cleanup)**

```typescript
// tests/utils/process-registry.ts
import { writeFileSync, readFileSync, existsSync, unlinkSync, mkdirSync } from 'fs';
import { join } from 'path';

const REGISTRY_DIR = join(process.cwd(), '.test-pids');
const REGISTRY_FILE = join(REGISTRY_DIR, 'active-servers.json');

interface ServerEntry {
  pid: number;
  testId: string;
  port: number;
  startedAt: number;
}

function ensureRegistryDir(): void {
  if (!existsSync(REGISTRY_DIR)) {
    mkdirSync(REGISTRY_DIR, { recursive: true });
  }
}

function readRegistry(): ServerEntry[] {
  ensureRegistryDir();
  if (!existsSync(REGISTRY_FILE)) return [];
  try {
    return JSON.parse(readFileSync(REGISTRY_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeRegistry(entries: ServerEntry[]): void {
  ensureRegistryDir();
  writeFileSync(REGISTRY_FILE, JSON.stringify(entries, null, 2));
}

export function registerServer(pid: number, testId: string, port: number): void {
  const entries = readRegistry();
  entries.push({ pid, testId, port, startedAt: Date.now() });
  writeRegistry(entries);
}

export function unregisterServer(pid: number): void {
  const entries = readRegistry().filter(e => e.pid !== pid);
  writeRegistry(entries);
}

export async function killAllRegisteredServers(): Promise<void> {
  const entries = readRegistry();

  for (const entry of entries) {
    try {
      process.kill(entry.pid, 'SIGKILL');
      console.log(`[CLEANUP] Killed PID ${entry.pid} (${entry.testId})`);
    } catch (err: any) {
      if (err.code !== 'ESRCH') { // ESRCH = process doesn't exist
        console.warn(`[CLEANUP] Failed to kill PID ${entry.pid}: ${err.message}`);
      }
    }
  }

  writeRegistry([]);
}
```

**Layer 2: Self-Destruct Watchdog (Crash Protection)**

Server monitors if parent process (vitest) is still alive:

```typescript
// tests/utils/create-test-server.ts (updated)
import { createServer } from 'http';
import { AddressInfo } from 'net';
import { registerServer, unregisterServer } from './process-registry.js';

export async function createTestServer(
  app: any,
  testId: string
): Promise<TestServerHandle> {
  const server = createServer(app.fetch);
  const parentPid = process.ppid;

  await new Promise<void>((resolve, reject) => {
    server.listen(0, '127.0.0.1', () => resolve());
    server.on('error', reject);
  });

  const { port } = server.address() as AddressInfo;
  const url = `http://127.0.0.1:${port}`;
  const pid = process.pid;

  // Register for cleanup
  registerServer(pid, testId, port);

  // Watchdog: check if parent is still alive every 5s
  const watchdog = setInterval(() => {
    try {
      process.kill(parentPid, 0); // Signal 0 = check if alive
    } catch {
      console.log(`[${testId}] Parent died, self-destructing`);
      server.close();
      clearInterval(watchdog);
      process.exit(0);
    }
  }, 5000);
  watchdog.unref(); // Don't keep process alive just for watchdog

  const shutdown = async () => {
    clearInterval(watchdog);
    unregisterServer(pid);
    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => {
        server.closeAllConnections?.();
        resolve();
      }, 5000);
      server.close(() => {
        clearTimeout(timeout);
        resolve();
      });
    });
  };

  return { server, port, url, shutdown };
}
```

**Layer 3: Wrapper Script (Final Safety Net)**

Bash wrapper ensures cleanup even on SIGKILL:

```bash
#!/bin/bash
# scripts/run-tests.sh

REGISTRY_FILE=".test-pids/active-servers.json"

cleanup() {
  echo "[WRAPPER] Cleaning up test servers..."

  # Kill all registered PIDs
  if [ -f "$REGISTRY_FILE" ]; then
    pids=$(jq -r '.[].pid' "$REGISTRY_FILE" 2>/dev/null)
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null && echo "[WRAPPER] Killed PID $pid"
    done
    rm -f "$REGISTRY_FILE"
  fi

  # Fallback: kill any node processes that look like test servers
  pkill -f "vitest" 2>/dev/null || true

  echo "[WRAPPER] Cleanup complete"
}

# Trap all exit signals
trap cleanup EXIT INT TERM

# Run vitest
npx vitest "$@"
EXIT_CODE=$?

# cleanup runs automatically via trap
exit $EXIT_CODE
```

**Layer 4: Global Setup (Handle Previous Crashes)**

```typescript
// tests/utils/global-setup.ts
import { killAllRegisteredServers } from './process-registry.js';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export default async function globalSetup(): Promise<void> {
  console.log('[GLOBAL SETUP] Cleaning up from previous runs...');

  // Kill any servers from previous crashed runs
  await killAllRegisteredServers();

  // Extra safety: kill any orphaned node test processes
  try {
    await execAsync(
      "ps aux | grep 'node.*\\.test-data' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true"
    );
  } catch {
    // Ignore
  }

  console.log('[GLOBAL SETUP] Ready');
}
```

**Layer 5: Package.json Scripts**

```json
{
  "scripts": {
    "test": "./scripts/run-tests.sh",
    "test:clean": "rm -rf .test-pids .test-data && pkill -f vitest || true"
  }
}
```

**Cleanup Layer Summary:**

| Layer | Handles | When It Runs |
|-------|---------|--------------|
| PID Registry | Normal test completion | `afterAll()` in each test |
| Watchdog | Parent process crash | Every 5s during test |
| Wrapper Script | SIGINT, SIGTERM, vitest crash | On any exit signal |
| Global Setup | Previous run crashes | Before first test |
| `test:clean` | Manual nuclear option | When all else fails |

**Pros:**
- Zero port collisions (OS guarantees uniqueness)
- No hash function or port range management
- Simpler mental model
- Works with parallel test files
- Defense-in-depth cleanup handles all crash scenarios

**Cons:**
- Port is only known after server starts (slight refactor needed)
- Harder to debug (port changes each run, but logged)
- More cleanup infrastructure than Solution A

---

#### Comparison

| Criterion | Solution A (Deterministic) | Solution B (Ephemeral + Defense-in-Depth) |
|-----------|---------------------------|------------------------------------------|
| Port collisions | Rare (hash-based) | Impossible (OS-assigned) |
| Debuggability | High (predictable ports) | Medium (logged, but varies per run) |
| Refactor effort | Medium | Medium (more cleanup infra) |
| Parallel safety | Needs `fileParallelism: false` | Works with parallel |
| Crash recovery | Good | Excellent (5 layers) |
| Orphan accumulation | Possible | Prevented (watchdog + registry) |
| Complexity | Medium | Medium-High (more moving parts) |

**Recommendation:** Use **Solution B** with the 5-layer cleanup. The extra infrastructure is worth it for guaranteed port uniqueness and robust crash recovery.

---

#### Files to Create/Modify (Bug 3 - Solution B)

| File | Purpose |
|------|---------|
| NEW: `tests/utils/process-registry.ts` | PID tracking for cleanup |
| NEW: `tests/utils/create-test-server.ts` | Server factory with port 0 + watchdog |
| NEW: `tests/utils/global-setup.ts` | Pre-test orphan cleanup |
| NEW: `tests/utils/global-teardown.ts` | Post-test final cleanup |
| NEW: `scripts/run-tests.sh` | Wrapper with trap for signal handling |
| MOD: `vitest.config.ts` | Add global setup/teardown |
| MOD: `package.json` | Add `test` and `test:clean` scripts |
| MOD: `**/tests/**/*.test.ts` (13 files) | Use new `createTestServer()` factory |
| ADD: `.gitignore` | Add `.test-pids/` directory |
