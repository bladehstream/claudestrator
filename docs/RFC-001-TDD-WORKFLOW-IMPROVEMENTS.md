# RFC-001: TDD Workflow and Retry Logic Improvements

> **Status:** Proposed
> **Author:** bladehstream
> **Date:** 2026-01-07
> **Affects:** orchestrator_runtime.md, failure_analysis_agent.md, testing_agent.md, implementation_agent.md, decomposition_agent.md, qa_agent.md

---

## Summary

This RFC proposes major changes to the orchestration workflow to implement:

1. **TDD (Test-Driven Development) Flow** - Tests written before implementation
2. **Improved Retry Logic** - Failure signature tracking to detect repeated identical failures
3. **QA Spot Check Specification** - Concrete, measurable test sampling criteria
4. **Test Coverage Validation** - Ensure all tests from test plan are mapped to tasks

---

## Motivation

### Problem 1: Tests Written by Implementation Agent (Fox Guarding Henhouse)

The current flow has implementation agents writing their own tests, which can lead to:
- Tests designed to pass easily
- Missing edge cases
- Mock-heavy tests that don't verify real functionality

### Problem 2: Infinite Retry Loops

When tests fail repeatedly for the same reason, the system:
- Retries with the same approach
- Wastes tokens and cycles
- No detection of "same failure, same result"

### Problem 3: Test Dropout During Decomposition

The task decomposer dropped 18 of 76 tests from the test plan without validation, including critical edge cases.

### Problem 4: Vague QA "Spot Check"

QA agent's "spot check" was undefined, leading to inconsistent verification.

---

## Proposed Changes

### Change 1: TDD Task Ordering

Tests must be written BEFORE implementation:

```
TEST tasks (Category: testing, Mode: write)
    │
    │  Must complete first (no dependencies)
    ▼
BUILD tasks (Category: backend/frontend/etc)
    │
    │  Depend on related TEST tasks
    ▼
QA verification
```

### Change 2: Failure Signature Tracking

Track failure signatures to detect repeated identical failures:

- **Per-issue Max-Retries:** 10 (different approaches)
- **Same-signature halt:** 3 (same error repeated)
- **Global retry cap:** 15 (all issues combined per run)

### Change 3: QA Spot Check Specification

Concrete test sampling with measurable success criteria:

| Category | % | Min | Max |
|----------|---|-----|-----|
| Smoke/Critical | 100% | - | - |
| Feature | 100% | - | - |
| Unit (non-feature) | 10% | 2 | 10 |
| Integration (non-feature) | 20% | 2 | 5 |
| E2E (non-feature) | 25% | 1 | 3 |
| Security | 30% | 2 | 5 |
| Performance | 10% | 1 | 2 |

### Change 4: Test Coverage Validation

Decomposition agent must validate 100% of test IDs are mapped to tasks.

---

## Detailed Diffs

### Diff 1: orchestrator_runtime.md

**Location:** `claudestrator/orchestrator_runtime.md`

```diff
@@ -530,6 +530,8 @@
 ## Auto-Retry Check (End of Loop)

 **After Analysis Agent completes**, check for critical issues flagged for auto-retry:
+
+### Retry Eligibility Check

 ```
 READ .orchestrator/issue_queue.md
@@ -537,9 +539,53 @@
 auto_retry_issues = issues WHERE:
   - Auto-Retry == true
   - Status == pending
-  - Retry-Count < Max-Retries
+  - Retry-Count < Max-Retries (default: 10)
+  - Signature-Repeat-Count < Max-Signature-Repeats (default: 3)
+
+# Filter out halted issues
+FOR each issue IN auto_retry_issues:
+    IF issue.Halted == true:
+        REMOVE from auto_retry_issues
+        CONTINUE

 IF auto_retry_issues is empty:
     GOTO Final Output
+```
+
+### Repeated Failure Detection
+
+Before retrying, check if the same fix was already attempted:
+
+```
+FOR each issue IN auto_retry_issues:
+    current_signature = issue.Failure-Signature
+    previous_signatures = issue.Previous-Signatures OR []
+
+    # Count how many times this exact failure occurred
+    signature_count = COUNT(current_signature IN previous_signatures) + 1
+
+    IF signature_count >= 3:
+        OUTPUT "⚠️ HALTING {issue.id}: Same failure repeated {signature_count} times"
+        OUTPUT "   Signature: {current_signature}"
+        OUTPUT "   Manual intervention required - fix approach isn't working"
+
+        # Mark issue as halted (not auto-retryable)
+        Edit issue:
+            | Halted | true |
+            | Halt-Reason | Repeated identical failure ({signature_count}x) |
+            | Auto-Retry | false |
+
+        REMOVE from auto_retry_issues
+        CONTINUE
+
+    # Track this signature for future detection
+    APPEND current_signature to issue.Previous-Signatures
+```

 # Check global cap
 READ .orchestrator/session_state.md
-IF total_auto_retries >= 5:
-    OUTPUT "⚠️ Auto-retry limit (5) reached. Manual intervention required."
+IF total_auto_retries >= 15:
+    OUTPUT "⚠️ Auto-retry limit (15) reached. Manual intervention required."
+    OUTPUT ""
+    OUTPUT "Unresolved issues:"
+    FOR each pending_issue IN issue_queue WHERE Auto-Retry == true AND Status == pending:
+        OUTPUT "  - {pending_issue.id}: {pending_issue.summary}"
+        OUTPUT "    Attempts: {pending_issue.Retry-Count}/10"
+        IF pending_issue.Halted:
+            OUTPUT "    STATUS: HALTED (repeated failure - same fix tried 3x)"
+        OUTPUT ""
     GOTO Final Output

@@ -578,10 +624,12 @@

 ```markdown
 | Auto-Retry | true |
-| Retry-Count | 0 |
-| Max-Retries | 3 |
+| Retry-Count | 0 |
+| Max-Retries | 10 |              ← Total attempts allowed (different approaches)
+| Failure-Signature | |           ← Hash of error output (set by Failure Analysis)
+| Previous-Signatures | [] |      ← History of past failure signatures
+| Signature-Repeat-Count | 0 |    ← Times same signature seen (max 3)
+| Halted | false |                ← Set true when repeated failure detected
 | Blocking | true |
 ```

@@ -590,8 +638,10 @@
 | Safeguard | Limit |
 |-----------|-------|
-| Per-issue retries | 3 (configurable via Max-Retries) |
-| Global retry cap | 5 per orchestration run |
+| Per-issue retries (different approaches) | 10 (Max-Retries) |
+| Per-issue retries (same approach) | 3 (Signature-Repeat-Count) |
+| Global retry cap | 15 per orchestration run |
 | Disable flag | `.orchestrator/no_auto_retry` file |
```

---

### Diff 2: failure_analysis_agent.md

**Location:** `claudestrator/prompts/failure_analysis_agent.md`

```diff
@@ -71,11 +71,44 @@
 ### Step 3: Create Remediation Issues

 **CRITICAL**: All issues MUST have `Priority | critical`
+**CRITICAL**: Generate a Failure-Signature for retry loop detection

 Write issues to `.orchestrator/issue_queue.md` with:
 - Clear summary
 - Detailed root cause analysis
 - Evidence from all 3 attempts
+- **Failure-Signature** (see below)
 - Specific, actionable fix steps
 - Verification command

+### Failure Signature Generation
+
+Generate a hash/signature of the failure to detect repeated identical failures:
+
+```
+SIGNATURE_INPUT = CONCAT(
+    root_cause_type,           # e.g., "implementation_bug"
+    primary_error_message,     # e.g., "TypeError: Cannot read property 'x' of undefined"
+    failing_test_name,         # e.g., "test_user_creation"
+    affected_file              # e.g., "src/services/user.ts"
+)
+
+FAILURE_SIGNATURE = SHA256(SIGNATURE_INPUT)[0:16]  # First 16 chars of hash
+```
+
+This signature allows the orchestrator to detect when the same failure keeps occurring,
+indicating the fix approach isn't working.
+
 ### Step 4: Update Failed Task

@@ -117,15 +150,21 @@
 | Field | Value |
 |-------|-------|
 | Status | pending |
 | Priority | critical |
 | Category | {from failed task} |
 | Complexity | {assessment} |
 | Type | failure-remediation |
 | Source Task | {task_id} |
 | Root Cause | {classification} |
+| Failure-Signature | {generated signature} |
+| Previous-Signatures | [] |
+| Signature-Repeat-Count | 0 |
 | Blocking | true |
 | Auto-Retry | true |
 | Retry-Count | 0 |
-| Max-Retries | 3 |
+| Max-Retries | 10 |
+| Halted | false |

 **Summary:** {one-line description}

@@ -145,6 +184,9 @@

 **Verification:**
 Run: `{command}`
 Expected: {outcome}
+
+**Failure Signature:**
+`{FAILURE_SIGNATURE}` - Used to detect repeated identical failures

 **Related Files:**
 - `{file1}`
@@ -186,6 +228,8 @@
 - [ ] Issue has specific, actionable fix steps
 - [ ] Updated original task with remediation reference
+- [ ] **Generated Failure-Signature from error details**
+- [ ] **Set Max-Retries to 10, Signature-Repeat-Count to 0**
 - [ ] **WROTE THE COMPLETION MARKER FILE**
```

---

### Diff 3: testing_agent.md

**Location:** `claudestrator/prompts/testing_agent.md`

```diff
@@ -1,10 +1,50 @@
 # Testing Implementation Agent

-> **Category**: Testing (unit tests, integration tests, E2E tests)
+> **Category**: Testing (unit tests, integration tests, E2E tests)
+> **Modes**: WRITE (create tests before implementation) | VERIFY (run tests after implementation)

 ---

 ## Mission

-You are a TESTING IMPLEMENTATION AGENT specialized in writing comprehensive, maintainable tests. You ensure code quality through strategic test coverage.
+You are a TESTING AGENT with two operational modes:
+
+### MODE: WRITE (TDD - Before Implementation)
+
+When `MODE: write` is specified:
+- Read test plan specifications (from task's Test IDs)
+- Write actual test code files
+- Tests will FAIL initially (no implementation yet) - this is expected
+- Mark task complete when test files exist and are syntactically valid
+
+### MODE: VERIFY (After Implementation)
+
+When `MODE: verify` is specified:
+- Run existing tests written in WRITE mode
+- Report pass/fail results
+- Create issues for failures with failure signatures
+
+---
+
+## TDD Flow Context
+
+```
+1. Testing Agent (WRITE mode)
+   └── Creates test files from specifications
+   └── Tests exist but fail (no implementation)
+
+2. Implementation Agent
+   └── Implements code to pass existing tests
+   └── Runs tests for feedback
+
+3. QA Agent
+   └── Spot checks automated tests
+   └── Interactive testing
+   └── Final verification
+```
+
+---

 ---
@@ -616,6 +656,42 @@
 **For CRITICAL/HIGH failures**, write issue to `.orchestrator/issue_queue.md`:

+### Generate Failure Signature
+
+Before writing the issue, generate a signature to detect repeated failures:
+
+```
+# Combine key failure identifiers
+SIGNATURE_INPUT = CONCAT(
+    failure_type,              # "build_fails" | "test_fails" | "server_error"
+    primary_error_message,     # First line of error output
+    failing_component,         # Test name or endpoint
+    task_id                    # TASK-XXX
+)
+
+FAILURE_SIGNATURE = SHA256(SIGNATURE_INPUT)[0:16]
+```
+
+### Issue Format with Retry Fields
+
 ```markdown
 ---

@@ -626,11 +702,17 @@
 | Type | bug |
 | Priority | critical |
 | Status | pending |
 | Source | generated |
 | Category | {from failed task's category} |
 | Created | {ISO timestamp} |
+| Failure-Signature | {FAILURE_SIGNATURE} |
+| Previous-Signatures | [] |
+| Signature-Repeat-Count | 0 |
 | Auto-Retry | true |
 | Retry-Count | 0 |
-| Max-Retries | 3 |
+| Max-Retries | 10 |
+| Halted | false |
 | Blocking | true |

@@ -651,6 +733,9 @@
 ### Affected Files
 [Files from the original task]

+### Failure Signature
+`{FAILURE_SIGNATURE}` - Detects if same failure recurs
+
 ### Suggested Fix
 [Based on error output, suggest what might fix it]
 ```
@@ -928,6 +1013,8 @@
 | **Not marking Source Issues completed** | **Critical loop never exits** | **Always run Phase 9.5** |
 | **Marking issues completed without running tests** | **Bugs slip through, false completion** | **MUST run actual build/test commands** |
 | **Trusting task status instead of verifying** | **Implementation Agent may have lied** | **Run verification yourself** |
 | **Orphaned background processes** | **Resource leaks, port conflicts** | **Track PIDs, attempt graceful shutdown** |
+| **Missing Failure-Signature** | **Can't detect repeated failures** | **Always generate signature from error** |
+| **Using Max-Retries: 3** | **Not enough attempts for complex issues** | **Use Max-Retries: 10** |
```

---

### Diff 4: implementation_agent.md

**Location:** `claudestrator/prompts/implementation_agent.md`

```diff
@@ -126,29 +126,35 @@

 ===============================================================================
-PHASE 3: CREATE TEST FILE FIRST
+PHASE 3: LOCATE EXISTING TESTS (TDD)
 ===============================================================================

-**CRITICAL**: Before implementing, you MUST create the test file from the task.
+**CRITICAL**: Tests are written by the Testing Agent BEFORE you implement.
+Your job is to implement code that passes the existing tests.

-### 3.0 Write the Test File
+### 3.0 Find Existing Test File

-The task includes a `Test File` path and `Test Code` section. Create this file FIRST:
+The task specifies a `Test File` path. The Testing Agent should have already created it:

 ```
-Write("{test_file_path}", <test_code_from_task>)
+Read("{test_file_path}")
 ```

-**Why tests first?**
-- Tests define the exact pass/fail criteria
-- You have a clear target to implement against
-- Verification is automated, not manual
+**If test file exists:**
+- Read and understand what the tests expect
+- Implement code to pass these tests

-### 3.0.1 Verify Test File Created
+**If test file does NOT exist:**
+- This is a dependency failure
+- The Testing Agent (WRITE mode) should have created it
+- Write `.failed` marker with reason: "Test file not found - dependency TASK-TXX not complete"
+- Do NOT create the test file yourself (violates TDD)

-```
-Read("{test_file_path}")
-```
+### 3.0.1 Understand Test Expectations
+
+Before implementing, understand what the tests expect:
+- Read each test case
+- Note the expected inputs and outputs
+- Identify edge cases being tested
+- Plan implementation to satisfy all tests

-Confirm the test file exists before proceeding.
+**You are implementing to pass tests you did not write.**

 ===============================================================================
@@ -370,6 +376,7 @@
 ```json
 {
   "task_id": "{task_id}",
   "loop_number": {loop_number},
   "run_id": "{run_id}",
   "status": "failed",
   "attempts": 3,
+  "failure_signature": "{SHA256(root_cause + primary_error + test_name + file)[0:16]}",
   "build_command": "{build_command}",
   "test_file": "{test_file_path}",
   "test_command": "{test_command}",
@@ -378,6 +385,7 @@
     {
       "attempt": 1,
       "approach": "Description of what you tried",
+      "approach_signature": "{SHA256(approach)[0:8]}",
       "build_passed": true,
       "build_output": "Build output if failed, null if passed",
       "test_output": "Actual error message from test run",
@@ -606,7 +614,9 @@
 | Mistake | Impact | Fix |
 |---------|--------|-----|
 | **Skipping build verification** | Missing imports, broken code deployed | Run build BEFORE tests |
-| **Skipping test file creation** | No verification criteria | Create test file FIRST |
+| **Creating test file yourself** | Violates TDD, fox guards henhouse | Tests written by Testing Agent |
+| **Test file not found** | Dependency failure | Check TASK-TXX completed first |
 | **More than 3 attempts** | Wasted effort, no analysis | Stop at 3, use failure protocol |
+| **Missing failure_signature** | Can't detect repeated failures | Always include in failure report |
```

---

### Diff 5: decomposition_agent.md

**Location:** `.claude/skills/orchestrator/decomposition_agent.md`

```diff
@@ -74,8 +74,127 @@
 - **Atomic**: One clear deliverable per task
 - **Testable**: Has verifiable acceptance criteria
 - **Sized right**: Completable in one agent session (not too large)
 - **Independent**: Minimize dependencies where possible
+- **For test tasks**: Include integration requirements (see Test Task Format below)
+
+---
+
+## TDD Task Ordering (CRITICAL)
+
+**Tests MUST be written BEFORE implementation.**
+
+```
+TEST tasks (Category: testing, Mode: write)
+    │
+    │  Must complete first (no dependencies)
+    ▼
+BUILD tasks (Category: backend/frontend/etc)
+    │
+    │  Depend on related TEST tasks
+    ▼
+QA verification
+```
+
+When creating tasks from test plan:
+
+1. **Create TEST tasks first** (TASK-T01, TASK-T02, etc.)
+   - Dependencies: None
+   - Mode: write (creates test files)
+   - Category: testing
+
+2. **Create BUILD tasks second** (TASK-001, TASK-002, etc.)
+   - Dependencies: Related TEST tasks
+   - Example: TASK-001 (LLM Gateway) depends on TASK-T01 (LLM Gateway tests)
+
+3. Orchestrator runs TEST tasks first, then BUILD tasks
+
+---
+
+## Test Task Format
+
+**CRITICAL**: Test tasks require additional fields for integration requirements.
+
+```markdown
+### TASK-T01
+
+| Field | Value |
+|-------|-------|
+| Status | pending |
+| Category | testing |
+| Complexity | normal |
+| Mode | write |
+| Test IDs | UNIT-001, UNIT-002, UNIT-003 |
+| Integration Level | real / mocked / unit |
+| External Dependencies | ollama, clamav, database |
+| Mock Policy | database-seeding-only |
+| Skip If Unavailable | ollama |
+
+**Objective:** Write tests for LLM Gateway provider handling
+
+**Test Specifications:**
+(Copy from test-plan-output.json for each Test ID)
+
+**Dependencies:** None
+
+---
+```
+
+### Integration Level Definitions
+
+| Level | Description | What's Mocked | What's Real |
+|-------|-------------|---------------|-------------|
+| **unit** | Isolated logic testing | Everything external | Only the function under test |
+| **mocked** | Component integration with test doubles | External services | Internal component interactions |
+| **real** | Actual integration with external systems | Nothing (or DB seeding only) | All services, APIs, connections |
+
+### Mock Policy Values
+
+| Policy | Allowed Mocks |
+|--------|---------------|
+| **none** | No mocking allowed - all calls must be real |
+| **database-seeding-only** | May seed test data, but queries must hit real DB |
+| **external-services-only** | May mock 3rd party APIs if skip-if-unavailable |
+| **internal-only** | May mock internal services, external must be real |
+
+---
+
+## Test Coverage Validation (MANDATORY)
+
+Before writing task_queue.md, you MUST verify:
+
+```
+1. Extract all test IDs from source (test-plan-output.json or PRD)
+2. Ensure EVERY test ID appears in exactly one test task's "Test IDs" field
+3. If any test ID is missing, create additional test tasks
+4. Edge cases are NOT optional - they must all be mapped
+
+COVERAGE REQUIREMENT: 100% of test plan IDs must be assigned to tasks
+```
+
+Add a coverage matrix to the bottom of task_queue.md:
+
+```markdown
+## Test Coverage Matrix
+
+| Category | Plan Count | Mapped Count | Missing IDs |
+|----------|------------|--------------|-------------|
+| unit | 21 | 21 | - |
+| integration | 10 | 10 | - |
+| e2e | 5 | 5 | - |
+| security | 14 | 14 | - |
+| performance | 9 | 9 | - |
+| edge_cases | 17 | 17 | - |
+
+**Coverage: 100% (76/76)**
+```

 ### Step 4: Write task_queue.md

@@ -109,6 +228,40 @@
 ---
 ```

+### Converting Issues to Tasks (MODE: convert_issues / critical_only)
+
+When converting issues that have retry fields, **preserve them** on the task:
+
+```markdown
+### TASK-078
+
+| Field | Value |
+|-------|-------|
+| Status | pending |
+| Category | {from issue} |
+| Complexity | {from issue or assess} |
+| Source Issue | ISSUE-20260107-032 |
+| Retry-Count | {from issue, or 0} |
+| Max-Retries | {from issue, or 10} |
+| Failure-Signature | {from issue, or empty} |
+| Previous-Signatures | {from issue, or []} |
+
+**Objective:** {from issue summary}
+...
+```
+
+**Why preserve retry fields?**
+- Allows orchestrator to track total attempts across decomposition cycles
+- Prevents infinite loops where same failure keeps creating new tasks
+- Enables signature-based duplicate detection
+
+If the source issue has `Halted | true`, do NOT create a task - the issue requires manual intervention.
+
 ### Category Guidelines

 Category helps the orchestrator select the right model and include domain-specific context:
@@ -122,6 +275,7 @@
 | devops | Ops | Docker, CI/CD, deployment, infrastructure |
 | testing | QA | Tests, validation, QA |
 | docs | Docs | Documentation, README |
+| testing:integration | QA | Tests requiring real external services |

 ### Step 5: Write Completion Marker

@@ -149,6 +303,10 @@
 - [ ] Each task has Objective and Acceptance Criteria
 - [ ] Dependencies noted where applicable
+- [ ] **TEST tasks created with Mode: write**
+- [ ] **BUILD tasks depend on related TEST tasks (TDD ordering)**
+- [ ] **TEST tasks have Integration Level specified**
+- [ ] **Test Coverage Matrix included at bottom of task_queue.md**
+- [ ] **100% of test IDs from source are mapped to tasks**
 - [ ] **WROTE THE COMPLETION MARKER FILE**

 ---
@@ -160,6 +318,10 @@
 3. **Forgetting the marker file** - System will hang forever
 4. **Not using Write tool** - You must use `Write()` to create files
 5. **Just outputting text** - You must USE TOOLS, not just describe what you would do
+6. **Dropping test IDs** - Every test from the plan must appear in a task
+7. **BUILD tasks without TEST dependencies** - Violates TDD ordering
+8. **Missing Integration Level** - Test tasks need explicit mock/real requirements
+9. **Not preserving retry fields** - Causes infinite loops on issue conversion
```

---

### Diff 6: qa_agent.md

**Location:** `.claude/skills/quality/qa_agent.md`

```diff
@@ -319,6 +319,149 @@

 ### Phase 0: Determine Testing Approach (MANDATORY FIRST STEP)

+### Phase 0.5: Spot Check Automated Tests
+
+The Implementation Agent already ran automated tests. Your job is to:
+
+1. **Trust but verify** - Don't re-run the full suite
+2. **Spot check** - Run a sample of tests as sanity check
+3. **Focus on interactive** - Your main value is manual testing
+
+---
+
+## Spot Check Specification
+
+### Test Selection Rules
+
+| Category | % | Min | Max | Notes |
+|----------|---|-----|-----|-------|
+| Smoke/Critical | 100% | - | - | Run all smoke tests |
+| Feature (task's Test IDs) | 100% | - | - | Run all feature tests |
+| Unit (non-feature) | 10% | 2 | 10 | Sample |
+| Integration (non-feature) | 20% | 2 | 5 | Sample |
+| E2E (non-feature) | 25% | 1 | 3 | Sample |
+| Security | 30% | 2 | 5 | Sample |
+| Performance | 10% | 1 | 2 | Sample |
+
+**Note:** Minimum only applies when percentage < 100%
+
+### Calculation Formula
+
+```
+FOR each category:
+    IF percentage == 100%:
+        selected = available
+    ELSE:
+        available = tests in category (excluding feature tests already counted)
+        calculated = CEIL(available × percentage)
+        selected = CLAMP(calculated, minimum, maximum)
+        IF selected > available: selected = available
+```
+
+### Test Selection Method (Deterministic)
+
+Use task ID for deterministic selection (reproducible, not random):
+
+```
+seed = HASH(task_id + category_name) mod 2^32
+step = available_count / selected_count
+
+FOR i in 0..selected_count:
+    index = (seed + i × step) mod available_count
+    select test at index
+```
+
+This ensures:
+- Deterministic (same task = same sample = reproducible)
+- Varied (different tasks = different samples = coverage over time)
+
+### Success Criteria (Measurable)
+
+| Category | Required Pass Rate | On Failure |
+|----------|-------------------|------------|
+| Smoke | 100% | CRITICAL - system broken |
+| Feature | 100% | FAIL - implementation incomplete |
+| Non-feature combined | ≥90% | WARN if 80-90%, FAIL if <80% |
+| Overall | ≥95% | FAIL if <95% |
+
+### Spot Check Decision Matrix
+
+```
+┌─────────────────────────────────────────────────────────────────┐
+│                    SPOT CHECK DECISION MATRIX                   │
+├─────────────┬─────────────┬─────────────┬──────────────────────┤
+│ Smoke       │ Feature     │ Non-Feature │ Action               │
+├─────────────┼─────────────┼─────────────┼──────────────────────┤
+│ 100% pass   │ 100% pass   │ ≥95% pass   │ ✓ PASS - proceed     │
+│ 100% pass   │ 100% pass   │ 90-94%      │ ⚠ WARN - investigate │
+│ 100% pass   │ 100% pass   │ <90%        │ ✗ FAIL - regression  │
+│ 100% pass   │ <100%       │ any         │ ✗ FAIL - incomplete  │
+│ <100%       │ any         │ any         │ ✗ CRITICAL - broken  │
+└─────────────┴─────────────┴─────────────┴──────────────────────┘
+```
+
+### Spot Check Output Format
+
+```markdown
+## Spot Check Results
+
+| Category | Selected | Passed | Failed | Rate |
+|----------|----------|--------|--------|------|
+| Smoke | 5 | 5 | 0 | 100% ✓ |
+| Feature | 6 | 6 | 0 | 100% ✓ |
+| Unit | 2 | 2 | 0 | 100% ✓ |
+| Integration | 2 | 2 | 0 | 100% ✓ |
+| E2E | 1 | 1 | 0 | 100% ✓ |
+| Security | 5 | 5 | 0 | 100% ✓ |
+| Performance | 1 | 1 | 0 | 100% ✓ |
+| **TOTAL** | **22** | **22** | **0** | **100%** |
+
+**SPOT CHECK: PASS** ✓
+```
+
+### Mismatch Detection
+
+If Implementation Agent claimed "all X tests passed" but spot check finds failures:
+
+```
+MISMATCH DETECTED:
+  Implementation claimed: 76 tests passed
+  Spot check found: 2 failures in 22 tests sampled
+
+  Failed tests:
+    - UNIT-015: Expected 200, got 500
+    - SEC-003: Auth bypass detected
+
+  Action: Create issue with | Source | qa_mismatch |
+```
+
+---
+
+## Failure Issue Creation
+
+**When QA recommendation is FAIL**, you MUST create an issue for the orchestrator:
+
+### Generate Failure Signature
+
+```
+SIGNATURE_INPUT = CONCAT(
+    "qa_failure",
+    task_id,
+    first_failed_criterion,
+    primary_bug_location
+)
+FAILURE_SIGNATURE = SHA256(SIGNATURE_INPUT)[0:16]
+```
+
+### Write Issue to Queue
+
+If your recommendation is **FAIL**, write to `.orchestrator/issue_queue.md`:
+
+```markdown
+---
+
+## ISSUE-{date}-{seq}
+
+| Field | Value |
+|-------|-------|
+| Type | bug |
+| Priority | high |
+| Status | pending |
+| Source | qa |
+| Category | {from task} |
+| Created | {ISO timestamp} |
+| Failure-Signature | {FAILURE_SIGNATURE} |
+| Previous-Signatures | [] |
+| Signature-Repeat-Count | 0 |
+| Auto-Retry | true |
+| Retry-Count | 0 |
+| Max-Retries | 10 |
+| Halted | false |
+| Blocking | true |
+| Source Task | {TASK-ID that failed QA} |
+
+### Summary
+QA Failed: {primary failure reason}
+
+### Failure Details
+**Task:** {task_id}
+**Criteria Failed:** {count} of {total}
+
+{For each failed criterion:}
+- **{Criterion}**: {Why it failed}
+
+### Bugs Found
+{Copy bug details from QA report}
+
+### Suggested Fix
+{Based on QA findings}
+
+### Failure Signature
+`{FAILURE_SIGNATURE}` - Detects if same QA failure recurs
+```
+
+### When NOT to Create Issues
+
+- If recommendation is **PASS** or **PASS WITH NOTES** - no issue needed
+- If failures are all **Low** severity - document in report only
+- If already exists in issue queue (check with Grep first)
+
+---
+
 ```
 STEP 1: Identify application type (see detection table above)
```

---

## Migration Notes

### Breaking Changes

1. **Implementation Agent no longer creates tests** - Tests must exist before implementation runs
2. **Test tasks required before build tasks** - Task queue ordering enforced
3. **Retry limits changed** - Max-Retries now 10 (was 3), global cap now 15 (was 5)

### Backward Compatibility

- Existing task queues without TDD ordering will still work but may have suboptimal flow
- Issues without Failure-Signature fields will be auto-retry eligible but won't benefit from duplicate detection

### Recommended Migration Path

1. Update agent prompts (this RFC)
2. Re-run decomposition on existing projects to get TDD-ordered task queue
3. Existing in-progress tasks can complete under old rules

---

## Acceptance Criteria

- [ ] All 6 files updated per diffs above
- [ ] Tests written before implementation in new task queues
- [ ] Failure signatures generated on all failure issues
- [ ] QA spot check follows percentage/minimum specification
- [ ] Retry halts after 3 identical failures OR 10 total attempts
- [ ] Test coverage validated at 100% during decomposition

---

## References

- Conversation: TDD workflow discussion (2026-01-07)
- Issue: ISSUE-20260107-006 through ISSUE-20260107-011 (test quality audit findings)
- Original test plan: `projectspec/test-plan-output.json` (76 tests, 18 dropped)
