---
name: Playwright QA Agent
id: playwright_qa_agent
version: 1.0.0
category: quality
domain: [web, testing]
task_types: [testing, automation, ui-testing, regression-testing, cross-browser, qa, post-implementation-verification]
keywords: [playwright, testing, automation, functional-testing, viewport, mobile-testing, desktop-testing, tablet-testing, screenshot, test-runner, browser-testing, responsive-testing, user-flows, smoke-test, regression-test, post-deployment, feature-verification, multi-viewport, cross-device]
complexity: intermediate
pairs_with: [qa_agent, webapp_testing, security_reviewer]
dependencies:
  npm: [playwright]
  cli: [node, npm]
  optional: [google-chrome, google-chrome-stable]
source: external
scripts: [scripts/test-runner.js]
---

# Playwright QA Agent

**Use this skill for**: Automated browser testing of web applications after implementing features. Testing websites across desktop, tablet, and mobile viewports to verify functionality, responsive design, user flows, and cross-browser compatibility.

**Do NOT use for**: General web research or data extraction (use `web_research_agent` instead).

## Pre-Flight Check

Before using this skill, verify dependencies:

```bash
# Check Node.js is installed
node --version  # Should be v14 or higher

# Check npm is available
npm --version

# Check Chrome is installed
which google-chrome || which google-chrome-stable

# Install Playwright (one-time per session)
npm install playwright
```

If any checks fail, install the missing dependencies before proceeding.

## Overview

Functional testing for web applications using Playwright with existing Chrome installation. Supports desktop, tablet, and mobile viewports with automated test flows, screenshot capture, and assertion validation.

**Primary Use Cases**:
- Post-implementation feature verification
- Regression testing after code changes
- Responsive design validation (mobile/tablet/desktop)
- User flow testing (login, checkout, forms)
- Smoke testing before deployment
- Cross-viewport compatibility checks

## Core Testing Script

```bash
node .claude/skills/quality/playwright_qa_agent/scripts/test-runner.js <url> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `--viewport` | desktop (1280x800), tablet (768x1024), mobile (375x667), all |
| `--flow` | Path to test flow JSON file |
| `--output, -o` | Output directory for screenshots/reports (default: ./test-results) |
| `--full` | Capture full-page screenshots |
| `--trace` | Enable Playwright trace recording |
| `--slow <ms>` | Slow down actions by ms (for debugging) |
| `--headed` | Run with visible browser window |
| `--no-sandbox` | Disable Chrome sandbox (for containers) |

## Quick Start Examples

### Basic Page Load Test
```bash
node .claude/skills/quality/playwright_qa_agent/scripts/test-runner.js \
  "https://app.example.com" \
  --viewport desktop \
  --output ./test-results
```

### Multi-Viewport Responsive Test
Test the same page across desktop, tablet, and mobile:
```bash
node .claude/skills/quality/playwright_qa_agent/scripts/test-runner.js \
  "https://app.example.com" \
  --viewport all \
  --output ./test-results
```

### User Flow Test with Custom Flow
```bash
node .claude/skills/quality/playwright_qa_agent/scripts/test-runner.js \
  "https://app.example.com" \
  --flow .claude/skills/quality/playwright_qa_agent/flows/login-happy-path.json \
  --output ./test-results
```

## Test Flow Definition

Create JSON files to define automated test sequences:

```json
{
  "name": "Login Flow",
  "steps": [
    { "action": "goto", "url": "https://app.example.com/login" },
    { "action": "screenshot", "name": "login-page" },
    { "action": "fill", "selector": "#email", "value": "test@example.com" },
    { "action": "fill", "selector": "#password", "value": "testpass123" },
    { "action": "screenshot", "name": "filled-form" },
    { "action": "click", "selector": "button[type=submit]" },
    { "action": "wait", "for": "navigation" },
    { "action": "screenshot", "name": "post-login" },
    { "action": "assert", "type": "url", "contains": "/dashboard" },
    { "action": "assert", "type": "visible", "selector": ".welcome-message" }
  ]
}
```

### Available Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `goto` | url | Navigate to URL |
| `click` | selector | Click element |
| `fill` | selector, value | Type into input |
| `select` | selector, value | Select dropdown option |
| `check` | selector | Check checkbox |
| `uncheck` | selector | Uncheck checkbox |
| `hover` | selector | Hover over element |
| `screenshot` | name | Capture screenshot |
| `wait` | for (navigation\|networkidle\|timeout), ms | Wait condition |
| `waitFor` | selector, state (visible\|hidden\|attached) | Wait for element |
| `assert` | type, various | Verify condition (see assertions) |
| `scroll` | selector OR position (top\|bottom\|{x,y}) | Scroll page/element |
| `press` | key | Press keyboard key |
| `evaluate` | script | Run JS in page context |

### Assertion Types

| Type | Parameters | Example |
|------|------------|---------|
| `url` | contains, equals, matches | `{"type": "url", "contains": "/dashboard"}` |
| `title` | contains, equals | `{"type": "title", "equals": "Home"}` |
| `visible` | selector | `{"type": "visible", "selector": ".success"}` |
| `hidden` | selector | `{"type": "hidden", "selector": ".loading"}` |
| `text` | selector, contains/equals | `{"type": "text", "selector": "h1", "contains": "Welcome"}` |
| `count` | selector, equals/min/max | `{"type": "count", "selector": ".item", "min": 1}` |
| `attribute` | selector, attr, value | `{"type": "attribute", "selector": "input", "attr": "disabled", "value": "true"}` |

## Device Presets

The test runner includes these viewport presets:

| Preset | Dimensions | User Agent |
|--------|------------|------------|
| `desktop` | 1280x800 | Chrome desktop |
| `desktop-hd` | 1920x1080 | Chrome desktop |
| `tablet` | 768x1024 | iPad |
| `tablet-landscape` | 1024x768 | iPad landscape |
| `mobile` | 375x667 | iPhone SE |
| `mobile-large` | 414x896 | iPhone 11 Pro Max |
| `mobile-android` | 360x740 | Pixel 5 |

Use `--viewport all` to run tests across desktop, tablet, and mobile automatically.

## Output Structure

```
test-results/
├── desktop/
│   ├── screenshots/
│   │   ├── 01-login-page.png
│   │   ├── 02-filled-form.png
│   │   └── 03-post-login.png
│   ├── trace.zip          # If --trace enabled
│   └── report.json
├── tablet/
│   └── ...
├── mobile/
│   └── ...
└── summary.json           # Cross-viewport summary
```

## Testing Guidelines

Consult `references/testing-methodology.md` for:
- Test case prioritization (critical paths first)
- What to test on each viewport
- Common failure patterns to check
- Accessibility testing checklist
- Performance metrics to capture
- Bug report formatting

Key principles:
1. **Critical paths first**: Login, checkout, core features before edge cases
2. **Mobile breakpoints matter**: Test at exact breakpoints, not just "mobile"
3. **State capture**: Screenshot before AND after interactions
4. **Error states**: Intentionally trigger validation errors, 404s, timeouts
5. **Console monitoring**: Capture JS errors and warnings

## Example Flows

The skill includes sample test flows in the `flows/` directory:

- `login-happy-path.json` - Standard login flow test
- `login-error-states.json` - Login with invalid credentials
- `responsive-audit.json` - Basic responsive design checks

Adapt these flows or create your own based on your application's requirements.

## Technical Reference

See `references/advanced-testing.md` for:
- Network request mocking
- Authentication handling
- File upload testing
- iframe and popup handling
- Performance profiling (Core Web Vitals)
- Visual regression comparison
- Accessibility audits (axe-core integration)

## Security Note

The test runner uses `page.evaluate()` to execute JavaScript in the browser context when processing test flows. Only use trusted test flow JSON files from verified sources. Do not load flows from untrusted or external sources.

## Workflow Integration

**Typical workflow**:
1. Implement new feature or fix bug
2. Start local dev server (`npm run dev`, etc.)
3. Create test flow JSON or use basic page test
4. Run Playwright QA Agent on localhost URL
5. Review screenshots and reports in output directory
6. Fix any failures and re-test
7. Run multi-viewport test before deployment

**Pairs well with**: `qa_agent` for comprehensive QA strategy, `security_reviewer` for security checks, `webapp_testing` for additional testing guidance.
