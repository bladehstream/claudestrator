#!/usr/bin/env node
/**
 * QA Test Runner - Functional testing with Playwright
 * Supports desktop, tablet, and mobile viewports
 * 
 * Usage:
 *   node test-runner.js <url> [options]
 * 
 * Options:
 *   --viewport <preset>   desktop|tablet|mobile|all (default: desktop)
 *   --flow <path>         Path to test flow JSON file
 *   --output, -o <dir>    Output directory (default: ./test-results)
 *   --full                Capture full-page screenshots
 *   --trace               Enable Playwright trace recording
 *   --slow <ms>           Slow down actions for debugging
 *   --headed              Run with visible browser
 *   --no-sandbox          Disable Chrome sandbox (for containers)
 */

const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

// Viewport presets
const VIEWPORTS = {
  'desktop': { width: 1280, height: 800, ua: null },
  'desktop-hd': { width: 1920, height: 1080, ua: null },
  'tablet': { 
    width: 768, 
    height: 1024, 
    ua: 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
  },
  'tablet-landscape': { 
    width: 1024, 
    height: 768, 
    ua: 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
  },
  'mobile': { 
    width: 375, 
    height: 667, 
    ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    isMobile: true,
    hasTouch: true
  },
  'mobile-large': { 
    width: 414, 
    height: 896, 
    ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    isMobile: true,
    hasTouch: true
  },
  'mobile-android': { 
    width: 360, 
    height: 740, 
    ua: 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
    isMobile: true,
    hasTouch: true
  }
};

function parseArgs(args) {
  const opts = {
    url: null,
    viewport: 'desktop',
    flow: null,
    output: './test-results',
    fullPage: false,
    trace: false,
    slow: 0,
    headed: false,
    noSandbox: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('http://') || arg.startsWith('https://')) {
      opts.url = arg;
    } else if (arg === '--viewport') {
      opts.viewport = args[++i];
    } else if (arg === '--flow') {
      opts.flow = args[++i];
    } else if (arg === '--output' || arg === '-o') {
      opts.output = args[++i];
    } else if (arg === '--full') {
      opts.fullPage = true;
    } else if (arg === '--trace') {
      opts.trace = true;
    } else if (arg === '--slow') {
      opts.slow = parseInt(args[++i], 10);
    } else if (arg === '--headed') {
      opts.headed = true;
    } else if (arg === '--no-sandbox') {
      opts.noSandbox = true;
    }
  }

  return opts;
}

// Execute a single test action
async function executeAction(page, action, context) {
  const { screenshotCount, outputDir, fullPage } = context;
  
  switch (action.action) {
    case 'goto':
      await page.goto(action.url, { waitUntil: action.waitUntil || 'networkidle' });
      break;
      
    case 'click':
      await page.click(action.selector);
      break;
      
    case 'fill':
      await page.fill(action.selector, action.value);
      break;
      
    case 'select':
      await page.selectOption(action.selector, action.value);
      break;
      
    case 'check':
      await page.check(action.selector);
      break;
      
    case 'uncheck':
      await page.uncheck(action.selector);
      break;
      
    case 'hover':
      await page.hover(action.selector);
      break;
      
    case 'press':
      await page.keyboard.press(action.key);
      break;
      
    case 'screenshot':
      context.screenshotCount++;
      const ssName = `${String(context.screenshotCount).padStart(2, '0')}-${action.name || 'screenshot'}.png`;
      await page.screenshot({ 
        path: path.join(outputDir, 'screenshots', ssName),
        fullPage: action.fullPage ?? fullPage
      });
      return { screenshot: ssName };
      
    case 'wait':
      if (action.for === 'navigation') {
        await page.waitForNavigation();
      } else if (action.for === 'networkidle') {
        await page.waitForLoadState('networkidle');
      } else if (action.for === 'timeout' || action.ms) {
        await page.waitForTimeout(action.ms || 1000);
      }
      break;
      
    case 'waitFor':
      await page.waitForSelector(action.selector, { 
        state: action.state || 'visible',
        timeout: action.timeout || 10000
      });
      break;
      
    case 'scroll':
      if (action.selector) {
        await page.locator(action.selector).scrollIntoViewIfNeeded();
      } else if (action.position === 'bottom') {
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      } else if (action.position === 'top') {
        await page.evaluate(() => window.scrollTo(0, 0));
      } else if (action.x !== undefined && action.y !== undefined) {
        await page.evaluate(({x, y}) => window.scrollTo(x, y), action);
      }
      break;
      
    case 'evaluate':
      return { result: await page.evaluate(action.script) };
      
    case 'assert':
      return await executeAssertion(page, action);
      
    default:
      console.warn(`Unknown action: ${action.action}`);
  }
  
  return { success: true };
}

// Execute assertion and return result
async function executeAssertion(page, assertion) {
  let passed = false;
  let actual = null;
  
  try {
    switch (assertion.type) {
      case 'url':
        actual = page.url();
        if (assertion.contains) passed = actual.includes(assertion.contains);
        else if (assertion.equals) passed = actual === assertion.equals;
        else if (assertion.matches) passed = new RegExp(assertion.matches).test(actual);
        break;
        
      case 'title':
        actual = await page.title();
        if (assertion.contains) passed = actual.includes(assertion.contains);
        else if (assertion.equals) passed = actual === assertion.equals;
        break;
        
      case 'visible':
        passed = await page.locator(assertion.selector).isVisible();
        actual = passed ? 'visible' : 'not visible';
        break;
        
      case 'hidden':
        passed = !(await page.locator(assertion.selector).isVisible());
        actual = passed ? 'hidden' : 'visible';
        break;
        
      case 'text':
        actual = await page.locator(assertion.selector).innerText();
        if (assertion.contains) passed = actual.includes(assertion.contains);
        else if (assertion.equals) passed = actual.trim() === assertion.equals;
        break;
        
      case 'count':
        actual = await page.locator(assertion.selector).count();
        if (assertion.equals !== undefined) passed = actual === assertion.equals;
        else if (assertion.min !== undefined) passed = actual >= assertion.min;
        else if (assertion.max !== undefined) passed = actual <= assertion.max;
        break;
        
      case 'attribute':
        actual = await page.locator(assertion.selector).getAttribute(assertion.attr);
        passed = actual === assertion.value;
        break;
    }
  } catch (err) {
    return { 
      assertion: assertion.type, 
      passed: false, 
      error: err.message,
      actual 
    };
  }
  
  return { 
    assertion: assertion.type, 
    passed, 
    actual,
    expected: assertion.contains || assertion.equals || assertion.matches || assertion.min || assertion.max || assertion.value
  };
}

// Run tests for a single viewport
async function runViewport(url, viewportName, opts) {
  const viewport = VIEWPORTS[viewportName];
  if (!viewport) {
    console.error(`Unknown viewport: ${viewportName}`);
    return null;
  }
  
  const outputDir = path.join(opts.output, viewportName);
  fs.mkdirSync(path.join(outputDir, 'screenshots'), { recursive: true });
  
  const launchOpts = {
    channel: 'chrome',
    headless: !opts.headed,
    slowMo: opts.slow
  };
  
  if (opts.noSandbox) {
    launchOpts.args = ['--no-sandbox', '--disable-setuid-sandbox'];
  }
  
  const browser = await chromium.launch(launchOpts);
  
  const contextOpts = {
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile || false,
    hasTouch: viewport.hasTouch || false
  };
  
  if (viewport.ua) {
    contextOpts.userAgent = viewport.ua;
  }
  
  const context = await browser.newContext(contextOpts);
  
  // Start tracing if enabled
  if (opts.trace) {
    await context.tracing.start({ screenshots: true, snapshots: true });
  }
  
  const page = await context.newPage();
  
  // Collect console messages and errors
  const consoleLogs = [];
  const errors = [];
  
  page.on('console', msg => {
    consoleLogs.push({ type: msg.type(), text: msg.text() });
  });
  
  page.on('pageerror', err => {
    errors.push({ message: err.message, stack: err.stack });
  });
  
  const results = {
    viewport: viewportName,
    dimensions: `${viewport.width}x${viewport.height}`,
    url,
    startTime: new Date().toISOString(),
    steps: [],
    assertions: [],
    consoleLogs: [],
    errors: [],
    screenshots: []
  };
  
  const execContext = {
    screenshotCount: 0,
    outputDir,
    fullPage: opts.fullPage
  };
  
  try {
    // Load flow if provided, otherwise do basic page test
    let steps = [];
    
    if (opts.flow) {
      const flowContent = fs.readFileSync(opts.flow, 'utf-8');
      const flow = JSON.parse(flowContent);
      steps = flow.steps || [];
      results.flowName = flow.name;
    } else {
      // Default: navigate and screenshot
      steps = [
        { action: 'goto', url },
        { action: 'screenshot', name: 'initial-load' },
        { action: 'wait', for: 'networkidle' },
        { action: 'screenshot', name: 'after-load' }
      ];
    }
    
    // Execute steps
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const stepResult = {
        index: i + 1,
        action: step.action,
        ...step
      };
      
      try {
        const actionResult = await executeAction(page, step, execContext);
        stepResult.result = actionResult;
        stepResult.passed = actionResult.passed !== false;
        
        if (actionResult.screenshot) {
          results.screenshots.push(actionResult.screenshot);
        }
        
        if (step.action === 'assert') {
          results.assertions.push(actionResult);
        }
      } catch (err) {
        stepResult.passed = false;
        stepResult.error = err.message;
        
        // Screenshot on failure
        execContext.screenshotCount++;
        const failName = `${String(execContext.screenshotCount).padStart(2, '0')}-FAIL-step${i + 1}.png`;
        await page.screenshot({ 
          path: path.join(outputDir, 'screenshots', failName),
          fullPage: true
        });
        results.screenshots.push(failName);
      }
      
      results.steps.push(stepResult);
    }
    
  } finally {
    results.consoleLogs = consoleLogs;
    results.errors = errors;
    results.endTime = new Date().toISOString();
    
    // Stop tracing
    if (opts.trace) {
      await context.tracing.stop({ path: path.join(outputDir, 'trace.zip') });
    }
    
    await browser.close();
  }
  
  // Calculate summary
  results.summary = {
    totalSteps: results.steps.length,
    passedSteps: results.steps.filter(s => s.passed).length,
    failedSteps: results.steps.filter(s => !s.passed).length,
    totalAssertions: results.assertions.length,
    passedAssertions: results.assertions.filter(a => a.passed).length,
    failedAssertions: results.assertions.filter(a => !a.passed).length,
    jsErrors: errors.length,
    consoleWarnings: consoleLogs.filter(l => l.type === 'warning').length,
    consoleErrors: consoleLogs.filter(l => l.type === 'error').length
  };
  
  // Write report
  fs.writeFileSync(
    path.join(outputDir, 'report.json'),
    JSON.stringify(results, null, 2)
  );
  
  return results;
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
QA Test Runner

Usage: node test-runner.js <url> [options]

Options:
  --viewport <preset>   desktop|desktop-hd|tablet|tablet-landscape|mobile|mobile-large|mobile-android|all
  --flow <path>         Path to test flow JSON file
  --output, -o <dir>    Output directory (default: ./test-results)
  --full                Capture full-page screenshots
  --trace               Enable Playwright trace recording
  --slow <ms>           Slow down actions for debugging
  --headed              Run with visible browser
  --no-sandbox          Disable Chrome sandbox (for containers/VMs)

Examples:
  node test-runner.js https://example.com --viewport desktop
  node test-runner.js https://example.com --viewport all --output ./results
  node test-runner.js https://app.com --flow login-flow.json --trace
`);
    process.exit(0);
  }
  
  const opts = parseArgs(args);
  
  if (!opts.url) {
    console.error('Error: URL required');
    console.error('Usage: node test-runner.js <url> [options]');
    process.exit(1);
  }
  
  console.log(`Starting QA tests for: ${opts.url}`);
  
  // Determine viewports to test
  let viewportsToTest = [];
  if (opts.viewport === 'all') {
    viewportsToTest = ['desktop', 'tablet', 'mobile'];
  } else {
    viewportsToTest = [opts.viewport];
  }
  
  const allResults = [];
  
  for (const vp of viewportsToTest) {
    console.log(`\nTesting viewport: ${vp}`);
    const result = await runViewport(opts.url, vp, opts);
    if (result) {
      allResults.push(result);
      console.log(`  Steps: ${result.summary.passedSteps}/${result.summary.totalSteps} passed`);
      console.log(`  Assertions: ${result.summary.passedAssertions}/${result.summary.totalAssertions} passed`);
      if (result.summary.jsErrors > 0) {
        console.log(`  ⚠️  JS Errors: ${result.summary.jsErrors}`);
      }
    }
  }
  
  // Write summary
  const summary = {
    url: opts.url,
    flow: opts.flow,
    timestamp: new Date().toISOString(),
    viewports: allResults.map(r => ({
      name: r.viewport,
      passed: r.summary.failedSteps === 0 && r.summary.failedAssertions === 0,
      steps: `${r.summary.passedSteps}/${r.summary.totalSteps}`,
      assertions: `${r.summary.passedAssertions}/${r.summary.totalAssertions}`,
      jsErrors: r.summary.jsErrors
    }))
  };
  
  fs.writeFileSync(
    path.join(opts.output, 'summary.json'),
    JSON.stringify(summary, null, 2)
  );
  
  console.log(`\nResults saved to: ${opts.output}`);
  
  // Exit with error code if any failures
  const anyFailed = allResults.some(r => 
    r.summary.failedSteps > 0 || r.summary.failedAssertions > 0
  );
  process.exit(anyFailed ? 1 : 0);
}

main().catch(err => {
  console.error('Test runner failed:', err.message);
  process.exit(1);
});
