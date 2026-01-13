---
name: Observability
id: observability
version: 1.0
category: support
domain: [monitoring, logging, backend, cloudflare]
task_types: [implementation, debugging, optimization]
keywords: [logging, monitoring, metrics, tracing, sentry, error tracking, cloudflare, workers, health checks, observability]
complexity: [normal, complex]
pairs_with: [serverless_infrastructure, api_development, backend_security]
source: backend-skills/observability/SKILL-observability.md
---

# Observability Skill

Monitor, debug, and understand your Cloudflare Workers applications through logs, metrics, traces, and error tracking.

## Quick Reference

### Cloudflare Workers Logs Setup

```toml
# wrangler.toml
[observability]
enabled = true

[observability.logs]
invocation_logs = true
head_sampling_rate = 1  # 1 = 100%, 0.01 = 1%
```

### Structured Logging Pattern

```typescript
// utils/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  requestId?: string;
  [key: string]: unknown;
}

export function createLogger(requestId?: string) {
  const log = (level: LogLevel, message: string, data?: Record<string, unknown>) => {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      requestId,
      ...data,
    };
    console.log(JSON.stringify(entry));
  };

  return {
    debug: (msg: string, data?: Record<string, unknown>) => log('debug', msg, data),
    info: (msg: string, data?: Record<string, unknown>) => log('info', msg, data),
    warn: (msg: string, data?: Record<string, unknown>) => log('warn', msg, data),
    error: (msg: string, data?: Record<string, unknown>) => log('error', msg, data),
  };
}
```

### Sentry Error Tracking

```typescript
// index.ts
import * as Sentry from '@sentry/cloudflare';

export default Sentry.withSentry(
  (env: Env) => ({
    dsn: env.SENTRY_DSN,
    release: env.CF_VERSION_METADATA?.id,
    tracesSampleRate: 0.1, // 10% of requests
    environment: env.ENVIRONMENT,
  }),
  {
    async fetch(request, env, ctx) {
      // Your handler
    },
  }
);
```

### Request ID Middleware

```typescript
import { createMiddleware } from 'hono/factory';

export const requestId = createMiddleware(async (c, next) => {
  const id = c.req.header('x-request-id') || crypto.randomUUID();
  c.set('requestId', id);
  c.header('x-request-id', id);
  await next();
});
```

## Observability Stack Decision

| Need | Tool | Use Case |
|------|------|----------|
| **Logs** | Workers Logs | Built-in, free tier, JSON auto-parsed |
| **Error tracking** | Sentry | Stack traces, releases, alerts |
| **Distributed tracing** | OpenTelemetry → Jaeger | Multi-service request flows |
| **Metrics** | Workers Analytics | Request counts, latency, errors |
| **External aggregation** | Logpush → S3/R2 | Long-term retention, compliance |

## Key Patterns

### 1. Structured JSON Logging
Always log in JSON format for Workers Logs auto-parsing:

```typescript
// Good - automatically indexed fields
console.log(JSON.stringify({
  event: 'payment_processed',
  userId: user.id,
  amount: 100.00,
  currency: 'USD',
  duration_ms: 45,
}));

// Bad - plain text, no structure
console.log(`Payment processed for user ${user.id}`);
```

### 2. Consistent Log Schema

```typescript
interface StandardLogFields {
  // Required
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: string;

  // Recommended
  requestId: string;
  service: string;
  environment: string;

  // Contextual
  userId?: string;
  traceId?: string;
  duration_ms?: number;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}
```

### 3. Error Logging with Context

```typescript
try {
  await processPayment(data);
} catch (error) {
  logger.error('Payment failed', {
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
    userId: user.id,
    paymentId: data.paymentId,
    amount: data.amount,
  });

  // Also send to Sentry for alerting
  Sentry.captureException(error, {
    extra: { userId: user.id, paymentId: data.paymentId },
  });

  throw error;
}
```

### 4. Performance Logging

```typescript
async function timedOperation<T>(
  name: string,
  fn: () => Promise<T>,
  logger: ReturnType<typeof createLogger>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const duration_ms = Math.round(performance.now() - start);
    logger.info(`${name} completed`, { duration_ms });
    return result;
  } catch (error) {
    const duration_ms = Math.round(performance.now() - start);
    logger.error(`${name} failed`, { duration_ms, error });
    throw error;
  }
}

// Usage
const user = await timedOperation('fetch_user', () => getUser(id), logger);
```

## Log Levels Guide

| Level | When to Use | Examples |
|-------|-------------|----------|
| **debug** | Development details | SQL queries, cache hits, internal state |
| **info** | Normal operations | Request received, user action, job completed |
| **warn** | Unexpected but handled | Rate limit approached, deprecated API used |
| **error** | Failures requiring attention | Payment failed, auth error, external API down |

### Production Level Configuration

```typescript
const LOG_LEVEL = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
} as const;

const currentLevel = env.LOG_LEVEL || 'info';

function shouldLog(level: keyof typeof LOG_LEVEL): boolean {
  return LOG_LEVEL[level] >= LOG_LEVEL[currentLevel];
}
```

## Reference Documents

| Document | Topics |
|----------|--------|
| [structured-logging.md](references/structured-logging.md) | JSON format, schema design, logger implementation |
| [workers-logs.md](references/workers-logs.md) | Workers Logs setup, Query Builder, dashboard |
| [error-tracking.md](references/error-tracking.md) | Sentry setup, breadcrumbs, context, source maps |
| [distributed-tracing.md](references/distributed-tracing.md) | OpenTelemetry, spans, context propagation |
| [metrics.md](references/metrics.md) | Workers Analytics, custom metrics, alerting |
| [health-checks.md](references/health-checks.md) | Liveness/readiness probes, dependency checks |
| [log-shipping.md](references/log-shipping.md) | Logpush, Tail Workers, external integrations |

## Observability Checklist

### Setup
- [ ] Enable Workers Logs in wrangler.toml
- [ ] Configure Sentry with DSN as secret
- [ ] Set up request ID middleware
- [ ] Create structured logger utility

### Implementation
- [ ] Log all API requests with method, path, status, duration
- [ ] Log business events (signups, payments, errors)
- [ ] Add user context to logs and error reports
- [ ] Include trace IDs for distributed operations

### Monitoring
- [ ] Set up Sentry alerts for error spikes
- [ ] Create Workers Analytics dashboard
- [ ] Configure Logpush for long-term retention (if needed)
- [ ] Document runbooks for common alerts

## Anti-Patterns to Avoid

```typescript
// ❌ Don't log sensitive data
console.log({ password, apiKey, ssn });

// ❌ Don't log entire request/response bodies
console.log(JSON.stringify(request.body)); // Could be huge

// ❌ Don't use console.log without structure
console.log('User', userId, 'did', action);

// ❌ Don't catch and swallow errors silently
try { ... } catch (e) { /* nothing */ }

// ❌ Don't log inside tight loops
for (const item of items) {
  console.log('Processing item', item.id); // Log summary instead
}

// ✅ Do log a summary
console.log(JSON.stringify({
  event: 'batch_processed',
  itemCount: items.length,
  duration_ms: elapsed,
}));
```

## Cost Considerations

- **Workers Logs**: Free tier generous, 5B logs/day/account limit
- **Sentry**: Free tier 5K errors/month, paid for higher volume
- **Logpush**: Pays for destination storage (R2, S3)
- **Sampling**: Use head_sampling_rate to reduce volume in high-traffic scenarios

## Quick Debugging Commands

```bash
# View real-time logs
npx wrangler tail

# Filter to errors only
npx wrangler tail --format json | jq 'select(.level == "error")'

# View logs for specific Worker
npx wrangler tail my-worker-name
```

---

*Skill Version: 1.0*
