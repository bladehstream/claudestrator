---
name: Web Research Agent
id: web_research_agent
version: 1.0.0
category: support
domain: [research, web]
task_types: [research, data-extraction, screenshot, web-scraping, documentation, content-gathering]
keywords: [playwright, research, screenshot, web-capture, scraping, data-extraction, visual-analysis, web-content, website-analysis, content-research, page-capture, documentation-capture, chart-capture, dashboard-screenshot, spa-scraping, dynamic-content, metadata-extraction]
complexity: [easy]
pairs_with: [documentation, prd_generator, doc_coauthoring]
dependencies:
  npm: [playwright]
  cli: [node, npm]
  optional: [google-chrome, google-chrome-stable]
source: external
scripts: [scripts/capture.js]
---

# Web Research Agent

**Use this skill for**: Capturing screenshots and extracting data from live websites for research, documentation, or content analysis. Ideal for scraping dynamic content, capturing visual elements (charts, dashboards, graphs), and gathering information from SPAs.

**Do NOT use for**: Automated testing or QA verification (use `playwright_qa_agent` instead).

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

Capture and analyze live web content visually using Playwright with your existing Chrome installation. Extract screenshots, text content, and structured metadata from websites for research and documentation purposes.

**Primary Use Cases**:
- Website research and competitive analysis
- Capturing visual elements (dashboards, charts, graphs)
- Extracting dynamic content from Single Page Applications
- Documenting current state of web interfaces
- Gathering data from multiple sources
- Screenshot capture for reports and presentations
- Content scraping for analysis

## Core Capture Script

```bash
node .claude/skills/support/web_research_agent/scripts/capture.js <url> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `--output, -o <name>` | Output base name (default: capture) |
| `--full` | Capture full page (scroll entire page) |
| `--text` | Extract visible text content to .txt file |
| `--meta` | Extract page metadata to _meta.json file |
| `--wait <ms>` | Additional wait time after page load |
| `--selector <css>` | Wait for specific element before capture |
| `--viewport <WxH>` | Set viewport size (default: 1280x800) |
| `--mobile` | Use mobile viewport (375x667) |
| `--tablet` | Use tablet viewport (768x1024) |

## Quick Start Examples

### Basic Screenshot Capture
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://example.com" \
  -o ./research/example
```
Output: `./research/example.png`

### Full Page Screenshot with Text Extraction
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://example.com" \
  --full \
  --text \
  -o ./research/example
```
Output: `./research/example.png`, `./research/example.txt`

### Capture with Metadata Extraction
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://dashboard.example.com" \
  --meta \
  --selector ".data-loaded" \
  -o ./research/dashboard
```
Output: `./research/dashboard.png`, `./research/dashboard_meta.json`

### Mobile Viewport Capture
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://m.example.com" \
  --mobile \
  --full \
  -o ./research/mobile_view
```

### Wait for Dynamic Content
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://spa.example.com" \
  --wait 3000 \
  --selector ".content-loaded" \
  -o ./research/spa_content
```

## Capture Workflow Pattern

The recommended research workflow:

1. **Capture**: Run capture script to get screenshot + optional text/metadata
2. **View**: Use Claude's Read tool on the screenshot for visual analysis
3. **Parse**: Read extracted text/JSON for searchable data
4. **Synthesize**: Combine visual observations with text data for insights

Example workflow:
```bash
# Step 1: Capture everything
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://competitor-dashboard.com" \
  --full --text --meta \
  -o ./research/competitor

# Step 2: Analyze with Claude
# - Read ./research/competitor.png (visual analysis)
# - Read ./research/competitor.txt (text content)
# - Read ./research/competitor_meta.json (structured data)

# Step 3: Synthesize findings in documentation or PRD
```

## Advanced Usage Patterns

### Inline Script Usage

You can also use Playwright directly in your workflow:

#### Simple Screenshot
```javascript
const { chromium } = require('playwright');

const browser = await chromium.launch({
  channel: 'chrome',
  headless: true
});
const page = await browser.newPage();
await page.setViewportSize({ width: 1280, height: 800 });
await page.goto('https://example.com', { waitUntil: 'networkidle' });
await page.screenshot({ path: 'screenshot.png' });
await browser.close();
```

#### Element-Specific Capture
```javascript
// Capture specific element (charts, tables, etc.)
await page.goto('https://dashboard.com');
const element = await page.locator('.main-chart').first();
await element.screenshot({ path: 'chart.png' });
```

#### Wait Strategies for Dynamic Content
```javascript
// Wait for specific element
await page.waitForSelector('.data-loaded', { timeout: 10000 });

// Wait for network idle (SPAs)
await page.waitForLoadState('networkidle');

// Wait for specific text
await page.waitForFunction(() =>
  document.body.innerText.includes('Loading complete')
);

// Custom delay (last resort)
await page.waitForTimeout(2000);
```

## Metadata Extraction

When using `--meta`, the script extracts:

```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "description": "Meta description content",
  "h1": ["Main Heading"],
  "h2": ["Subheading 1", "Subheading 2"],
  "links": [
    { "text": "Link text", "href": "https://..." }
  ],
  "images": [
    { "alt": "Image description", "src": "https://..." }
  ],
  "tables": 3,
  "forms": 1
}
```

This structured data is useful for:
- Analyzing site structure
- Extracting navigation patterns
- Identifying key content sections
- Building site maps

## Handling Authentication

For sites requiring login:

### Option 1: Persistent Context
```javascript
const context = await chromium.launchPersistentContext(
  '/path/to/chrome/profile',  // e.g., ~/.config/google-chrome/Default
  { channel: 'chrome', headless: false }  // headless: false for initial auth
);
```

### Option 2: Cookie Injection
```javascript
await context.addCookies([
  { name: 'session', value: 'xxx', domain: '.example.com' }
]);
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Chrome not found | Verify path: `which google-chrome` or set `executablePath` explicitly |
| Timeout on SPA | Increase timeout with `--wait` or use `--selector` for dynamic content |
| Blank screenshot | Add delay or wait for specific selector to appear |
| Permission denied | Run Chrome with `--no-sandbox` in containerized environments |
| Bot detection | Some sites block headless browsers; use persistent context with real profile |

## Limitations

- Cannot bypass CAPTCHAs or bot detection without additional tooling
- Some sites block headless browsers (try persistent context with real Chrome profile)
- Heavy JavaScript sites may need longer wait times
- Authentication requires manual session setup or cookie injection
- Rate limiting may apply for high-volume scraping

## Research Guidance

Before starting research, consult `references/research-methodology.md` for:
- Source priority framework (primary sources > expert analysis > community > general)
- What to screenshot vs. text-extract
- Source evaluation checklist (currency, authority, accuracy, purpose, bias)
- Domain-specific guidance (cybersecurity, fintech, technical, medical)
- Synthesis guidelines and red flags

Key principles:
1. **Lead with authoritative sources**: .gov, official docs, peer-reviewed first
2. **Screenshot visuals, extract text**: Charts/diagrams need visual capture; prose doesn't
3. **Note contradictions**: Flag conflicting sources for human review
4. **State confidence levels**: Distinguish fact from consensus from speculation

## Technical Reference

See `references/advanced-patterns.md` for:
- Table/chart data extraction techniques
- Multi-page crawling patterns
- PDF capture from web pages
- Mobile viewport emulation
- Network interception (capturing API responses)
- Bot detection workarounds

## Example Use Cases

### 1. Competitive Analysis
Capture competitor dashboards and product pages:
```bash
for url in "https://competitor1.com" "https://competitor2.com"; do
  node .claude/skills/support/web_research_agent/scripts/capture.js \
    "$url" --full --meta -o "./research/$(echo $url | sed 's/https:\/\///')"
done
```

### 2. Documentation Screenshots
Capture current state of UI for documentation:
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "http://localhost:3000/dashboard" \
  --full \
  -o ./docs/images/dashboard-2024
```

### 3. Data Dashboard Capture
Capture data visualizations:
```bash
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://analytics.example.com" \
  --selector ".charts-loaded" \
  --wait 2000 \
  -o ./reports/analytics-snapshot
```

### 4. Mobile vs Desktop Comparison
```bash
# Desktop
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://example.com" -o ./compare/desktop

# Mobile
node .claude/skills/support/web_research_agent/scripts/capture.js \
  "https://example.com" --mobile -o ./compare/mobile
```

## Workflow Integration

**Typical workflow**:
1. Identify target websites for research
2. Use capture script to gather screenshots and data
3. Analyze captured content with Claude
4. Extract insights and synthesize findings
5. Document research in PRD, reports, or documentation

**Pairs well with**: `prd_generator` for requirements gathering, `documentation` for creating docs, `doc_coauthoring` for collaborative research reports.
