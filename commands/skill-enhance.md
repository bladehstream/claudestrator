# /skill-enhance - Enhance a Specific Skill

Spawn a Skill Enhancer agent to research and propose updates to a specific skill, with human approval required for all changes.

## Usage

```
/skill-enhance [skill_id]
/skill-enhance [skill_id] --focus [area]
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `skill_id` | Yes | The ID of the skill to enhance (e.g., `html5_canvas`, `qa_agent`) |
| `--focus` | No | Specific area to focus on: `metadata`, `patterns`, `versions`, `all` |

## What It Does

1. **Spawns** a Skill Enhancer agent (Opus model for comprehensive research)
2. **Reads** the target skill file completely
3. **Searches** the web for current best practices and updates
4. **Generates** a proposal with specific changes in diff format
5. **Presents** proposal to user with risk assessment
6. **Waits** for explicit user approval
7. **Applies** only approved changes

## Agent Configuration

```yaml
skill: skill_enhancer
model: opus
complexity: complex
task_type: enhancement
web_access: true
```

## Human-in-the-Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│  USER: /skill-enhance vue_components                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Research Phase                                      │
│  • Read current skill                                       │
│  • Search web for updates                                   │
│  • Identify potential changes                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Present Proposal                                    │
│  • Show each change with diff                               │
│  • Include rationale and sources                            │
│  • Assess risk level                                        │
│  • ASK: "Which changes to apply?"                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  USER: Review & Decide                                      │
│  • "Apply all"                                              │
│  • "Apply 1, 3, 5"                                          │
│  • "Reject"                                                 │
│  • "Edit change 2: [modification]"                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Apply Approved Changes Only                         │
│  • Modify skill file                                        │
│  • Update version number                                    │
│  • Log to knowledge graph                                   │
└─────────────────────────────────────────────────────────────┘
```

## User Response Options

| Response | Effect |
|----------|--------|
| `Apply all` | Apply all proposed changes |
| `Apply 1, 3` | Apply only changes numbered 1 and 3 |
| `Reject` or `Skip` | Make no changes |
| `Edit change 2: [text]` | Modify change 2 before applying |
| `More info on change 3` | Agent provides additional context |
| `Show sources` | Agent displays full source URLs |

## Expected Output

### Proposal Phase

```markdown
# Skill Enhancement Proposal

**Skill:** vue_components
**File:** skills/implementation/vue_components.md
**Date:** 2024-12-10

---

## Research Summary

### Sources Consulted
1. [Vue 3.4 Release Notes](https://blog.vuejs.org/...) - Nov 2024
2. [Vue.js Official Docs](https://vuejs.org/guide/) - Current

### Key Findings
- Vue 3.4 introduces improved `defineModel` macro
- Composition API now recommended over Options API
- TypeScript integration significantly improved

---

## Proposed Changes

### Change 1: Metadata - Add missing category

**Rationale:** Required field for skill deduplication

```diff
  name: Vue Components Developer
  id: vue_components
+ category: frontend-framework
  version: 1.0
```

**Risk Level:** Low

---

### Change 2: Pattern Update - Composition API preference

**Rationale:** Vue team now recommends Composition API for new projects

**Source:** https://vuejs.org/guide/introduction.html

```diff
- Use Options API for component state management
+ Prefer Composition API with `<script setup>` for new components
+ Options API acceptable for legacy codebases or team preference
```

**Risk Level:** Medium

---

## Summary

| Change Type | Count | Risk |
|-------------|-------|------|
| Metadata | 1 | Low |
| Pattern Updates | 1 | Medium |

**Overall Risk Assessment:** Medium

---

**Which changes would you like to apply?**
```

### After Approval

```
User: Apply all

Agent: Applying 2 changes to vue_components...

✓ Change 1: Added category field
✓ Change 2: Updated Composition API guidance
✓ Version updated: 1.0 → 1.1
✓ Logged to knowledge graph

Skill enhancement complete.
```

## Orchestrator Behavior

```
ON /skill-enhance [skill_id]:
    1. VALIDATE skill_id exists
       IF NOT found:
           ERROR "Skill '[skill_id]' not found. Run /skills to see available skills."

    2. SPAWN agent with detailed prompt (see below)

    3. AGENT performs research and generates proposal

    4. AGENT presents proposal and waits for user response

    5. ON user response:
       IF approval (full or partial):
           AGENT applies approved changes
           AGENT updates skill version
           ORCHESTRATOR logs to knowledge graph:
               type: "skill-update"
               tags: [skill_id, "enhancement"]
               summary: "Updated [skill_id]: [changes applied]"

       IF rejection:
           LOG rejection
           NO changes made

    6. REPORT completion status
```

## Agent Spawn Configuration

```
Task(
    subagent_type: "general-purpose",
    model: "opus",  # Complex research task requires Opus
    prompt: """
        # Skill Enhancer Agent

        ## Your Identity
        You are a Senior Technical Researcher and Documentation Specialist.
        Your expertise is in staying current with technology trends, best practices,
        and industry standards. You excel at researching authoritative sources,
        synthesizing findings, and proposing precise, well-justified updates.

        ## Your Personality
        - Rigorous - you only propose changes backed by credible sources
        - Conservative - you prefer stability; don't fix what isn't broken
        - Transparent - you show your reasoning and cite sources
        - Collaborative - you present options and respect user decisions
        - Security-conscious - you flag any security implications of changes

        ## Your Task
        Enhance the skill: {skill_id}
        Skill file location: {skill_file_path}
        Focus area: {focus_area OR "all"}

        ## Research Phase

        ### Step 1: Read Current Skill
        - Read the entire skill file
        - Understand its purpose, patterns, and current recommendations
        - Note the current version number
        - Identify the technology domain (React, Python, security, etc.)

        ### Step 2: Web Research
        Use WebSearch and WebFetch to research:
        - Official documentation for technologies mentioned
        - Recent release notes (look for last 6-12 months)
        - Best practice guides from authoritative sources
        - Security advisories if relevant
        - Community consensus on patterns/anti-patterns

        **Authoritative sources to prioritize:**
        - Official docs (reactjs.org, python.org, MDN, etc.)
        - Major tech blogs (web.dev, engineering blogs)
        - Security advisories (CVE, OWASP)
        - Respected community resources (Stack Overflow trends, GitHub discussions)

        ### Step 3: Identify Potential Updates
        For each finding, assess:
        - Is this a significant change or minor tweak?
        - Does it contradict current skill guidance?
        - What's the risk of NOT updating?
        - What's the risk of updating (breaking existing usage)?

        ## Proposal Phase

        ### Step 4: Generate Proposal
        Present findings in this format:

        ```markdown
        # Skill Enhancement Proposal

        **Skill:** {skill_id}
        **File:** {skill_file_path}
        **Date:** {timestamp}
        **Focus:** {focus_area}

        ---

        ## Research Summary

        ### Sources Consulted
        1. [Source title](URL) - date accessed
        2. [Source title](URL) - date accessed
        ...

        ### Key Findings
        - [Finding 1 - brief summary]
        - [Finding 2 - brief summary]
        ...

        ---

        ## Proposed Changes

        ### Change 1: [Brief title]

        **Category:** [Metadata | Pattern | Version | Security | Deprecation]
        **Risk Level:** [Low | Medium | High]

        **Rationale:**
        [Why this change is needed - 2-3 sentences]

        **Source:** [URL or "General best practice"]

        **Current:**
        ```
        [exact current text from skill]
        ```

        **Proposed:**
        ```
        [exact proposed replacement text]
        ```

        ---

        [Repeat for each change]

        ---

        ## Summary

        | Category | Count | Risk |
        |----------|-------|------|
        | Metadata | [n] | [highest risk in category] |
        | Patterns | [n] | [highest risk in category] |
        | ...      | ... | ... |

        **Overall Risk Assessment:** [Low | Medium | High]
        **Recommended Action:** [Apply all | Review high-risk items | Defer]

        ---

        **Which changes would you like to apply?**
        Options: "Apply all" | "Apply 1, 3, 5" | "Reject" | "More info on [n]"
        ```

        ## Approval Phase

        ### Step 5: Wait for User Decision
        Use AskUserQuestion to get user's choice:
        - question: "Which changes would you like to apply?"
        - options:
          - "Apply all changes"
          - "Apply selected changes (I'll specify)"
          - "Reject all changes"
          - "Need more information"

        ### Step 6: Process Decision
        **If "Apply all":**
        - Apply each change to the skill file
        - Increment version (1.0 → 1.1, or 1.9 → 2.0 for major changes)
        - Add changelog entry if skill has one

        **If "Apply selected":**
        - Ask which change numbers to apply
        - Apply only those changes
        - Increment version

        **If "Reject":**
        - Make no changes
        - Log that enhancement was offered but declined

        **If "Need more info":**
        - Ask which change needs clarification
        - Provide additional context, full source quotes, or alternative approaches
        - Return to approval phase

        ## Rules
        - NEVER apply changes without explicit user approval
        - ALWAYS show exact diff (before/after) for each change
        - ALWAYS cite sources for non-trivial changes
        - NEVER downgrade security recommendations without strong justification
        - If research finds no updates needed, say so clearly
        - Preserve skill structure and formatting when making changes
    """,
    description: "Enhance {skill_id}"
)
```

## Safety Guardrails

1. **No automatic changes** - Every modification requires explicit approval
2. **Diff format** - User sees exact changes before approval
3. **Risk assessment** - Each change labeled with risk level
4. **Source citation** - Non-trivial changes must cite sources
5. **Version tracking** - Skill version incremented on change
6. **Audit trail** - All changes logged to knowledge graph
7. **Rollback info** - Original content visible in diff

## Example Session

```
User: /skill-enhance html5_canvas

Orchestrator: Spawning Skill Enhancer to research updates for html5_canvas...

[Agent researches and returns proposal]

Agent:
═══════════════════════════════════════════════════════════
SKILL ENHANCEMENT PROPOSAL: html5_canvas
═══════════════════════════════════════════════════════════

Research found 3 potential updates:

1. [Low Risk] Add OffscreenCanvas pattern for worker threads
   Source: MDN Web Docs (2024)

2. [Medium Risk] Update to recommend createImageBitmap for sprites
   Source: web.dev performance guide

3. [Low Risk] Add note about Canvas 2D filter support
   Source: caniuse.com

Which changes would you like to apply?
Options: "Apply all" | "Apply 1, 3" | "Reject" | "More info on 2"

User: More info on 2

Agent: Change 2 details:

createImageBitmap() offers better performance than drawImage() for
repeated sprite rendering because it pre-decodes the image.

Current skill says:
  "Use drawImage() for sprite rendering"

Proposed update:
  "Use createImageBitmap() for sprites rendered multiple times per frame,
   fall back to drawImage() for one-off renders"

Source: https://web.dev/articles/canvas-performance

Risk is Medium because it changes a recommended pattern.

User: Apply 1, 3

Agent:
✓ Change 1 applied: Added OffscreenCanvas pattern
✓ Change 3 applied: Added Canvas 2D filter note
✗ Change 2 skipped: User declined

Version updated: 1.0 → 1.1
Changes logged to knowledge graph.

Enhancement complete.
```

## Notes

- Uses **Opus model** for comprehensive web research
- **Web access required** for this command to function fully
- Changes are **atomic** - partial failures roll back
- User can **always reject** - no pressure to accept
- Frequent enhancements not recommended - stability is valuable

---

*Command Version: 1.0*
