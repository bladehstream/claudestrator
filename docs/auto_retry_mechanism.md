# Auto-Retry Mechanism

> Automatic remediation of critical issues discovered during QA.

---

## Overview

When the QA/Testing agent discovers a critical blocking issue (e.g., server won't start, build fails), it can flag the issue for automatic retry. The orchestrator will run additional improvement loops to fix these issues without user intervention.

---

## Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LOOP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Implementation Tasks                                         │
│         ↓                                                        │
│  2. QA/Testing Agent                                            │
│         → Executes verification steps                           │
│         → If critical failure: writes issue with auto_retry flag │
│         ↓                                                        │
│  3. Analysis Agent                                              │
│         → Collects ALL reports (including failures)             │
│         → Appends to history.csv                                │
│         → Generates analytics                                    │
│         ↓                                                        │
│  4. Auto-Retry Check (END OF LOOP)                              │
│         → Orchestrator reads issue_queue.md                     │
│         → Checks for auto_retry: true AND status: pending       │
│         → If found AND retries < max: START NEW LOOP            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Issue Queue Format (Auto-Retry Fields)

```markdown
## ISSUE-YYYYMMDD-NNN

| Field | Value |
|-------|-------|
| Type | bug |
| Priority | critical |
| Status | pending |
| Source | generated |
| Category | [backend/frontend/etc] |
| Created | [ISO timestamp] |
| Auto-Retry | true |
| Retry-Count | 0 |
| Max-Retries | 3 |
| Blocking | true |

### Summary
[One-line description of the failure]

### Failure Details
[Stack trace, error message, or test output]

### Verification Step
[Which verification step failed]

### Suggested Fix
[What the QA agent thinks might fix it]
```

---

## Auto-Retry Fields

| Field | Type | Description |
|-------|------|-------------|
| `Auto-Retry` | boolean | If `true`, orchestrator will automatically attempt to fix |
| `Retry-Count` | integer | Number of times this issue has been retried (starts at 0) |
| `Max-Retries` | integer | Maximum retry attempts before escalating to user (default: 3) |
| `Blocking` | boolean | If `true`, this issue prevents the build from being usable |

---

## When to Flag for Auto-Retry

The QA/Testing agent should set `Auto-Retry: true` for:

| Failure Type | Auto-Retry | Rationale |
|--------------|------------|-----------|
| Build fails (compilation error) | **Yes** | Code is broken, must fix |
| Server won't start | **Yes** | App is unusable |
| Critical security vulnerability | **Yes** | Unsafe to deploy |
| Database connection fails | **Yes** | App is unusable |
| Tests fail (critical path) | **Yes** | Core functionality broken |
| Tests fail (non-critical) | No | Can be fixed in next run |
| Performance below threshold | No | Degraded but functional |
| Lint/style errors | No | Not blocking |
| Missing documentation | No | Not blocking |

---

## Orchestrator Logic (End of Loop)

```pseudocode
FUNCTION checkAutoRetry():
    READ .orchestrator/issue_queue.md

    auto_retry_issues = issues.filter(i =>
        i.auto_retry == true AND
        i.status == "pending" AND
        i.retry_count < i.max_retries
    )

    IF auto_retry_issues.length == 0:
        RETURN false  # No auto-retry needed

    # Check global retry cap
    READ .orchestrator/session_state.md
    IF session.total_auto_retries >= 5:
        LOG "Max auto-retries (5) reached for this run"
        OUTPUT "⚠️ Auto-retry limit reached. Manual intervention required."
        RETURN false

    # Increment counters
    FOR each issue IN auto_retry_issues:
        issue.retry_count += 1
        issue.status = "in_progress"

    session.total_auto_retries += 1

    WRITE .orchestrator/issue_queue.md
    WRITE .orchestrator/session_state.md

    OUTPUT "🔄 Auto-retry triggered for {auto_retry_issues.length} critical issue(s)"
    RETURN true  # Signal to run another loop
```

---

## Safeguards

### 1. Per-Issue Retry Limit
Each issue has `Max-Retries` (default 3). After 3 failed attempts to fix the same issue, stop and escalate.

### 2. Global Retry Cap
Maximum 5 auto-retry loops per orchestration run, regardless of how many issues. Prevents runaway loops.

### 3. Same Error Detection
If the exact same error occurs on consecutive retries, increment a `consecutive_failures` counter. After 2 consecutive identical failures, stop retrying that issue.

### 4. User Override
Create `.orchestrator/no_auto_retry` to disable auto-retry entirely:
```bash
touch .orchestrator/no_auto_retry
```

### 5. Timeout
Auto-retry loops have the same timeout as regular loops. If an agent hangs, the loop fails.

---

## Session State Tracking

Add to `.orchestrator/session_state.md`:

```markdown
## Auto-Retry State

| Field | Value |
|-------|-------|
| total_auto_retries | 0 |
| last_retry_reason | null |
| auto_retry_enabled | true |
```

---

## Output Messages

### Auto-Retry Triggered
```
═══════════════════════════════════════════════════════════════════════════════
🔄 AUTO-RETRY TRIGGERED
═══════════════════════════════════════════════════════════════════════════════

Critical issue detected: Server fails to start (TypeError in src/index.ts:42)

Attempt: 1 of 3
Action: Running improvement loop to fix issue

═══════════════════════════════════════════════════════════════════════════════
```

### Auto-Retry Succeeded
```
═══════════════════════════════════════════════════════════════════════════════
✅ AUTO-RETRY SUCCEEDED
═══════════════════════════════════════════════════════════════════════════════

Issue fixed after 1 retry attempt(s).
Original issue: Server fails to start (TypeError in src/index.ts:42)

═══════════════════════════════════════════════════════════════════════════════
```

### Auto-Retry Exhausted
```
═══════════════════════════════════════════════════════════════════════════════
⚠️ AUTO-RETRY EXHAUSTED
═══════════════════════════════════════════════════════════════════════════════

Failed to fix after 3 attempts:
  - ISSUE-20241213-001: Server fails to start

Manual intervention required. Review:
  - .orchestrator/issue_queue.md
  - .orchestrator/analytics.html

═══════════════════════════════════════════════════════════════════════════════
```

---

## Integration Points

| Component | Change Required |
|-----------|-----------------|
| `orchestrator_runtime.md` | Add auto-retry check at end of loop |
| `commands/orchestrate.md` | Add auto-retry check at end of loop |
| `prompts/implementation/testing_agent.md` | Add logic to flag critical issues |
| `.orchestrator/issue_queue.md` | Add auto-retry fields to format |
| `.orchestrator/session_state.md` | Track retry counts |

---

*Auto-Retry Mechanism v1.0*
