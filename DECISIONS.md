# Architectural Decisions

This document records key architectural decisions made during Claudestrator development.

---

## ADR-001: Concurrency Control for Agent Spawning

**Date:** 2026-01-13
**Status:** Implemented
**Version:** 3.8

### Context

When task_queue.md contains many tasks with `Depends On | None` (e.g., all TEST tasks in a test-only workflow), the orchestrator would spawn all agents simultaneously. This caused:

1. **Resource exhaustion** - CPU, memory, and API rate limits exceeded
2. **Context pollution** - Orchestrator context filled with parallel Task() calls
3. **Unpredictable behavior** - System became unresponsive

### Decision

Implement a **worker pool pattern** with MAX_CONCURRENT_AGENTS = 10:

1. Track running tasks in `.orchestrator/running_tasks.txt`
2. Before spawning, check if at capacity
3. If at capacity, use **single bash blocking wait** until ANY task completes
4. Remove completed task from list, spawn new task

### Why Bash Blocking Wait?

Alternative considered: Polling in orchestrator context with repeated TaskOutput() calls.

**Rejected because:**
- Each poll consumes orchestrator context tokens
- Multiple simultaneous polls create context explosion
- Bash wait is efficient and doesn't pollute orchestrator context

**Chosen approach:**
```bash
while true; do
  for TASK in $(cat running_tasks.txt); do
    if [ -f "complete/${TASK}.done" ]; then
      # Found one - exit
      break 2
    fi
  done
  sleep 5
done
```

This single bash command blocks until completion, keeping orchestrator context clean.

### Consequences

- Maximum 10 agents run concurrently
- Orchestrator context remains predictable size
- Slight delay when waiting for slots (acceptable trade-off)

---

## ADR-002: E2E Test Integrity Requirements

**Date:** 2026-01-13
**Status:** Implemented
**Version:** testing_agent.md v1.4

### Context

Testing Agent was creating "E2E tests" that:

1. Used `Database(':memory:')` instead of real databases
2. Created `MockWebSocket` classes instead of real connections
3. Made direct service calls instead of HTTP requests
4. Never launched a browser for UI testing

These tests passed but tested nothing real. They violated the testing_agent.md requirements which clearly state: "E2E Tests MUST start real server, MUST use real database, MUST NOT mock."

### Root Cause Analysis

Agents are incentivized to **complete tasks**, not to **flag blockers**. When faced with missing infrastructure (no Playwright, no frontend), the agent took the path of least resistance: fake the tests and mark complete.

### Decision

Implement three complementary fixes:

#### 1. Anti-Pattern Detection (Structural)

Add explicit forbidden patterns with grep detection:

| Anti-Pattern | Detection |
|--------------|-----------|
| `Database(':memory:')` | `grep -r ":memory:" e2e/*.test.ts` |
| `class Mock*` | `grep -r "class Mock" e2e/*.test.ts` |
| `vi.fn()` in E2E | `grep -r "vi.fn" e2e/*.test.ts` |

If detected, task is rejected.

#### 2. Evidence Requirements (Verification)

E2E task reports MUST include:
- Server startup logs (proof server ran)
- HTTP request/response logs (proof real requests made)
- Browser screenshots (proof browser launched for UI tests)

No evidence = task rejected.

#### 3. BLOCKED as Valid Completion (Cultural)

Make it explicit: **"Flagging a blocker early is SUCCESS, not failure."**

Valid BLOCKED reasons:
- Browser automation not available
- No frontend exists
- Server won't start
- External service unavailable

Faking tests to hide blockers is FAILURE.

### Browser Automation Tool Selection

Rather than hardcoding one tool, detect what's available:

1. `mcp__claude-in-chrome__*` - Chrome extension (preferred if available)
2. Playwright - If `playwright.config.*` exists
3. Puppeteer - If in package.json
4. BLOCKED - If none available

This supports both development (Chrome extension) and CI/headless (Playwright) environments.

### Consequences

- E2E tests will fail initially if infrastructure is missing (correct behavior)
- Tasks may be marked BLOCKED more often (acceptable - surfaces real issues)
- Test reports will be larger (include evidence)
- Agents cannot cheat by faking tests

---

## ADR-003: Blocker-Positive Culture

**Date:** 2026-01-13
**Status:** Implemented
**Version:** testing_agent.md v1.4

### Context

Agent prompts implicitly reward task completion. When an agent encounters a blocker (missing dependency, unavailable service), it has two choices:

1. **Flag the blocker** - Feels like failure, task stays incomplete
2. **Work around it** - Fake the functionality, mark task complete

Agents consistently chose option 2, creating technical debt and false confidence.

### Decision

Explicitly reframe blockers as success:

```markdown
**BLOCKED Is A Valid Completion State**

If required infrastructure is missing, **do not fake the tests**. Instead:

BLOCKED: [dependency] not available
Missing: [what's missing]
Required for: [which tests]
To unblock: [what needs to happen]

**Flagging a blocker early is SUCCESS, not failure.**
**Faking tests to hide blockers is FAILURE.**
```

This language is added to the end of testing_agent.md as a "negative prompt" - final reinforcement before completion.

### Consequences

- More tasks will be marked BLOCKED (good - surfaces real issues)
- Issue queue will grow with infrastructure requirements (good - makes dependencies explicit)
- False completion rate decreases
- Technical debt from faked tests eliminated

---

## ADR-004: Two-Agent Testing Architecture (Adversarial Validation)

**Date:** 2026-01-13
**Status:** Implemented
**Version:** 4.0

### Context

Despite adding anti-pattern detection and evidence requirements (ADR-002, ADR-003), testing agents continued to find ways to "cheat":

1. **Loophole exploitation** - When we banned `:memory:` databases, agents used `app.request()` (in-process handlers)
2. **Misleading comments** - Agents added "NO MOCKS" comments while code did the opposite
3. **Self-verification failure** - Agents marked their own work complete without genuine checking
4. **Incentive misalignment** - Agents optimized for "task complete" rather than "task correct"

Root cause: A single agent cannot objectively validate its own work.

### Decision

Split testing into two adversarial agents:

#### 1. Test Creation Agent (`test_creation_agent.md`)

**Role:** Write tests that cannot be trivially passed

**Key principle:** Assume the implementation agent will try to cheat

- Requires real HTTP (fetch to localhost), not `app.request()`
- Requires real database (file), not `:memory:`
- Requires real browser (MCP/Playwright), not jsdom
- Evidence-carrying with hash validation
- Built-in anti-cheat grep checks

#### 2. Test Verification Agent (`test_verification_agent.md`)

**Role:** Independently validate tests actually work

**Key principle:** Zero-trust - treat all other agents as adversarial

- Re-executes all tests (doesn't trust producer evidence)
- Validates evidence hashes (detects tampering)
- E2E boundary verification (detects `app.request()` cheating)
- Verdicts: PASS, FAIL, or BLOCKED with evidence

### Why Two Agents?

| Single Agent | Two Agents |
|--------------|------------|
| Self-validates (conflict of interest) | Independent validation |
| Can rationalize shortcuts | Adversarial checking |
| One point of failure | Defense in depth |
| Incentive to complete | Incentive to verify |

### New Task Pattern

```
TASK-T## (test_creation) → TASK-### (implementation) → TASK-V## (test_verification)
```

### Consequences

- More rigorous test validation
- Cheating patterns detected and rejected
- Slightly longer workflow (three stages instead of two)
- Clear separation of concerns
- Each agent has clear, non-conflicting incentives

### Deprecation

`testing_agent.md` is deprecated. Kept for reference with deprecation notice.

Migration:
- `category: testing` → `category: test_creation` (for writing tests)
- Add `category: test_verification` tasks after implementation

---

## Future Considerations

### Automated Anti-Pattern Scanning

~~Consider adding a verification agent that runs grep checks on all test files before accepting task completion.~~

**IMPLEMENTED** in ADR-004: Test Verification Agent now performs this role.

### Concurrency Auto-Tuning

MAX_CONCURRENT_AGENTS = 10 is a safe default. Could be tuned based on:
- Available system resources
- API rate limits
- Task complexity distribution

### Evidence Storage

Currently evidence is described in task reports. Could store actual artifacts:
- Screenshots in `.orchestrator/evidence/`
- HTTP logs in structured format
- Server logs captured to files

---

*Last updated: 2026-01-13 (v4.0)*
