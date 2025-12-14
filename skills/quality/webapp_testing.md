---
name: Web Application Tester
id: webapp_testing
version: 1.0
category: quality
domain: [web, frontend, qa]
task_types: [testing, quality, verification]
keywords: [test, testing, playwright, e2e, end-to-end, browser, automation, selenium, cypress, integration, qa, functional]
complexity: [normal, complex]
pairs_with: [qa_agent, security_reviewer, frontend_design]
source: Adapted from Anthropic webapp-testing skill
---

# Web Application Tester

## Role

You write and execute browser-based tests for web applications. You use Playwright (preferred), Cypress, or Selenium to verify functionality, catch regressions, and ensure quality.

## Core Competencies

- End-to-end test design
- Playwright/Cypress scripting
- Test data management
- Flaky test prevention
- CI/CD integration
- Visual regression testing
- Accessibility testing

## Testing Principles

### Reconnaissance Before Action
```
1. Wait for network idle / page load
2. Inspect rendered DOM
3. Screenshot current state
4. Identify selectors
5. Execute actions
```

**Critical**: On dynamic apps (React, Vue, etc.), never inspect DOM before JavaScript execution completes.

### Test Structure (AAA Pattern)
```javascript
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
  await expect(page.locator('[data-testid="transaction-list"]'))
    .toContainText('Groceries');
});
```

## Playwright Patterns

### Basic Setup
```javascript
// playwright.config.js
export default {
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
};
```

### Selectors (Best to Worst)
```javascript
// ✅ Best: data-testid (stable, semantic)
await page.click('[data-testid="submit-button"]');

// ✅ Good: role-based (accessible)
await page.click('button[role="submit"]');
await page.getByRole('button', { name: 'Submit' });

// ⚠️ Okay: text content (can break with copy changes)
await page.click('text=Submit');
await page.getByText('Submit');

// ❌ Avoid: CSS classes (unstable)
await page.click('.btn-primary');

// ❌ Avoid: XPath (brittle, hard to read)
await page.click('//div[@class="form"]/button[1]');
```

### Waiting Strategies
```javascript
// Wait for element
await page.waitForSelector('[data-testid="results"]');

// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for specific request
await page.waitForResponse(resp =>
  resp.url().includes('/api/transactions') && resp.status() === 200
);

// Wait for element state
await expect(page.locator('[data-testid="spinner"]')).toBeHidden();

// Custom wait with polling
await expect(async () => {
  const count = await page.locator('.item').count();
  expect(count).toBeGreaterThan(0);
}).toPass({ timeout: 5000 });
```

### Page Object Pattern
```javascript
// pages/DashboardPage.js
export class DashboardPage {
  constructor(page) {
    this.page = page;
    this.addButton = page.locator('[data-testid="add-transaction"]');
    this.transactionList = page.locator('[data-testid="transaction-list"]');
    this.balanceDisplay = page.locator('[data-testid="balance"]');
  }

  async goto() {
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
  }

  async addTransaction(amount, category) {
    await this.addButton.click();
    await this.page.fill('[data-testid="amount"]', amount);
    await this.page.selectOption('[data-testid="category"]', category);
    await this.page.click('[data-testid="save"]');
    await this.page.waitForResponse(r => r.url().includes('/api/transactions'));
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
```javascript
test.describe('smoke', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Finance/);
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

### Functional Tests
```javascript
test.describe('transactions', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('can create expense', async ({ page }) => { /* ... */ });
  test('can edit transaction', async ({ page }) => { /* ... */ });
  test('can delete transaction', async ({ page }) => { /* ... */ });
  test('can filter by category', async ({ page }) => { /* ... */ });
  test('can filter by date range', async ({ page }) => { /* ... */ });
});
```

### Visual Regression
```javascript
test('dashboard matches snapshot', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Full page screenshot
  await expect(page).toHaveScreenshot('dashboard.png', {
    maxDiffPixels: 100,
  });

  // Component screenshot
  await expect(page.locator('[data-testid="chart"]'))
    .toHaveScreenshot('chart.png');
});
```

### Accessibility Tests
```javascript
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

### Stable Test Patterns
```javascript
// ❌ Flaky: Fixed timeout
await page.waitForTimeout(2000);

// ✅ Stable: Wait for condition
await page.waitForSelector('[data-testid="loaded"]');

// ❌ Flaky: Exact text match
await expect(page.locator('.date')).toHaveText('December 10, 2024');

// ✅ Stable: Pattern match
await expect(page.locator('.date')).toHaveText(/December \d+, 2024/);

// ❌ Flaky: Shared test user
const user = 'shared@test.com';

// ✅ Stable: Unique test data
const user = `test-${Date.now()}@test.com`;
```

## CI/CD Integration

### GitHub Actions Example
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

## Test Data Management

```javascript
// fixtures/testData.js
export const testUser = {
  email: 'e2e-test@example.com',
  password: 'TestPass123!',
};

export const testTransactions = [
  { amount: -45.00, category: 'groceries', description: 'Weekly shop' },
  { amount: -12.50, category: 'coffee', description: 'Coffee meeting' },
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

## Output Expectations

When this skill is applied, the agent should:

- [ ] Use stable selectors (data-testid preferred)
- [ ] Implement proper wait strategies
- [ ] Follow AAA test pattern
- [ ] Avoid flaky patterns (timeouts, shared state)
- [ ] Include smoke tests for critical paths
- [ ] Consider accessibility testing
- [ ] Provide CI/CD configuration

---

*Skill Version: 1.0*
*Adapted from: Anthropic webapp-testing skill and Playwright best practices*
