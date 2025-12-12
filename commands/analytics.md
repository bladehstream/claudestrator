# /analytics - Learning Analytics and Trend Analysis

Analyze orchestrator learning and performance over time. Tracks how effectively the system adapts based on past experience.

## Usage

```
/analytics                    Full learning report
/analytics trends             Success rate and cost trends across sessions
/analytics skills             Skill effectiveness rankings
/analytics models             Model performance comparison
/analytics errors             Error pattern analysis
/analytics decisions          Key decisions and their impact
/analytics forecast <task>    Predict effort for a task description
```

---

## Session Archival

Analytics requires historical data. The orchestrator automatically archives session data when a run completes:

**Archive Location**: `.claude/analytics/`

```
.claude/analytics/
├── sessions/
│   ├── 2025-12-01-run-001.json   # Archived metrics
│   ├── 2025-12-05-run-002.json
│   └── 2025-12-12-run-003.json
├── trends.json                    # Aggregated trend data
├── skill_rankings.json            # Skill effectiveness over time
├── error_patterns.json            # Common error classifications
└── learning_report.md             # Latest full analysis
```

---

## Full Learning Report (`/analytics`)

```
═══════════════════════════════════════════════════════════════════════════════
LEARNING ANALYTICS REPORT
═══════════════════════════════════════════════════════════════════════════════

Project: [Project Name]
Sessions Analyzed: 5 (Dec 1 - Dec 12, 2025)
Total Tasks Completed: 47

───────────────────────────────────────────────────────────────────────────────
LEARNING TRAJECTORY
───────────────────────────────────────────────────────────────────────────────

Success Rate Over Time:
  Run 1:  75% ████████░░░░░░░
  Run 2:  82% █████████░░░░░░
  Run 3:  88% ██████████░░░░░
  Run 4:  91% ███████████░░░░
  Run 5:  94% ████████████░░░
            ↑ +19% improvement

First-Try Success (no iteration needed):
  Run 1:  40%
  Run 5:  72%  ↑ +32%

Cost Accuracy (estimated vs actual):
  Run 1:  ±45% variance
  Run 5:  ±12% variance  ↑ Improved

───────────────────────────────────────────────────────────────────────────────
TOP LEARNINGS APPLIED
───────────────────────────────────────────────────────────────────────────────

1. [HIGH CONFIDENCE] Always include api_designer for endpoint tasks
   Applied: 8 times | Success: 100%
   Source: Run 2 task-004 failure → strategy update

2. [HIGH CONFIDENCE] Use Sonnet for complex React components
   Applied: 5 times | Success: 100%
   Source: Run 1 task-007 Haiku inadequate

3. [MEDIUM CONFIDENCE] Pair security_reviewer with authentication
   Applied: 3 times | Success: 100%
   Source: Run 3 security issue discovered in QA

4. [LOW CONFIDENCE] Consider database_designer for data-heavy APIs
   Applied: 1 time | Success: 100%
   Source: Run 5 recent addition

───────────────────────────────────────────────────────────────────────────────
ANTI-PATTERNS LEARNED
───────────────────────────────────────────────────────────────────────────────

❌ Don't use Haiku for complex state management
   Discovered: Run 1 | Avoided since: 4 times | Prevented failures: ~4

❌ Don't skip QA for UI changes
   Discovered: Run 2 | Enforced since: 6 tasks | Caught issues: 3

❌ Context > 50K tokens causes degradation
   Discovered: Run 3 | Reduced context: 5 times | Improved: 80%

───────────────────────────────────────────────────────────────────────────────
SKILL EVOLUTION
───────────────────────────────────────────────────────────────────────────────

Most Valuable Skills (by success impact):
  1. api_designer       +23% success when matched
  2. authentication     +18% success when matched
  3. react_patterns     +15% success when matched

Skills Needing Improvement:
  1. data_visualization  67% success (below avg)
  2. performance_tuning  75% success (below avg)

Skill Gaps Encountered:
  - "GraphQL" mentioned 3 times, no skill available
  - "WebSocket" mentioned 2 times, partial coverage

───────────────────────────────────────────────────────────────────────────────
MODEL OPTIMIZATION
───────────────────────────────────────────────────────────────────────────────

Model Selection Accuracy:
  Haiku correctly assigned:  92% (upgraded 2 tasks to Sonnet)
  Sonnet correctly assigned: 95% (1 could have been Haiku)
  Opus correctly assigned:   100%

Cost Efficiency:
  Haiku:  $0.02/task avg (simple tasks)
  Sonnet: $0.15/task avg (moderate tasks)
  Opus:   $0.45/task avg (complex tasks)

Recommendation: Current model selection is well-calibrated.

───────────────────────────────────────────────────────────────────────────────
ITERATION EFFECTIVENESS
───────────────────────────────────────────────────────────────────────────────

Iteration Success Rate: 89% (fix issues on first iteration)

Iteration Causes:
  - QA failures:           45%
  - Missing requirements:  30%
  - Integration issues:    15%
  - Performance concerns:  10%

Tasks Benefiting from Iteration:
  Run 1: 60% needed iteration
  Run 5: 28% needed iteration  ↓ Improvement

───────────────────────────────────────────────────────────────────────────────
KNOWLEDGE ACCUMULATION
───────────────────────────────────────────────────────────────────────────────

Knowledge Graph Stats:
  Total Nodes:     142
  Decision Nodes:  23 (key architectural choices)
  Pattern Nodes:   45 (code conventions learned)
  Gotcha Nodes:    18 (warnings and edge cases)
  Insight Nodes:   56 (general learnings)

Most Referenced:
  1. "API response format" (referenced 12 times)
  2. "Auth token handling" (referenced 8 times)
  3. "Error boundary pattern" (referenced 6 times)

───────────────────────────────────────────────────────────────────────────────
FORECAST ACCURACY
───────────────────────────────────────────────────────────────────────────────

Task Duration Estimates:
  Run 1: ±35% error
  Run 5: ±15% error  ↑ Improved

Token Usage Estimates:
  Run 1: ±40% error
  Run 5: ±18% error  ↑ Improved

Cost Estimates:
  Run 1: ±45% error
  Run 5: ±12% error  ↑ Improved

═══════════════════════════════════════════════════════════════════════════════
RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════

1. Consider creating a GraphQL skill (3 mentions, no coverage)
2. Review data_visualization skill (67% success is below average)
3. Current model selection is effective - maintain approach
4. Iteration rate has improved - continue emphasizing first-try quality

═══════════════════════════════════════════════════════════════════════════════
```

---

## Trend Analysis (`/analytics trends`)

```
═══════════════════════════════════════════════════════════════════════════════
PERFORMANCE TRENDS
═══════════════════════════════════════════════════════════════════════════════

Sessions: 5 | Period: Dec 1-12, 2025

SUCCESS RATE TREND
──────────────────
Run │ Tasks │ Success │ Trend
────┼───────┼─────────┼──────────────────────────
  1 │    8  │   75%   │ ████████░░░░░░░░
  2 │   10  │   82%   │ █████████░░░░░░░ ↑
  3 │   12  │   88%   │ ██████████░░░░░░ ↑
  4 │    9  │   91%   │ ███████████░░░░░ ↑
  5 │    8  │   94%   │ ████████████░░░░ ↑

Learning Rate: +4.75% per run
Projected Run 6: ~96% success

FIRST-TRY SUCCESS (no iteration)
────────────────────────────────
Run │ First-Try │ Trend
────┼───────────┼───────────────────────────
  1 │    40%    │ ████░░░░░░░░░░░░
  2 │    50%    │ █████░░░░░░░░░░░ ↑
  3 │    58%    │ ██████░░░░░░░░░░ ↑
  4 │    65%    │ ███████░░░░░░░░░ ↑
  5 │    72%    │ ████████░░░░░░░░ ↑

Learning Rate: +8% per run

COST PER SUCCESSFUL TASK
────────────────────────
Run │ $/Task │ Trend
────┼────────┼───────────────────────────
  1 │ $0.28  │ ████████████░░░░
  2 │ $0.22  │ █████████░░░░░░░ ↓ better
  3 │ $0.19  │ ████████░░░░░░░░ ↓ better
  4 │ $0.17  │ ███████░░░░░░░░░ ↓ better
  5 │ $0.15  │ ██████░░░░░░░░░░ ↓ better

Efficiency Gain: -46% cost per task

ESTIMATION ACCURACY
───────────────────
Run │ Token Est Error │ Trend
────┼─────────────────┼───────────────────────
  1 │     ±40%        │ Very inaccurate
  2 │     ±32%        │ Improving
  3 │     ±25%        │ Better
  4 │     ±18%        │ Good
  5 │     ±12%        │ Excellent

═══════════════════════════════════════════════════════════════════════════════
```

---

## Skill Rankings (`/analytics skills`)

```
═══════════════════════════════════════════════════════════════════════════════
SKILL EFFECTIVENESS RANKINGS
═══════════════════════════════════════════════════════════════════════════════

Based on 47 tasks across 5 sessions

TOP PERFORMERS (≥90% success when matched)
──────────────────────────────────────────
Rank │ Skill               │ Uses │ Success │ Impact
─────┼─────────────────────┼──────┼─────────┼──────────────────
  1  │ api_designer        │  12  │  100%   │ +23% vs baseline
  2  │ authentication      │   8  │  100%   │ +18% vs baseline
  3  │ react_patterns      │  10  │   95%   │ +15% vs baseline
  4  │ database_designer   │   6  │   95%   │ +12% vs baseline
  5  │ software_security   │   5  │   92%   │ +10% vs baseline

AVERAGE PERFORMERS (75-89% success)
───────────────────────────────────
Rank │ Skill               │ Uses │ Success │ Notes
─────┼─────────────────────┼──────┼─────────┼──────────────────
  6  │ frontend_design     │   7  │   86%   │ UI complexity varies
  7  │ testing_patterns    │   4  │   82%   │ Consider pairing with qa
  8  │ documentation       │   3  │   80%   │ Adequate

NEEDS IMPROVEMENT (<75% success)
────────────────────────────────
Rank │ Skill               │ Uses │ Success │ Recommendation
─────┼─────────────────────┼──────┼─────────┼───────────────────────
  9  │ data_visualization  │   3  │   67%   │ Review/enhance skill
 10  │ performance_tuning  │   4  │   75%   │ Add more techniques

SKILL GAPS (requested but unavailable)
──────────────────────────────────────
Gap          │ Mentions │ Substitution Used │ Effectiveness
─────────────┼──────────┼───────────────────┼──────────────
GraphQL      │    3     │ api_designer      │ 67% (partial)
WebSocket    │    2     │ api_designer      │ 50% (poor)
i18n         │    1     │ none              │ N/A

SKILL COMBINATIONS (synergy analysis)
─────────────────────────────────────
Combination                        │ Uses │ Success │ Synergy
───────────────────────────────────┼──────┼─────────┼─────────
api_designer + database_designer   │  4   │  100%   │ +15%
authentication + software_security │  3   │  100%   │ +20%
react_patterns + frontend_design   │  5   │   92%   │ +8%

═══════════════════════════════════════════════════════════════════════════════
```

---

## Model Comparison (`/analytics models`)

```
═══════════════════════════════════════════════════════════════════════════════
MODEL PERFORMANCE ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

Based on 47 tasks across 5 sessions

OVERALL PERFORMANCE
───────────────────
Model  │ Tasks │ Success │ Avg Time │ Avg Tokens │ Avg Cost
───────┼───────┼─────────┼──────────┼────────────┼──────────
Haiku  │  15   │   93%   │   45s    │   3,500    │  $0.02
Sonnet │  28   │   89%   │   85s    │  12,000    │  $0.15
Opus   │   4   │  100%   │  120s    │  25,000    │  $0.45

BY COMPLEXITY
─────────────
            │ Easy Tasks │ Normal Tasks │ Complex Tasks
────────────┼────────────┼──────────────┼──────────────
Haiku       │    100%    │     85%      │     N/A
Sonnet      │     95%    │     90%      │     80%
Opus        │     N/A    │    100%      │    100%

UPGRADE/DOWNGRADE ANALYSIS
──────────────────────────
Scenario                          │ Count │ Outcome
──────────────────────────────────┼───────┼─────────
Haiku → Sonnet (complexity)       │   2   │ Both succeeded after upgrade
Sonnet → Haiku (could simplify)   │   1   │ Would have saved $0.13
Sonnet → Opus (complexity)        │   1   │ Succeeded after upgrade

MODEL SELECTION ACCURACY
────────────────────────
Initial Selection │ Correct │ Upgraded │ Could Downgrade
──────────────────┼─────────┼──────────┼────────────────
Haiku             │   92%   │    8%    │      0%
Sonnet            │   95%   │    4%    │      1%
Opus              │  100%   │    0%    │      0%

COST EFFICIENCY
───────────────
Model  │ $/Success │ Tokens/Success │ Best For
───────┼───────────┼────────────────┼─────────────────────────────
Haiku  │   $0.02   │    3,500       │ Setup, simple CRUD, docs
Sonnet │   $0.17   │   13,500       │ Features, integrations, tests
Opus   │   $0.45   │   25,000       │ Architecture, complex logic

RECOMMENDATION:
Current model selection is well-calibrated. Consider:
- Moving more "normal" tasks to Haiku when acceptance criteria are simple
- Continue using Opus sparingly for high-stakes decisions

═══════════════════════════════════════════════════════════════════════════════
```

---

## Error Pattern Analysis (`/analytics errors`)

```
═══════════════════════════════════════════════════════════════════════════════
ERROR PATTERN ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

Based on 47 tasks, 8 failures, 12 iterations

ERROR FREQUENCY
───────────────
Category              │ Count │ Trend     │ Impact
──────────────────────┼───────┼───────────┼──────────────────
Missing requirements  │   4   │ ↓ Decreasing │ Medium (iteration)
Type/lint errors      │   3   │ → Stable     │ Low (quick fix)
Integration failures  │   2   │ ↓ Decreasing │ High (rework)
Performance issues    │   1   │ → New        │ Medium (iteration)

ERROR PATTERNS
──────────────
Pattern                               │ Occurrences │ Prevention Applied
──────────────────────────────────────┼─────────────┼─────────────────────
API response format mismatch          │     3       │ api_designer skill
Missing null checks in data handling  │     2       │ Added to code review
Auth token expiry not handled         │     2       │ authentication skill
Component re-render loops             │     1       │ react_patterns skill

ERRORS BY TASK TYPE
───────────────────
Task Type      │ Errors │ Most Common
───────────────┼────────┼────────────────────────────
Implementation │   5    │ Missing edge cases
Integration    │   2    │ API contract mismatches
Testing        │   1    │ Flaky test conditions

ERRORS BY MODEL
───────────────
Model  │ Errors │ Rate │ Pattern
───────┼────────┼──────┼──────────────────────────────
Haiku  │   3    │ 20%  │ Complexity underestimation
Sonnet │   5    │ 18%  │ Integration assumptions
Opus   │   0    │  0%  │ N/A

ROOT CAUSE ANALYSIS
───────────────────
Root Cause                    │ Count │ Mitigation
──────────────────────────────┼───────┼─────────────────────────────
Insufficient context provided │   3   │ ↑ Context budget for type
Skill gap (missing expertise) │   2   │ Created/enhanced skills
Ambiguous requirements        │   2   │ PRD clarification process
Model capability limit        │   1   │ Upgraded to higher model

PREVENTION EFFECTIVENESS
────────────────────────
After mitigation applied:
- Insufficient context:  0 recurrences (100% prevented)
- Skill gaps:            0 recurrences (100% prevented)
- Ambiguous requirements: 1 recurrence (50% prevented)

═══════════════════════════════════════════════════════════════════════════════
```

---

## Forecast (`/analytics forecast <task>`)

Predict effort for a task before execution:

```
/analytics forecast "Add user profile editing with avatar upload"

═══════════════════════════════════════════════════════════════════════════════
TASK FORECAST
═══════════════════════════════════════════════════════════════════════════════

Task: "Add user profile editing with avatar upload"

SIMILAR PAST TASKS
──────────────────
1. "Add user settings page" (Run 2, task-005)
   Complexity: normal | Model: Sonnet | Duration: 4m 12s | Success: ✓

2. "Implement file upload for documents" (Run 3, task-008)
   Complexity: normal | Model: Sonnet | Duration: 5m 45s | Success: ✓

3. "Create profile display component" (Run 1, task-003)
   Complexity: easy | Model: Haiku | Duration: 2m 30s | Success: ✓

PREDICTIONS
───────────
                  │ Estimate │ Confidence │ Range
──────────────────┼──────────┼────────────┼───────────
Complexity        │ normal   │    85%     │ easy-normal
Recommended Model │ Sonnet   │    90%     │ -
Duration          │ 4-6 min  │    80%     │ 3-8 min
Tokens            │ ~12,000  │    75%     │ 8K-16K
Cost              │ ~$0.15   │    75%     │ $0.10-$0.22

SKILL RECOMMENDATIONS
─────────────────────
Required:  frontend_design, react_patterns
Suggested: api_designer (for avatar upload endpoint)
Consider:  software_security (file upload validation)

RISK FACTORS
────────────
⚠ File upload adds complexity - consider Opus if real-time preview needed
⚠ Avatar resizing may need image processing - check dependencies
✓ Similar tasks succeeded - good precedent

ITERATION LIKELIHOOD: 25%
Based on: 72% first-try success rate for similar complexity

═══════════════════════════════════════════════════════════════════════════════
```

---

## Implementation

### Session Archival (automatic)

When a run completes (Phase 5), archive metrics:

```
FUNCTION archiveSession():
    session_id = FORMAT(NOW(), "YYYY-MM-DD") + "-run-" + run_number

    # Copy metrics to archive
    COPY .claude/metrics.json TO .claude/analytics/sessions/{session_id}.json

    # Update trends
    updateTrendData(session_id, metrics)

    # Update skill rankings
    updateSkillRankings(metrics)

    # Detect error patterns
    analyzeErrorPatterns(journal_entries)

    # Generate learning report
    generateLearningReport()
```

### Trend Calculation

```
FUNCTION updateTrendData(session_id, metrics):
    READ .claude/analytics/trends.json

    session_summary = {
        id: session_id,
        date: NOW(),
        tasks_total: metrics.totals.tasks,
        tasks_success: metrics.totals.success,
        success_rate: metrics.totals.success / metrics.totals.tasks,
        first_try_rate: countFirstTrySuccess(journal) / metrics.totals.tasks,
        cost_per_task: metrics.totals.estimated_cost / metrics.totals.tasks,
        token_estimate_error: calculateEstimateError(metrics),
        iterations_needed: countIterations(journal)
    }

    trends.sessions.append(session_summary)

    # Calculate learning rate
    IF trends.sessions.length >= 2:
        trends.learning_rate = (
            trends.sessions[-1].success_rate -
            trends.sessions[0].success_rate
        ) / trends.sessions.length

    WRITE .claude/analytics/trends.json
```

### Learning Score

Composite metric for overall learning:

```
FUNCTION calculateLearningScore():
    weights = {
        success_improvement: 0.3,    # Success rate trend
        first_try_improvement: 0.25, # Reduced iterations
        cost_efficiency: 0.2,        # Lower cost per success
        estimate_accuracy: 0.15,     # Better predictions
        error_prevention: 0.1        # Avoided repeat errors
    }

    scores = {
        success_improvement: (latest.success_rate - first.success_rate) / first.success_rate,
        first_try_improvement: (latest.first_try - first.first_try) / first.first_try,
        cost_efficiency: (first.cost_per_task - latest.cost_per_task) / first.cost_per_task,
        estimate_accuracy: (first.estimate_error - latest.estimate_error) / first.estimate_error,
        error_prevention: prevented_errors / total_potential_errors
    }

    learning_score = SUM(scores[k] * weights[k] for k in weights)

    RETURN {
        score: learning_score,
        grade: scoreToGrade(learning_score),  # A, B, C, D, F
        breakdown: scores
    }
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `.claude/analytics/sessions/*.json` | Archived session metrics |
| `.claude/analytics/trends.json` | Aggregated trend data |
| `.claude/analytics/skill_rankings.json` | Skill effectiveness over time |
| `.claude/analytics/error_patterns.json` | Classified error patterns |
| `.claude/analytics/learning_report.md` | Latest full analysis |

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/progress metrics` | Current session metrics |
| `/progress tasks` | Current task status |
| `/audit-skills` | Skill library health |

---

*Analytics Command Version: 1.0*
*Tracks learning, trends, and performance optimization over time*
