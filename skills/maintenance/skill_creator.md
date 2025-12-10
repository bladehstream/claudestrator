---
name: Skill Creator
id: skill_creator
version: 1.0
category: maintenance
domain: [orchestrator, skills, meta]
task_types: [creation, documentation, planning]
keywords: [skill, create, new, extend, capability, workflow, tool, integration, domain]
complexity: [normal, complex]
pairs_with: [skill_auditor, skill_enhancer]
source: https://github.com/anthropics/skills/tree/main/skills/skill-creator
---

# Skill Creator

## Role

Guide for creating effective skills. Use when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.

## About Skills

Skills are modular packages extending Claude's capabilities through specialized knowledge, workflows, and tool integrations - essentially domain-specific onboarding systems.

### What Skills Provide

1. **Specialized workflows**: Multi-step procedures for specific domains
2. **Tool integrations**: Instructions for working with specific file formats or APIs
3. **Domain expertise**: Company-specific knowledge, schemas, business logic
4. **Bundled resources**: Scripts, references, and assets for complex tasks

## Core Principles

### Concise is Key

"The context window is a public good." Assume Claude possesses existing knowledge; only contribute information that's genuinely absent. Validate whether each component justifies its token consumption.

### Set Appropriate Degrees of Freedom

Match specificity to task requirements:

| Freedom Level | Format | When to Use |
|---------------|--------|-------------|
| High | Text instructions | Valid alternatives exist, context-dependent |
| Medium | Pseudocode/parameters | Preferred patterns, some variation OK |
| Low | Specific scripts | Operations demand precision |

## Skill Anatomy

### Required Structure
```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/
    ├── references/
    └── assets/
```

### SKILL.md Requirements

**Frontmatter**:
```yaml
---
name: Human-Readable Name
description: When to use this skill. Include trigger contexts.
---
```

**Body**: Instructions for using skill and bundled resources.

### Bundled Resources

**Scripts** (`scripts/`):
- Executable code for deterministic tasks
- Include when code is consistently rewritten

**References** (`references/`):
- Documentation loaded contextually
- Schemas, API docs, policies, detailed workflows
- Preferred for large files (>10k words)

**Assets** (`assets/`):
- Output-destined files (templates, images, boilerplate)
- Logos, templates, fonts

**Do NOT Include**:
- README.md
- INSTALLATION_GUIDE.md
- CHANGELOG.md
- Auxiliary documentation

## Progressive Disclosure

### Three-Level Loading

1. **Metadata** (name + description) - Always present
2. **SKILL.md body** - When triggered (<5k words)
3. **Bundled resources** - As needed

### Implementation Patterns

**Pattern 1: High-level guide with references**
Keep core workflow in SKILL.md, move variant details to separate files.

**Pattern 2: Domain-specific organization**
Organize by domain (finance.md, sales.md) to load only relevant context.

**Pattern 3: Conditional details**
Show basics, link advanced content conditionally.

**Guidelines**:
- One-level-deep references from SKILL.md
- Structure longer files (>100 lines) with table of contents

## Skill Creation Process

### Step 1: Understanding with Concrete Examples

Establish clear usage patterns through:
- Direct examples from user
- Validated generated examples

Understand:
- Required functionality
- Triggering language
- Expected outputs

### Step 2: Planning Reusable Contents

Analyze examples to identify:
- Scripts needed
- References required
- Assets to bundle

### Step 3: Initializing the Skill

```bash
# Create skill structure
mkdir -p skill-name/{scripts,references,assets}
touch skill-name/SKILL.md
```

### Step 4: Edit the Skill

**Writing guidelines**:
- Use imperative/infinitive form
- Include procedural knowledge
- Add domain-specific details

**Frontmatter requirements**:
- `name`: Skill identifier
- `description`: Primary trigger mechanism with "when to use" contexts

**Body**: Instructions for using skill and bundled resources

### Step 5: Validate the Skill

Check:
- YAML structure valid
- Naming conventions followed
- Resources complete
- Instructions clear

### Step 6: Iterate

1. Test on real tasks
2. Identify improvements
3. Update SKILL.md or resources
4. Retest

## Skill Template

```yaml
---
name: [Skill Name]
id: [skill_id]
version: 1.0
category: [category]
domain: [domain1, domain2]
task_types: [type1, type2]
keywords: [keyword1, keyword2]
complexity: [easy, normal, complex]
pairs_with: [other_skill_id]
---

# [Skill Name]

## Role

[One paragraph describing specialization and when to use]

## Core Competencies

- [Competency 1]
- [Competency 2]

## Patterns and Standards

### [Pattern Name]

```[language]
[Code example]
```

**When to use**: [Brief explanation]

## Quality Standards

- [Standard 1]
- [Standard 2]

## Anti-Patterns to Avoid

| Anti-Pattern | Why Bad | Better Approach |
|--------------|---------|-----------------|
| [Bad practice] | [Consequence] | [Good practice] |

## Output Expectations

- [ ] [Expected behavior 1]
- [ ] [Expected behavior 2]
```

## Quality Checklist

- [ ] Frontmatter complete and valid
- [ ] Description includes trigger contexts
- [ ] Instructions are actionable
- [ ] Code examples tested
- [ ] Resources are necessary (not bloat)
- [ ] Progressive disclosure implemented
- [ ] Tested on real tasks

---

*Skill Version: 1.0*
*Source: Anthropic skill-creator skill*
