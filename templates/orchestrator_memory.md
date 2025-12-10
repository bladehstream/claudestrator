# Orchestrator Memory

**Project:** [project name]
**Initialized:** [YYYY-MM-DD]
**Memory Version:** 1

---

## Project Understanding

Captured once during initialization. Updated only when project scope changes significantly.

### What We're Building
[High-level description from user - captured during initialization]

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Technical Constraints
- **Language/Framework:** [specified or "flexible"]
- **Dependencies:** [any required]
- **Platform:** [target platform]
- **Other:** [other constraints]

### Domain Tags
[Tags for skill matching: web, game, api, data, etc.]

---

## Key Decisions

Architectural and design decisions. Append-only log.

| ID | Date | Decision | Rationale | Impact | Task |
|----|------|----------|-----------|--------|------|
| D001 | [date] | [what] | [why] | [affects] | [task-XXX] |

---

## Learned Context

Patterns and conventions discovered during execution. Updated when agents report new learnings.

### Code Patterns
| Pattern | Location | Notes |
|---------|----------|-------|
| [pattern name] | [where used] | [details] |

### Project Conventions
| Convention | Description |
|------------|-------------|
| [naming/structure/etc] | [how it works] |

### Gotchas & Warnings
| Issue | Discovered | Mitigation |
|-------|------------|------------|
| [problem] | [task-XXX] | [how to avoid] |

---

## User Preferences

Preferences expressed during sessions. Informs agent behavior.

| Preference | Expressed | Notes |
|------------|-----------|-------|
| [preference] | [date] | [context] |

---

## Blockers & Risks

| ID | Item | Status | Impact | Mitigation |
|----|------|--------|--------|------------|
| B001 | [blocker/risk] | [active/resolved/watching] | [severity] | [approach] |

---

## Session History

Append-only log of sessions. Summary only.

| Session | Date | Duration | Tasks | Outcome |
|---------|------|----------|-------|---------|
| 1 | [date] | [mins] | [IDs] | [brief note] |

---

## Strategy Notes

High-level strategic observations. Informs planning.

### What's Working
- [Approach that's effective]

### What's Not Working
- [Approach that's ineffective]

### Observations
- [Date]: [observation]

---

*Cold state - read at session start, append during execution*
*Do not modify historical entries*
