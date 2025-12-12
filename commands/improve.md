# /improve - Autonomous Self-Improvement Loops

Run iterative improvement cycles that analyze current state, identify enhancements, and implement them automatically.

## Usage

```
/improve                      Run 1 improvement cycle
/improve 5                    Run 5 improvement cycles
/improve --continuous         Run until stopped (Ctrl+C)
/improve 10 --focus "performance"   Focus improvements on specific area
/improve 3 --skip-tests       Skip test runs between cycles (faster, riskier)
```

---

## How It Works

Each improvement cycle follows this pattern:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  IMPROVEMENT CYCLE N                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. REVIEW      → Analyze what was done in previous cycle               │
│       ↓                                                                  │
│  2. ASSESS      → Evaluate current project state                        │
│       ↓                                                                  │
│  3. IDENTIFY    → Generate 5 specific improvements                      │
│       ↓                                                                  │
│  4. PRIORITIZE  → Rank by impact and feasibility                        │
│       ↓                                                                  │
│  5. IMPLEMENT   → Execute top improvements as tasks                     │
│       ↓                                                                  │
│  6. VERIFY      → Run tests/build to confirm no regressions            │
│       ↓                                                                  │
│  7. COMMIT      → Auto-commit with cycle summary                        │
│                                                                          │
└──────────────────────────────► NEXT CYCLE ──────────────────────────────┘
```

---

## Cycle Phases

### Phase 1: Review Previous Cycle

```
IF cycle > 1:
    READ .claude/improvement_log.md (last cycle entry)

    ANALYZE:
        - What improvements were attempted?
        - Which succeeded? Which failed?
        - Any unexpected issues?
        - What patterns emerged?

    CARRY_FORWARD:
        - Incomplete items from last cycle
        - Lessons learned
        - Blocked items (with reason)
```

### Phase 2: Assess Current State

```
FUNCTION assessCurrentState():
    # Code quality signals
    RUN: npm run lint (or equivalent) → capture issues
    RUN: npm run typecheck (if applicable) → capture errors
    RUN: npm test → capture failures
    RUN: npm run build → capture warnings

    # Codebase analysis
    SCAN for:
        - TODO/FIXME comments
        - Deprecated patterns
        - Code duplication
        - Missing tests
        - Documentation gaps
        - Performance concerns
        - Security issues
        - Accessibility problems

    # Project health
    CHECK:
        - Dependency freshness (outdated packages)
        - Bundle size trends
        - Test coverage
        - Type coverage

    RETURN assessment_report
```

### Phase 3: Identify 5 Improvements

```
FUNCTION identifyImprovements(assessment, focus_area):
    improvements = []

    # Categorize potential improvements
    categories = [
        'bugs',           # Fix broken functionality
        'performance',    # Speed, memory, bundle size
        'code_quality',   # Refactoring, patterns, DRY
        'testing',        # Coverage, reliability
        'documentation',  # Comments, README, types
        'security',       # Vulnerabilities, best practices
        'ux',             # User experience issues
        'dx'              # Developer experience
    ]

    # Generate candidates from assessment
    FOR category IN categories:
        candidates = extractCandidates(assessment, category)
        improvements.extend(candidates)

    # Apply focus filter if specified
    IF focus_area:
        improvements = improvements.filter(i => i.category == focus_area)

    # Score and rank
    FOR improvement IN improvements:
        improvement.score = calculateImprovementScore(improvement)
            # Factors: impact, effort, risk, dependencies

    # Select top 5
    RETURN improvements.sortBy(score, DESC).take(5)
```

### Phase 4: Prioritize

```
FUNCTION prioritizeImprovements(improvements):
    # Apply ordering rules
    ORDER BY:
        1. Bugs first (broken > degraded > inconvenient)
        2. Quick wins (high impact, low effort)
        3. Blockers for other improvements
        4. User-facing before internal
        5. Lower risk before higher risk

    # Check dependencies
    FOR improvement IN improvements:
        IF improvement.depends_on NOT IN improvements:
            EITHER add dependency OR defer improvement

    # Estimate total effort
    total_effort = SUM(improvement.estimated_minutes)
    IF total_effort > 60:
        WARN: "Cycle may take longer than expected"
        TRIM to fit time budget if needed

    RETURN ordered_improvements
```

### Phase 5: Implement

```
FUNCTION implementImprovements(improvements):
    results = []

    FOR improvement IN improvements:
        REPORT: "🔧 Implementing: {improvement.title}"

        # Create task
        task = {
            objective: improvement.description,
            acceptance_criteria: improvement.criteria,
            type: improvement.type,
            complexity: improvement.complexity
        }

        # Execute via standard orchestration
        result = executeTask(task)

        results.append({
            improvement: improvement,
            outcome: result.outcome,
            files_changed: result.files,
            notes: result.notes
        })

        IF result.outcome == 'failed':
            LOG: "⚠️ Improvement failed, continuing with next"
            # Don't stop cycle on individual failures

    RETURN results
```

### Phase 6: Verify

```
FUNCTION verifyNoRegressions():
    IF skip_tests:
        RETURN { status: 'skipped' }

    # Run verification suite
    results = {
        lint: RUN npm run lint,
        typecheck: RUN npm run typecheck,
        test: RUN npm test,
        build: RUN npm run build
    }

    IF any(results.*.failed):
        REPORT: "⚠️ Regressions detected"

        # Attempt auto-fix
        FOR failure IN results.failures:
            IF isAutoFixable(failure):
                attemptAutoFix(failure)

        # Re-verify
        results = rerunVerification()

        IF still failing:
            OPTION: Revert changes from this cycle
            OPTION: Continue anyway (log warning)

    RETURN results
```

### Phase 7: Commit

```
FUNCTION commitCycleResults(cycle_number, improvements, results):
    # Stage all changes
    RUN: git add -A

    # Generate commit message
    successful = results.filter(r => r.outcome == 'completed')
    failed = results.filter(r => r.outcome == 'failed')

    message = """
    improve(cycle-{cycle_number}): {successful.length} improvements

    Improvements made:
    {FOR s IN successful}
    - {s.improvement.title}
    {END FOR}

    {IF failed.length > 0}
    Attempted but failed:
    {FOR f IN failed}
    - {f.improvement.title}: {f.reason}
    {END FOR}
    {END IF}

    🤖 Generated with [Claude Code](https://claude.com/claude-code)

    Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
    """

    RUN: git commit -m "{message}"

    # Update improvement log
    appendToImprovementLog(cycle_number, improvements, results)
```

---

## Improvement Log

Persistent record at `.claude/improvement_log.md`:

```markdown
# Improvement Log

## Cycle 5 - 2025-12-12T15:30:00Z

### Improvements Attempted
1. ✅ Fix null pointer in UserService.getProfile()
2. ✅ Add missing aria-labels to navigation buttons
3. ✅ Remove unused lodash import (reduced bundle 12kb)
4. ⚠️ Add unit tests for PaymentController - partial (3/5 tests)
5. ❌ Upgrade React to 19.x - blocked by incompatible dependency

### Metrics
- Duration: 8 minutes
- Files changed: 12
- Tests: 145 passing, 0 failing
- Lint issues: 3 → 0

### Notes
- PaymentController tests need mock for Stripe API
- React upgrade blocked by react-datepicker, needs v5.0

---

## Cycle 4 - 2025-12-12T15:20:00Z
...
```

---

## Focus Areas

When using `--focus`, improvements are filtered to specific areas:

| Focus | Targets |
|-------|---------|
| `bugs` | Broken functionality, error handling, edge cases |
| `performance` | Speed, memory, bundle size, lazy loading |
| `security` | Vulnerabilities, auth issues, input validation |
| `testing` | Coverage gaps, flaky tests, missing assertions |
| `accessibility` | ARIA, keyboard nav, screen readers, contrast |
| `documentation` | Comments, README, JSDoc, type annotations |
| `dependencies` | Outdated packages, unused deps, security updates |
| `refactoring` | Code smells, duplication, pattern consistency |

---

## Safety Guardrails

```
GUARDRAILS:
    # Never modify in improvement mode
    - .env files
    - Secrets or credentials
    - CI/CD configuration (unless --allow-ci)
    - Package lock files (unless --allow-deps)
    - Database migrations (unless --allow-migrations)

    # Always verify after changes
    - Run tests after each cycle
    - Check build succeeds
    - Revert on critical failures

    # Rate limiting
    - Max 20 files changed per cycle
    - Max 500 lines changed per cycle
    - Pause if 3 consecutive cycles fail
```

---

## Example Session

```
$ claude /improve 3 --focus "code_quality"

═══════════════════════════════════════════════════════════════════════════════
IMPROVEMENT MODE: 3 cycles, focus: code_quality
═══════════════════════════════════════════════════════════════════════════════

─── CYCLE 1/3 ─────────────────────────────────────────────────────────────────

📊 Assessing current state...
   Lint issues: 12
   Type errors: 0
   Test failures: 0
   TODOs found: 8

🔍 Identifying improvements...
   1. Extract duplicate validation logic into shared util
   2. Replace magic numbers with named constants
   3. Convert callback-based API to async/await
   4. Remove 3 unused variables flagged by linter
   5. Add explicit return types to 5 exported functions

🔧 Implementing...
   ✅ Extract duplicate validation logic (3 files)
   ✅ Replace magic numbers (2 files)
   ✅ Convert to async/await (1 file)
   ✅ Remove unused variables (3 files)
   ✅ Add return types (2 files)

✓ Verifying...
   Lint: 12 → 3 issues (75% reduction)
   Tests: 145 passing
   Build: success

💾 Committed: improve(cycle-1): 5 improvements

─── CYCLE 2/3 ─────────────────────────────────────────────────────────────────

📊 Reviewing cycle 1...
   All 5 improvements succeeded
   Lint issues reduced from 12 to 3

🔍 Identifying improvements...
   1. Fix remaining 3 lint issues
   2. Extract common error handling pattern
   3. Add JSDoc to public API functions
   4. Consolidate similar test utilities
   5. Replace deprecated Buffer() usage

🔧 Implementing...
   ✅ Fix lint issues (3 files)
   ✅ Extract error handling (4 files)
   ✅ Add JSDoc (6 files)
   ✅ Consolidate test utils (2 files)
   ⚠️ Buffer replacement - partial (2/4 occurrences)

✓ Verifying...
   Lint: 0 issues ✨
   Tests: 147 passing (+2 new)
   Build: success

💾 Committed: improve(cycle-2): 5 improvements

─── CYCLE 3/3 ─────────────────────────────────────────────────────────────────

📊 Reviewing cycle 2...
   4 complete, 1 partial
   Lint now at 0 issues

🔍 Identifying improvements...
   1. Complete Buffer replacement (2 remaining)
   2. Reduce cognitive complexity in parseConfig()
   3. Add missing null checks in data layer
   4. Improve error messages with more context
   5. Extract inline styles to CSS modules

🔧 Implementing...
   ✅ Complete Buffer replacement (2 files)
   ✅ Reduce complexity - split into 3 functions
   ✅ Add null checks (5 files)
   ✅ Improve error messages (8 files)
   ✅ Extract styles (3 files)

✓ Verifying...
   Lint: 0 issues
   Tests: 147 passing
   Build: success

💾 Committed: improve(cycle-3): 5 improvements

═══════════════════════════════════════════════════════════════════════════════
IMPROVEMENT COMPLETE
═══════════════════════════════════════════════════════════════════════════════

Summary:
  Cycles completed: 3
  Improvements made: 15 (14 complete, 1 partial)
  Files changed: 38
  Lint issues: 12 → 0
  Time elapsed: 24 minutes

View full log: .claude/improvement_log.md
═══════════════════════════════════════════════════════════════════════════════
```

---

## Implementation Notes

### Integration with Orchestrator

The `/improve` command uses the existing orchestration infrastructure:

1. Each improvement becomes a task in the journal
2. Skills are matched as normal
3. Agents execute improvements
4. QA verification runs after each cycle

### Autonomy Level

Improvement mode requires elevated autonomy:

```
IF autonomy_level < "trust_agents":
    PROMPT: "Improvement mode works best with 'Trust Agents' or higher.
             Current level: {autonomy_level}

             Switch to Trust Agents for this session?"

    IF user confirms:
        SET autonomy_level = "trust_agents" (session only)
```

### Stopping Continuous Mode

When running `--continuous`:

- Press `Ctrl+C` to stop after current cycle completes
- The system will finish the current improvement, commit, then exit
- Partial cycles are logged with "interrupted" status

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/orchestrate` | Standard task-driven orchestration |
| `/progress` | View current state |
| `/analytics` | See improvement impact over time |

---

*Improve Command Version: 1.0*
*Autonomous iterative enhancement for continuous improvement*
