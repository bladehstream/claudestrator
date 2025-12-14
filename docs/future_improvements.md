# Future Improvements

Planned enhancements for the Claudestrator orchestration system.

---

## `/audit-skills --fix` Mode

**Priority:** Medium
**Status:** Planned

### Overview

Add an optional `--fix` flag to `/audit-skills` that offers granular remediation for issues found during the audit.

### Behavior

```bash
/audit-skills           # Read-only audit (current behavior)
/audit-skills --fix     # Audit + offer to fix issues interactively
```

### Interaction Model

When `--fix` is provided, after identifying issues:

1. **Group issues by type** (pairs_with mismatches, missing fields, etc.)
2. **Present each fixable issue individually**
3. **Use AskUserQuestion for each fix** with options:
   - "Fix this issue"
   - "Skip this issue"
   - "Fix all issues of this type"
   - "Skip all remaining"

### Example Session

```
═══════════════════════════════════════════════════════════
AUDIT COMPLETE - 3 fixable issues found
═══════════════════════════════════════════════════════════

Issue 1/3: pairs_with mismatch in html5_canvas.md
  Current:  pairs_with: [svg_asset_gen, game_feel]
  Problem:  "svg_asset_gen" does not exist
  Similar:  "svg_asset_generator" found
  Proposed: pairs_with: [svg_asset_generator, game_feel]

[Fix this] [Skip] [Fix all pairs_with issues] [Cancel]
```

### Fixable Issue Types

| Issue Type | Auto-Fixable | Requires Confirmation |
|------------|--------------|----------------------|
| `pairs_with` ID mismatch | Yes (if similar ID found) | Yes |
| Missing `source` field | Yes (default: `original`) | Yes |
| Complexity not array | Yes (wrap in array) | Yes |
| Non-standard category | No (needs user choice) | N/A |
| Missing required field | No (needs user input) | N/A |

### Implementation Notes

- Only offer fixes for issues with clear, safe resolutions
- Never auto-fix without confirmation
- Log all fixes made for audit trail
- Show diff preview before applying

---

## Additional Planned Improvements

### `/audit-skills --fix-pairs`

Subset of `--fix` that only addresses `pairs_with` mismatches.

### `/audit-skills --dry-run`

Show what `--fix` would do without making changes.

### Bidirectional `pairs_with` Enforcement

When skill A declares `pairs_with: [B]`, suggest adding `pairs_with: [A]` to skill B.

### Skill ID Fuzzy Matching

When validating `pairs_with` references, use fuzzy matching to suggest corrections:
- `svg_asset_gen` → "Did you mean `svg_asset_generator`?"
- `user_persona` → "Did you mean `user_persona_reviewer`?"

---

*Document Version: 1.0*
*Created: December 14, 2025*
