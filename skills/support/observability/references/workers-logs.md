# Cloudflare Workers Logs

Native observability built into Cloudflare Workers for logging, querying, and analyzing your application.

## Setup

### Enable Workers Logs

```toml
# wrangler.toml
[observability]
enabled = true

[observability.logs]
invocation_logs = true      # Log each invocation
head_sampling_rate = 1      # 1 = 100%, 0.1 = 10%, 0.01 = 1%
```

### Per-Environment Configuration

```toml
# wrangler.toml

# Development: full logging
[env.development.observability]
enabled = true

[env.development.observability.logs]
invocation_logs = true
head_sampling_rate = 1

# Production: sampled logging for high traffic
[env.production.observability]
enabled = true

[env.production.observability.logs]
invocation_logs = true
head_sampling_rate = 0.1  # 10% sampling
```

## Console Logging

Workers Logs captures all console output:

```typescript
// All these are captured
console.log('Info message');
console.info('Info with level');
console.warn('Warning message');
console.error('Error message');
console.debug('Debug message');

// JSON is auto-parsed for field extraction
console.log(JSON.stringify({
  event: 'user_signup',
  userId: '123',
  plan: 'premium',
}));
```

### Structured Logging Best Practice

```typescript
// Workers Logs automatically parses JSON and indexes fields
function log(level: string, message: string, data?: Record<string, unknown>) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...data,
  }));
}

// Usage
log('info', 'Payment processed', {
  userId: 'user_123',
  amount: 99.99,
  currency: 'USD',
  paymentId: 'pay_abc',
});
```

This produces searchable fields in the Workers Logs dashboard.

## Real-Time Logs (wrangler tail)

View logs in real-time during development:

```bash
# Basic tail
npx wrangler tail

# Tail specific worker
npx wrangler tail my-worker-name

# JSON format for piping
npx wrangler tail --format json

# Filter by status
npx wrangler tail --status error

# Filter by IP (useful for debugging specific users)
npx wrangler tail --ip 192.168.1.1

# Filter by method
npx wrangler tail --method POST

# Filter by path
npx wrangler tail --search "/api/users"

# Combine filters
npx wrangler tail --status error --method POST --format json
```

### Processing Tail Output

```bash
# Filter to errors only
npx wrangler tail --format json | jq 'select(.outcome == "exception")'

# Extract specific fields
npx wrangler tail --format json | jq '{path: .event.request.url, status: .event.response.status}'

# Watch for specific events
npx wrangler tail --format json | jq 'select(.logs[].message | contains("payment"))'
```

## Dashboard: Query Builder

Access via: **Workers & Pages → Observability → Query Builder**

### Common Queries

**Error Rate by Endpoint:**
- Visualization: Count
- Filter: outcome = "exception"
- Group by: request.path

**P95 Response Time:**
- Visualization: Percentile (95th)
- Field: wallTime
- Group by: request.path

**Requests by Status Code:**
- Visualization: Count
- Group by: response.status

**Errors Over Time:**
- Visualization: Count
- Filter: level = "error"
- Group by: timestamp (1h buckets)

### Filtering Syntax

```
# Exact match
level = "error"

# Contains
message CONTAINS "payment"

# Numeric comparison
wallTime > 1000

# Multiple conditions
level = "error" AND request.path CONTAINS "/api"

# Field exists
userId IS NOT NULL
```

## Invocations View

Workers Logs groups logs by invocation (single request execution):

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // All these logs are grouped together per invocation
    console.log('Request received');
    console.log(JSON.stringify({ step: 'auth', userId: 'user_123' }));
    console.log(JSON.stringify({ step: 'db_query', duration_ms: 45 }));
    console.log(JSON.stringify({ step: 'response', status: 200 }));
    
    return new Response('OK');
  },
};
```

Each invocation shows:
- Request details (method, URL, headers)
- All console logs
- CPU time and wall time
- Outcome (ok/exception)
- Response status

## Logpush (External Destinations)

Send logs to external destinations for long-term storage or integration with existing tools.

### Enable Logpush

```toml
# wrangler.toml
logpush = true
```

### Supported Destinations

- **Cloudflare R2** (recommended for cost)
- **Amazon S3**
- **Google Cloud Storage**
- **Azure Blob Storage**
- **Sumo Logic**
- **Datadog**
- **Splunk**
- **New Relic**

### Creating a Logpush Job (Dashboard)

1. Go to **Analytics & Logs → Logs → Logpush**
2. Click **Create a Logpush job**
3. Select **Workers trace events** as dataset
4. Choose destination and configure credentials
5. (Optional) Filter by script name or outcome

### Creating a Logpush Job (API)

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/{account_id}/logpush/jobs" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "workers-to-r2",
    "logpull_options": "fields=Event,EventTimestampMs,Outcome,ScriptName,Logs",
    "destination_conf": "r2://{bucket_name}/{daily_date}?account-id={account_id}&access-key-id={r2_access_key}&secret-access-key={r2_secret}",
    "dataset": "workers_trace_events",
    "enabled": true
  }'
```

### Logpush Fields

| Field | Description |
|-------|-------------|
| `Event` | Event type (fetch, scheduled, etc.) |
| `EventTimestampMs` | Unix timestamp in milliseconds |
| `Outcome` | ok, exception, exceededCpu, etc. |
| `ScriptName` | Worker script name |
| `Logs` | Array of console.log messages |
| `Exceptions` | Array of uncaught exceptions |
| `ScriptVersion` | Script version metadata |

### Log Retention

| Tier | Workers Logs Retention | Logpush |
|------|------------------------|---------|
| Free | 24 hours | Not available |
| Paid | 7 days | Available |

For longer retention, use Logpush to R2 or external storage.

## Tail Workers

For advanced log processing, use Tail Workers to receive logs from other Workers:

```typescript
// tail-worker.ts
interface TailEvent {
  scriptName: string;
  outcome: string;
  event: {
    request?: {
      url: string;
      method: string;
    };
  };
  logs: Array<{
    level: string;
    message: unknown[];
    timestamp: number;
  }>;
  exceptions: Array<{
    name: string;
    message: string;
  }>;
}

export default {
  async tail(events: TailEvent[], env: Env): Promise<void> {
    for (const event of events) {
      // Filter and process logs
      if (event.outcome === 'exception') {
        // Send to external alerting
        await sendToSlack(event, env);
      }
      
      // Send all logs to external system
      await sendToLoggingService(event, env);
    }
  },
};

async function sendToSlack(event: TailEvent, env: Env): Promise<void> {
  await fetch(env.SLACK_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `🚨 Worker exception in ${event.scriptName}`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*Worker:* ${event.scriptName}\n*Exception:* ${event.exceptions[0]?.message}`,
          },
        },
      ],
    }),
  });
}
```

### Configure Tail Worker

```toml
# producer-worker wrangler.toml
[[tail_consumers]]
service = "my-tail-worker"
```

## Limits and Quotas

| Limit | Value |
|-------|-------|
| Daily log limit | 5 billion logs/account/day |
| Single log size | 256 KB max (truncated if larger) |
| Log retention | 7 days (paid), 24 hours (free) |
| Real-time tail | 10 connections per account |

### When Limits Are Exceeded

- After 5B logs/day: 1% head sampling applied automatically
- Logs > 256 KB: Truncated, `$cloudflare.truncated` field set to true

## Cost Optimization

### Sampling Strategy

```toml
# High traffic production
[env.production.observability.logs]
head_sampling_rate = 0.1  # 10% of requests

# Staging: full visibility
[env.staging.observability.logs]
head_sampling_rate = 1

# Critical paths: always log via code
```

```typescript
// Override sampling for important events
function logCritical(data: Record<string, unknown>) {
  // These always log regardless of sampling
  console.log(JSON.stringify({
    ...data,
    _critical: true,  // Marker for queries
  }));
}
```

### Efficient Logging

```typescript
// Don't log large payloads
// Bad
console.log(JSON.stringify({ body: await request.text() }));

// Good - log metadata only
console.log(JSON.stringify({
  bodySize: request.headers.get('content-length'),
  contentType: request.headers.get('content-type'),
}));

// Don't log in loops
// Bad
items.forEach(item => console.log(JSON.stringify({ itemId: item.id })));

// Good - log summary
console.log(JSON.stringify({
  event: 'batch_processed',
  count: items.length,
  firstId: items[0]?.id,
  lastId: items[items.length - 1]?.id,
}));
```

## Debugging with Workers Logs

### Debug Flow

1. **Real-time issue**: Use `wrangler tail` with filters
2. **Recent issue**: Query Builder with time filter
3. **Pattern analysis**: Group by fields, visualize counts
4. **Full investigation**: Logpush data in external tools

### Common Debug Queries

```
# Find slow requests
wallTime > 5000

# Find specific user's requests  
userId = "user_123"

# Find all errors for an endpoint
outcome = "exception" AND request.path CONTAINS "/api/payments"

# Track request through services
requestId = "abc-123"
```
