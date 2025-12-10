# /audit-skills - Audit Skill Library Health

Spawn a Skill Auditor agent to analyze the skill library and generate a health report.

## Usage

```
/audit-skills
/audit-skills [path]
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `path` | No | Custom skill directory path. Defaults to configured skill directory. |

## What It Does

1. **Spawns** a Skill Auditor agent (Sonnet model)
2. **Scans** all `.md` files in the skill directory
3. **Validates** metadata against required schema
4. **Checks** for stale skills (>90 days without updates)
5. **Detects** deprecated references in skill content
6. **Analyzes** category coverage
7. **Returns** a comprehensive health report

## Agent Configuration

```yaml
skill: skill_auditor
model: sonnet
complexity: normal
task_type: audit
```

## Expected Output

The agent returns a structured report:

```markdown
# Skill Audit Report

**Generated:** 2024-12-10 14:30:00
**Skills Directory:** ~/.claude/skills/
**Total Skills Scanned:** 12

---

## Summary

| Metric | Count |
|--------|-------|
| Valid Skills | 10 |
| Missing Metadata | 2 |
| Stale (>90 days) | 3 |
| Deprecated References | 1 |
| Categories Covered | 8 |

### Health Score: 78/100

---

## 1. Missing or Invalid Metadata
[Details...]

## 2. Stale Skills
[Details...]

## 3. Deprecated References Found
[Details...]

## 4. Category Analysis
[Details...]

## 5. Recommendations Summary
[Priority-ordered action items...]
```

## Orchestrator Behavior

```
ON /audit-skills:
    1. DETERMINE skill directory
       - Use provided path if given
       - Otherwise use configured skill_directory
       - Fall back to default locations

    2. SPAWN agent
       Task(
           subagent_type: "general-purpose",
           model: "sonnet",
           prompt: [skill_auditor skill + directory path],
           description: "Skill library audit"
       )

    3. RECEIVE report from agent

    4. DISPLAY report to user

    5. PROMPT user:
       "To enhance a specific skill, run: /skill-enhance [skill_id]"
```

## Follow-Up Actions

After reviewing the audit report, user can:

| Finding | Action |
|---------|--------|
| Missing metadata | Edit skill file directly OR `/skill-enhance [id]` |
| Stale skill | `/skill-enhance [skill_id]` for research-backed updates |
| Deprecated reference | `/skill-enhance [skill_id]` to propose updates |
| Coverage gap | Create new skill using `skill_template.md` |

## Example Session

```
User: /audit-skills

Orchestrator: Spawning Skill Auditor to analyze skill library...

[Agent runs, returns report]

Orchestrator:
═══════════════════════════════════════════════════════════
SKILL AUDIT COMPLETE
═══════════════════════════════════════════════════════════

Health Score: 78/100

Issues Found:
• 2 skills missing required metadata
• 3 skills not updated in >90 days
• 1 deprecated reference (Node 16)

High Priority:
1. Add 'category' field to custom_react skill
2. Review vue_components for Vue 3 updates

To address issues:
  /skill-enhance vue_components
  /skill-enhance custom_react

Full report saved to: .claude/reports/skill-audit-2024-12-10.md
═══════════════════════════════════════════════════════════

User: /skill-enhance vue_components
[Enhancement flow begins...]
```

## Notes

- Audit is **read-only** - no files are modified
- Report can be saved for tracking over time
- Run periodically (monthly recommended) to maintain skill health
- Agent does NOT require web access (local analysis only)

---

*Command Version: 1.0*
