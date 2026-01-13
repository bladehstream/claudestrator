---
name: Internal Communications
id: internal_comms
version: 1.0
category: support
domain: [writing, business, communication]
task_types: [writing, documentation, communication]
keywords: [internal, comms, communication, newsletter, update, status, report, 3p, faq, leadership]
complexity: [easy, normal]
pairs_with: [doc_coauthoring, documentation]
source: https://github.com/anthropics/skills/tree/main/skills/internal-comms
---

# Internal Communications

## Role

Write various internal company communications using standardized formats. Cover seven communication types with appropriate structure and tone.

## Communication Types

### 1. 3P Updates (Progress, Plans, Problems)

**Format**:
```markdown
## Progress (What we accomplished)
- [Accomplishment 1]
- [Accomplishment 2]

## Plans (What we're working on next)
- [Plan 1]
- [Plan 2]

## Problems (Blockers or concerns)
- [Problem 1] - [Proposed solution or help needed]
```

**Tone**: Factual, concise, action-oriented

### 2. Newsletters

**Structure**:
```markdown
# [Newsletter Title] - [Date]

## Highlights
[2-3 sentence summary of key items]

## Section 1: [Topic]
[Content]

## Section 2: [Topic]
[Content]

## Upcoming
- [Event/deadline 1]
- [Event/deadline 2]
```

**Tone**: Engaging, informative, celebratory where appropriate

### 3. FAQs

**Format**:
```markdown
## Frequently Asked Questions: [Topic]

### Q: [Question]
**A:** [Answer]

### Q: [Question]
**A:** [Answer]
```

**Guidelines**:
- Anticipate real user questions
- Provide complete, actionable answers
- Link to resources where helpful
- Update as new questions emerge

### 4. Status Reports

**Structure**:
```markdown
# Status Report: [Project/Initiative]
**Period**: [Date range]
**Status**: [On Track / At Risk / Blocked]

## Summary
[2-3 sentences on overall status]

## Key Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| [Metric] | [Value] | [Value] | [Status] |

## Accomplishments
- [Item 1]
- [Item 2]

## Next Steps
- [Item 1]
- [Item 2]

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk] | [H/M/L] | [H/M/L] | [Action] |
```

### 5. Leadership Updates

**Structure**:
```markdown
# [Topic] Update

## Context
[Why this matters, background]

## Key Points
1. [Point 1]
2. [Point 2]
3. [Point 3]

## Implications
[What this means for the organization]

## Next Steps
[What leadership should expect or do]
```

**Tone**: Strategic, clear, forward-looking

### 6. Project Updates

**Structure**:
```markdown
# Project Update: [Project Name]
**Date**: [Date]

## TL;DR
[One paragraph summary]

## Progress Since Last Update
- [Milestone/accomplishment]
- [Milestone/accomplishment]

## Current Focus
[What the team is working on now]

## Timeline
| Milestone | Target Date | Status |
|-----------|-------------|--------|
| [Item] | [Date] | [Status] |

## Dependencies
- [Dependency 1]: [Status]

## Team Needs
[Any asks or support needed]
```

### 7. Incident Reports

**Structure**:
```markdown
# Incident Report: [Incident Title]
**Date**: [Date]
**Severity**: [Critical/High/Medium/Low]
**Status**: [Resolved/Ongoing/Monitoring]

## Summary
[What happened in 2-3 sentences]

## Timeline
| Time | Event |
|------|-------|
| [Time] | [Event] |
| [Time] | [Event] |

## Impact
- [Impact 1]
- [Impact 2]

## Root Cause
[What caused the incident]

## Resolution
[How it was fixed]

## Action Items
| Item | Owner | Due Date |
|------|-------|----------|
| [Action] | [Name] | [Date] |

## Lessons Learned
- [Lesson 1]
- [Lesson 2]
```

## Writing Guidelines

### Tone by Audience
| Audience | Tone |
|----------|------|
| All-hands | Accessible, engaging |
| Leadership | Strategic, concise |
| Technical team | Detailed, precise |
| Cross-functional | Clear, jargon-free |

### Best Practices
- Lead with the most important information
- Use headers and bullets for scannability
- Be specific with numbers and dates
- Include clear next steps or calls to action
- Keep paragraphs short (2-4 sentences)

### Anti-Patterns
| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Burying the lead | Key info missed | Start with summary |
| Wall of text | Hard to scan | Use structure |
| Vague status | No actionable info | Specific metrics |
| Missing context | Confusion | Provide background |
| No next steps | Unclear expectations | Always include actions |

---

*Skill Version: 1.0*
*Source: Anthropic internal-comms skill*
