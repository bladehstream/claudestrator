---
name: Browser Automation
id: browser_automation
version: 1.0
category: implementation
domain: [web, automation, testing]
task_types: [automation, testing, scraping]
keywords: [browser, chrome, mcp, devtools, automation, scraping, testing, form, screenshot, navigate]
complexity: [normal]
pairs_with: [beautifulsoup_scraper, playwright_qa_agent, web_research_agent]
source: local
---

# Browser Automation via Chrome DevTools MCP

Control a live Chrome browser directly from Claude Code using the Model Context Protocol.

## When to Use This vs Other Skills

| Skill | Use When |
|-------|----------|
| **browser_automation** (this) | Claude Code MCP integration, authenticated sessions, real-time debugging |
| **web_research_agent** | Standalone Playwright scripts, batch captures, no MCP needed |
| **playwright_qa_agent** | Automated test suites, CI/CD integration, test flow definitions |
| **beautifulsoup_scraper** | Static HTML parsing, no JavaScript rendering needed |

## Quick Setup

### 1. Add MCP Server to Claude Code

```bash
# One-liner install
claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest
```

### 2. Launch Chrome with Remote Debugging

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"

# Linux
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\.chrome-debug-profile"
```

### 3. Verify Connection

In Claude Code:
```
/mcp
```
Look for `chrome-devtools` with status "Connected".

## Available MCP Tools

All tools are prefixed with `mcp__chrome-devtools__`:

| Tool | Description |
|------|-------------|
| `navigate` | Go to a URL |
| `click` | Click an element by selector |
| `type` | Type text into an input field |
| `screenshot` | Capture page or element screenshot |
| `evaluate` | Execute JavaScript in the page |
| `get_page_content` | Get page HTML or text content |
| `get_console_logs` | Retrieve browser console output |
| `get_network_requests` | List network requests/responses |
| `wait_for_selector` | Wait for element to appear |
| `scroll` | Scroll page or element |

## Common Workflows

### Web Navigation & Data Extraction

```
Claude, navigate to https://news.ycombinator.com,
extract the top 10 story titles and their point counts,
and save them to a CSV file.
```

### Form Automation

```
Claude, go to localhost:3000/signup, fill out the form with:
- Name: Test User
- Email: test@example.com
- Password: SecurePass123
Then submit and verify the success message appears.
```

### Visual Testing

```
Claude, take screenshots of my homepage at:
- 1920x1080 (desktop)
- 768x1024 (tablet)
- 375x667 (mobile)
Save them to ./screenshots/ with descriptive names.
```

### Authenticated Session Scraping

```
Claude, I'm logged into LinkedIn in Chrome.
Go to my notifications page and summarize any connection requests.
```

### Console Log Debugging

```
Claude, open localhost:3000, interact with the login form,
and show me any console errors that appear.
```

## Persistent Session Setup

For tasks requiring login state (email, social media, internal tools):

### 1. Create Dedicated Debug Profile

```bash
# Start Chrome with persistent profile
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-debug-profile"
```

### 2. Log Into Your Accounts

Manually log into Gmail, GitHub, LinkedIn, etc. in this Chrome window.
Sessions persist across restarts when using the same `--user-data-dir`.

### 3. Configure MCP with Browser URL

```bash
claude mcp add --transport stdio chrome-devtools -- \
  npx -y chrome-devtools-mcp@latest \
  --browserUrl=http://127.0.0.1:9222
```

## Safety Considerations

### Security Warnings

1. **Remote debugging exposes your browser** - Any process on your machine can connect to port 9222
2. **AI can see everything** - All content in the browser window is accessible to Claude
3. **Use a dedicated profile** - Don't use your main Chrome profile with sensitive accounts
4. **Close when done** - Debugging port closes when Chrome exits

### Best Practices

- ✅ Use a separate `--user-data-dir` for debug sessions
- ✅ Only log into accounts you're comfortable exposing
- ✅ Avoid banking, healthcare, and highly sensitive sites
- ✅ Review actions before confirming high-risk operations
- ❌ Don't browse sensitive personal accounts
- ❌ Don't store passwords for critical services in the debug profile

## Troubleshooting

### "Chrome DevTools not connected"

```bash
# Check if Chrome is running with debugging
curl http://127.0.0.1:9222/json/version

# Should return JSON with Chrome info
# If empty/error, restart Chrome with --remote-debugging-port=9222
```

### "Cannot connect to browser"

```bash
# Kill existing Chrome instances
pkill -f chrome

# Restart with debugging port
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug"
```

### MCP Server Not Appearing

```bash
# Re-add the MCP server
claude mcp remove chrome-devtools
claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest

# Restart Claude Code
```

## Integration with Other Skills

### Combined with web_research_agent

Use browser_automation for authenticated access, web_research_agent for batch processing:

```
1. Use browser_automation to log into internal dashboard
2. Export data to CSV
3. Use beautifulsoup_scraper to parse the exported data
```

### Combined with playwright_qa_agent

Use browser_automation for exploratory testing, playwright_qa_agent for repeatable test suites:

```
1. Explore app manually with browser_automation
2. Create test flow JSON based on discoveries
3. Run automated tests with playwright_qa_agent
```
