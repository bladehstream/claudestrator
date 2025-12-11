# Product Requirements Document

```yaml
# PRD Metadata (machine-readable for orchestrator)
metadata:
  schema_version: "2.0"
  project:
    name: "[Project Name]"
    type: minimal
    complexity: simple | moderate | complex
  mvp:
    target_date: "[YYYY-MM-DD or TBD]"
    feature_count: 0
  tech_stack:
    languages: []
    frameworks: []
    databases: []
  constraints:
    team_size: 1
    timeline: "[e.g., 2 weeks]"
  tags: []
```

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | [Project Name] |
| **Version** | 2.0 |
| **Date** | [Date] |
| **Author** | [Author] |

---

## 1. Overview

### Vision
[One sentence: what this will become]

### Problem
[What problem are you solving? 2-3 sentences.]

### Solution
[What are you building? 2-3 sentences.]

### Target Users
[Who will use this? Be specific about their context.]

---

## 2. Success Metrics

| ID | Goal | Metric | Target |
|----|------|--------|--------|
| G-001 | [Goal] | [How measured] | [Target value] |
| G-002 | [Goal] | [How measured] | [Target value] |

---

## 3. MVP Feature List

| ID | Feature | Priority | Complexity | Dependencies |
|----|---------|----------|------------|--------------|
| F-001 | [Feature] | Must Have | Easy/Normal | None |
| F-002 | [Feature] | Must Have | Easy/Normal | F-001 |
| F-003 | [Feature] | Should Have | Easy/Normal | F-001 |
| F-004 | [Feature] | Could Have | Easy/Normal | F-002 |

---

## 4. Feature Specifications

### F-001: [Feature Name]

**Priority:** Must Have
**Complexity:** Normal
**Dependencies:** None

#### Description
[What the feature does]

#### Acceptance Criteria

| ID | Given | When | Then |
|----|-------|------|------|
| AC-001 | [context] | [action] | [outcome] |
| AC-002 | [context] | [action] | [outcome] |

---

### F-002: [Feature Name]

**Priority:** Must Have
**Complexity:** Normal
**Dependencies:** F-001

#### Description
[What the feature does]

#### Acceptance Criteria

| ID | Given | When | Then |
|----|-------|------|------|
| AC-003 | [context] | [action] | [outcome] |
| AC-004 | [context] | [action] | [outcome] |

---

[Add more F-XXX sections as needed]

---

## 5. Technical Constraints

```yaml
tech_stack:
  language: "[e.g., TypeScript, Python]"
  framework: "[e.g., React, FastAPI]"
  database: "[e.g., PostgreSQL, SQLite]"
  hosting: "[e.g., Vercel, local]"
```

| Constraint | Details |
|------------|---------|
| Platform | [Where it runs] |
| Performance | [Key performance requirements] |
| Security | [Security requirements] |

---

## 6. User Flow

### Primary Flow: [Flow Name]

```
1. User [action]
   → System [response]
2. User [action]
   → System [response]
3. [Outcome]
```

---

## 7. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-001 | Performance | [Requirement] | [Target] |
| NFR-002 | Security | [Requirement] | [Target] |
| NFR-003 | Accessibility | [Requirement] | [Target] |

---

## 8. Implementation Guidance

### Suggested Task Order
1. Project setup
2. [Core feature - F-001]
3. [Next feature - F-002]
4. Testing
5. Documentation

### Definition of Done
- [ ] All acceptance criteria passing
- [ ] Basic tests written
- [ ] No critical bugs
- [ ] Code reviewed

---

## 9. Out of Scope

- [Explicitly excluded item 1]
- [Explicitly excluded item 2]
- [Explicitly excluded item 3]

---

## 10. Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-001 | [Question] | Open |

---

## 11. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-001 | [Risk] | Low/Med/High | Low/Med/High | [Plan] |

---

*Generated with Claudestrator PRD Generator v2.0*
