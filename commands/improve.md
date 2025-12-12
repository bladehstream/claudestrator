# /improve - Autonomous Self-Improvement Loops

Run iterative improvement cycles that analyze current state, identify enhancements, and implement them automatically.

## Usage

```
/improve                      Run 1 improvement cycle
/improve 5                    Run 5 improvement cycles
/improve --continuous         Run until stopped (Ctrl+C)
/improve 10 --focus "performance"   Focus on single area
/improve 3 --skip-tests       Skip test runs between cycles (faster, riskier)
/improve UI, authentication, security    Focus on multiple areas (comma-separated)
/improve new features                    Creative mode with deep research
/improve 5 security, new features        Mix targeted fixes with creative research
```

### Multi-Focus Syntax

Specify multiple improvement areas as comma-separated values:

```
/improve [cycles] <area1>, <area2>, <area3>...
```

Areas can be:
- **Predefined**: `bugs`, `performance`, `security`, `UI`, `UX`, `authentication`, `testing`, `documentation`, `accessibility`, `dependencies`, `refactoring`
- **Custom**: Any free-text description (e.g., `database optimization`, `error handling`)
- **Special**: `new features` - triggers creative research mode (see below)

---

## Working Copies

After each cycle, a snapshot is saved to `.claude/improve_snapshots/`:

```
.claude/improve_snapshots/
├── cycle-001/
│   ├── CHANGES.md           # Summary of changes made
│   ├── REVIEW.md            # Invite to review + /issue instructions
│   └── diff.patch           # Git diff of all changes
├── cycle-002/
│   └── ...
└── latest/                  # Symlink to most recent cycle
```

### Reviewing Between Cycles

While `/improve` runs (especially with `--continuous`), you can:

1. **Open a second terminal**
2. **Browse snapshots**: `ls .claude/improve_snapshots/latest/`
3. **Review changes**: `cat .claude/improve_snapshots/latest/CHANGES.md`
4. **Provide feedback**: `/issue The auth changes in cycle-003 break SSO`

The orchestrator polls for new issues and incorporates them into the next cycle.

### CHANGES.md Format

```markdown
# Cycle 3 Changes - 2025-12-12T15:30:00Z

## Improvements Made
1. ✅ Refactored UserService authentication flow
2. ✅ Added rate limiting to API endpoints
3. ✅ Fixed XSS vulnerability in search input
4. ⚠️ Database index optimization - partial
5. ❌ OAuth2 PKCE implementation - blocked

## Files Changed
- src/services/UserService.ts (47 lines)
- src/middleware/rateLimit.ts (new file)
- src/components/Search.tsx (12 lines)
- migrations/add_indexes.sql (created, not applied)

## Test Results
- 156 passing, 0 failing
- Coverage: 78% → 81%

## To Provide Feedback
Run in Terminal 2:
  /issue <your feedback about these changes>

Issues will be addressed in the next cycle.
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

### Phase 7: Commit & Snapshot

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

    # Create working copy snapshot
    createCycleSnapshot(cycle_number, improvements, results)


FUNCTION createCycleSnapshot(cycle_number, improvements, results):
    cycle_id = formatCycleId(cycle_number)  # e.g., "cycle-003"
    snapshot_dir = ".claude/improve_snapshots/{cycle_id}"

    # Create snapshot directory
    RUN: mkdir -p {snapshot_dir}

    # Generate diff patch
    RUN: git diff HEAD~1 > {snapshot_dir}/diff.patch

    # Generate CHANGES.md
    changes_content = generateChangesMarkdown(cycle_number, improvements, results)
    WRITE: {snapshot_dir}/CHANGES.md

    # Generate REVIEW.md with feedback instructions
    review_content = """
    # Review Cycle {cycle_number}

    Changes from this improvement cycle are ready for review.

    ## Quick Commands

    View changes:
        cat .claude/improve_snapshots/{cycle_id}/CHANGES.md

    View full diff:
        cat .claude/improve_snapshots/{cycle_id}/diff.patch

    Apply diff to compare in editor:
        git apply --check .claude/improve_snapshots/{cycle_id}/diff.patch

    ## Provide Feedback

    If you see issues with these changes, report them:

        /issue <description of problem>

    Examples:
        /issue The new rate limiter is too aggressive, 10 req/min is too low
        /issue Auth refactor broke remember-me functionality
        /issue Missing error handling in UserService.updateProfile

    Feedback will be incorporated into the next improvement cycle.

    ## Revert This Cycle

    If this cycle's changes are unacceptable:

        git revert HEAD --no-edit

    """
    WRITE: {snapshot_dir}/REVIEW.md

    # Update 'latest' symlink
    RUN: rm -f .claude/improve_snapshots/latest
    RUN: ln -s {cycle_id} .claude/improve_snapshots/latest

    REPORT: "📁 Snapshot saved: .claude/improve_snapshots/{cycle_id}/"
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

When using focus areas, improvements are filtered to specific categories:

| Focus | Targets |
|-------|---------|
| `bugs` | Broken functionality, error handling, edge cases |
| `performance` | Speed, memory, bundle size, lazy loading |
| `security` | Vulnerabilities, auth issues, input validation |
| `UI` | Visual design, layout, styling, responsiveness |
| `UX` | User flows, interactions, feedback, accessibility |
| `authentication` | Login, session management, OAuth, permissions |
| `testing` | Coverage gaps, flaky tests, missing assertions |
| `accessibility` | ARIA, keyboard nav, screen readers, contrast |
| `documentation` | Comments, README, JSDoc, type annotations |
| `dependencies` | Outdated packages, unused deps, security updates |
| `refactoring` | Code smells, duplication, pattern consistency |
| `new features` | **Creative mode** - deep research for novel enhancements |

---

## Creative Research Mode: `new features`

When `new features` is included in the focus areas, a special research phase activates:

```
/improve new features
/improve 3 security, new features
/improve --continuous UI, new features
```

### How Creative Mode Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CREATIVE RESEARCH PHASE (before normal cycle)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. ANALYZE PROJECT  → Understand purpose, stack, domain                │
│        ↓                                                                 │
│  2. DEEP RESEARCH    → Web search for trends, best practices            │
│        ↓              → Competitor analysis                              │
│                       → Industry standards                               │
│        ↓                                                                 │
│  3. IDEATE           → Generate 10+ creative improvement ideas          │
│        ↓                                                                 │
│  4. EVALUATE         → Score by impact, feasibility, novelty            │
│        ↓                                                                 │
│  5. SELECT           → Pick top 2-3 for implementation                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Research Agent Configuration

Creative mode uses a high-complexity model for maximum insight:

```
RESEARCH_AGENT:
    model: opus                    # Highest capability for creative thinking
    complexity: complex            # Extended context and reasoning
    tools:
        - WebSearch               # Industry trends, best practices
        - WebFetch                # Documentation, competitor sites
        - Read                    # Understand current codebase
        - Grep                    # Find patterns and opportunities

    research_queries:
        - "{project_type} best practices 2025"
        - "{project_type} common features users expect"
        - "{tech_stack} advanced patterns"
        - "innovative {domain} features"
        - "{competitor} features comparison"

    time_budget: 5-10 minutes     # Deep research takes time
```

### Creative Improvement Categories

The research agent looks for opportunities in:

| Category | Example Ideas |
|----------|---------------|
| **Missing Standards** | "Most React apps have dark mode, this one doesn't" |
| **UX Enhancements** | "Add keyboard shortcuts for power users" |
| **Performance Wins** | "Implement virtual scrolling for large lists" |
| **Modern Patterns** | "Convert to server components for better SEO" |
| **Developer Tools** | "Add Storybook for component documentation" |
| **Accessibility** | "Add skip-to-content links, focus trapping" |
| **Internationalization** | "Prepare for i18n with extraction tooling" |
| **Analytics** | "Add privacy-respecting usage analytics" |
| **Security Hardening** | "Implement CSP headers, SRI for scripts" |

### Example Creative Session

```
$ claude /improve 2 new features

═══════════════════════════════════════════════════════════════════════════════
IMPROVEMENT MODE: 2 cycles, focus: new features (creative research enabled)
═══════════════════════════════════════════════════════════════════════════════

🔬 CREATIVE RESEARCH PHASE
───────────────────────────────────────────────────────────────────────────────

📖 Analyzing project...
   Type: React e-commerce application
   Stack: React 18, TypeScript, Tailwind, Zustand
   Domain: Online retail / shopping

🌐 Researching industry trends...
   ├─ Searching: "e-commerce UX best practices 2025"
   ├─ Searching: "React e-commerce features users expect"
   ├─ Searching: "modern shopping cart patterns"
   ├─ Fetching: competitor sites for feature comparison
   └─ Duration: 4 minutes

💡 Generated 12 creative ideas:
   1. Add wishlist/save-for-later functionality
   2. Implement product comparison feature
   3. Add "recently viewed" products section
   4. Progressive image loading with blur placeholder
   5. Quick-view modal for products
   6. Advanced filtering with URL persistence
   7. Estimated delivery date calculator
   8. Stock alerts / back-in-stock notifications
   9. Social proof: "X people viewing this"
   10. Size guide with measurement converter
   11. AR product preview (for applicable items)
   12. Guest checkout optimization

📊 Evaluating ideas...
   Selected for implementation:
   ├─ #1 Wishlist (high impact, medium effort)
   ├─ #4 Progressive images (high impact, low effort)
   └─ #5 Quick-view modal (high impact, medium effort)

─── CYCLE 1/2 ─────────────────────────────────────────────────────────────────

🔍 Improvements from research:
   1. Implement wishlist with localStorage persistence
   2. Add blur-up progressive image loading
   3. Create quick-view product modal

🔧 Implementing...
   ✅ Wishlist functionality (4 files)
   ✅ Progressive image component (2 files)
   ✅ Quick-view modal (3 files)

✓ Verifying...
   Tests: 89 passing
   Build: success

💾 Committed: improve(cycle-1): 3 creative enhancements
📁 Snapshot saved: .claude/improve_snapshots/cycle-001/

─── CYCLE 2/2 ─────────────────────────────────────────────────────────────────

🔍 Continuing from research backlog:
   1. Add "recently viewed" section
   2. URL-persisted filters
   3. Estimated delivery calculator

🔧 Implementing...
   ✅ Recently viewed products (3 files)
   ✅ Filter URL persistence (2 files)
   ⚠️ Delivery calculator - partial (needs shipping API)

✓ Verifying...
   Tests: 94 passing (+5 new)
   Build: success

💾 Committed: improve(cycle-2): 3 creative enhancements
📁 Snapshot saved: .claude/improve_snapshots/cycle-002/

═══════════════════════════════════════════════════════════════════════════════
IMPROVEMENT COMPLETE
═══════════════════════════════════════════════════════════════════════════════

Summary:
  Creative ideas generated: 12
  Ideas implemented: 6 (5 complete, 1 partial)
  Remaining in backlog: 6 (saved for future cycles)

Backlog saved: .claude/improve_backlog.md
```

### Creative Backlog

Unimplemented ideas are saved for future cycles:

```markdown
# Improvement Backlog

## From Creative Research (2025-12-12)

### High Priority
- [ ] Estimated delivery date calculator (needs shipping API integration)
- [ ] Stock alerts / back-in-stock notifications

### Medium Priority
- [ ] Social proof: "X people viewing this"
- [ ] Size guide with measurement converter
- [ ] Guest checkout optimization

### Future Consideration
- [ ] AR product preview (requires significant infrastructure)

---
Run `/improve new features` to continue implementing from this backlog.
```

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
