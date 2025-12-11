# Log Shipping

Send logs from Cloudflare Workers to external destinations for long-term storage, analysis, and alerting.

## Options Overview

| Method | Use Case | Real-time | Custom Processing |
|--------|----------|-----------|-------------------|
| **Workers Logs** | Built-in storage, dashboard queries | No | Limited |
| **Logpush** | High-volume to storage (R2, S3, etc.) | Near real-time | No |
| **Tail Workers** | Custom processing, real-time delivery | Yes | Full control |

## Workers Logs (Built-in)

Simplest option - logs stored in Cloudflare, queryable via dashboard.

### Configuration
```toml
# wrangler.toml
[observability]
enabled = true

[observability.logs]
invocation_logs = true
head_sampling_rate = 1  # 0-1, 1 = log 100% of requests
```

### Querying
- Dashboard: Workers & Pages → Your Worker → Logs
- API: Workers Observability API

### Limits
- 5 billion logs/day per account
- 256 KB max per log entry
- 7-day retention (default)

## Workers Logpush

Push logs to external storage destinations.

### Supported Destinations
- Cloudflare R2
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
- Splunk
- Datadog
- Sumo Logic

### Enable Logpush
```toml
# wrangler.toml
logpush = true
```

### Create Logpush Job (R2 Example)

```bash
# Create R2 bucket first
npx wrangler r2 bucket create worker-logs

# Create Logpush job via API
curl -X POST \
  "https://api.cloudflare.com/client/v4/accounts/{account_id}/logpush/jobs" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "worker-logs-to-r2",
    "output_options": {
      "field_names": ["Event", "EventTimestampMs", "Outcome", "ScriptName"],
      "timestamp_format": "rfc3339"
    },
    "destination_conf": "r2://worker-logs/logs/{DATE}?account-id={account_id}",
    "dataset": "workers_trace_events",
    "enabled": true
  }'
```

### Available Fields
```
Event                 # Log entry content
EventTimestampMs      # Timestamp in milliseconds  
Outcome              # "ok", "exception", "exceededCpu", etc.
ScriptName           # Worker name
Exceptions           # Array of exception details
Logs                 # Array of console.log outputs
```

### Filtering Logs
```json
{
  "filter": "{\"where\":{\"and\":[{\"key\":\"Outcome\",\"operator\":\"eq\",\"value\":\"exception\"}]}}"
}
```

## Tail Workers

Consumer Workers that receive logs from producer Workers in real-time.

### Create Tail Worker
```typescript
// tail-worker.ts
interface TailItem {
  event: {
    request: {
      url: string;
      method: string;
    };
    response?: {
      status: number;
    };
  } | null;
  eventTimestamp: number;
  logs: {
    level: string;
    message: unknown[];
    timestamp: number;
  }[];
  exceptions: {
    name: string;
    message: string;
    timestamp: number;
  }[];
  outcome: string;
  scriptName: string;
}

export default {
  async tail(events: TailItem[]): Promise<void> {
    for (const event of events) {
      // Process each event
      await processEvent(event);
    }
  },
};

async function processEvent(event: TailItem): Promise<void> {
  // Filter for errors only
  if (event.outcome !== 'ok' || event.exceptions.length > 0) {
    // Send to external service
    await sendToLoggingService({
      timestamp: event.eventTimestamp,
      scriptName: event.scriptName,
      outcome: event.outcome,
      exceptions: event.exceptions,
      logs: event.logs,
      request: event.event?.request,
    });
  }
}

async function sendToLoggingService(data: unknown): Promise<void> {
  // Send to Datadog, Splunk, etc.
  await fetch('https://http-intake.logs.datadoghq.com/api/v2/logs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': '{your-api-key}',
    },
    body: JSON.stringify({
      ddsource: 'cloudflare-worker',
      ddtags: `env:production,service:${data.scriptName}`,
      message: JSON.stringify(data),
    }),
  });
}
```

### Configure Tail Worker
```toml
# wrangler.toml (tail worker)
name = "log-processor"
main = "src/tail-worker.ts"
compatibility_date = "2024-01-01"
```

### Attach to Producer Worker
```toml
# wrangler.toml (producer worker)
name = "my-api"
main = "src/index.ts"

[[tail_consumers]]
service = "log-processor"
```

Or via dashboard: Worker → Settings → Tail Consumers → Add

## Sending to External Services

### Datadog

```typescript
// tail-worker.ts for Datadog
interface Env {
  DD_API_KEY: string;
}

export default {
  async tail(events: TailItem[], env: Env): Promise<void> {
    const logs = events.map(event => ({
      ddsource: 'cloudflare-worker',
      ddtags: `env:production,worker:${event.scriptName}`,
      hostname: 'cloudflare-edge',
      service: event.scriptName,
      message: JSON.stringify({
        outcome: event.outcome,
        logs: event.logs,
        exceptions: event.exceptions,
        request: event.event?.request,
      }),
      timestamp: event.eventTimestamp,
    }));

    await fetch('https://http-intake.logs.datadoghq.com/api/v2/logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'DD-API-KEY': env.DD_API_KEY,
      },
      body: JSON.stringify(logs),
    });
  },
};
```

### Splunk

```typescript
// tail-worker.ts for Splunk
interface Env {
  SPLUNK_HEC_TOKEN: string;
  SPLUNK_HEC_URL: string;
}

export default {
  async tail(events: TailItem[], env: Env): Promise<void> {
    const splunkEvents = events.map(event => ({
      time: event.eventTimestamp / 1000, // Splunk uses seconds
      host: 'cloudflare-edge',
      source: 'cloudflare-worker',
      sourcetype: '_json',
      event: {
        scriptName: event.scriptName,
        outcome: event.outcome,
        logs: event.logs,
        exceptions: event.exceptions,
        request: event.event?.request,
      },
    }));

    await fetch(env.SPLUNK_HEC_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${env.SPLUNK_HEC_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: splunkEvents.map(e => JSON.stringify(e)).join('\n'),
    });
  },
};
```

### Sumo Logic

```typescript
// tail-worker.ts for Sumo Logic
interface Env {
  SUMO_ENDPOINT: string;
}

export default {
  async tail(events: TailItem[], env: Env): Promise<void> {
    const logs = events.map(event => JSON.stringify({
      timestamp: new Date(event.eventTimestamp).toISOString(),
      scriptName: event.scriptName,
      outcome: event.outcome,
      logs: event.logs,
      exceptions: event.exceptions,
      request: event.event?.request,
    }));

    await fetch(env.SUMO_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sumo-Category': 'cloudflare/workers',
      },
      body: logs.join('\n'),
    });
  },
};
```

## Buffering and Batching

For high-volume scenarios, buffer logs before sending:

```typescript
interface Env {
  LOG_BUFFER: KVNamespace;
  LOG_ENDPOINT: string;
}

const BATCH_SIZE = 100;
const FLUSH_INTERVAL_MS = 10000;

export default {
  async tail(events: TailItem[], env: Env): Promise<void> {
    // Get current buffer
    const bufferKey = 'log-buffer';
    const existingBuffer = await env.LOG_BUFFER.get(bufferKey);
    const buffer: TailItem[] = existingBuffer ? JSON.parse(existingBuffer) : [];
    
    // Add new events
    buffer.push(...events);
    
    // Flush if batch size reached
    if (buffer.length >= BATCH_SIZE) {
      await flushLogs(buffer, env);
      await env.LOG_BUFFER.delete(bufferKey);
    } else {
      // Store buffer for next invocation
      await env.LOG_BUFFER.put(bufferKey, JSON.stringify(buffer), {
        expirationTtl: 60, // Auto-expire after 60 seconds
      });
    }
  },
  
  // Scheduled handler to flush remaining logs
  async scheduled(event: ScheduledEvent, env: Env): Promise<void> {
    const bufferKey = 'log-buffer';
    const buffer = await env.LOG_BUFFER.get(bufferKey);
    
    if (buffer) {
      await flushLogs(JSON.parse(buffer), env);
      await env.LOG_BUFFER.delete(bufferKey);
    }
  },
};

async function flushLogs(logs: TailItem[], env: Env): Promise<void> {
  if (logs.length === 0) return;
  
  await fetch(env.LOG_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(logs),
  });
}
```

## Error Handling in Tail Workers

```typescript
export default {
  async tail(events: TailItem[], env: Env): Promise<void> {
    try {
      await processEvents(events, env);
    } catch (error) {
      // Tail Workers can't easily retry, so log failure
      console.error('Failed to process tail events:', error);
      
      // Optionally store failed events for retry
      const failedKey = `failed-${Date.now()}`;
      await env.KV.put(failedKey, JSON.stringify({
        events,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      }), { expirationTtl: 3600 }); // Keep for 1 hour
    }
  },
};
```

## Choosing the Right Method

| Scenario | Recommendation |
|----------|----------------|
| Simple debugging | Workers Logs |
| Compliance/audit logs | Logpush to R2/S3 |
| Real-time alerting | Tail Workers → Alerting service |
| Custom enrichment | Tail Workers with processing |
| Cost-sensitive high volume | Logpush (batched, compressed) |
| Integration with existing tools | Tail Workers to Datadog/Splunk/etc. |

## Best Practices

1. **Filter at source** - Don't ship everything, filter for errors/warnings
2. **Use structured JSON** - Easier to parse and query
3. **Include context** - Request IDs, user IDs, timestamps
4. **Handle failures gracefully** - Tail Workers shouldn't block producers
5. **Monitor your log pipeline** - Watch for dropped logs
6. **Consider costs** - External services charge per volume
7. **Use appropriate sampling** - 100% logging may not be necessary
