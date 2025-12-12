# Advanced Capture Patterns

## Table Data Extraction

```javascript
const tableData = await page.evaluate(() => {
  const tables = [];
  document.querySelectorAll('table').forEach((table, i) => {
    const rows = [];
    table.querySelectorAll('tr').forEach(tr => {
      const cells = Array.from(tr.querySelectorAll('th, td'))
        .map(cell => cell.innerText.trim());
      rows.push(cells);
    });
    tables.push({ index: i, rows });
  });
  return tables;
});
fs.writeFileSync('tables.json', JSON.stringify(tableData, null, 2));
```

## Chart/Graph Capture

For charts rendered with Canvas or SVG:

```javascript
// Target specific chart container
const chart = await page.locator('.chart-container').first();
await chart.screenshot({ path: 'chart.png' });

// For multiple charts
const charts = await page.locator('[class*="chart"]').all();
for (let i = 0; i < charts.length; i++) {
  await charts[i].screenshot({ path: `chart_${i}.png` });
}
```

## Multi-Page Research Crawl

```javascript
const { chromium } = require('playwright');
const fs = require('fs');

async function crawl(startUrl, maxPages = 5) {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  const visited = new Set();
  const results = [];

  async function visit(url) {
    if (visited.size >= maxPages || visited.has(url)) return;
    visited.add(url);

    await page.goto(url, { waitUntil: 'networkidle' });
    
    const data = {
      url,
      title: await page.title(),
      text: await page.evaluate(() => document.body.innerText.slice(0, 5000))
    };
    results.push(data);
    
    // Screenshot each page
    const safeName = url.replace(/[^a-z0-9]/gi, '_').slice(0, 50);
    await page.screenshot({ path: `crawl_${safeName}.png` });

    // Get internal links
    const links = await page.evaluate((base) => {
      const origin = new URL(base).origin;
      return Array.from(document.querySelectorAll('a[href]'))
        .map(a => a.href)
        .filter(h => h.startsWith(origin))
        .slice(0, 10);
    }, url);

    for (const link of links) {
      await visit(link);
    }
  }

  await visit(startUrl);
  await browser.close();
  
  fs.writeFileSync('crawl_results.json', JSON.stringify(results, null, 2));
  return results;
}
```

## PDF Generation from Web Page

```javascript
await page.pdf({
  path: 'page.pdf',
  format: 'A4',
  printBackground: true,
  margin: { top: '1cm', bottom: '1cm', left: '1cm', right: '1cm' }
});
```

## Mobile Device Emulation

```javascript
const { devices } = require('playwright');
const iPhone = devices['iPhone 13'];

const context = await browser.newContext({
  ...iPhone,
});
const page = await context.newPage();
```

Available device presets:
- `iPhone 13`, `iPhone 13 Pro Max`
- `Pixel 5`, `Pixel 7`
- `iPad Pro 11`, `Galaxy Tab S4`

## Intercepting Network Requests

Useful for capturing API responses:

```javascript
const apiResponses = [];

page.on('response', async response => {
  const url = response.url();
  if (url.includes('/api/') && response.status() === 200) {
    try {
      const json = await response.json();
      apiResponses.push({ url, data: json });
    } catch (e) {}
  }
});

await page.goto(targetUrl);
fs.writeFileSync('api_data.json', JSON.stringify(apiResponses, null, 2));
```

## Handling Infinite Scroll

```javascript
async function scrollToBottom(page) {
  let previousHeight = 0;
  let currentHeight = await page.evaluate(() => document.body.scrollHeight);
  
  while (previousHeight < currentHeight) {
    previousHeight = currentHeight;
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);  // Wait for content load
    currentHeight = await page.evaluate(() => document.body.scrollHeight);
  }
}

await scrollToBottom(page);
await page.screenshot({ path: 'full_scroll.png', fullPage: true });
```

## Bypassing Basic Bot Detection

```javascript
const browser = await chromium.launch({
  channel: 'chrome',
  headless: false,  // Use headed mode
  args: [
    '--disable-blink-features=AutomationControlled'
  ]
});

const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
});
```

Note: This is for legitimate research. Respect robots.txt and site ToS.

## Error Recovery Pattern

```javascript
async function resilientCapture(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const browser = await chromium.launch({ channel: 'chrome', headless: true });
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.screenshot({ path: 'output.png' });
      await browser.close();
      return true;
    } catch (err) {
      console.error(`Attempt ${i + 1} failed: ${err.message}`);
      if (i === retries - 1) throw err;
      await new Promise(r => setTimeout(r, 2000 * (i + 1)));  // Backoff
    }
  }
}
```
