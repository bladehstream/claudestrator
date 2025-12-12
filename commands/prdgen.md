# /prdgen - Generate Product Requirements Document

Spawn a PRD Generator agent to conduct a requirements interview and produce a structured PRD document.

## Usage

```
/prdgen
/prdgen --template [template_name]
/prdgen --output [path]
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--template` | No | Pre-select a template: `web`, `cli`, `api`, `game`, `mobile`, `library`, `minimal` |
| `--output` | No | Custom output path for PRD (default: `./PRD.md`) |

## What It Does

1. **Spawns** a PRD Generator agent (Opus model with web access)
2. **Prompts** user to select a template (or uses `--template` if provided)
3. **Conducts** structured requirements interview
4. **Researches** via web to validate and enrich requirements
5. **Generates** PRD document from template
6. **Saves** document to file
7. **Analyzes** skill coverage against PRD requirements
8. **Reports** gaps and recommendations
9. **Provides** next steps for orchestration

## Agent Spawn Configuration

```
Task(
    subagent_type: "general-purpose",
    model: "opus",
    prompt: """
        # PRD Generator Agent

        ## Your Identity
        You are a Senior Product Manager and Requirements Analyst with extensive
        experience in software product development. Your expertise is in extracting
        clear, actionable requirements from stakeholders through structured interviews,
        and producing comprehensive PRD documents that development teams can execute against.

        ## Your Personality
        - Curious - you dig deeper to understand the "why" behind requests
        - Organized - you follow a structured interview flow
        - Practical - you focus on MVP scope and avoid feature creep
        - Collaborative - you help users think through their ideas
        - Thorough - you identify gaps and assumptions proactively
        - Web-savvy - you research to validate and enrich requirements
        - Visual-minded - you capture competitor UIs for reference and inspiration

        ## Your Task
        Conduct a requirements interview and generate a PRD document.

        Template requested: {template OR "auto-select based on interview"}
        Output path: {output_path OR "./PRD.md"}

        ## Reference Documents
        Load and follow these documents:
        - Skill: .claudestrator/skills/support/prd_generator.md
        - Protocol: .claudestrator/prd_generator/prd_protocol.md
        - Constraints: .claudestrator/prd_generator/prd_constraints.md
        - Templates: .claudestrator/prd_generator/templates/

        ## Interview Flow

        ### Phase 1: Template Selection
        Use AskUserQuestion with clickable options to select project type:
        1. First ask category: Web/API, Mobile/Game, CLI/Library, Quick/Simple
        2. Then ask specific template based on category

        ### Phase 2: Vision & Context
        Ask about:
        - What problem does this solve?
        - Who are the target users?
        - What's the core value proposition?
        - Are there competitors or alternatives?

        ### Phase 3: Scope Definition
        Ask about:
        - What's the MVP scope?
        - What features are must-have vs nice-to-have?
        - What's explicitly out of scope?
        - Any hard deadlines or constraints?

        ### Phase 4: Requirements Deep Dive
        Based on template, ask template-specific questions:
        - Features and user flows
        - Technical requirements
        - Non-functional requirements (performance, security, etc.)
        - Edge cases and error handling

        ### Phase 4.5: Visual Research (Optional)
        If competitors or reference implementations were mentioned, use web_research_agent
        to capture live screenshots for visual reference:

        ```bash
        # Pre-flight (once per session)
        node --version && npm install playwright

        # Capture competitor UI/UX
        node .claude/skills/support/web_research_agent/scripts/capture.js \
          "https://competitor.com/dashboard" \
          --full --text --meta \
          -o ./research/competitor

        # Read screenshot for visual analysis
        Read("./research/competitor.png")
        ```

        Use visual research when:
        - User mentions specific competitors to emulate or differentiate from
        - Discussing UI patterns that benefit from visual reference
        - Analyzing dashboard/data visualization requirements
        - Documenting current state of existing systems being replaced

        Save captures to `./research/` for inclusion in PRD appendix.

        ### Phase 5: Validation
        Summarize understanding and confirm with user:
        - Present key requirements
        - List assumptions made
        - Note any gaps or open questions

        ### Phase 6: Document Generation
        - Generate PRD from template with gathered requirements
        - Mark unclear items as [TBD]
        - Include Open Questions section

        ### Phase 7: Skill Gap Analysis
        After saving PRD:
        - Scan .claude/skills/ for available skills
        - Match PRD requirements to skills
        - Report coverage percentage
        - Warn about critical gaps

        ## Completion Message
        After saving PRD:
        - Confirm file saved with path
        - Show skill coverage summary
        - Suggest next step: /orchestrate

        ## Rules
        - Use AskUserQuestion for choices (provides clickable UI)
        - Use freeform questions for open-ended answers
        - Research via web to validate technical choices
        - Don't assume - ask clarifying questions
        - Keep interview focused - typically 10-20 minutes
        - PRD should be actionable, not vague
    """,
    description: "Generate PRD"
)
```

### Agent Configuration Summary

```yaml
skill: prd_generator
model: opus
complexity: normal
task_type: discovery
web_access: true
user_interaction: heavy
visual_research: web_research_agent
```

## Available Templates

| Template | File | Best For |
|----------|------|----------|
| `web` | `web_application.md` | SaaS, dashboards, CRUD apps |
| `cli` | `cli_tool.md` | Command-line utilities |
| `api` | `api_service.md` | REST/GraphQL backends |
| `game` | `game.md` | Browser/mobile games |
| `mobile` | `mobile_app.md` | iOS/Android applications |
| `library` | `library.md` | Packages, SDKs, libraries |
| `minimal` | `minimal.md` | Quick projects, prototypes |

## Session Flow

```
┌─────────────────────────────────────────────────────────────┐
│  USER: /prdgen                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Template Selection                                  │
│  "What type of project is this?"                           │
│  [1-7 options + custom]                                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Discovery Interview                                 │
│  • Vision & Context (what, why, who)                       │
│  • Scope Definition (MVP, priorities)                      │
│  • Requirements Deep Dive (features, flows, edge cases)    │
│  • Validation (confirm understanding)                      │
│  [Web research as needed]                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Document Generation                                 │
│  • Populate template with gathered requirements            │
│  • Mark gaps as [TBD]                                      │
│  • Add open questions                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Review & Refinement                                 │
│  • Present summary to user                                 │
│  • Offer to expand or modify sections                      │
│  • Iterate until user satisfied                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Save PRD                                            │
│  ✓ PRD saved to ./PRD.md                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Skill Gap Analysis                                  │
│  • Scan available skills                                   │
│  • Match requirements to skills                            │
│  • Report coverage and gaps                                │
│  • Recommend actions for gaps                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT: Next Steps                                          │
│  ✓ Coverage report shown                                   │
│  "To begin implementation, run: /orchestrate"              │
└─────────────────────────────────────────────────────────────┘
```

## Standalone Operation

This command operates **independently of the orchestrator**. It:
- Does NOT require `/orchestrate` to be running
- Does NOT consume orchestrator context
- DOES produce a clean artifact (`PRD.md`) for later orchestration
- DOES maintain its own conversation context

## Expected Output

### During Interview

The agent uses Claude Code's native `AskUserQuestion` tool for structured questions:

```
┌─ Project Type ─────────────────────────────────────────────┐
│ What type of project are you building?                     │
│                                                            │
│ ○ Web/API                                                  │
│   Web apps, dashboards, REST/GraphQL services              │
│                                                            │
│ ○ Mobile/Game                                              │
│   iOS, Android apps, or browser/mobile games               │
│                                                            │
│ ○ CLI/Library                                              │
│   Command-line tools, packages, SDKs                       │
│                                                            │
│ ○ Quick/Simple                                             │
│   Minimal template for prototypes                          │
└────────────────────────────────────────────────────────────┘

User: [Clicks CLI/Library]

┌─ Specific Type ────────────────────────────────────────────┐
│ More specifically?                                         │
│                                                            │
│ ○ CLI Tool                                                 │
│   Command-line utilities                                   │
│                                                            │
│ ○ Library/SDK                                              │
│   Reusable packages, npm modules                           │
└────────────────────────────────────────────────────────────┘

User: [Clicks CLI Tool]

Agent: CLI Tool template selected. Let's start with the basics.
       What problem does this tool solve?

[... freeform interview continues for open-ended questions ...]
```

### Structured vs Freeform Questions

| Question Type | Interaction Style |
|---------------|-------------------|
| Template selection | AskUserQuestion (clickable) |
| Platform choices | AskUserQuestion multi-select |
| Priority ranking | AskUserQuestion |
| Yes/No confirmations | AskUserQuestion |
| Feature descriptions | Freeform text input |
| Problem explanations | Freeform text input |
| User workflows | Freeform text input |

### On Completion

```
═══════════════════════════════════════════════════════════
PRD COMPLETE: [Project Name]
═══════════════════════════════════════════════════════════

Template: cli_tool
Sections completed: 14/16
Open questions: 2

Key Requirements:
• Primary command: [command] - [description]
• Target users: [user type]
• Install method: [methods]
• MVP scope: [summary]

Saved to: ./PRD.md

───────────────────────────────────────────────────────────
SKILL COVERAGE ANALYSIS
───────────────────────────────────────────────────────────

✅ Covered (8 requirements):
   • CLI argument parsing → cli_tool skill
   • File operations → standard library
   • JSON output → data_visualization skill
   • Error handling → built-in patterns
   ...

⚠️ Gaps Identified (2 requirements):

   [WARNING] Cloud sync feature
   • No skill available for AWS S3 integration
   • Recommendation: Create custom skill or use /ingest-skill
   • Impact: May require manual implementation guidance

   [CRITICAL] OAuth authentication
   • No skill covers OAuth 2.0 flows
   • Recommendation: Use /ingest-skill to import auth skill
   • Impact: Core feature - orchestrator may struggle without guidance

───────────────────────────────────────────────────────────
COVERAGE: 80% (8/10 requirements)
───────────────────────────────────────────────────────────

⚠️ 1 critical gap identified - consider adding skills before orchestration

Next step: /orchestrate
═══════════════════════════════════════════════════════════
```

### Skill Gap Analysis

After saving the PRD, the agent automatically analyzes skill coverage:

**Coverage Levels:**

| Level | Score | Description |
|-------|-------|-------------|
| ✅ High | ≥0.7 | Strong skill match - confident implementation |
| ⚠️ Partial | 0.4-0.69 | Partial coverage - may need guidance |
| ❌ None | <0.4 | No skill coverage - manual implementation likely |

**Gap Severity:**

| Severity | Meaning | Recommendation |
|----------|---------|----------------|
| `warning` | Nice-to-have or secondary feature | Can proceed, note in tasks |
| `critical` | Core feature lacking coverage | Consider adding skill first |

**Addressing Gaps:**

1. **Use `/ingest-skill`** to import a skill from URL or local file
2. **Create custom skill** in `skills/` directory
3. **Proceed anyway** - orchestrator will use general-purpose agents

## Example Sessions

### Quick Project

```
User: /prdgen --template minimal

Agent: Using minimal template. Let's keep this brief.
       What are you building?

User: A script to batch rename files with regex patterns.

Agent: Got it. Who will use this?

User: Just me, for personal use.

Agent: What's the core feature?

User: Take a regex pattern and replacement, apply to files in a directory.

Agent: Any constraints?

User: Should work on Linux and Mac. Python preferred.

Agent: Here's your PRD:

[Generates minimal PRD]

✓ PRD saved to ./PRD.md
  Run /orchestrate to begin implementation.
```

### Complex Project

```
User: /prdgen

Agent: What type of project is this?

User: A mobile app for tracking personal finances.

Agent: Mobile App template it is. Tell me about the problem you're solving.

User: People struggle to track spending. Existing apps are too complex
      or require linking bank accounts, which feels risky.

Agent: Interesting - so privacy/simplicity is a differentiator.
       Let me research the competitive landscape...

       [Researches finance apps]

       I see apps like Mint require bank linking while simpler ones
       like Spending Tracker are manual. You're targeting the manual
       space but with better UX?

User: Exactly. Manual entry but smart categorization suggestions.

[... detailed interview continues ...]

Agent: Here's your PRD. It's comprehensive - 20 sections covered.

       Key points:
       • Manual transaction entry with AI categorization
       • iOS first, Android v1.1
       • No bank linking (privacy focus)
       • Offline-first architecture

       3 open questions noted for follow-up.

✓ PRD saved to ./PRD.md
```

## Integration with Orchestrator

After PRD generation:

```
User: /orchestrate

Orchestrator: Found PRD.md in project root.
              Reading requirements...

              Project: [Name]
              Type: [Type from PRD]
              MVP Scope: [X] requirements

              Decomposing into tasks...
```

The orchestrator will:
1. Read the PRD file
2. Extract requirements
3. Decompose into tasks
4. Begin execution planning

## Notes

- **Web access** enables research during interviews for validation
- **Opus model** provides highest quality for complex requirements discovery
- **Visual research** via web_research_agent captures competitor UI/UX for reference
- **Interview duration** typically 10-20 minutes depending on complexity
- **Templates are customizable** - users can provide their own template files
- **PRD can be edited** after generation before orchestration

---

*Command Version: 1.2*
*Updated: December 2025*
*Added: Opus model upgrade, web_research_agent integration*
