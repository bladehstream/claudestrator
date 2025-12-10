# Skill Manifest (Reference Only)

## Overview

> **Note**: This manifest is now **optional**. Skills are auto-discovered from frontmatter at runtime. This file serves as a reference and documentation of bundled skills.

See `skill_loader.md` for the dynamic discovery system.

## How Skills Are Loaded

1. **Orchestrator scans** the skill directory for `*.md` files
2. **Parses YAML frontmatter** from each file
3. **Builds runtime index** - no static manifest required
4. **New skills**: Just drop a file with valid frontmatter into the directory

---

## Quick Reference

| ID | Name | Category | Domain | Task Types | Complexity |
|----|------|----------|--------|------------|------------|
| html5_canvas | HTML5 Canvas Developer | rendering | web, game | impl, feature, bugfix | normal, complex |
| svg_asset_gen | SVG Asset Generator | assets | web, game | asset, impl | easy, normal |
| game_designer | Game Designer | game-mechanics | game | design, planning | normal, complex |
| game_feel | Game Feel Developer | polish | game | polish, feature | normal |
| qa_agent | QA Agent | testing | any | testing, verification | normal |
| user_persona | User Persona Reviewer | ux-review | any | testing, review | normal |
| api_designer | API Designer | api-design | backend, api | design, planning | normal, complex |
| security_reviewer | Security Reviewer | security | any | review, audit | complex |
| refactoring | Refactoring Specialist | refactoring | any | refactor | normal, complex |
| documentation | Documentation Writer | documentation | any | documentation | easy, normal |

> **Note**: Only one skill per category is selected for each agent. This ensures diverse expertise without redundancy.

---

## Skill Details

### html5_canvas

| Field | Value |
|-------|-------|
| **Name** | HTML5 Canvas Developer |
| **ID** | html5_canvas |
| **Category** | rendering |
| **Path** | skills/implementation/html5_canvas.md |
| **Domain** | web, game, visualization |
| **Task Types** | implementation, feature, bugfix |
| **Keywords** | canvas, html5, javascript, game, animation, rendering, sprite, 2d, graphics, gameloop, collision |
| **Complexity** | normal, complex |
| **Pairs With** | svg_asset_gen, game_feel |
| **Description** | Expert in HTML5 Canvas 2D rendering, game loops, input handling, and interactive graphics |

---

### svg_asset_gen

| Field | Value |
|-------|-------|
| **Name** | SVG Asset Generator |
| **ID** | svg_asset_gen |
| **Category** | assets |
| **Path** | skills/support/svg_asset_generator.md |
| **Domain** | web, game, design |
| **Task Types** | asset, implementation |
| **Keywords** | svg, sprite, icon, graphic, vector, animation, visual, art, image |
| **Complexity** | easy, normal |
| **Pairs With** | html5_canvas, game_designer |
| **Description** | Creates inline SVG graphics for games and web applications |

---

### game_designer

| Field | Value |
|-------|-------|
| **Name** | Game Designer |
| **ID** | game_designer |
| **Category** | game-mechanics |
| **Path** | skills/design/game_designer.md |
| **Domain** | game |
| **Task Types** | design, planning, specification |
| **Keywords** | game, mechanics, balance, progression, player, experience, loop, difficulty, scoring |
| **Complexity** | normal, complex |
| **Pairs With** | game_feel, user_persona |
| **Description** | Designs game mechanics, progression systems, and player experiences |

---

### game_feel

| Field | Value |
|-------|-------|
| **Name** | Game Feel Developer |
| **ID** | game_feel |
| **Category** | polish |
| **Path** | skills/implementation/game_feel.md |
| **Domain** | game |
| **Task Types** | polish, feature, implementation |
| **Keywords** | juice, polish, animation, feedback, shake, particle, easing, effect, feel |
| **Complexity** | normal |
| **Pairs With** | html5_canvas, game_designer |
| **Description** | Adds polish and "juice" to games - screen shake, particles, satisfying feedback |

---

### qa_agent

| Field | Value |
|-------|-------|
| **Name** | QA Agent |
| **ID** | qa_agent |
| **Category** | testing |
| **Path** | skills/quality/qa_agent.md |
| **Domain** | any |
| **Task Types** | testing, verification, validation |
| **Keywords** | test, qa, quality, bug, verify, check, validate, acceptance, criteria |
| **Complexity** | normal |
| **Pairs With** | any |
| **Description** | Systematic testing and verification of implementations against requirements |

---

### user_persona

| Field | Value |
|-------|-------|
| **Name** | User Persona Reviewer |
| **ID** | user_persona |
| **Category** | ux-review |
| **Path** | skills/quality/user_persona_reviewer.md |
| **Domain** | any |
| **Task Types** | testing, review, evaluation |
| **Keywords** | user, player, experience, ux, accessibility, friction, usability, persona |
| **Complexity** | normal |
| **Pairs With** | qa_agent, game_designer |
| **Description** | Simulates real user experiences to identify friction points and UX issues |

---

### api_designer

| Field | Value |
|-------|-------|
| **Name** | API Designer |
| **ID** | api_designer |
| **Category** | api-design |
| **Path** | skills/design/api_designer.md |
| **Domain** | backend, api, web |
| **Task Types** | design, planning, specification |
| **Keywords** | api, rest, graphql, endpoint, schema, request, response, http, service |
| **Complexity** | normal, complex |
| **Pairs With** | security_reviewer, documentation |
| **Description** | Designs RESTful and GraphQL APIs with proper structure and conventions |

---

### security_reviewer

| Field | Value |
|-------|-------|
| **Name** | Security Reviewer |
| **ID** | security_reviewer |
| **Category** | security |
| **Path** | skills/quality/security_reviewer.md |
| **Domain** | any |
| **Task Types** | review, audit, verification |
| **Keywords** | security, vulnerability, injection, xss, csrf, authentication, authorization, owasp |
| **Complexity** | complex |
| **Pairs With** | qa_agent |
| **Description** | Reviews code for security vulnerabilities and suggests remediations |

---

### refactoring

| Field | Value |
|-------|-------|
| **Name** | Refactoring Specialist |
| **ID** | refactoring |
| **Category** | refactoring |
| **Path** | skills/support/refactoring.md |
| **Domain** | any |
| **Task Types** | refactor, cleanup |
| **Keywords** | refactor, clean, restructure, extract, rename, simplify, pattern, technical debt |
| **Complexity** | normal, complex |
| **Pairs With** | qa_agent |
| **Description** | Restructures code for clarity and maintainability without changing behavior |

---

### documentation

| Field | Value |
|-------|-------|
| **Name** | Documentation Writer |
| **ID** | documentation |
| **Category** | documentation |
| **Path** | skills/support/documentation.md |
| **Domain** | any |
| **Task Types** | documentation |
| **Keywords** | docs, readme, comment, guide, api, reference, tutorial, explain |
| **Complexity** | easy, normal |
| **Pairs With** | any |
| **Description** | Writes clear, concise documentation for code and systems |

---

## Adding New Skills

1. Create skill file using `skill_template.md`
2. Add entry to Quick Reference table above
3. Add detailed entry in Skill Details section
4. Ensure frontmatter metadata matches manifest entry

## Skill File Locations

```
orchestrator/skills/
├── implementation/          # Code-writing skills
│   ├── html5_canvas.md
│   └── game_feel.md
├── design/                  # Design/planning skills
│   ├── game_designer.md
│   └── api_designer.md
├── quality/                 # QA/review skills
│   ├── qa_agent.md
│   ├── user_persona_reviewer.md
│   └── security_reviewer.md
└── support/                 # Supporting skills
    ├── svg_asset_generator.md
    ├── refactoring.md
    └── documentation.md
```

---

*Manifest Version: 1.0*
*Last Updated: December 2024*
