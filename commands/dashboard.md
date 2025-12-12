# /dashboard - Generate Visual Learning Dashboard

Generate an interactive HTML dashboard that visualizes learning progress, decision influences, and issue detection over time.

## Usage

```
/dashboard                    Generate and open dashboard
/dashboard --no-open          Generate without opening browser
/dashboard --output <path>    Generate to specific path
```

---

## What It Shows

The dashboard provides visual insights into:

### 1. Learning Trajectory
- Success rate trend across runs
- First-try success improvement
- Cost efficiency gains
- Estimation accuracy improvement

### 2. Self-Detected vs Reported Issues
- **Self-Detected**: Issues found by QA agents during testing
- **User Reported**: Issues submitted via `/issue` command
- **Prevented**: Issues that didn't occur due to learned patterns

### 3. Decisions Influenced by Learning
- Which task decisions were influenced by past experience
- Links between current decisions and their knowledge sources
- Anti-patterns avoided due to prior failures
- Patterns reused from successful tasks

### 4. Skill Effectiveness
- Visual bar chart of skill success rates
- Impact scoring vs baseline
- Usage frequency

### 5. Knowledge Flow
- How knowledge propagates from task → pattern → future decisions
- Visual connections in the knowledge graph

### 6. Cost Analysis
- Cost breakdown by model
- Efficiency improvements over time

---

## Dashboard Generation

```
FUNCTION generateDashboard():
    # Load analytics data
    trends = READ .claude/analytics/trends.json
    skills = READ .claude/analytics/skill_rankings.json
    errors = READ .claude/analytics/error_patterns.json
    insights = READ .claude/analytics/learning_insights.json
    sessions = READ .claude/analytics/sessions/*.json

    # Compile dashboard data
    data = {
        project: getProjectName(),
        sessionCount: sessions.length,
        lastUpdated: trends.last_updated,
        generatedAt: NOW(),

        learningScore: trends.learning_score,

        metrics: {
            successRate: trends.sessions[-1].success_rate * 100,
            successImprovement: trends.learning_metrics.success_rate_trend.improvement * 100,
            firstTryRate: trends.sessions[-1].first_try_rate * 100,
            firstTryImprovement: trends.learning_metrics.first_try_rate_trend.improvement * 100,
            costPerTask: trends.sessions[-1].cost_per_task,
            costImprovement: trends.learning_metrics.cost_efficiency_trend.improvement_percent,
            totalTasks: skills.total_tasks_analyzed,
            tasksCompleted: countCompleted(sessions),
            tasksFailed: countFailed(sessions)
        },

        sessions: formatSessionsForChart(trends.sessions),

        issues: {
            selfDetected: insights.issue_detection.self_detected.count,
            userReported: insights.issue_detection.user_reported.count,
            prevented: insights.issue_detection.prevented_by_learning.count,
            list: formatIssueList(insights, sessions)
        },

        decisions: formatDecisions(insights.decisions_influenced_by_learning),

        skills: formatSkillRankings(skills),

        knowledgeFlow: formatKnowledgeFlow(insights.knowledge_application),

        costByModel: formatCostByModel(sessions),

        estimationAccuracy: formatEstimationAccuracy(sessions)
    }

    # Read template
    template = READ .claudestrator/templates/analytics/dashboard.html

    # Replace placeholders with actual data
    html = replaceTemplatePlaceholders(template, data)

    # Write dashboard
    output_path = .claude/analytics/dashboard.html
    WRITE output_path = html

    # Open in browser (unless --no-open)
    IF NOT args.includes('--no-open'):
        OPEN output_path in default browser

    RETURN output_path
```

---

## Issue Source Tracking

Issues are categorized by how they were detected:

### Self-Detected (by QA Agent)
```yaml
source: self_detected
category: qa_found | build_error | test_failure | lint_error | type_error | runtime_error
detected_by: qa_agent | build_system | test_runner | linter | compiler
task: task-XXX
description: "..."
```

### User Reported (via /issue)
```yaml
source: user_reported
priority: critical | high | medium | low
issue_id: ISSUE-YYYYMMDD-NNN
task_created: task-XXX
description: "..."
```

### Prevented by Learning
```yaml
source: prevented
anti_pattern_id: AP-XXX
original_failure: { session, task, description }
prevention_method: "Avoided X because of prior failure in Y"
```

---

## Decision Influence Tracking

Each decision that references prior learning is logged:

```yaml
decision:
  task: task-007
  type: skill_selection | model_upgrade | context_adjustment | approach_change
  title: "Used api_designer skill for endpoint task"
  description: "Selected api_designer based on 100% success rate for similar tasks"
  influenced_by:
    type: learning | error | insight
    source: "Run 2, task-004: API endpoint failed without api_designer"
    knowledge_node: KN-XXX
  impact: positive | neutral | negative (assessed after task completes)
```

---

## Protocol Integration

### During Task Execution (Phase 3)

When selecting skills or making decisions, check for learning influence:

```
FUNCTION selectSkillsWithLearning(task):
    # Normal skill matching
    matched = matchSkillsToTask(task)

    # Check for learning-based adjustments
    strategy_log = READ .claude/strategy_log.json

    FOR signal IN strategy_log WHERE signal.type == 'skill_mismatch':
        IF signal.context.task_type == task.type:
            # Apply learned adjustment
            adjustment = applyLearnedAdjustment(signal)
            matched = adjustSkills(matched, adjustment)

            # Log the influence
            logDecisionInfluence({
                task: task.id,
                type: 'skill_selection',
                title: "Adjusted skills based on prior {signal.context.task}",
                influenced_by: {
                    type: 'error',
                    source: signal.source,
                    knowledge_node: signal.related_node
                }
            })

    RETURN matched
```

### During QA (Phase 4)

Track issue sources:

```
FUNCTION recordIssue(issue, source):
    insights = READ .claude/analytics/learning_insights.json

    IF source == 'qa_agent':
        insights.issue_detection.self_detected.count += 1
        insights.issue_detection.self_detected.by_category[issue.category] += 1
    ELSE IF source == 'user_reported':
        insights.issue_detection.user_reported.count += 1
        insights.issue_detection.user_reported.by_priority[issue.priority] += 1

    insights.issue_detection.total_issues += 1

    # Update detection ratio
    total = insights.issue_detection.total_issues
    self = insights.issue_detection.self_detected.count
    insights.issue_detection.self_detected.percentage = (self / total) * 100

    WRITE .claude/analytics/learning_insights.json
```

### Checking for Prevented Issues

When a pattern would have caused an issue but was avoided:

```
FUNCTION checkPreventedIssues(task, approach):
    anti_patterns = READ .claude/strategies.md (anti-patterns section)

    FOR pattern IN anti_patterns:
        IF wouldHaveApplied(pattern, task, approach):
            # This anti-pattern was avoided
            logPreventedIssue({
                anti_pattern: pattern.id,
                task: task.id,
                original_failure: pattern.source,
                prevention_method: pattern.alternative
            })

            insights.issue_detection.prevented_by_learning.count += 1
```

---

## Example Dashboard Output

When you run `/dashboard`, it generates:

```
═══════════════════════════════════════════════════════════════════════════════
DASHBOARD GENERATED
═══════════════════════════════════════════════════════════════════════════════

📊 Dashboard created: .claude/analytics/dashboard.html

Key Insights:
  • Learning Score: B+ (improving)
  • Success Rate: 75% → 94% (+19%)
  • Self-Detected Issues: 67% (vs 33% user-reported)
  • Decisions Influenced by Learning: 23 of 47 tasks (49%)
  • Issues Prevented: 4 (avoided due to learned anti-patterns)

Opening in browser...

═══════════════════════════════════════════════════════════════════════════════
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `.claude/analytics/dashboard.html` | Generated dashboard |
| `.claude/analytics/learning_insights.json` | Issue detection + decision influence data |

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/analytics` | Text-based analytics report |
| `/analytics trends` | Trend data in text format |
| `/progress` | Current session status |

---

*Dashboard Command Version: 1.0*
*Visualizes learning progression and decision influences*
