#!/usr/bin/env node
/**
 * Web capture script for research workflows
 * Uses existing Chrome installation via Playwright
 * 
 * Usage:
 *   node capture.js <url> [options]
 * 
 * Options:
 *   --output, -o    Output base name (default: capture)
 *   --full          Capture full page scroll
 *   --text          Extract text content
 *   --meta          Extract page metadata (title, headings, links)
 *   --wait          Wait time in ms after load (default: 0)
 *   --selector      Wait for specific CSS selector
 *   --viewport      Viewport size WxH (default: 1280x800)
 *   --mobile        Use mobile viewport (375x667)
 *   --tablet        Use tablet viewport (768x1024)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function parseArgs(args) {
  const opts = {
    url: null,
    output: 'capture',
    fullPage: false,
    extractText: false,
    extractMeta: false,
    wait: 0,
    selector: null,
    viewport: { width: 1280, height: 800 }
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('http://') || arg.startsWith('https://')) {
      opts.url = arg;
    } else if (arg === '--output' || arg === '-o') {
      opts.output = args[++i];
    } else if (arg === '--full') {
      opts.fullPage = true;
    } else if (arg === '--text') {
      opts.extractText = true;
    } else if (arg === '--meta') {
      opts.extractMeta = true;
    } else if (arg === '--wait') {
      opts.wait = parseInt(args[++i], 10);
    } else if (arg === '--selector') {
      opts.selector = args[++i];
    } else if (arg === '--viewport') {
      const [w, h] = args[++i].split('x').map(Number);
      opts.viewport = { width: w, height: h };
    } else if (arg === '--mobile') {
      opts.viewport = { width: 375, height: 667 };
    } else if (arg === '--tablet') {
      opts.viewport = { width: 768, height: 1024 };
    }
  }

  return opts;
}

async function capture(opts) {
  if (!opts.url) {
    console.error('Usage: node capture.js <url> [options]');
    console.error('Run with --help for options');
    process.exit(1);
  }

  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true
  });

  try {
    const page = await browser.newPage();
    await page.setViewportSize(opts.viewport);

    console.log(`Navigating to: ${opts.url}`);
    await page.goto(opts.url, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    // Wait for selector if specified
    if (opts.selector) {
      console.log(`Waiting for: ${opts.selector}`);
      await page.waitForSelector(opts.selector, { timeout: 10000 });
    }

    // Additional wait if specified
    if (opts.wait > 0) {
      console.log(`Waiting ${opts.wait}ms...`);
      await page.waitForTimeout(opts.wait);
    }

    // Ensure output directory exists
    const outputDir = path.dirname(opts.output);
    if (outputDir && outputDir !== '.') {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Capture screenshot
    const screenshotPath = `${opts.output}.png`;
    await page.screenshot({ 
      path: screenshotPath, 
      fullPage: opts.fullPage 
    });
    console.log(`Screenshot saved: ${screenshotPath}`);

    // Extract text if requested
    if (opts.extractText) {
      const text = await page.evaluate(() => document.body.innerText);
      const textPath = `${opts.output}.txt`;
      fs.writeFileSync(textPath, text);
      console.log(`Text saved: ${textPath}`);
    }

    // Extract metadata if requested
    if (opts.extractMeta) {
      const metadata = await page.evaluate(() => ({
        url: window.location.href,
        title: document.title,
        description: document.querySelector('meta[name="description"]')?.content || null,
        h1: Array.from(document.querySelectorAll('h1')).map(e => e.innerText.trim()),
        h2: Array.from(document.querySelectorAll('h2')).map(e => e.innerText.trim()),
        links: Array.from(document.querySelectorAll('a[href]'))
          .slice(0, 30)
          .map(a => ({
            text: a.innerText.trim().slice(0, 100),
            href: a.href
          }))
          .filter(l => l.text && l.href.startsWith('http')),
        images: Array.from(document.querySelectorAll('img[src]'))
          .slice(0, 20)
          .map(img => ({
            alt: img.alt || null,
            src: img.src
          })),
        tables: document.querySelectorAll('table').length,
        forms: document.querySelectorAll('form').length
      }));
      const metaPath = `${opts.output}_meta.json`;
      fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2));
      console.log(`Metadata saved: ${metaPath}`);
    }

  } finally {
    await browser.close();
  }
}

// Run
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Web Capture Script

Usage: node capture.js <url> [options]

Options:
  --output, -o <name>   Output base name (default: capture)
  --full                Capture full page (scroll entire page)
  --text                Extract visible text content to .txt file
  --meta                Extract page metadata to _meta.json file
  --wait <ms>           Additional wait time after page load
  --selector <css>      Wait for specific element before capture
  --viewport <WxH>      Set viewport size (default: 1280x800)
  --mobile              Use mobile viewport (375x667)
  --tablet              Use tablet viewport (768x1024)

Examples:
  node capture.js https://example.com -o ./output/site
  node capture.js https://dashboard.com --full --text --meta
  node capture.js https://app.com --selector ".data-loaded" --wait 2000
  node capture.js https://m.site.com --mobile -o mobile_view
`);
  process.exit(0);
}

const opts = parseArgs(args);
capture(opts).catch(err => {
  console.error('Capture failed:', err.message);
  process.exit(1);
});
