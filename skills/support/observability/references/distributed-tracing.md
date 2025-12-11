# Distributed Tracing

Track requests across multiple services using OpenTelemetry for end-to-end visibility.

## Overview

Distributed tracing helps you:
- Follow a request through multiple services
- Identify slow operations and bottlenecks
- Understand service dependencies
- Debug failures across system boundaries

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | Complete journey of a request through all services |
| **Span** | Single unit of work within a trace |
| **Context** | Propagated data linking spans across services |
| **Trace ID** | Unique identifier for the entire trace |
| **Span ID** | Unique identifier for a single span |
| **Parent Span ID** | Links child span to its parent |

## Manual Tracing (Lightweight)

For simple cases without full OpenTelemetry:

### Request Correlation

```typescript
// middleware/tracing.ts
import { createMiddleware } from 'hono/factory';

export interface TraceContext {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
}

// Generate IDs
function generateId(): string {
  return crypto.randomUUID().replace(/-/g, '').slice(0, 16);
}

// Parse W3C Trace Context header
function parseTraceparent(header: string | undefined): Partial<TraceContext> {
  if (!header) return {};
  
  // Format: 00-traceId-parentSpanId-flags
  const parts = header.split('-');
  if (parts.length !== 4) return {};
  
  return {
    traceId: parts[1],
    parentSpanId: parts[2],
  };
}

// Create W3C Trace Context header
function createTraceparent(ctx: TraceContext): string {
  return `00-${ctx.traceId}-${ctx.spanId}-01`;
}

export const tracingMiddleware = createMiddleware(async (c, next) => {
  const incoming = parseTraceparent(c.req.header('traceparent'));
  
  const traceCtx: TraceContext = {
    traceId: incoming.traceId || generateId() + generateId(), // 32 chars
    spanId: generateId(), // 16 chars
    parentSpanId: incoming.parentSpanId,
  };
  
  c.set('trace', traceCtx);
  c.header('traceparent', createTraceparent(traceCtx));
  
  await next();
});

// Use in outgoing requests
export async function tracedFetch(
  url: string,
  options: RequestInit,
  trace: TraceContext
): Promise<Response> {
  const childSpan: TraceContext = {
    traceId: trace.traceId,
    spanId: generateId(),
    parentSpanId: trace.spanId,
  };
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'traceparent': createTraceparent(childSpan),
    },
  });
}
```

### Usage

```typescript
import { Hono } from 'hono';
import { tracingMiddleware, tracedFetch, TraceContext } from './middleware/tracing';

type Variables = {
  trace: TraceContext;
};

const app = new Hono<{ Variables: Variables }>();

app.use('*', tracingMiddleware);

app.post('/orders', async (c) => {
  const trace = c.get('trace');
  const logger = c.get('logger');
  
  // Log with trace context
  logger.info('Processing order', {
    traceId: trace.traceId,
    spanId: trace.spanId,
  });
  
  // Call downstream service with trace propagation
  const inventoryResponse = await tracedFetch(
    'https://inventory.example.com/check',
    { method: 'POST', body: JSON.stringify(items) },
    trace
  );
  
  return c.json({ orderId: order.id });
});
```

## OpenTelemetry Integration

For full-featured tracing with visualization backends.

### Installation

```bash
npm install @opentelemetry/api \
  @opentelemetry/sdk-trace-base \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

### Basic Setup

```typescript
// tracing.ts
import { trace, SpanKind, SpanStatusCode, context } from '@opentelemetry/api';
import { BasicTracerProvider, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

let provider: BasicTracerProvider | null = null;

export function initTracing(env: Env) {
  if (provider) return;
  
  const exporter = new OTLPTraceExporter({
    url: env.OTEL_ENDPOINT || 'https://otel-collector.example.com/v1/traces',
    headers: {
      'Authorization': `Bearer ${env.OTEL_API_KEY}`,
    },
  });
  
  provider = new BasicTracerProvider({
    resource: new Resource({
      [ATTR_SERVICE_NAME]: 'my-api',
      [ATTR_SERVICE_VERSION]: env.CF_VERSION_METADATA?.id || '1.0.0',
      'deployment.environment': env.ENVIRONMENT,
    }),
  });
  
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  provider.register();
}

export function getTracer(name: string = 'default') {
  return trace.getTracer(name, '1.0.0');
}
```

### Creating Spans

```typescript
import { getTracer } from './tracing';
import { SpanKind, SpanStatusCode } from '@opentelemetry/api';

const tracer = getTracer('user-service');

// Async operation with span
async function getUser(userId: string): Promise<User> {
  return tracer.startActiveSpan(
    'getUser',
    { kind: SpanKind.INTERNAL },
    async (span) => {
      try {
        span.setAttribute('user.id', userId);
        
        const user = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
        
        span.setAttribute('user.found', !!user);
        span.setStatus({ code: SpanStatusCode.OK });
        
        return user;
      } catch (error) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

// HTTP client span
async function callExternalApi(endpoint: string, data: unknown): Promise<Response> {
  return tracer.startActiveSpan(
    `HTTP POST ${endpoint}`,
    { kind: SpanKind.CLIENT },
    async (span) => {
      span.setAttribute('http.method', 'POST');
      span.setAttribute('http.url', endpoint);
      
      const start = performance.now();
      
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: JSON.stringify(data),
          headers: {
            'Content-Type': 'application/json',
            // Inject trace context
            ...getTraceHeaders(),
          },
        });
        
        span.setAttribute('http.status_code', response.status);
        span.setAttribute('http.response_time_ms', performance.now() - start);
        
        if (!response.ok) {
          span.setStatus({ code: SpanStatusCode.ERROR });
        }
        
        return response;
      } catch (error) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR });
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
```

### Context Propagation

```typescript
import { context, propagation, trace } from '@opentelemetry/api';

// Extract context from incoming request
function extractContext(request: Request): Context {
  const carrier: Record<string, string> = {};
  
  // Copy relevant headers
  const traceparent = request.headers.get('traceparent');
  const tracestate = request.headers.get('tracestate');
  
  if (traceparent) carrier['traceparent'] = traceparent;
  if (tracestate) carrier['tracestate'] = tracestate;
  
  return propagation.extract(context.active(), carrier);
}

// Inject context into outgoing request
function injectContext(headers: Headers): void {
  const carrier: Record<string, string> = {};
  propagation.inject(context.active(), carrier);
  
  for (const [key, value] of Object.entries(carrier)) {
    headers.set(key, value);
  }
}

// Usage in middleware
app.use('*', async (c, next) => {
  const parentContext = extractContext(c.req.raw);
  
  await context.with(parentContext, async () => {
    await tracer.startActiveSpan(
      `${c.req.method} ${c.req.path}`,
      { kind: SpanKind.SERVER },
      async (span) => {
        span.setAttribute('http.method', c.req.method);
        span.setAttribute('http.url', c.req.url);
        
        try {
          await next();
          span.setAttribute('http.status_code', c.res.status);
        } catch (error) {
          span.recordException(error);
          span.setStatus({ code: SpanStatusCode.ERROR });
          throw error;
        } finally {
          span.end();
        }
      }
    );
  });
});
```

## Span Attributes (Semantic Conventions)

Follow OpenTelemetry semantic conventions for consistent naming:

### HTTP Spans

```typescript
span.setAttribute('http.method', 'POST');
span.setAttribute('http.url', 'https://api.example.com/users');
span.setAttribute('http.target', '/users');
span.setAttribute('http.host', 'api.example.com');
span.setAttribute('http.scheme', 'https');
span.setAttribute('http.status_code', 200);
span.setAttribute('http.request_content_length', 1234);
span.setAttribute('http.response_content_length', 5678);
```

### Database Spans

```typescript
span.setAttribute('db.system', 'sqlite');  // or 'postgresql', 'mysql'
span.setAttribute('db.name', 'mydb');
span.setAttribute('db.statement', 'SELECT * FROM users WHERE id = ?');
span.setAttribute('db.operation', 'SELECT');
span.setAttribute('db.sql.table', 'users');
```

### Custom Business Spans

```typescript
span.setAttribute('order.id', orderId);
span.setAttribute('order.total', 99.99);
span.setAttribute('order.item_count', 3);
span.setAttribute('customer.id', customerId);
span.setAttribute('payment.method', 'credit_card');
```

## Visualization Backends

### Jaeger (Self-hosted)

```typescript
const exporter = new OTLPTraceExporter({
  url: 'http://jaeger:4318/v1/traces',
});
```

### Grafana Tempo

```typescript
const exporter = new OTLPTraceExporter({
  url: 'https://tempo.grafana.net/otlp',
  headers: {
    'Authorization': `Basic ${btoa(`${userId}:${apiKey}`)}`,
  },
});
```

### Honeycomb

```typescript
const exporter = new OTLPTraceExporter({
  url: 'https://api.honeycomb.io/v1/traces',
  headers: {
    'x-honeycomb-team': env.HONEYCOMB_API_KEY,
    'x-honeycomb-dataset': 'my-service',
  },
});
```

### Datadog

```typescript
const exporter = new OTLPTraceExporter({
  url: 'https://trace.agent.datadoghq.com/v1/traces',
  headers: {
    'DD-API-KEY': env.DD_API_KEY,
  },
});
```

## Best Practices

### 1. Name Spans Meaningfully

```typescript
// Good
'HTTP GET /api/users/:id'
'DB query users'
'Process payment'

// Bad
'span1'
'operation'
'doSomething'
```

### 2. Set Appropriate Span Kind

```typescript
SpanKind.SERVER   // Incoming HTTP request
SpanKind.CLIENT   // Outgoing HTTP request
SpanKind.PRODUCER // Message queue producer
SpanKind.CONSUMER // Message queue consumer
SpanKind.INTERNAL // Internal operation
```

### 3. Record Errors Properly

```typescript
try {
  await operation();
} catch (error) {
  span.recordException(error);
  span.setStatus({
    code: SpanStatusCode.ERROR,
    message: error.message,
  });
  throw error;
}
```

### 4. Don't Create Too Many Spans

```typescript
// Bad: span per loop iteration
for (const item of items) {
  tracer.startActiveSpan('processItem', ...);
}

// Good: single span for batch
tracer.startActiveSpan('processBatch', (span) => {
  span.setAttribute('batch.size', items.length);
  // process all items
});
```

### 5. Use Sampling in Production

```typescript
import { ParentBasedSampler, TraceIdRatioBasedSampler } from '@opentelemetry/sdk-trace-base';

const sampler = new ParentBasedSampler({
  root: new TraceIdRatioBasedSampler(0.1), // 10% sampling
});

const provider = new BasicTracerProvider({
  sampler,
  // ...
});
```

## Debugging Tips

### Finding Slow Operations

```sql
-- In your tracing backend (e.g., Jaeger)
-- Find spans > 1 second
duration > 1000ms

-- Find errors
status.code = ERROR

-- Find specific service
service.name = "payment-service"
```

### Correlating Logs and Traces

```typescript
// Include trace context in logs
logger.info('Processing request', {
  traceId: span.spanContext().traceId,
  spanId: span.spanContext().spanId,
  ...data,
});
```

Then search logs by trace ID when investigating issues.
