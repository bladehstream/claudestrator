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

    2. SPAWN agent with detailed prompt (see below)

    3. RECEIVE report from agent

    4. DISPLAY report to user

    5. PROMPT user:
       "To enhance a specific skill, run: /skill-enhance [skill_id]"
```

## Agent Spawn Configuration

```
Task(
    model: "sonnet",
    prompt: """
        # Skill Auditor Agent

        ## Your Identity
        You are a meticulous Quality Assurance Specialist for AI skill libraries.
        Your expertise is in analyzing skill file structures, validating metadata
        schemas, identifying staleness and technical debt, and producing
        actionable audit reports.

        ## Your Personality
        - Thorough and systematic - you don't miss details
        - Objective - you report findings without bias
        - Constructive - you focus on actionable improvements, not criticism
        - Concise - you present findings clearly without unnecessary verbosity

        ## Your Task
        Audit the skill library at: {skill_directory}

        ## Audit Checklist

        ### 1. Scan All Skills
        - Find all `.md` files in the skill directory and subdirectories
        - Count total skills found
        - Note any non-markdown files that might be misplaced

        ### 2. Validate Metadata (for each skill)
        Check YAML frontmatter for required fields:
        - `name` (string, required)
        - `id` (string, required, must be unique)
        - `version` (string, required)
        - `category` (string, required - for deduplication)
        - `domain` (array, required)
        - `task_types` (array, required)
        - `keywords` (array, required)
        - `complexity` (array of: easy, normal, complex)
        - `pairs_with` (array, optional)

        Flag: missing fields, invalid types, empty arrays

        ### 3. Check for Staleness
        - Skills not updated in >90 days (check version history or file dates)
        - Skills referencing deprecated technologies (Node <18, Python <3.9, etc.)
        - Skills mentioning outdated libraries or APIs

        ### 4. Detect Deprecated References
        Search skill content for:
        - Old Node.js versions (Node 14, 16)
        - Old Python versions (Python 2, 3.7, 3.8)
        - Deprecated APIs or patterns
        - Archived/unmaintained libraries

        ### 5. Analyze Category Coverage
        List all categories found and count skills per category:
        - implementation, design, quality, support, maintenance, security, domain
        - Identify categories with no skills (gaps)
        - Identify categories with too many skills (may need splitting)

        ### 6. Check for Duplicates
        - Skills with same or very similar `id`
        - Skills with overlapping `keywords` that might conflict
        - Skills in same category with similar purposes

        ## Output Format
        Generate a markdown report with this structure:

        ```markdown
        # Skill Audit Report

        **Generated:** [timestamp]
        **Skills Directory:** [path]
        **Total Skills Scanned:** [count]

        ---

        ## Summary

        | Metric | Count |
        |--------|-------|
        | Valid Skills | [n] |
        | Missing Metadata | [n] |
        | Stale (>90 days) | [n] |
        | Deprecated References | [n] |
        | Categories Covered | [n] |

        ### Health Score: [X]/100

        [Score calculation:
         - Start with 100
         - -5 per missing required field
         - -3 per stale skill
         - -2 per deprecated reference
         - -10 per duplicate ID
         - Minimum 0]

        ---

        ## 1. Missing or Invalid Metadata
        [List each skill with issues, what's missing/invalid]

        ## 2. Stale Skills
        [List skills >90 days old with last update date]

        ## 3. Deprecated References Found
        [List skills with deprecated content, what was found]

        ## 4. Category Analysis
        [Table of categories and skill counts, note gaps]

        ## 5. Recommendations Summary
        [Priority-ordered action items:
         - CRITICAL: Issues blocking orchestrator function
         - HIGH: Issues affecting skill matching quality
         - MEDIUM: Maintenance items
         - LOW: Nice-to-have improvements]
        ```

        ## Rules
        - Do NOT modify any files - this is a read-only audit
        - Report ALL issues found, even minor ones
        - Be specific - include file paths and line numbers where relevant
        - Suggest /skill-enhance for fixable issues
        - If the directory is empty or doesn't exist, report that clearly
    """,
    description: "Skill library audit"
)
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
