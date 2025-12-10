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

1. **Spawns** a PRD Generator agent (Sonnet model with web access)
2. **Prompts** user to select a template (or uses `--template` if provided)
3. **Conducts** structured requirements interview
4. **Researches** via web to validate and enrich requirements
5. **Generates** PRD document from template
6. **Saves** document to file
7. **Provides** next steps for orchestration

## Agent Configuration

```yaml
skill: prd_generator
model: sonnet
complexity: normal
task_type: discovery
web_access: true
user_interaction: heavy
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
│  AGENT: Save & Next Steps                                   │
│  ✓ PRD saved to ./PRD.md                                   │
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

Next step: /orchestrate
═══════════════════════════════════════════════════════════
```

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
- **Sonnet model** balances capability with response speed for interactive sessions
- **Interview duration** typically 10-20 minutes depending on complexity
- **Templates are customizable** - users can provide their own template files
- **PRD can be edited** after generation before orchestration

---

*Command Version: 1.0*
