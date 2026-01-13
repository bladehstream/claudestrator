---
name: Browser Automation
id: browser_automation
version: 2.0
category: implementation
domain: [web, automation, testing, qa]
task_types: [automation, testing, scraping, e2e, verification]
keywords: [browser, chrome, mcp, claude-in-chrome, automation, scraping, testing, form, screenshot, navigate, e2e, test-harness, interactive-testing]
complexity: [normal, complex]
pairs_with: [beautifulsoup_scraper, playwright_qa_agent, web_research_agent, qa_agent]
source: local
---

# Browser Automation via Claude-in-Chrome MCP

Control a live Chrome browser directly from Claude Code using the Claude-in-Chrome extension and Model Context Protocol.

## When to Use This vs Other Skills

| Skill | Use When |
|-------|----------|
| **browser_automation** (this) | Interactive E2E testing, real-time browser control, test harness workflows |
| **web_research_agent** | Standalone Playwright scripts, batch captures, CI/CD pipelines |
| **playwright_qa_agent** | Automated test suites, repeatable test flows, headless execution |
| **beautifulsoup_scraper** | Static HTML parsing, no JavaScript rendering needed |
| **qa_agent** | General QA methodology, test planning, verification strategies |

## Quick Setup

### 1. Install Claude-in-Chrome Extension

Install the extension from: https://claude.ai/chrome

After installation, **restart Chrome** for the connection to take effect.

### 2. Verify Connection

Call `tabs_context_mcp` to verify the extension is connected:

```
mcp__claude-in-chrome__tabs_context_mcp with createIfEmpty: true
```

**Expected response:**
```json
{
  "availableTabs": [{"tabId": 123456, "title": "New Tab", "url": "chrome://newtab"}],
  "tabGroupId": 1234567890
}
```

**If you see "Browser extension is not connected":**
1. Ensure Chrome is running
2. Verify the extension is installed and enabled
3. Restart Chrome if recently installed

### 3. Session Initialization

Every browser automation session should start with:

```
1. tabs_context_mcp (createIfEmpty: true)  → Get tab context
2. tabs_create_mcp                          → Create dedicated tab for this session
3. navigate (url, tabId)                    → Navigate to target URL
4. computer (action: "screenshot", tabId)   → Verify page loaded
```

## Available MCP Tools

All tools are prefixed with `mcp__claude-in-chrome__`:

### Session Management

| Tool | Description |
|------|-------------|
| `tabs_context_mcp` | Get available tabs in the MCP group, create group if needed |
| `tabs_create_mcp` | Create a new tab in the MCP tab group |
| `update_plan` | Present action plan to user for approval before executing |

### Navigation & Interaction

| Tool | Description |
|------|-------------|
| `navigate` | Go to URL, or use "back"/"forward" for history navigation |
| `computer` | Mouse actions (click, double_click, scroll), keyboard (type, key), screenshots |
| `form_input` | Set form field values using element reference IDs |
| `find` | Natural language element search (e.g., "login button", "email input") |

### Observation & Inspection

| Tool | Description |
|------|-------------|
| `read_page` | Get accessibility tree with element refs for interaction |
| `get_page_text` | Extract raw text content, prioritizing article content |
| `javascript_tool` | Execute JavaScript in page context |
| `read_console_messages` | Read browser console (log, error, warn) |
| `read_network_requests` | Monitor XHR/Fetch requests and responses |

### Media & Recording

| Tool | Description |
|------|-------------|
| `gif_creator` | Record browser session and export as animated GIF |
| `upload_image` | Upload images to file inputs or drag-drop targets |
| `resize_window` | Change browser window dimensions for responsive testing |

## E2E Test Harness

Use the Claude-in-Chrome tools as an interactive test harness for E2E testing.

### Core Concept

Tests follow an **action-observe-verify** loop:

```
1. ACTION   → Perform interaction (click, type, navigate)
2. OBSERVE  → Read page state (screenshot, accessibility tree, text)
3. VERIFY   → Assert expected conditions are met
4. REPEAT   → Continue test steps or fail with diagnostics
```

### Session Initialization Protocol

```markdown
Before any test:
1. Call `tabs_context_mcp` with createIfEmpty=true
2. Store the returned tabId for all subsequent calls
3. Create a dedicated test tab with `tabs_create_mcp` (isolates from user tabs)
4. Navigate to the application under test
5. Take initial screenshot to confirm page load
```

### Interaction Primitives

| Intent | Tool | Parameters |
|--------|------|------------|
| Navigate to URL | `navigate` | `url`, `tabId` |
| Click element (by ref) | `computer` | `action: "left_click"`, `ref`, `tabId` |
| Click element (by coords) | `computer` | `action: "left_click"`, `coordinate: [x, y]`, `tabId` |
| Type text | `computer` | `action: "type"`, `text`, `tabId` |
| Fill form field | `form_input` | `ref`, `value`, `tabId` |
| Press key | `computer` | `action: "key"`, `text: "Enter"`, `tabId` |
| Take screenshot | `computer` | `action: "screenshot"`, `tabId` |
| Wait | `computer` | `action: "wait"`, `duration: 2`, `tabId` |
| Scroll | `computer` | `action: "scroll"`, `scroll_direction`, `coordinate`, `tabId` |

### Observation Primitives

| Intent | Tool | Returns |
|--------|------|---------|
| Get page structure | `read_page` | Accessibility tree with `ref_id` for each element |
| Find element by description | `find` | Matching elements with refs (e.g., "submit button") |
| Get page text | `get_page_text` | Raw text content |
| Check console | `read_console_messages` | Console logs/errors (use `pattern` to filter) |
| Check network | `read_network_requests` | XHR/fetch calls (use `urlPattern` to filter) |
| Execute JS assertion | `javascript_tool` | Custom check result |

### Verification Patterns

#### Element Exists
```markdown
1. Call `find` with query: "submit button"
2. Verify results array is non-empty
3. Store ref for subsequent interaction
```

#### Text Content Matches
```markdown
1. Call `get_page_text` or `read_page`
2. Check for expected string in response
3. Report PASS/FAIL with evidence
```

#### Visual State Verification
```markdown
1. Call `computer` with action: "screenshot"
2. Describe what should be visible
3. Compare against expected state
```

#### Network Call Made
```markdown
1. Call `read_network_requests` with urlPattern: "/api/login"
2. Verify request exists with expected method
3. Check response status code
```

#### No Console Errors
```markdown
1. Call `read_console_messages` with onlyErrors: true
2. Verify empty result or only expected errors
3. Flag unexpected errors as test failures
```

### Agent Instructions Template

When instructing an agent to perform E2E testing:

```markdown
## E2E Test Execution

You are testing [APPLICATION_NAME] at [BASE_URL].

### Setup
1. Initialize browser session with `tabs_context_mcp` (createIfEmpty: true)
2. Create test tab with `tabs_create_mcp`
3. Navigate to [BASE_URL]
4. Take screenshot to verify page load

### Test: [TEST_NAME]

**Preconditions:** [state required before test]

**Steps:**
1. [Action description]
   - Tool: [tool_name]
   - Params: [params]
   - Expected: [what should happen]

2. [Verification]
   - Tool: [observation_tool]
   - Assert: [condition]

### On Failure
- Take screenshot immediately
- Capture console errors with `read_console_messages`
- Report: step that failed, expected vs actual, screenshot evidence

### On Success
- Report: test passed, steps completed, any warnings observed
```

## Common Workflows

### Basic Page Load Test

```markdown
1. tabs_context_mcp (createIfEmpty: true) → get tabId
2. tabs_create_mcp → create test tab, get new tabId
3. navigate (url: "https://example.com", tabId)
4. computer (action: "wait", duration: 2, tabId)
5. computer (action: "screenshot", tabId) → verify page rendered
6. get_page_text (tabId) → verify expected content present
```

### Form Submission Test

```markdown
1. Navigate to form page
2. find (query: "email input field", tabId) → get ref
3. form_input (ref, value: "test@example.com", tabId)
4. find (query: "password field", tabId) → get ref
5. form_input (ref, value: "SecurePass123", tabId)
6. computer (action: "screenshot", tabId) → capture filled form
7. find (query: "submit button", tabId) → get ref
8. computer (action: "left_click", ref, tabId)
9. computer (action: "wait", duration: 2, tabId)
10. read_network_requests (urlPattern: "/api/", tabId) → verify API call
11. computer (action: "screenshot", tabId) → capture result
```

### Multi-Viewport Responsive Test

```markdown
1. Navigate to page
2. resize_window (width: 1920, height: 1080, tabId) → desktop
3. computer (action: "screenshot", tabId) → capture desktop view
4. resize_window (width: 768, height: 1024, tabId) → tablet
5. computer (action: "screenshot", tabId) → capture tablet view
6. resize_window (width: 375, height: 667, tabId) → mobile
7. computer (action: "screenshot", tabId) → capture mobile view
8. Compare layouts, verify responsive breakpoints
```

### Console Error Monitoring

```markdown
1. Navigate to application
2. Perform user interactions
3. read_console_messages (onlyErrors: true, tabId)
4. If errors found:
   - Document each error
   - Correlate with user action that triggered it
   - Flag as test failure if unexpected
```

### Network Request Verification

```markdown
1. Navigate to page that makes API calls
2. Perform action that triggers request
3. read_network_requests (urlPattern: "/api/users", tabId)
4. Verify:
   - Request was made
   - Correct HTTP method
   - Expected status code in response
   - Response body structure (if needed, use javascript_tool)
```

## Test Flow Patterns

### Login Flow Test

```markdown
## Test: User Login

### Setup
- tabs_context_mcp → get tabId
- navigate to "http://localhost:3000/login"
- computer action: "screenshot" → verify login page loads

### Steps
1. Find email field
   - find query: "email input"
   - form_input ref: [returned ref], value: "test@example.com"

2. Find password field
   - find query: "password input"
   - form_input ref: [returned ref], value: "password123"

3. Submit form
   - find query: "login button" or "submit button"
   - computer action: "left_click", ref: [returned ref]

4. Wait for navigation
   - computer action: "wait", duration: 2

### Verify
- get_page_text → should contain "Welcome" or "Dashboard"
- read_network_requests urlPattern: "/api/auth" → should show 200 status
- read_console_messages onlyErrors: true → should be empty
```

### Form Validation Test

```markdown
## Test: Form Validation Errors

### Setup
- Navigate to form page

### Steps
1. Submit empty form
   - find query: "submit button"
   - computer action: "left_click", ref: [returned ref]

2. Check for validation errors
   - read_page → look for error message elements
   - find query: "error message" or "validation error"

### Verify
- Error messages are visible
- Form was not submitted (no network request to API)
- Required fields are highlighted
```

### Navigation Flow Test

```markdown
## Test: Multi-Page Navigation

### Setup
- Navigate to homepage

### Steps
1. Click navigation link
   - find query: "About link" or "nav link about"
   - computer action: "left_click", ref: [returned ref]
   - computer action: "wait", duration: 1

2. Verify navigation
   - get_page_text → should contain About page content

3. Use browser back
   - navigate url: "back"
   - computer action: "wait", duration: 1

4. Verify return
   - get_page_text → should contain homepage content

### Verify
- Each page loads correct content
- Browser history works correctly
- No console errors during navigation
```

## Safety Considerations

### Extension Permission Model

The Claude-in-Chrome extension has built-in safety:

1. **Plan Approval**: Use `update_plan` to present intended actions before executing
2. **Domain Whitelisting**: Approved domains are remembered for the session
3. **Sensitive Actions**: Certain actions require explicit user confirmation
4. **Tab Isolation**: MCP operations are scoped to the tab group

### Best Practices

- **Create dedicated test tabs** - Don't reuse tabs with user's active sessions
- **Verify before destructive actions** - Take screenshots before form submissions
- **Monitor console errors** - Unexpected errors may indicate security issues
- **Respect authentication boundaries** - Don't access authenticated sessions without permission
- **Use test accounts** - Avoid using production credentials in E2E tests

### What NOT to Automate

- Banking or financial transactions
- Password changes on real accounts
- Deletion of user data
- Actions requiring 2FA/MFA
- Accessing sensitive personal information

## Troubleshooting

### "Browser extension is not connected"

```markdown
1. Verify Chrome is running
2. Check extension is installed: chrome://extensions
3. Ensure extension is enabled (toggle on)
4. Restart Chrome completely (quit and relaunch)
5. Try again with tabs_context_mcp
```

### "Invalid tab ID" or "Tab not found"

```markdown
1. Tab IDs are session-specific - don't reuse from previous sessions
2. Call tabs_context_mcp to get fresh tab IDs
3. Tab may have been closed - create new tab with tabs_create_mcp
4. Verify tabId is from the current MCP tab group
```

### "Element not found" when clicking

```markdown
1. Call read_page first to get accessibility tree
2. Use find with natural language query to locate element
3. Page may not be fully loaded - add wait action
4. Element may be off-screen - use scroll_to action
5. Element may be in iframe - check page structure
```

### Actions not working / No response

```markdown
1. Take screenshot to see current page state
2. Check if dialog/alert is blocking (dismiss manually)
3. Verify correct tabId is being used
4. Check read_console_messages for JavaScript errors
5. Page may have navigation guard - check network requests
```

### Screenshots appear blank or wrong

```markdown
1. Add wait action before screenshot (page may be loading)
2. Check if page requires scroll to show content
3. Verify correct tabId - may be capturing wrong tab
4. Check resize_window if testing specific viewport
```

### Form inputs not being set

```markdown
1. Use find to get correct element ref
2. Verify element is an input, textarea, or select
3. Check if field is disabled or readonly
4. Some fields require click to focus first
5. Use javascript_tool to inspect element state
```

## Integration with Other Skills

### Combined with qa_agent

Use browser_automation as the execution layer for qa_agent test plans:

```markdown
1. qa_agent designs test cases and acceptance criteria
2. browser_automation executes interactive tests
3. qa_agent evaluates results and generates report
```

### Combined with playwright_qa_agent

Use browser_automation for exploratory testing, playwright_qa_agent for CI/CD:

```markdown
1. Explore application manually with browser_automation
2. Identify test scenarios and edge cases
3. Convert successful flows to Playwright scripts
4. Run automated tests with playwright_qa_agent in CI/CD
```

### Combined with web_research_agent

Use browser_automation for authenticated access, web_research_agent for batch operations:

```markdown
1. Use browser_automation to authenticate and explore
2. Export data or capture patterns
3. Use web_research_agent for large-scale data collection
```
