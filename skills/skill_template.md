---
name: [Skill Name]
id: [skill_id_lowercase]
version: 1.0
category: [primary_category]
domain: [domain1, domain2]
task_types: [type1, type2]
keywords: [keyword1, keyword2, keyword3]
complexity: [easy, normal, complex]
pairs_with: [other_skill_id1, other_skill_id2]
---

# [Skill Name]

## Role

[One paragraph describing what this agent specializes in and when it should be used.]

## Core Competencies

- [Competency 1]
- [Competency 2]
- [Competency 3]
- [Competency 4]
- [Competency 5]

## Patterns and Standards

### [Pattern Name 1]

```[language]
[Code example demonstrating the pattern]
```

**When to use**: [Brief explanation]

### [Pattern Name 2]

```[language]
[Code example demonstrating the pattern]
```

**When to use**: [Brief explanation]

## Quality Standards

- [Standard 1 - what good looks like]
- [Standard 2 - what good looks like]
- [Standard 3 - what good looks like]

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| [Bad practice] | [Consequence] | [Good practice] |
| [Bad practice] | [Consequence] | [Good practice] |

## Decision Framework

When facing [common decision type]:

1. **Consider**: [Factor 1]
2. **Evaluate**: [Factor 2]
3. **Choose based on**: [Decision criteria]

## Output Expectations

When this skill is applied, the agent should:

- [ ] [Expected behavior 1]
- [ ] [Expected behavior 2]
- [ ] [Expected behavior 3]

## Example Task

**Objective**: [Example task this skill would handle]

**Approach**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Output**: [What the result looks like]

---

## Metadata Reference

| Field | Description | Example Values |
|-------|-------------|----------------|
| name | Human-readable skill name | "HTML5 Canvas Developer" |
| id | Unique lowercase identifier | "html5_canvas" |
| version | Skill version | "1.0" |
| category | Primary skill category (for deduplication) | rendering, testing, design, documentation, security, refactoring, assets |
| domain | Applicable project domains | web, game, backend, api, data, devops |
| task_types | Types of tasks this handles | design, implementation, feature, bugfix, refactor, testing, documentation |
| keywords | Matching keywords | Any relevant terms |
| complexity | Complexity levels supported | easy, normal, complex |
| pairs_with | Complementary skill IDs | Other skill IDs |

### Category Field

The `category` field enables skill deduplication: only one skill per category is selected for each agent. This prevents redundant skills (e.g., two debugging skills or three rendering skills).

**Standard Categories:**
| Category | Description |
|----------|-------------|
| `rendering` | Graphics, canvas, sprites, visual output |
| `game-mechanics` | Game design, physics, gameplay |
| `polish` | Game feel, juice, UX polish |
| `api-design` | API architecture, endpoints |
| `testing` | QA, verification, validation |
| `security` | Security review, vulnerabilities |
| `ux-review` | User experience, accessibility |
| `assets` | SVG, images, audio generation |
| `refactoring` | Code restructuring |
| `documentation` | Technical writing, docs |

---

*Template Version: 1.0*
