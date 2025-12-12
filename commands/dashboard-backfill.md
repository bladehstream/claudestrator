# /dashboard backfill - Infer Historical Analytics Data

Parse historical journal and issue queue data to populate analytics for runs that predate instrumentation.

## Usage

```
/dashboard backfill              Run backfill with default settings
/dashboard backfill --dry-run    Preview what would be inferred without writing
/dashboard backfill --strict     Only infer high-confidence data (skip guessed)
```

---

## What Gets Backfilled

| Data Type | Source | Confidence | Notes |
|-----------|--------|------------|-------|
| Issue sources | Journal task files | `inferred` | Parse for "QA found", "bug discovered" |
| Issue sources | Issue queue | `inferred` | All queue entries → `user_reported` |
| Prevented issues | Strategy anti-patterns | `guessed` | Very speculative, only with `--include-guessed` |
| Decision influences | Strategy log | `inferred` | Match signals to subsequent tasks |
| Session metrics | Metrics.json / journal | `observed` if metrics exist | May be partial |

---

## Backfill Algorithm

```
FUNCTION backfillHistoricalData(options):
    dry_run = options.includes('--dry-run')
    strict = options.includes('--strict')

    results = {
        sessions_found: 0,
        sessions_backfilled: 0,
        issues_inferred: 0,
        decisions_inferred: 0,
        skipped_low_confidence: 0
    }

    # Find historical data sources
    journal_archive = GLOB .claude/journal/archive/run-*/
    journal_current = .claude/journal/
    issue_queue = .orchestrator/issue_queue.md
    strategy_log = .claude/strategy_log.json

    # Process archived runs
    FOR run_dir IN journal_archive:
        run_number = extractRunNumber(run_dir)
        session_id = inferSessionId(run_dir)

        # Check if already has instrumented data
        IF EXISTS .claude/analytics/sessions/{session_id}.json:
            existing = READ .claude/analytics/sessions/{session_id}.json
            IF existing._meta.confidence_tagging AND existing.data_quality.source == 'instrumented':
                SKIP  # Don't overwrite good data
                CONTINUE

        # Backfill this run
        session = backfillSession(run_dir, run_number, strict)
        results.sessions_backfilled += 1
        results.issues_inferred += session.issues_inferred
        results.decisions_inferred += session.decisions_inferred

        IF NOT dry_run:
            writeBackfilledSession(session)

    # Process issue queue for user-reported issues
    IF EXISTS issue_queue:
        issues = parseIssueQueue(issue_queue)
        FOR issue IN issues:
            IF issue.status IN ['complete', 'wont_fix']:
                recordInferredIssue(issue, 'user_reported', 'inferred')
                results.issues_inferred += 1

    # Update aggregate analytics
    IF NOT dry_run:
        updateLearningInsights(results)
        regenerateTrends()

    RETURN results


FUNCTION backfillSession(run_dir, run_number, strict):
    session = createSessionTemplate()
    session.session_id = inferSessionId(run_dir)
    session.run_number = run_number
    session.data_quality.source = 'backfilled'
    session.data_quality.overall = 'inferred'

    # Parse task files for issues
    task_files = GLOB {run_dir}/task-*.md
    FOR task_file IN task_files:
        content = READ task_file
        issues = inferIssuesFromTask(content, strict)
        session.issues.details.extend(issues)

        decisions = inferDecisionsFromTask(content, strict)
        session.decisions_influenced.extend(decisions)

    # Tally by confidence
    FOR issue IN session.issues.details:
        IF issue.source == 'self_detected':
            session.issues.self_detected += 1
            IF issue.confidence == 'observed':
                session.issues.self_detected_observed += 1
            ELSE:
                session.issues.self_detected_inferred += 1

    # Calculate data quality
    total = session.issues.details.length + session.decisions_influenced.length
    observed = countByConfidence(session, 'observed')
    session.data_quality.verified_percentage = (observed / total) * 100 IF total > 0 ELSE 0

    RETURN session


FUNCTION inferIssuesFromTask(content, strict):
    issues = []

    # Pattern: QA explicitly found something
    qa_patterns = [
        /QA found:?\s*(.+)/i,
        /QA identified:?\s*(.+)/i,
        /testing revealed:?\s*(.+)/i,
        /QA agent reported:?\s*(.+)/i,
        /verification failed:?\s*(.+)/i
    ]

    FOR pattern IN qa_patterns:
        matches = content.matchAll(pattern)
        FOR match IN matches:
            issues.append({
                source: 'self_detected',
                confidence: 'inferred',
                confidence_reason: 'Matched pattern: ' + pattern,
                description: match[1],
                category: 'qa_found'
            })

    # Pattern: Build/test failures
    build_patterns = [
        /build failed:?\s*(.+)/i,
        /test failed:?\s*(.+)/i,
        /lint error:?\s*(.+)/i,
        /type error:?\s*(.+)/i,
        /compilation error:?\s*(.+)/i
    ]

    FOR pattern IN build_patterns:
        matches = content.matchAll(pattern)
        FOR match IN matches:
            category = inferCategoryFromPattern(pattern)
            issues.append({
                source: 'self_detected',
                confidence: 'inferred',
                confidence_reason: 'Matched pattern: ' + pattern,
                description: match[1],
                category: category
            })

    # Pattern: Generic bug mentions (lower confidence)
    IF NOT strict:
        bug_patterns = [
            /bug:?\s*(.+)/i,
            /issue:?\s*(.+)/i,
            /error:?\s*(.+)/i,
            /fix(?:ed)?:?\s*(.+)/i
        ]

        FOR pattern IN bug_patterns:
            matches = content.matchAll(pattern)
            FOR match IN matches:
                # Only if not already captured by higher-confidence patterns
                IF NOT alreadyCaptured(match[1], issues):
                    issues.append({
                        source: 'unknown',  # Can't determine source
                        confidence: 'guessed',
                        confidence_reason: 'Generic pattern match, source unknown',
                        description: match[1],
                        category: 'unknown'
                    })

    RETURN issues


FUNCTION inferDecisionsFromTask(content, strict):
    decisions = []

    # Pattern: Explicit learning reference
    learning_patterns = [
        /based on (?:prior|previous) (?:experience|learning|failure)/i,
        /learned from:?\s*(.+)/i,
        /avoiding (?:previous|prior) (?:issue|error|mistake)/i,
        /applied (?:pattern|lesson) from:?\s*(.+)/i
    ]

    FOR pattern IN learning_patterns:
        IF content.match(pattern):
            decisions.append({
                type: 'approach_change',
                confidence: 'inferred',
                confidence_reason: 'Explicit learning reference in task',
                title: 'Applied prior learning',
                description: extractContext(content, pattern)
            })

    # Pattern: Skill selection mentions
    IF content.match(/selected .+ skill because/i):
        decisions.append({
            type: 'skill_selection',
            confidence: 'inferred',
            confidence_reason: 'Skill selection rationale mentioned',
            title: 'Skill selected based on reasoning',
            description: extractContext(content, /selected .+ skill/)
        })

    # Pattern: Model upgrade mentions
    IF content.match(/upgraded to (sonnet|opus) (?:because|due to)/i):
        decisions.append({
            type: 'model_upgrade',
            confidence: 'inferred',
            confidence_reason: 'Model upgrade rationale mentioned',
            title: 'Model upgraded',
            description: extractContext(content, /upgraded to/)
        })

    RETURN decisions
```

---

## Output Example

```
/dashboard backfill --dry-run

═══════════════════════════════════════════════════════════════════════════════
BACKFILL PREVIEW (Dry Run)
═══════════════════════════════════════════════════════════════════════════════

Historical Data Found:
  • 3 archived runs in journal/archive/
  • 1 current run in journal/
  • 12 issues in issue queue

Would Infer:
  Sessions:
    run-001: 4 issues (inferred), 2 decisions (inferred)
    run-002: 6 issues (inferred), 3 decisions (inferred)
    run-003: 2 issues (inferred), 1 decision (inferred)

  Issues by Source:
    Self-detected (inferred): 8
    User-reported (inferred): 12
    Prevented (guessed): 0 (skipped - use --include-guessed)

  Decisions Influenced:
    Skill selection: 3
    Model upgrade: 2
    Approach change: 1

Data Quality:
    Verified (observed): 0%
    Inferred: 100%
    Notes: All data from pattern matching, no instrumented runs

───────────────────────────────────────────────────────────────────────────────
Run without --dry-run to apply these changes.
Backfilled data will be clearly marked as 'inferred' in the dashboard.
═══════════════════════════════════════════════════════════════════════════════
```

---

## Conservative Inference Rules

1. **Never upgrade confidence**: Inferred data stays inferred, even if patterns are strong
2. **Prefer undercount**: If uncertain about source, mark as `unknown` not `self_detected`
3. **No guessing prevented**: Prevented issues require explicit anti-pattern matches
4. **Preserve existing**: Never overwrite instrumented data with inferred data
5. **Track reasoning**: Every inference includes `confidence_reason` explaining how it was determined

---

## Reversion

To remove all backfilled data:

```bash
# Find and remove backfilled sessions
for f in .claude/analytics/sessions/*.json; do
    if grep -q '"source": "backfilled"' "$f"; then
        rm "$f"
    fi
done

# Regenerate analytics from remaining (instrumented) data
/dashboard --regenerate
```

Or use the reversion guide in `docs/analytics_confidence_tagging.md`.

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/dashboard` | Generate dashboard (uses all available data) |
| `/dashboard --verified-only` | Dashboard with only observed data |
| `/analytics` | Text-based analytics |

---

*Backfill Command Version: 1.0*
*See: docs/analytics_confidence_tagging.md for data quality policy*
