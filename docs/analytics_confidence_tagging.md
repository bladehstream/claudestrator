# Analytics Confidence Tagging

## Overview

Analytics data points are tagged with confidence levels to distinguish between directly observed data (from instrumented runs) and inferred data (from parsing historical records).

**Added**: December 2025
**Status**: Experimental
**Reversion**: See [Reversion Guide](#reversion-guide) below

---

## Why Confidence Tagging?

When we added learning analytics, we faced a choice:
1. Only show data from runs after analytics was added (loses history)
2. Backfill historical data with inferences (risks polluting clean data)
3. **Do both, but tag data quality transparently** (chosen approach)

This allows the dashboard to show historical trends while being honest about data quality.

---

## Confidence Levels

| Level | Code | Meaning | Example |
|-------|------|---------|---------|
| **Observed** | `observed` | Directly captured by instrumented code | Issue recorded by `recordIssueSource()` function |
| **Inferred** | `inferred` | Parsed from structured records with high confidence | Journal task file explicitly says "QA found bug" |
| **Guessed** | `guessed` | Best-effort interpretation, may be wrong | Issue exists but source unclear, assumed from context |
| **Unknown** | `unknown` | Cannot determine, not counted in statistics | Pre-analytics run with no parseable data |

---

## Schema Changes

### Issue Records

```json
{
  "id": "IR-20251212-001",
  "source": "self_detected",
  "confidence": "observed",
  "confidence_reason": "Recorded by recordIssueSource() in Phase 4.4",
  "detector": "qa_agent",
  "description": "...",

  "_meta": {
    "schema_version": "2.0",
    "confidence_tagging": true
  }
}
```

### Decision Influences

```json
{
  "task": "task-007",
  "type": "skill_selection",
  "confidence": "observed",
  "confidence_reason": "Logged by logDecisionInfluences() during execution",
  "influenced_by": { ... },

  "_meta": {
    "schema_version": "2.0",
    "confidence_tagging": true
  }
}
```

### Session Archives

```json
{
  "session_id": "2025-12-12-run-003",
  "data_quality": {
    "overall": "observed",
    "issues_observed": 5,
    "issues_inferred": 0,
    "decisions_observed": 12,
    "decisions_inferred": 0
  },

  "_meta": {
    "schema_version": "2.0",
    "confidence_tagging": true
  }
}
```

---

## Backfill Rules

When parsing historical data, these conservative rules apply:

### Issue Source Inference

| Evidence | Inferred Source | Confidence |
|----------|-----------------|------------|
| Journal task mentions "QA found", "QA identified", "testing revealed" | `self_detected` | `inferred` |
| Issue queue entry with `ISSUE-*` ID | `user_reported` | `inferred` |
| Journal mentions "bug", "error", "fix" but no clear source | `unknown` | `unknown` |
| Strategy log shows anti-pattern was applicable but not triggered | `prevented` | `guessed` |

**Rule**: Never infer `prevented` with confidence higher than `guessed`.

### Decision Influence Inference

| Evidence | Inferred Type | Confidence |
|----------|---------------|------------|
| Strategy log entry directly before task with matching context | `skill_selection` | `inferred` |
| Task uses skill that was flagged in prior strategy feedback | `skill_selection` | `guessed` |
| Model upgraded after prior task failure at same complexity | `model_upgrade` | `guessed` |
| No evidence of learning influence | Not recorded | - |

**Rule**: If uncertain, don't record. Better to undercount than overcount.

---

## Dashboard Display

### Data Quality Indicator

```
┌─────────────────────────────────────────┐
│ DATA QUALITY: Mixed                     │
│ ████████████░░░░ 75% Verified           │
│                                         │
│ ○ 5 sessions with full instrumentation  │
│ ○ 2 sessions with inferred data         │
│ ○ 1 session with limited data           │
│                                         │
│ [Show verified only] [Show all]         │
└─────────────────────────────────────────┘
```

### Per-Metric Indicators

```
Self-Detected Issues: 67%
  └─ ✓ 45% verified  ⚡ 22% inferred

Decisions Influenced: 49%
  └─ ✓ 49% verified  (no inferred data)
```

### Filtered View

When "Show verified only" is selected:
- Only `observed` confidence data is included
- Charts may show fewer data points
- Warning: "Showing 5 of 8 sessions (verified only)"

---

## Reversion Guide

If confidence tagging proves problematic, here's how to cleanly remove it:

### Step 1: Identify Files Changed

```
templates/analytics/learning_insights.json   # Added confidence fields
templates/analytics/session_archive.json     # Added data_quality section
templates/analytics/dashboard.html           # Added quality indicators
commands/dashboard.md                        # Added backfill documentation
orchestrator_protocol_v3.md                  # Added confidence params to functions
docs/analytics_confidence_tagging.md         # This file (delete)
```

### Step 2: Schema Reversion

Remove from all analytics JSON files:
- `confidence` field from issue records
- `confidence_reason` field
- `data_quality` section from session archives
- `_meta.confidence_tagging` flag

### Step 3: Function Reversion

In `orchestrator_protocol_v3.md`:
- Remove `confidence` parameter from `recordIssueSource()`
- Remove `confidence` parameter from `logDecisionInfluences()`
- Remove `backfillHistoricalData()` function entirely

### Step 4: Dashboard Reversion

In `dashboard.html`:
- Remove data quality indicator section
- Remove "verified only" filter toggle
- Remove confidence-based styling (⚡ indicators)

### Step 5: Regenerate Analytics

```bash
# Delete analytics with inferred data
rm -rf .claude/analytics/

# Re-run to generate clean observed-only data
/dashboard
```

### Git Reversion

If all else fails, revert to commit before confidence tagging:

```bash
git log --oneline | grep "confidence tagging"
git revert <commit-hash>
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-12 | Added confidence tagging | Balance historical data value vs accuracy concerns |
| 2025-12-12 | Conservative inference rules | Prefer undercounting to overcounting |
| 2025-12-12 | Never infer "prevented" as observed | Too speculative, could inflate learning metrics |
| 2025-12-12 | Created reversion guide | User requested reversibility if approach fails |

---

## Success Criteria

Confidence tagging is working well if:
- [ ] Users understand what "verified" vs "inferred" means
- [ ] Dashboard is more useful with historical data than without
- [ ] No one is misled by inferred statistics
- [ ] "Verified only" view is trusted for important decisions

Consider removing if:
- [ ] Users find the quality indicators confusing
- [ ] Inferred data proves consistently wrong
- [ ] Maintenance burden outweighs value
- [ ] Simpler "observed only" approach is preferred

---

*Document Version: 1.0*
*Last Updated: December 2025*
