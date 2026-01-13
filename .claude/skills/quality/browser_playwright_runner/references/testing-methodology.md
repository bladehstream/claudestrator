# QA Testing Methodology

## Test Prioritization Framework

### Priority 1: Critical Path (Test First)
User flows that directly impact revenue or core functionality:
- Authentication (login, logout, password reset, session handling)
- Payment/checkout flows
- Core feature interactions (the reason users visit)
- Data submission forms that cannot be recovered
- Account creation/onboarding

### Priority 2: High Impact
Features affecting significant user segments:
- Navigation and wayfinding
- Search functionality
- User profile/settings
- Notifications and alerts
- Data display and filtering

### Priority 3: Supporting Features
Important but recoverable:
- Help/documentation access
- Social features (share, comment)
- Preferences and customization
- Analytics/reporting views
- Export/download functions

### Priority 4: Edge Cases
After core paths are verified:
- Unusual input combinations
- Boundary conditions
- Interrupted flows (back button, refresh mid-action)
- Concurrent sessions
- Timeout behaviors

## Viewport-Specific Testing

### Desktop (1280x800, 1920x1080)
Test for:
- Full navigation visibility
- Multi-column layouts render correctly
- Hover states function
- Keyboard navigation (Tab, Enter, Escape)
- Large form layouts
- Data tables with many columns
- Modal/dialog positioning

### Tablet (768x1024)
Test for:
- Navigation collapse/hamburger trigger point
- Touch target sizes (minimum 44x44px)
- Landscape vs portrait layouts
- Split-view compatibility
- Soft keyboard doesn't obscure inputs
- Horizontal scroll prevention

### Mobile (375x667, 360x740)
Test for:
- Single-column layout enforcement
- Touch target spacing (no accidental taps)
- Viewport meta tag (no zoom issues)
- Fixed headers/footers don't overlap content
- Form inputs trigger appropriate keyboards (email, tel, number)
- Bottom navigation reachability
- Thumb-zone accessibility for key actions
- Scroll performance on long lists

### Breakpoint Boundaries
Always test AT the breakpoint, not just below:
- If breakpoint is 768px, test at 768px and 767px
- Layout shifts are most visible at exact breakpoints

## State Coverage Matrix

For each critical flow, test these states:

| State | What to Verify |
|-------|----------------|
| Empty | No data, first-time user experience |
| Loading | Skeleton screens, spinners, progressive load |
| Partial | Some data loaded, pagination mid-stream |
| Full | Maximum expected data volume |
| Error | API failure, network timeout, validation error |
| Offline | Service worker behavior, cached content |
| Expired | Session timeout, stale data handling |

## Common Failure Patterns to Check

### Layout Issues
- [ ] Content overflow (text/images breaking containers)
- [ ] Z-index conflicts (elements hiding behind others)
- [ ] Flexbox/grid collapse on edge content
- [ ] Fixed position elements overlapping
- [ ] Unintended horizontal scroll
- [ ] Font rendering differences

### Interaction Issues
- [ ] Click handlers on wrong element (event bubbling)
- [ ] Double-submit on forms
- [ ] Race conditions on rapid clicks
- [ ] Focus trap in modals (can't escape)
- [ ] Focus loss after dynamic content update
- [ ] Disabled buttons still clickable

### Data Issues
- [ ] Empty state not handled
- [ ] Long text truncation/overflow
- [ ] Special characters breaking display (HTML entities, Unicode)
- [ ] Date/time timezone handling
- [ ] Number formatting (locales, decimals)
- [ ] Null/undefined rendering as "null" or "undefined"

### Performance Issues
- [ ] Layout shift during load (CLS)
- [ ] Interaction delay (FID)
- [ ] Slow largest contentful paint (LCP)
- [ ] Memory leaks on navigation
- [ ] Unnecessary re-renders

## Form Testing Checklist

For every form, verify:

### Input Validation
- [ ] Required fields enforced
- [ ] Email format validation
- [ ] Phone number format (with country codes)
- [ ] Password requirements displayed and enforced
- [ ] Min/max length constraints
- [ ] Numeric range validation
- [ ] Date range validation
- [ ] File type/size restrictions

### User Experience
- [ ] Error messages appear near relevant field
- [ ] Error messages are specific (not just "Invalid")
- [ ] Success confirmation is clear
- [ ] Form doesn't clear on validation error
- [ ] Tab order is logical
- [ ] Autofill works correctly
- [ ] Labels are associated with inputs (accessibility)

### Edge Cases
- [ ] Paste into fields works
- [ ] Browser autocomplete compatibility
- [ ] Submit with Enter key
- [ ] Duplicate submission prevention
- [ ] Unsaved changes warning on navigation

## Error State Testing

### Intentionally Trigger
1. **Network errors**: Disconnect network, use slow 3G throttling
2. **API errors**: Mock 400, 401, 403, 404, 500 responses
3. **Validation errors**: Submit invalid data
4. **Timeout errors**: Set aggressive timeouts
5. **Permission errors**: Access restricted resources

### Verify Error Handling
- [ ] Error message is user-friendly (not stack trace)
- [ ] Error is dismissible or recoverable
- [ ] Retry option where appropriate
- [ ] User data not lost on error
- [ ] Error logged for debugging (check console)

## Accessibility Quick Checks

### Automated (run on every page)
- Color contrast (WCAG AA minimum 4.5:1 for text)
- Alt text on images
- Form labels present
- Heading hierarchy (h1 → h2 → h3)
- Link text descriptive (not "click here")

### Manual Verification
- [ ] Keyboard-only navigation possible
- [ ] Focus indicator visible
- [ ] Screen reader announces dynamic content
- [ ] Error messages announced
- [ ] Skip link to main content
- [ ] No keyboard traps

## Performance Metrics to Capture

### Core Web Vitals
| Metric | Good | Needs Work | Poor |
|--------|------|------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | ≤4.0s | >4.0s |
| FID (First Input Delay) | ≤100ms | ≤300ms | >300ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | ≤0.25 | >0.25 |

### Additional Metrics
- Time to Interactive (TTI)
- Total Blocking Time (TBT)
- First Contentful Paint (FCP)
- Bundle size (JS/CSS)
- Number of requests
- Memory usage over time

## Bug Report Format

When documenting issues:

```
## Summary
[One-line description]

## Environment
- Viewport: [desktop/tablet/mobile + dimensions]
- Browser: [Chrome version]
- OS: [Ubuntu/Windows/etc]
- URL: [exact page URL]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Step where issue occurs]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happened]

## Evidence
- Screenshot: [filename]
- Console errors: [if any]
- Network issues: [if any]

## Severity
- [ ] Critical (blocks core functionality)
- [ ] High (significant impact, workaround exists)
- [ ] Medium (noticeable but minor impact)
- [ ] Low (cosmetic/polish)
```

## Test Session Workflow

### Before Testing
1. Clear browser cache and cookies
2. Disable browser extensions
3. Document browser version
4. Set up network throttling if testing performance
5. Prepare test data/accounts

### During Testing
1. Follow test flows systematically
2. Screenshot BEFORE and AFTER each interaction
3. Note any console errors immediately
4. Test happy path first, then error cases
5. Document deviations from expected behavior

### After Testing
1. Review all screenshots
2. Consolidate console errors
3. Categorize issues by severity
4. Cross-reference with previous test runs
5. Update regression test suite if needed
