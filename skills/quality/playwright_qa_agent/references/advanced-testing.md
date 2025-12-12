# Advanced Testing Patterns

## Network Request Mocking

Intercept and mock API responses for testing error states:

```javascript
// Mock specific API endpoint
await page.route('**/api/users', route => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ users: [{ id: 1, name: 'Test User' }] })
  });
});

// Simulate API error
await page.route('**/api/checkout', route => {
  route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ error: 'Payment service unavailable' })
  });
});

// Simulate slow response
await page.route('**/api/data', route => {
  setTimeout(() => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ data: [] })
    });
  }, 5000);
});

// Block specific resources (ads, analytics)
await page.route('**/*google-analytics*/**', route => route.abort());
await page.route('**/*.{png,jpg,jpeg}', route => route.abort()); // Block images
```

## Authentication Handling

### Cookie Injection
```javascript
// Load saved auth state
const cookies = JSON.parse(fs.readFileSync('auth-cookies.json'));
await context.addCookies(cookies);

// Save auth state after login
const cookies = await context.cookies();
fs.writeFileSync('auth-cookies.json', JSON.stringify(cookies));
```

### Storage State (Recommended)
```javascript
// Save complete auth state (cookies + localStorage)
await context.storageState({ path: 'auth-state.json' });

// Restore auth state
const context = await browser.newContext({
  storageState: 'auth-state.json'
});
```

### Login Flow Helper
```javascript
async function login(page, username, password) {
  await page.goto('/login');
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**');
  return await page.context().storageState();
}
```

## File Upload Testing

```javascript
// Single file upload
const input = page.locator('input[type="file"]');
await input.setInputFiles('/path/to/file.pdf');

// Multiple files
await input.setInputFiles(['/path/to/file1.pdf', '/path/to/file2.pdf']);

// Create file from buffer (no actual file needed)
await input.setInputFiles({
  name: 'test.txt',
  mimeType: 'text/plain',
  buffer: Buffer.from('Test file content')
});

// Clear file input
await input.setInputFiles([]);

// Drag and drop upload
const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
const dropzone = page.locator('.dropzone');
await dropzone.dispatchEvent('drop', { dataTransfer });
```

## iframe and Popup Handling

### iframes
```javascript
// Get iframe by selector
const frame = page.frameLocator('iframe#payment');
await frame.locator('#card-number').fill('4242424242424242');

// Get frame by name
const frame = page.frame('checkout-frame');

// Wait for iframe to load
await page.waitForSelector('iframe#dynamic');
const frame = page.frameLocator('iframe#dynamic');
await frame.locator('.loaded').waitFor();
```

### Popups and New Windows
```javascript
// Handle popup
const [popup] = await Promise.all([
  page.waitForEvent('popup'),
  page.click('a[target="_blank"]')
]);
await popup.waitForLoadState();
console.log(await popup.title());
await popup.close();

// Handle dialog (alert, confirm, prompt)
page.on('dialog', async dialog => {
  console.log(dialog.message());
  await dialog.accept(); // or dialog.dismiss()
});
```

## Performance Profiling

### Core Web Vitals
```javascript
const metrics = await page.evaluate(() => {
  return new Promise(resolve => {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      resolve({
        lcp: entries.find(e => e.entryType === 'largest-contentful-paint')?.startTime,
        fid: entries.find(e => e.entryType === 'first-input')?.processingStart,
        cls: entries.filter(e => e.entryType === 'layout-shift')
          .reduce((sum, e) => sum + e.value, 0)
      });
    }).observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
  });
});
```

### Navigation Timing
```javascript
const timing = await page.evaluate(() => {
  const t = performance.timing;
  return {
    dns: t.domainLookupEnd - t.domainLookupStart,
    tcp: t.connectEnd - t.connectStart,
    ttfb: t.responseStart - t.requestStart,
    download: t.responseEnd - t.responseStart,
    domInteractive: t.domInteractive - t.navigationStart,
    domComplete: t.domComplete - t.navigationStart,
    loadComplete: t.loadEventEnd - t.navigationStart
  };
});
```

### Resource Timing
```javascript
const resources = await page.evaluate(() => {
  return performance.getEntriesByType('resource').map(r => ({
    name: r.name,
    type: r.initiatorType,
    duration: r.duration,
    size: r.transferSize
  }));
});

// Find slow resources
const slowResources = resources.filter(r => r.duration > 1000);
```

### Memory Profiling
```javascript
// Requires Chrome with --enable-precise-memory-info
const memory = await page.evaluate(() => {
  if (performance.memory) {
    return {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
    };
  }
  return null;
});
```

## Visual Regression Testing

### Pixel Comparison
```javascript
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

async function compareScreenshots(img1Path, img2Path, diffPath) {
  const img1 = PNG.sync.read(fs.readFileSync(img1Path));
  const img2 = PNG.sync.read(fs.readFileSync(img2Path));
  
  const { width, height } = img1;
  const diff = new PNG({ width, height });
  
  const mismatchedPixels = pixelmatch(
    img1.data, img2.data, diff.data, 
    width, height,
    { threshold: 0.1 }
  );
  
  fs.writeFileSync(diffPath, PNG.sync.write(diff));
  
  const totalPixels = width * height;
  const diffPercent = (mismatchedPixels / totalPixels) * 100;
  
  return {
    mismatchedPixels,
    totalPixels,
    diffPercent: diffPercent.toFixed(2)
  };
}
```

### Element Masking
```javascript
// Hide dynamic content before screenshot
await page.evaluate(() => {
  // Hide timestamps, ads, etc.
  document.querySelectorAll('.timestamp, .ad-banner, .random-content')
    .forEach(el => el.style.visibility = 'hidden');
});
await page.screenshot({ path: 'masked.png' });
```

## Accessibility Testing

### axe-core Integration
```javascript
// npm install @axe-core/playwright

const { injectAxe, checkA11y, getViolations } = require('@axe-core/playwright');

await injectAxe(page);
const violations = await getViolations(page);

console.log(`Found ${violations.length} accessibility violations`);
violations.forEach(v => {
  console.log(`- ${v.id}: ${v.description}`);
  console.log(`  Impact: ${v.impact}`);
  console.log(`  Elements: ${v.nodes.map(n => n.target).join(', ')}`);
});
```

### Manual Checks Script
```javascript
const a11yReport = await page.evaluate(() => {
  const report = {
    images: [],
    forms: [],
    headings: [],
    links: [],
    color: []
  };
  
  // Images without alt
  document.querySelectorAll('img').forEach(img => {
    if (!img.alt) {
      report.images.push({ src: img.src, issue: 'missing alt' });
    }
  });
  
  // Form inputs without labels
  document.querySelectorAll('input, select, textarea').forEach(input => {
    const id = input.id;
    const label = id ? document.querySelector(`label[for="${id}"]`) : null;
    const ariaLabel = input.getAttribute('aria-label');
    if (!label && !ariaLabel) {
      report.forms.push({ name: input.name || input.id, issue: 'missing label' });
    }
  });
  
  // Heading hierarchy
  let lastLevel = 0;
  document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
    const level = parseInt(h.tagName[1]);
    if (level > lastLevel + 1) {
      report.headings.push({ 
        text: h.innerText.slice(0, 50), 
        issue: `skipped from h${lastLevel} to h${level}` 
      });
    }
    lastLevel = level;
  });
  
  // Links with generic text
  document.querySelectorAll('a').forEach(a => {
    const text = a.innerText.toLowerCase().trim();
    if (['click here', 'read more', 'learn more', 'here'].includes(text)) {
      report.links.push({ href: a.href, text, issue: 'generic link text' });
    }
  });
  
  return report;
});
```

## Network Throttling

```javascript
// Create CDP session for network throttling
const client = await context.newCDPSession(page);

// Simulate slow 3G
await client.send('Network.emulateNetworkConditions', {
  offline: false,
  downloadThroughput: (500 * 1024) / 8, // 500 kb/s
  uploadThroughput: (500 * 1024) / 8,
  latency: 400 // 400ms
});

// Simulate offline
await client.send('Network.emulateNetworkConditions', {
  offline: true,
  downloadThroughput: 0,
  uploadThroughput: 0,
  latency: 0
});

// Presets
const NETWORK_PRESETS = {
  'slow-3g': { download: 500, upload: 500, latency: 400 },
  'fast-3g': { download: 1600, upload: 750, latency: 150 },
  '4g': { download: 9000, upload: 9000, latency: 60 },
  'wifi': { download: 30000, upload: 15000, latency: 10 }
};
```

## Console and Error Monitoring

```javascript
// Comprehensive logging
const logs = { console: [], errors: [], requests: [], responses: [] };

page.on('console', msg => {
  logs.console.push({
    type: msg.type(),
    text: msg.text(),
    location: msg.location()
  });
});

page.on('pageerror', error => {
  logs.errors.push({
    message: error.message,
    stack: error.stack
  });
});

page.on('request', request => {
  logs.requests.push({
    url: request.url(),
    method: request.method(),
    resourceType: request.resourceType()
  });
});

page.on('response', response => {
  logs.responses.push({
    url: response.url(),
    status: response.status(),
    ok: response.ok()
  });
});

page.on('requestfailed', request => {
  logs.errors.push({
    type: 'network',
    url: request.url(),
    failure: request.failure()?.errorText
  });
});
```

## Test Data Generation

```javascript
// Random test data helpers
const testData = {
  email: () => `test_${Date.now()}@example.com`,
  phone: () => `555-${Math.floor(1000 + Math.random() * 9000)}`,
  name: () => ['John', 'Jane', 'Bob', 'Alice'][Math.floor(Math.random() * 4)],
  address: () => `${Math.floor(100 + Math.random() * 9900)} Test Street`,
  
  // Credit card test numbers (Stripe test cards)
  card: {
    valid: '4242424242424242',
    declined: '4000000000000002',
    expired: '4000000000000069',
    cvc_fail: '4000000000000127'
  }
};
```

## Retry and Flaky Test Handling

```javascript
async function withRetry(fn, retries = 3, delay = 1000) {
  let lastError;
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      console.log(`Attempt ${i + 1} failed: ${err.message}`);
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, delay * (i + 1)));
      }
    }
  }
  throw lastError;
}

// Usage
await withRetry(async () => {
  await page.click('.flaky-button');
  await page.waitForSelector('.success');
});
```
