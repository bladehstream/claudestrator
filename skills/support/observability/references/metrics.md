# Metrics and Analytics

Monitor your Cloudflare Workers performance with built-in analytics and custom metrics.

## Workers Analytics (Built-in)

Cloudflare automatically collects metrics for all Workers:

### Available Metrics

| Metric | Description |
|--------|-------------|
| **Requests** | Total invocations |
| **Subrequests** | fetch() calls made by Worker |
| **Duration (CPU Time)** | Actual CPU time consumed |
| **Duration (Wall Time)** | Total request duration including I/O |
| **Errors** | Failed invocations |
| **Data In/Out** | Request/response body sizes |

### Dashboard Access

1. **Workers & Pages → Your Worker → Analytics**
2. **Workers & Pages → Observability → Metrics** (cross-worker view)

### GraphQL Analytics API

```typescript
// Query Workers analytics via GraphQL
const query = `
  query WorkerAnalytics($accountTag: String!, $filter: AccountWorkersInvocationsAdaptiveFilter!) {
    viewer {
      accounts(filter: { accountTag: $accountTag }) {
        workersInvocationsAdaptive(
          filter: $filter
          limit: 1000
        ) {
          sum {
            requests
            errors
            subrequests
          }
          avg {
            cpuTime
            duration
          }
          dimensions {
            datetime
            scriptName
            status
          }
        }
      }
    }
  }
`;

async function getAnalytics(env: Env, since: Date): Promise<AnalyticsData> {
  const response = await fetch('https://api.cloudflare.com/client/v4/graphql', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.CF_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      variables: {
        accountTag: env.CF_ACCOUNT_ID,
        filter: {
          datetime_geq: since.toISOString(),
          datetime_lt: new Date().toISOString(),
        },
      },
    }),
  });
  
  return response.json();
}
```

## Custom Metrics via Logs

Use structured logging to create queryable metrics:

```typescript
// Log metrics as JSON for Workers Logs Query Builder
function logMetric(name: string, value: number, tags: Record<string, string> = {}) {
  console.log(JSON.stringify({
    _type: 'metric',
    metric: name,
    value,
    timestamp: Date.now(),
    ...tags,
  }));
}

// Usage
logMetric('payment_amount', 99.99, { currency: 'USD', method: 'card' });
logMetric('api_latency_ms', 45, { endpoint: '/users', method: 'GET' });
logMetric('cache_hit', 1, { key_prefix: 'user' });
```

### Query in Workers Logs

```
# Filter to metrics
_type = "metric"

# Specific metric
_type = "metric" AND metric = "payment_amount"

# Aggregate in Query Builder
Visualization: Sum
Field: value
Filter: _type = "metric" AND metric = "payment_amount"
Group by: currency
```

## Request Metrics Middleware

```typescript
import { createMiddleware } from 'hono/factory';

interface RequestMetrics {
  path: string;
  method: string;
  status: number;
  duration_ms: number;
  cpuTime_ms?: number;
}

export const metricsMiddleware = createMiddleware(async (c, next) => {
  const start = performance.now();
  const startCpu = Date.now(); // Rough CPU estimate
  
  try {
    await next();
  } finally {
    const duration_ms = Math.round(performance.now() - start);
    
    const metrics: RequestMetrics = {
      path: c.req.path,
      method: c.req.method,
      status: c.res.status,
      duration_ms,
    };
    
    // Log as metric for analytics
    console.log(JSON.stringify({
      _type: 'request_metric',
      ...metrics,
      timestamp: Date.now(),
    }));
    
    // Log slow requests as warnings
    if (duration_ms > 1000) {
      console.log(JSON.stringify({
        level: 'warn',
        message: 'Slow request',
        ...metrics,
      }));
    }
  }
});
```

## Business Metrics

Track application-specific metrics:

```typescript
// metrics/business.ts
export class BusinessMetrics {
  private logger: Logger;
  
  constructor(logger: Logger) {
    this.logger = logger;
  }
  
  // User metrics
  userSignup(userId: string, plan: string, source: string) {
    this.logger.info('metric.user.signup', {
      _type: 'business_metric',
      event: 'user_signup',
      userId,
      plan,
      source,
      value: 1,
    });
  }
  
  // Payment metrics
  paymentProcessed(amount: number, currency: string, method: string) {
    this.logger.info('metric.payment.processed', {
      _type: 'business_metric',
      event: 'payment_processed',
      amount,
      currency,
      method,
      value: amount,
    });
  }
  
  paymentFailed(amount: number, currency: string, reason: string) {
    this.logger.info('metric.payment.failed', {
      _type: 'business_metric',
      event: 'payment_failed',
      amount,
      currency,
      reason,
      value: 1,
    });
  }
  
  // API usage metrics
  apiCall(endpoint: string, userId: string, responseTime: number) {
    this.logger.info('metric.api.call', {
      _type: 'business_metric',
      event: 'api_call',
      endpoint,
      userId,
      responseTime,
      value: 1,
    });
  }
}

// Usage
const metrics = new BusinessMetrics(logger);
metrics.paymentProcessed(99.99, 'USD', 'credit_card');
```

## Durable Objects Metrics

Track Durable Object usage and performance:

```typescript
export class RateLimiter implements DurableObject {
  private requests = 0;
  private blocked = 0;
  
  async fetch(request: Request): Promise<Response> {
    const allowed = await this.checkLimit();
    
    // Log metrics periodically or on specific events
    if (this.requests % 100 === 0) {
      this.logMetrics();
    }
    
    if (allowed) {
      this.requests++;
      return new Response('OK');
    } else {
      this.blocked++;
      return new Response('Rate limited', { status: 429 });
    }
  }
  
  private logMetrics() {
    console.log(JSON.stringify({
      _type: 'do_metric',
      class: 'RateLimiter',
      id: this.state.id.toString(),
      requests: this.requests,
      blocked: this.blocked,
      blockRate: this.blocked / (this.requests + this.blocked),
    }));
  }
}
```

## External Metrics Services

### Sending to Datadog

```typescript
interface DatadogMetric {
  metric: string;
  type: 'count' | 'gauge' | 'rate';
  points: Array<[number, number]>;
  tags?: string[];
}

async function sendToDatadog(
  metrics: DatadogMetric[],
  apiKey: string
): Promise<void> {
  await fetch('https://api.datadoghq.com/api/v2/series', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'DD-API-KEY': apiKey,
    },
    body: JSON.stringify({ series: metrics }),
  });
}

// Usage
await sendToDatadog([
  {
    metric: 'worker.requests',
    type: 'count',
    points: [[Math.floor(Date.now() / 1000), 1]],
    tags: ['env:production', 'service:api'],
  },
], env.DD_API_KEY);
```

### Sending to Prometheus Pushgateway

```typescript
async function pushToPrometheus(
  metrics: string,
  pushgatewayUrl: string,
  jobName: string
): Promise<void> {
  await fetch(`${pushgatewayUrl}/metrics/job/${jobName}`, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: metrics,
  });
}

// Format Prometheus metrics
const metrics = `
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/users",status="200"} 1024
http_requests_total{method="POST",endpoint="/api/users",status="201"} 256

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 900
http_request_duration_seconds_bucket{le="0.5"} 1200
http_request_duration_seconds_bucket{le="1"} 1280
http_request_duration_seconds_bucket{le="+Inf"} 1280
http_request_duration_seconds_sum 128.5
http_request_duration_seconds_count 1280
`;

await pushToPrometheus(metrics, env.PROMETHEUS_PUSHGATEWAY, 'my-worker');
```

## Alerting

### Workers Logs-Based Alerts

Use Query Builder saved queries with notification hooks:

```typescript
// Tail Worker for alerting
export default {
  async tail(events: TailEvent[], env: Env): Promise<void> {
    const errors = events.filter(e => e.outcome === 'exception');
    const errorRate = errors.length / events.length;
    
    // Alert on high error rate
    if (errorRate > 0.1 && events.length > 10) {
      await sendAlert(env, {
        type: 'high_error_rate',
        errorRate: errorRate * 100,
        sampleSize: events.length,
        errors: errors.slice(0, 5).map(e => ({
          script: e.scriptName,
          message: e.exceptions[0]?.message,
        })),
      });
    }
    
    // Alert on slow requests
    const slowRequests = events.filter(e => 
      e.event?.response?.duration > 5000
    );
    
    if (slowRequests.length > 5) {
      await sendAlert(env, {
        type: 'slow_requests',
        count: slowRequests.length,
        avgDuration: slowRequests.reduce((sum, e) => 
          sum + e.event.response.duration, 0
        ) / slowRequests.length,
      });
    }
  },
};

async function sendAlert(env: Env, alert: object): Promise<void> {
  // Slack
  await fetch(env.SLACK_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `🚨 Alert: ${JSON.stringify(alert, null, 2)}`,
    }),
  });
  
  // PagerDuty
  await fetch('https://events.pagerduty.com/v2/enqueue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      routing_key: env.PAGERDUTY_KEY,
      event_action: 'trigger',
      payload: {
        summary: `Worker Alert: ${alert.type}`,
        severity: 'error',
        source: 'cloudflare-workers',
        custom_details: alert,
      },
    }),
  });
}
```

## Dashboard Recommendations

### Key Metrics to Track

1. **Request Volume**: Requests per minute/hour
2. **Error Rate**: Errors / Total requests
3. **Latency**: P50, P95, P99 response times
4. **Throughput**: Successful requests per second
5. **Subrequest Ratio**: fetch() calls per request

### Example Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│ Request Volume (last 24h)                           │
│ [Line chart: requests over time]                    │
├─────────────────────────────────────────────────────┤
│ Error Rate          │ P95 Latency                   │
│ 0.5%                │ 145ms                         │
│ [Gauge]             │ [Gauge]                       │
├─────────────────────────────────────────────────────┤
│ Requests by Status Code                             │
│ [Stacked area chart: 2xx, 4xx, 5xx]                │
├─────────────────────────────────────────────────────┤
│ Slowest Endpoints (P95)                             │
│ /api/reports    892ms                               │
│ /api/export     654ms                               │
│ /api/search     423ms                               │
└─────────────────────────────────────────────────────┘
```

## Best Practices

1. **Use consistent metric names**: `service.component.action` (e.g., `api.payments.processed`)

2. **Add meaningful tags**: environment, endpoint, status, user_tier

3. **Set appropriate granularity**: Don't track every request individually in high-traffic scenarios

4. **Aggregate before sending**: Batch metrics to reduce API calls to external services

5. **Monitor your monitoring**: Track metrics collection overhead

6. **Set up baselines**: Know your normal ranges before setting alert thresholds

7. **Use histograms for latency**: Track percentiles, not just averages

```typescript
// Track latency distribution
const buckets = [10, 50, 100, 250, 500, 1000, 2500, 5000];
const histogram = new Map<number, number>();

function recordLatency(duration: number) {
  for (const bucket of buckets) {
    if (duration <= bucket) {
      histogram.set(bucket, (histogram.get(bucket) || 0) + 1);
      break;
    }
  }
}
```
