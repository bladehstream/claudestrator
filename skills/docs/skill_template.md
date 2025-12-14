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
source: original  # REQUIRED: original, external, local, or URL
external_dependencies: []  # See External Dependencies section below
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
| version | Skill version (X.Y format) | "1.0", "1.1" |
| category | **REQUIRED** Directory category | implementation, design, quality, support, maintenance, security, domain, orchestrator |
| domain | Applicable project domains | web, game, backend, api, data, devops, mobile |
| task_types | Types of tasks this handles | design, implementation, feature, bugfix, refactor, testing, documentation |
| keywords | Matching keywords | Any relevant terms |
| complexity | **MUST be array** | [easy], [normal], [complex], [easy, normal] |
| pairs_with | Complementary skill IDs | Other skill IDs (verify they exist) |
| source | **REQUIRED** Origin of skill | original, external, local, or URL |
| external_dependencies | External APIs/services/env vars required | See External Dependencies section |

### External Dependencies Field

Skills that require external APIs, services, or environment variables must declare them in the `external_dependencies` array and include a **Pre-Flight Check** section.

**Dependency Types:**

| Type | Description | Example |
|------|-------------|---------|
| `env_var` | Environment variable (API key, token) | `OPENAI_API_KEY`, `GEMINI_API_KEY` |
| `service` | Running service (database, server) | PostgreSQL, Redis, local server |
| `cli_tool` | Command-line tool | `ffmpeg`, `imagemagick`, `docker` |
| `npm_package` | Node.js package (global) | `typescript`, `eslint` |
| `python_package` | Python package | `pandas`, `numpy` |

**Frontmatter Format:**

```yaml
external_dependencies:
  - type: env_var
    name: GEMINI_API_KEY
    description: Google Gemini API key for image/code generation
    setup_url: https://aistudio.google.com/apikey
    required: true
  - type: cli_tool
    name: ffmpeg
    description: Video/audio processing
    setup_url: https://ffmpeg.org/download.html
    required: false  # Optional dependency
```

**Pre-Flight Check Section:**

Skills with external dependencies MUST include a "Pre-Flight Check" section immediately after the Capabilities/Role section:

```markdown
## Pre-Flight Check (MANDATORY)

**You MUST run this check before using this skill. Do NOT skip.**

\`\`\`bash
# Check for required API key
if [ -n "$REQUIRED_VAR" ]; then
    echo "✓ REQUIRED_VAR is set"
else
    echo "✗ REQUIRED_VAR is NOT set - CANNOT PROCEED"
    echo ""
    echo "This skill requires [description]."
    echo "Setup instructions:"
    echo "  1. [Step 1]"
    echo "  2. [Step 2]"
    echo "  3. Set: export REQUIRED_VAR=\"your-value\""
    echo ""
    echo "STOP: Report this task as BLOCKED with the above instructions."
    exit 1
fi
\`\`\`

**If the check fails:**
1. Do NOT attempt to proceed with the task
2. Do NOT try workarounds or alternative approaches
3. Report the task as **BLOCKED** in your handoff
4. Include the setup instructions in your blocker notes
5. The orchestrator will surface this to the user
```

### Category Field

The `category` field determines which directory the skill is stored in and enables skill deduplication. Only one skill per category is selected for each agent to prevent redundant skills.

**Standard Categories (must match directory structure):**

| Category | Description | Examples |
|----------|-------------|----------|
| `implementation` | Building/coding features | api_development, databases, html5_canvas, game_feel |
| `design` | Planning/architecture | api_designer, database_designer, frontend_design |
| `quality` | Testing/review/QA | qa_agent, security_reviewer, playwright_qa_agent |
| `support` | Supporting tasks | documentation, refactoring, prd_generator, xlsx |
| `maintenance` | Skill/system maintenance | skill_auditor, skill_enhancer, dependency_updater |
| `security` | Security implementation | authentication, software_security, backend_security |
| `domain` | Domain-specific expertise | financial_app, healthcare, e-commerce |
| `orchestrator` | Orchestration agents | decomposition_agent, agent_construction |

**IMPORTANT:** The category value MUST match one of the directory names under `.claude/skills/`. Non-standard categories will be flagged by `/audit-skills`.

---

*Template Version: 1.0*
