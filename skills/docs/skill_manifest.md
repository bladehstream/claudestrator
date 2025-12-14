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

## Standard Categories

Skills MUST use one of these standard categories (matching directory structure):

| Category | Description |
|----------|-------------|
| `implementation` | Building/coding features |
| `design` | Planning/architecture |
| `quality` | Testing/review/QA |
| `support` | Supporting tasks |
| `maintenance` | Skill/system maintenance |
| `security` | Security implementation |
| `domain` | Domain-specific expertise |
| `orchestrator` | Orchestration agents |

## Quick Reference

| ID | Name | Category | Domain | Complexity |
|----|------|----------|--------|------------|
| html5_canvas | HTML5 Canvas Developer | implementation | web, game | [normal, complex] |
| svg_asset_generator | SVG Asset Generator | design | web, game | [easy, normal] |
| game_designer | Game Designer | design | game | [normal, complex] |
| game_feel | Game Feel Developer | implementation | game | [normal] |
| qa_agent | QA Agent | quality | any | [normal] |
| user_persona_reviewer | User Persona Reviewer | quality | any | [normal] |
| api_designer | API Designer | design | backend, api | [normal, complex] |
| security_reviewer | Security Reviewer | quality | any | [complex] |
| refactoring | Refactoring Specialist | support | any | [normal, complex] |
| documentation | Documentation Writer | support | any | [easy, normal] |
| prd_generator | PRD Generator | support | product, planning | [normal, complex] |
| skill_auditor | Skill Auditor | maintenance | orchestrator | [normal] |
| skill_enhancer | Skill Enhancer | maintenance | orchestrator | [complex] |
| device_hardware | Device Hardware | implementation | react-native, mobile | [normal] |
| ui_generator | UI Generator | support | ui, frontend | [normal] |
| decomposition_agent | Decomposition Agent | orchestrator | orchestration | [normal] |
| agent_construction | Agent Construction | orchestrator | orchestration | [normal] |

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

### prd_generator

| Field | Value |
|-------|-------|
| **Name** | PRD Generator |
| **ID** | prd_generator |
| **Category** | requirements |
| **Path** | skills/support/prd_generator.md |
| **Domain** | product, planning, requirements |
| **Task Types** | discovery, documentation, planning |
| **Keywords** | prd, requirements, product, specification, scope, interview, discovery, planning |
| **Complexity** | normal, complex |
| **Pairs With** | - |
| **Description** | Conducts structured interviews to extract requirements and generate PRD documents |

---

## Adding New Skills

1. Create skill file using `skill_template.md`
2. Add entry to Quick Reference table above
3. Add detailed entry in Skill Details section
4. Ensure frontmatter metadata matches manifest entry

## Skill File Locations

```
.claude/skills/  (or skills/ in orchestrator repo)
├── implementation/          # Code-writing skills
│   ├── html5_canvas.md
│   ├── game_feel.md
│   ├── api_development.md
│   ├── databases.md
│   ├── device-hardware.md
│   └── ...
├── design/                  # Design/planning skills
│   ├── game_designer.md
│   ├── api_designer.md
│   ├── frontend_design.md
│   ├── database_designer.md
│   └── svg_asset_generator.md
├── quality/                 # QA/review skills
│   ├── qa_agent.md
│   ├── user_persona_reviewer.md
│   ├── security_reviewer.md
│   ├── playwright_qa_agent.md
│   └── webapp_testing.md
├── support/                 # Supporting skills
│   ├── documentation.md
│   ├── refactoring.md
│   ├── prd_generator.md
│   ├── ui-generator.md
│   └── ...
├── security/                # Security implementation
│   ├── backend_security.md
│   ├── software_security.md
│   └── ...
├── maintenance/             # Skill/system maintenance
│   ├── skill_auditor.md
│   ├── skill_enhancer.md
│   └── skill_creator.md
├── domain/                  # Domain-specific expertise
│   └── financial_app.md
└── orchestrator/            # Orchestration agents
    ├── decomposition_agent.md
    └── agent_construction.md
```

---

### device_hardware

| Field | Value |
|-------|-------|
| **Name** | Device Hardware |
| **ID** | device_hardware |
| **Category** | implementation |
| **Path** | skills/implementation/device-hardware.md |
| **Domain** | react-native, expo, mobile, hardware, fintech |
| **Task Types** | implementation, feature |
| **Keywords** | biometrics, face id, touch id, fido2, passkeys, camera, nfc, bluetooth, ble, sensors, haptics, location, secure storage |
| **Complexity** | normal |
| **Pairs With** | software_security, frontend_design |
| **Description** | React Native/Expo hardware integration including biometrics, FIDO2, camera, NFC, BLE, sensors |

---

### ui_generator

| Field | Value |
|-------|-------|
| **Name** | UI Generator |
| **ID** | ui_generator |
| **Category** | support |
| **Path** | skills/support/ui-generator.md |
| **Domain** | ui, frontend, react-native, react, html, design |
| **Task Types** | implementation, design |
| **Keywords** | ui generation, mockup, wireframe, gemini, nano banana, code generation, react native, tailwind, component |
| **Complexity** | normal |
| **Pairs With** | frontend_design, brand_guidelines |
| **Description** | AI-powered UI asset and code generation using Google Gemini API |

---

### api_development

| Field | Value |
|-------|-------|
| **Name** | API Development |
| **ID** | api_development |
| **Category** | implementation |
| **Path** | skills/implementation/api_development.md |
| **Domain** | api, backend, typescript, web |
| **Task Types** | design, implementation, documentation |
| **Keywords** | api, rest, graphql, trpc, hono, endpoint, validation, zod, openapi, http, request, response, pagination, rate-limiting, versioning |
| **Complexity** | normal, complex |
| **Pairs With** | database_designer, security_reviewer, authentication |
| **Description** | Build production-ready APIs with modern TypeScript patterns, REST/GraphQL/tRPC |

---

### databases

| Field | Value |
|-------|-------|
| **Name** | Databases |
| **ID** | databases |
| **Category** | implementation |
| **Path** | skills/implementation/databases.md |
| **Domain** | database, orm, sql, backend |
| **Task Types** | design, implementation, optimization |
| **Keywords** | database, postgresql, prisma, drizzle, orm, sql, migration, query, index, transaction, d1, connection pooling |
| **Complexity** | normal, complex |
| **Pairs With** | api_development, backend_security |
| **Description** | Database management with PostgreSQL, Prisma/Drizzle ORMs, migrations, query optimization |

---

### web_auth_security

| Field | Value |
|-------|-------|
| **Name** | Web Auth Security |
| **ID** | web_auth_security |
| **Category** | security |
| **Path** | skills/security/web_auth_security.md |
| **Domain** | backend, web, api |
| **Task Types** | implementation, security, design |
| **Keywords** | auth, login, logout, session, jwt, oauth, password, mfa, csrf, xss, owasp, express |
| **Complexity** | normal, complex |
| **Pairs With** | api_designer, security_reviewer, database_designer |
| **Description** | Server-side authentication with OWASP guidelines, JWT, OAuth2, session management |

---

### react_native_mobile_auth

| Field | Value |
|-------|-------|
| **Name** | React Native Auth |
| **ID** | react_native_mobile_auth |
| **Category** | security |
| **Path** | skills/security/react_native_mobile_auth.md |
| **Domain** | mobile, react-native, expo, api |
| **Task Types** | implementation, security, design |
| **Keywords** | auth, biometrics, face id, touch id, passkeys, webauthn, expo, react native, secure storage, oauth, pkce, hono |
| **Complexity** | normal, complex |
| **Pairs With** | web_auth_security, api_development, device_hardware |
| **Description** | Mobile authentication with React Native/Expo biometrics, passkeys, OAuth PKCE |

---

### serverless_infrastructure

| Field | Value |
|-------|-------|
| **Name** | Serverless Infrastructure |
| **ID** | serverless_infrastructure |
| **Category** | implementation |
| **Path** | skills/implementation/serverless_infrastructure.md |
| **Domain** | cloudflare, serverless, backend, typescript |
| **Task Types** | implementation, deployment, design |
| **Keywords** | cloudflare, workers, serverless, hono, kv, d1, r2, durable objects, wrangler, edge, cron |
| **Complexity** | normal, complex |
| **Pairs With** | api_development, databases, backend_security |
| **Description** | Cloudflare Workers deployment with Hono, KV, D1, R2, Durable Objects |

---

### backend_security

| Field | Value |
|-------|-------|
| **Name** | Backend Security |
| **ID** | backend_security |
| **Category** | security |
| **Path** | skills/security/backend_security.md |
| **Domain** | security, api, backend |
| **Task Types** | implementation, security, review |
| **Keywords** | security, owasp, injection, xss, csrf, validation, zod, headers, secrets, cors, rate limiting, sql injection |
| **Complexity** | normal, complex |
| **Pairs With** | api_development, web_auth_security, databases |
| **Description** | Secure APIs against OWASP Top 10, injection attacks, misconfigurations |

---

### observability

| Field | Value |
|-------|-------|
| **Name** | Observability |
| **ID** | observability |
| **Category** | support |
| **Path** | skills/support/observability.md |
| **Domain** | monitoring, logging, backend, cloudflare |
| **Task Types** | implementation, debugging, optimization |
| **Keywords** | logging, monitoring, metrics, tracing, sentry, error tracking, cloudflare, workers, health checks |
| **Complexity** | normal, complex |
| **Pairs With** | serverless_infrastructure, api_development, backend_security |
| **Description** | Logging, metrics, tracing, error tracking for Cloudflare Workers |

---

### service_integrations

| Field | Value |
|-------|-------|
| **Name** | Service Integrations |
| **ID** | service_integrations |
| **Category** | implementation |
| **Path** | skills/implementation/service_integrations.md |
| **Domain** | api, backend, payments, webhooks |
| **Task Types** | implementation, integration |
| **Keywords** | api client, webhooks, retry, circuit breaker, rate limiting, airwallex, stripe, sendgrid, http, fetch |
| **Complexity** | normal, complex |
| **Pairs With** | api_development, backend_security, observability |
| **Description** | External API integration with retry, circuit breaker, webhooks, payment providers |

---

*Manifest Version: 1.1*
*Last Updated: December 2025*
