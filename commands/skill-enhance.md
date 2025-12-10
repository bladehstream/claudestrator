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

    2. SPAWN agent
       Task(
           subagent_type: "general-purpose",
           model: "opus",  # Complex task requires Opus
           prompt: [skill_enhancer skill + skill file path + focus area],
           description: "Enhance " + skill_id
       )

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
