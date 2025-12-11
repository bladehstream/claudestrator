# Cloudflare Cron Triggers and Scheduled Events

Run Workers on a schedule for background jobs, maintenance tasks, and periodic processing.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Max triggers per Worker** | 3 cron expressions |
| **Time zone** | UTC only |
| **Min interval** | 1 minute |
| **Propagation time** | ~15 minutes for changes |
| **Cost** | No additional cost (included in Workers) |

## Configuration

### wrangler.toml
```toml
name = "scheduled-worker"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[triggers]
crons = [
  "0 * * * *",      # Every hour
  "0 0 * * *",      # Daily at midnight UTC
  "0 0 * * 1",      # Every Monday at midnight UTC
]
```

### Handler Implementation
```typescript
// src/index.ts
import { Hono } from 'hono';

interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
}

const app = new Hono<{ Bindings: Env }>();

// HTTP routes
app.get('/', (c) => c.json({ status: 'ok' }));

// Export both fetch and scheduled handlers
export default {
  fetch: app.fetch,
  
  async scheduled(
    event: ScheduledEvent,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    console.log(`Cron triggered at ${event.scheduledTime}`);
    console.log(`Cron pattern: ${event.cron}`);
    
    // Perform scheduled task
    await performMaintenanceTask(env);
  },
};

async function performMaintenanceTask(env: Env): Promise<void> {
  // Your scheduled task logic
}
```

## Cron Expression Format

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

### Common Patterns

| Pattern | Description |
|---------|-------------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour (on the hour) |
| `0 */6 * * *` | Every 6 hours |
| `0 0 * * *` | Daily at midnight UTC |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `0 0 1 1 *` | Yearly on January 1st |
| `0 9 * * 1-5` | Weekdays at 9 AM UTC |
| `0 0,12 * * *` | Twice daily (midnight and noon) |
| `30 4 1,15 * *` | 1st and 15th at 4:30 AM |

### Step Values
```toml
[triggers]
crons = [
  "*/15 * * * *",   # Every 15 minutes
  "0 */2 * * *",    # Every 2 hours
  "0 0 */3 * *",    # Every 3 days
]
```

## Multiple Cron Triggers

### Different Tasks per Pattern
```typescript
export default {
  fetch: app.fetch,
  
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    switch (event.cron) {
      case '*/5 * * * *':
        await checkHealthEndpoints(env);
        break;
        
      case '0 * * * *':
        await aggregateHourlyMetrics(env);
        break;
        
      case '0 0 * * *':
        await cleanupOldData(env);
        break;
        
      default:
        console.log(`Unknown cron pattern: ${event.cron}`);
    }
  },
};
```

### wrangler.toml
```toml
[triggers]
crons = [
  "*/5 * * * *",   # Health checks every 5 min
  "0 * * * *",     # Hourly metrics
  "0 0 * * *",     # Daily cleanup
]
```

## Common Use Cases

### Database Cleanup
```typescript
async function cleanupOldData(env: Env): Promise<void> {
  // Delete records older than 30 days
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const { meta } = await env.DB.prepare(`
    DELETE FROM audit_logs
    WHERE created_at < ?
  `).bind(thirtyDaysAgo.toISOString()).run();
  
  console.log(`Deleted ${meta.changes} old audit logs`);
  
  // Delete soft-deleted records
  const { meta: softDeleted } = await env.DB.prepare(`
    DELETE FROM users
    WHERE deleted_at IS NOT NULL
      AND deleted_at < ?
  `).bind(thirtyDaysAgo.toISOString()).run();
  
  console.log(`Permanently deleted ${softDeleted.changes} users`);
}
```

### Cache Warming
```typescript
async function warmCache(env: Env): Promise<void> {
  // Fetch popular items and cache them
  const { results } = await env.DB.prepare(`
    SELECT * FROM products
    WHERE featured = TRUE
    ORDER BY views DESC
    LIMIT 100
  `).all();
  
  for (const product of results) {
    await env.CACHE.put(
      `product:${product.id}`,
      JSON.stringify(product),
      { expirationTtl: 3600 }
    );
  }
  
  console.log(`Warmed cache with ${results.length} products`);
}
```

### External API Sync
```typescript
async function syncFromExternalAPI(env: Env): Promise<void> {
  const response = await fetch('https://api.example.com/data', {
    headers: { 'Authorization': `Bearer ${env.API_KEY}` },
  });
  
  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }
  
  const data = await response.json();
  
  // Update local database
  const statements = data.items.map((item: any) =>
    env.DB.prepare(`
      INSERT INTO external_data (id, name, value, synced_at)
      VALUES (?, ?, ?, datetime('now'))
      ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        value = excluded.value,
        synced_at = excluded.synced_at
    `).bind(item.id, item.name, item.value)
  );
  
  await env.DB.batch(statements);
  console.log(`Synced ${data.items.length} items`);
}
```

### Report Generation
```typescript
async function generateDailyReport(env: Env): Promise<void> {
  // Aggregate yesterday's data
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = yesterday.toISOString().split('T')[0];
  
  const { results } = await env.DB.prepare(`
    SELECT 
      COUNT(*) as total_orders,
      SUM(amount) as total_revenue,
      AVG(amount) as avg_order_value
    FROM orders
    WHERE DATE(created_at) = ?
  `).bind(dateStr).all();
  
  const report = results[0];
  
  // Store report
  await env.CACHE.put(
    `report:daily:${dateStr}`,
    JSON.stringify(report)
  );
  
  // Send webhook notification
  await fetch(env.WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'daily_report',
      date: dateStr,
      ...report,
    }),
  });
}
```

### Health Monitoring
```typescript
interface HealthCheck {
  name: string;
  url: string;
  expectedStatus: number;
}

const healthChecks: HealthCheck[] = [
  { name: 'API', url: 'https://api.example.com/health', expectedStatus: 200 },
  { name: 'Website', url: 'https://example.com', expectedStatus: 200 },
  { name: 'CDN', url: 'https://cdn.example.com/test.txt', expectedStatus: 200 },
];

async function checkHealth(env: Env): Promise<void> {
  const results = await Promise.allSettled(
    healthChecks.map(async (check) => {
      const start = Date.now();
      const response = await fetch(check.url, {
        method: 'HEAD',
        signal: AbortSignal.timeout(5000),
      });
      const duration = Date.now() - start;
      
      return {
        name: check.name,
        status: response.status,
        ok: response.status === check.expectedStatus,
        duration,
      };
    })
  );
  
  const failures = results
    .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
    .map(r => r.value)
    .filter(r => !r.ok);
  
  if (failures.length > 0) {
    await sendAlert(env, failures);
  }
  
  // Log all results
  console.log('Health check results:', JSON.stringify(results));
}
```

### Session Cleanup
```typescript
async function cleanupExpiredSessions(env: Env): Promise<void> {
  // List all session keys
  const { keys } = await env.CACHE.list({ prefix: 'session:' });
  
  let expired = 0;
  
  for (const key of keys) {
    const session = await env.CACHE.get(key.name, 'json') as {
      expiresAt: number;
    } | null;
    
    if (session && session.expiresAt < Date.now()) {
      await env.CACHE.delete(key.name);
      expired++;
    }
  }
  
  console.log(`Cleaned up ${expired} expired sessions`);
}
```

## Error Handling

```typescript
export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    const startTime = Date.now();
    
    try {
      await performTask(env);
      
      // Log success
      console.log(JSON.stringify({
        type: 'cron_success',
        cron: event.cron,
        duration: Date.now() - startTime,
      }));
    } catch (error) {
      // Log failure
      console.error(JSON.stringify({
        type: 'cron_failure',
        cron: event.cron,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
      }));
      
      // Optionally send alert
      ctx.waitUntil(sendErrorAlert(env, error, event.cron));
      
      // Re-throw to mark cron as failed in dashboard
      throw error;
    }
  },
};
```

## Testing Locally

### Enable Test Mode
```bash
# Start dev server with scheduled endpoint
npx wrangler dev --test-scheduled
```

### Trigger Manually
```bash
# HTTP request to trigger scheduled handler
curl "http://localhost:8787/__scheduled?cron=*+*+*+*+*"

# Or in browser
# http://localhost:8787/__scheduled
```

### In Code
```typescript
// Test helper for cron handlers
async function testScheduled(env: Env, cron: string): Promise<void> {
  const mockEvent: ScheduledEvent = {
    scheduledTime: Date.now(),
    cron,
  };
  
  const mockCtx: ExecutionContext = {
    waitUntil: () => {},
    passThroughOnException: () => {},
  };
  
  await scheduled(mockEvent, env, mockCtx);
}
```

## Cloudflare Workflows Integration

For complex multi-step tasks, combine cron with Workflows:

```typescript
// wrangler.toml
[[workflows]]
name = "data-pipeline"
binding = "PIPELINE"
class_name = "DataPipeline"

[triggers]
crons = ["0 0 * * *"]
```

```typescript
// Workflow definition
export class DataPipeline extends Workflow {
  async run(event: WorkflowEvent, step: WorkflowStep) {
    // Step 1: Fetch data
    const data = await step.do('fetch-data', async () => {
      return fetchFromAPI();
    });
    
    // Step 2: Process (can take minutes/hours)
    const processed = await step.do('process-data', async () => {
      return processData(data);
    });
    
    // Step 3: Store results
    await step.do('store-results', async () => {
      return storeResults(processed);
    });
  }
}

// Trigger workflow from cron
export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    // Start workflow instance
    const instance = await env.PIPELINE.create({
      params: { triggeredBy: 'cron', cron: event.cron },
    });
    
    console.log(`Started workflow: ${instance.id}`);
  },
};
```

## Green Compute

Run crons only in regions powered by renewable energy:

```toml
# wrangler.toml
[triggers]
crons = ["0 0 * * *"]

[placement]
mode = "smart"  # or "off"

# Green compute (renewable energy regions)
# Note: May increase latency
```

## Monitoring and Debugging

### Logs
```bash
# Tail production logs
npx wrangler tail

# Filter for cron events
npx wrangler tail --format json | jq 'select(.trigger == "cron")'
```

### Metrics
- View in Cloudflare Dashboard → Workers → your-worker → Metrics
- Cron invocations show separately from HTTP requests
- Track success/failure rates

### Alerting
```typescript
async function sendErrorAlert(
  env: Env,
  error: unknown,
  cron: string
): Promise<void> {
  await fetch(env.SLACK_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `🚨 Cron job failed`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Cron Pattern:* \`${cron}\`\n*Error:* ${error instanceof Error ? error.message : 'Unknown'}`,
          },
        },
      ],
    }),
  });
}
```

## Best Practices

1. **Use UTC times** - Crons always run in UTC
2. **Handle idempotency** - Crons may occasionally run twice
3. **Set timeouts** - Use AbortSignal.timeout() for external calls
4. **Log structured data** - JSON logs for easier debugging
5. **Monitor failures** - Set up alerting for cron failures
6. **Keep tasks short** - Crons have same CPU limits as Workers
7. **Use Workflows for long tasks** - Chain steps, persist state
8. **Test locally** - Use --test-scheduled flag
9. **Stagger schedules** - Avoid all crons at :00
10. **Document cron patterns** - Comments in wrangler.toml
