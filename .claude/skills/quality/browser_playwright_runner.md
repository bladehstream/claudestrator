---
name: Playwright Browser Testing
id: browser_playwright_runner
version: 1.0
category: quality
domain: [web, testing, qa]
task_types: [testing, automation, e2e, regression-testing, ci-cd]
keywords: [playwright, testing, automation, e2e, end-to-end, browser, functional, viewport, mobile, desktop, tablet, cross-browser, responsive, smoke-test, regression, ci-cd, headless]
complexity: [normal, complex]
pairs_with: [browser_automation, qa_agent, security_reviewer]
dependencies:
  npm: [playwright]
  cli: [node, npm]
  optional: [google-chrome, google-chrome-stable]
source: merged from playwright_qa_agent and webapp_testing
scripts: [.claude/skills/quality/browser_playwright_runner/scripts/test-runner.js]
---

# Playwright Browser Testing

Automated browser testing using Playwright for CI/CD pipelines, regression testing, and headless test execution.

## When to Use This vs Other Skills

| Skill | Use When |
|-------|----------|
| **browser_playwright_runner** (this) | CI/CD pipelines, headless testing, batch execution, repeatable test suites |
| **browser_automation** | Interactive testing with Claude-in-Chrome MCP, real-time control |
| **qa_agent** | General QA methodology, test planning, acceptance criteria |
| **beautifulsoup_scraper** | Static HTML parsing, no JavaScript rendering needed |

**Use Playwright when:**
- Tests need to run in CI/CD pipelines
- You need headless execution
- Tests should be repeatable and deterministic
- You need cross-browser testing (Chromium, Firefox, WebKit)
- You're writing test files (.spec.ts) for a test suite

**Use Claude-in-Chrome when:**
- You need real-time interactive testing
- You want to watch tests execute
- Tests need human judgment during execution
- Exploratory testing

## Quick Setup

### Pre-Flight Check

```bash
# Check Node.js is installed
node --version  # Should be v14 or higher

# Check npm is available
npm --version

# Install Playwright
npm install -D @playwright/test

# Install browsers
npx playwright install
```

### Project Setup

```bash
# Initialize Playwright in project
npm init playwright@latest

# This creates:
# - playwright.config.ts
# - tests/ directory
# - tests-examples/ with sample tests
```

## Two Execution Modes

Playwright can be used two ways:

### Mode 1: Test Runner Script (JSON Flows)

Use the bundled test-runner.js for quick testing without writing test files:

```bash
node .claude/skills/quality/browser_playwright_runner/scripts/test-runner.js <url> [options]
```

**Options:**

| Flag | Description |
|------|-------------|
| `--viewport` | desktop, tablet, mobile, all (default: desktop) |
| `--flow` | Path to test flow JSON file |
| `--output, -o` | Output directory (default: ./test-results) |
| `--full` | Capture full-page screenshots |
| `--trace` | Enable Playwright trace recording |
| `--slow <ms>` | Slow down actions for debugging |
| `--headed` | Run with visible browser |
| `--no-sandbox` | Disable Chrome sandbox (for containers) |

**Examples:**

```bash
# Basic page test
node .claude/skills/quality/browser_playwright_runner/scripts/test-runner.js \
  "https://example.com" \
  --viewport desktop

# Multi-viewport responsive test
node .claude/skills/quality/browser_playwright_runner/scripts/test-runner.js \
  "https://example.com" \
  --viewport all \
  --output ./test-results

# Custom flow test
node .claude/skills/quality/browser_playwright_runner/scripts/test-runner.js \
  "https://app.example.com" \
  --flow ./flows/login-flow.json \
  --trace
```

### Mode 2: Playwright Test Files (.spec.ts)

Write test files for integration with `npx playwright test`:

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password123');
  await page.click('[data-testid="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
```

Run with:
```bash
npx playwright test
npx playwright test --headed  # Visible browser
npx playwright test --ui      # Interactive UI mode
```

## Test Flow JSON Format (Mode 1)

Define test sequences in JSON for the test-runner.js:

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
| `goto` | url, waitUntil? | Navigate to URL |
| `click` | selector | Click element |
| `fill` | selector, value | Type into input |
| `select` | selector, value | Select dropdown option |
| `check` | selector | Check checkbox |
| `uncheck` | selector | Uncheck checkbox |
| `hover` | selector | Hover over element |
| `press` | key | Press keyboard key |
| `screenshot` | name, fullPage? | Capture screenshot |
| `wait` | for (navigation\|networkidle\|timeout), ms? | Wait condition |
| `waitFor` | selector, state?, timeout? | Wait for element |
| `scroll` | selector OR position (top\|bottom) OR {x, y} | Scroll |
| `evaluate` | script | Run JS in page context |
| `assert` | type, various | Verify condition |

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

## Viewport Presets

The test-runner.js includes these presets:

| Preset | Dimensions | Device |
|--------|------------|--------|
| `desktop` | 1280x800 | Chrome desktop |
| `desktop-hd` | 1920x1080 | Chrome desktop |
| `tablet` | 768x1024 | iPad portrait |
| `tablet-landscape` | 1024x768 | iPad landscape |
| `mobile` | 375x667 | iPhone SE |
| `mobile-large` | 414x896 | iPhone 11 Pro Max |
| `mobile-android` | 360x740 | Pixel 5 |

Use `--viewport all` to test desktop, tablet, and mobile automatically.

## Writing Test Files (Mode 2)

### Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});
```

### Selector Best Practices

```typescript
// Best: data-testid (stable, semantic)
await page.click('[data-testid="submit-button"]');

// Good: role-based (accessible)
await page.getByRole('button', { name: 'Submit' });

// Okay: text content (can break with copy changes)
await page.getByText('Submit');

// Avoid: CSS classes (unstable)
await page.click('.btn-primary');

// Avoid: XPath (brittle)
await page.click('//div[@class="form"]/button[1]');
```

### Waiting Strategies

```typescript
// Wait for element
await page.waitForSelector('[data-testid="results"]');

// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for specific request
await page.waitForResponse(resp =>
  resp.url().includes('/api/data') && resp.status() === 200
);

// Wait for element state
await expect(page.locator('[data-testid="spinner"]')).toBeHidden();

// Custom wait with polling
await expect(async () => {
  const count = await page.locator('.item').count();
  expect(count).toBeGreaterThan(0);
}).toPass({ timeout: 5000 });
```

### Test Structure (AAA Pattern)

```typescript
test('user can add transaction', async ({ page }) => {
  // Arrange - Set up test state
  await page.goto('/dashboard');
  await loginAsTestUser(page);

  // Act - Perform the action
  await page.click('[data-testid="add-transaction"]');
  await page.fill('[data-testid="amount"]', '45.00');
  await page.selectOption('[data-testid="category"]', 'groceries');
  await page.click('[data-testid="save"]');

  // Assert - Verify outcome
  await expect(page.locator('[data-testid="transaction-list"]'))
    .toContainText('$45.00');
});
```

### Page Object Pattern

```typescript
// pages/DashboardPage.ts
export class DashboardPage {
  constructor(private page: Page) {}

  readonly addButton = this.page.locator('[data-testid="add-transaction"]');
  readonly transactionList = this.page.locator('[data-testid="transaction-list"]');
  readonly balanceDisplay = this.page.locator('[data-testid="balance"]');

  async goto() {
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
  }

  async addTransaction(amount: string, category: string) {
    await this.addButton.click();
    await this.page.fill('[data-testid="amount"]', amount);
    await this.page.selectOption('[data-testid="category"]', category);
    await this.page.click('[data-testid="save"]');
  }

  async getBalance() {
    return this.balanceDisplay.textContent();
  }
}

// Usage in test
test('add transaction updates balance', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();

  const initialBalance = await dashboard.getBalance();
  await dashboard.addTransaction('100.00', 'income');

  await expect(dashboard.balanceDisplay).not.toHaveText(initialBalance);
});
```

## Test Categories

### Smoke Tests (Critical Path)

```typescript
test.describe('smoke', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/MyApp/);
  });

  test('user can log in', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'testpass');
    await page.click('[data-testid="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });
});
```

### Visual Regression

```typescript
test('dashboard matches snapshot', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Full page screenshot comparison
  await expect(page).toHaveScreenshot('dashboard.png', {
    maxDiffPixels: 100,
  });

  // Component screenshot
  await expect(page.locator('[data-testid="chart"]'))
    .toHaveScreenshot('chart.png');
});
```

### Accessibility Tests

```typescript
import AxeBuilder from '@axe-core/playwright';

test('dashboard is accessible', async ({ page }) => {
  await page.goto('/dashboard');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

## Avoiding Flaky Tests

| Problem | Cause | Solution |
|---------|-------|----------|
| Element not found | Race condition | Use proper waits, not `sleep` |
| Timing issues | Animation/transition | Wait for animation end or disable |
| Test order dependency | Shared state | Isolate test data |
| Network flakiness | External API | Mock API responses |
| Date/time issues | System time | Mock Date or use test time |

### Stable Patterns

```typescript
// Flaky: Fixed timeout
await page.waitForTimeout(2000);

// Stable: Wait for condition
await page.waitForSelector('[data-testid="loaded"]');

// Flaky: Exact text match
await expect(page.locator('.date')).toHaveText('January 13, 2026');

// Stable: Pattern match
await expect(page.locator('.date')).toHaveText(/January \d+, 2026/);

// Flaky: Shared test user
const user = 'shared@test.com';

// Stable: Unique test data
const user = `test-${Date.now()}@test.com`;
```

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run tests
        run: npx playwright test

      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

### Test Data Management

```typescript
// fixtures/testData.ts
export const testUser = {
  email: 'e2e-test@example.com',
  password: 'TestPass123!',
};

export const testTransactions = [
  { amount: -45.00, category: 'groceries', description: 'Weekly shop' },
  { amount: 3500.00, category: 'income', description: 'Salary' },
];

// Seed before test suite
test.beforeAll(async ({ request }) => {
  await request.post('/api/test/seed', {
    data: { user: testUser, transactions: testTransactions }
  });
});

// Cleanup after test suite
test.afterAll(async ({ request }) => {
  await request.post('/api/test/cleanup', {
    data: { email: testUser.email }
  });
});
```

## Output Structure (Mode 1)

When using test-runner.js:

```
test-results/
├── desktop/
│   ├── screenshots/
│   │   ├── 01-initial-load.png
│   │   ├── 02-after-load.png
│   │   └── ...
│   ├── trace.zip          # If --trace enabled
│   └── report.json
├── tablet/
│   └── ...
├── mobile/
│   └── ...
└── summary.json           # Cross-viewport summary
```

## Example Flow Files

The skill includes sample flows at `.claude/skills/quality/browser_playwright_runner/flows/`:

- `login-happy-path.json` - Standard login flow test
- `login-error-states.json` - Login with invalid credentials
- `responsive-audit.json` - Basic responsive design checks

## Troubleshooting

### Browser not launching

```bash
# Reinstall browsers
npx playwright install --with-deps

# Check Chrome is available
which google-chrome || which google-chrome-stable
```

### Tests timing out

```typescript
// Increase timeout for slow operations
test.setTimeout(60000);

// Or per-action
await page.click('button', { timeout: 10000 });
```

### Flaky in CI but passes locally

```typescript
// Add retries for CI
// playwright.config.ts
retries: process.env.CI ? 2 : 0,

// Ensure network idle
await page.waitForLoadState('networkidle');
```

### Screenshots blank

```typescript
// Wait for content to render
await page.waitForSelector('[data-testid="main-content"]');
await page.waitForLoadState('networkidle');
await page.screenshot({ path: 'screenshot.png' });
```

## Integration with Other Skills

### Combined with browser_automation

Use browser_automation for exploratory testing, then codify findings:

```markdown
1. Explore app interactively with Claude-in-Chrome
2. Identify test scenarios and edge cases
3. Create JSON flows or .spec.ts files
4. Run automated tests with Playwright in CI/CD
```

### Combined with qa_agent

Use qa_agent for test planning, Playwright for execution:

```markdown
1. qa_agent designs acceptance criteria
2. Write Playwright tests to verify criteria
3. qa_agent evaluates results and generates report
```

---

*Skill Version: 1.0*
*Merged from: playwright_qa_agent.md, webapp_testing.md*
