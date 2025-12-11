# PRD Iteration/Extension Template

This template is appended to PRD.md during iteration or extension cycles.

---

## Iteration Section Template

```markdown
---

## Iteration [N] - [YYYY-MM-DD]

### Feedback Summary

**Categories addressed:**
- [ ] Performance issues
- [ ] UX/UI improvements
- [ ] Bug fixes
- [ ] Feature enhancements
- [ ] Code quality

### Detailed Feedback

#### [Category 1]
[User's description of issues/improvements needed]

#### [Category 2]
[User's description of issues/improvements needed]

### New Requirements

Based on feedback, the following changes are required:

1. **[Requirement name]**
   - Description: [what needs to change]
   - Improves: task-[XXX]
   - Priority: [high/medium/low]

2. **[Requirement name]**
   - Description: [what needs to change]
   - Improves: task-[XXX]
   - Priority: [high/medium/low]

### Success Criteria

- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
```

---

## Extension Section Template

```markdown
---

## Extension [N] - [YYYY-MM-DD]

### New Feature Overview

[Brief description of new features being added]

### Requirements

#### Feature: [Feature Name]

**Description:**
[Detailed description of the feature]

**User Stories:**
- As a [user type], I want [action] so that [benefit]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Technical Notes:**
- Integration points with existing code
- Dependencies on existing features
- Constraints or considerations

#### Feature: [Feature Name 2]

[Repeat structure for each new feature]

### Non-Functional Requirements

- Performance: [any performance requirements]
- Security: [any security considerations]
- Compatibility: [integration requirements]

### Success Criteria

- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
```

---

## Usage Notes

1. **During Iteration:**
   - Archive current PRD to `PRD-history/v{N}-{date}.md`
   - Append iteration section to PRD.md
   - Reference original task IDs in "Improves" field

2. **During Extension:**
   - Archive current PRD to `PRD-history/v{N}-{date}.md`
   - If using /prdgen: merge generated PRD with existing
   - If inline: append extension section to PRD.md

3. **PRD History Structure:**
   ```
   project/
   ├── PRD.md                      # Current/active PRD
   └── PRD-history/
       ├── v1-initial.md           # Original PRD
       ├── v2-iteration-1.md       # After iteration 1
       ├── v3-extension-1.md       # After extension 1
       └── v4-iteration-2.md       # After iteration 2
   ```

4. **Naming Convention:**
   - `v{N}-initial.md` - Original PRD
   - `v{N}-iteration-{M}.md` - After iteration M
   - `v{N}-extension-{M}.md` - After extension M
   - `v{N}-final.md` - Archived when starting fresh

---

*Template version: 1.0*
*Created: December 2025*
