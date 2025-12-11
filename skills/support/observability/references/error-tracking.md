# Error Tracking with Sentry

Capture, track, and alert on errors in your Cloudflare Workers applications using Sentry.

## Installation

```bash
npm install @sentry/cloudflare
```

## Basic Setup

### Cloudflare Workers

```typescript
// index.ts
import * as Sentry from '@sentry/cloudflare';

interface Env {
  SENTRY_DSN: string;
  ENVIRONMENT: string;
  CF_VERSION_METADATA: { id: string };
}

export default Sentry.withSentry(
  (env: Env) => ({
    dsn: env.SENTRY_DSN,
    release: env.CF_VERSION_METADATA?.id,
    environment: env.ENVIRONMENT,
    tracesSampleRate: 0.1, // 10% of transactions for performance
    sendDefaultPii: true,  // Include request headers, IP
  }),
  {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
      // Your handler code
      // Errors are automatically captured
      return new Response('OK');
    },
  }
);
```

### With Hono

```typescript
import { Hono } from 'hono';
import * as Sentry from '@sentry/cloudflare';

interface Env {
  SENTRY_DSN: string;
  ENVIRONMENT: string;
  CF_VERSION_METADATA: { id: string };
}

const app = new Hono<{ Bindings: Env }>();

// Your routes
app.get('/', (c) => c.text('Hello'));

app.post('/users', async (c) => {
  const data = await c.req.json();
  // If this throws, Sentry captures it
  const user = await createUser(data, c.env);
  return c.json(user, 201);
});

// Export wrapped with Sentry
export default Sentry.withSentry(
  (env: Env) => ({
    dsn: env.SENTRY_DSN,
    release: env.CF_VERSION_METADATA?.id,
    environment: env.ENVIRONMENT,
    tracesSampleRate: 0.1,
  }),
  app
);
```

## Configuration Options

```typescript
Sentry.withSentry(
  (env: Env) => ({
    // Required
    dsn: env.SENTRY_DSN,
    
    // Release tracking
    release: env.CF_VERSION_METADATA?.id,
    
    // Environment
    environment: env.ENVIRONMENT, // 'production', 'staging', 'development'
    
    // Performance monitoring
    tracesSampleRate: 0.1,        // 10% of transactions
    // Or dynamic sampling:
    tracesSampler: (samplingContext) => {
      // Always sample errors
      if (samplingContext.transactionContext?.name?.includes('/health')) {
        return 0; // Don't sample health checks
      }
      return 0.1;
    },
    
    // Privacy
    sendDefaultPii: true,  // Include request headers, IP, cookies
    
    // Logs integration
    enableLogs: true,
    
    // Filtering
    beforeSend: (event) => {
      // Filter out specific errors
      if (event.exception?.values?.[0]?.value?.includes('NetworkError')) {
        return null; // Don't send
      }
      return event;
    },
    
    // Ignored errors
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      /^Network request failed/,
    ],
  }),
  handler
);
```

## Manual Error Capture

```typescript
import * as Sentry from '@sentry/cloudflare';

// Capture exception with context
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error, {
    extra: {
      userId: user.id,
      operation: 'payment_processing',
      amount: payment.amount,
    },
    tags: {
      paymentProvider: 'stripe',
      retryCount: 2,
    },
  });
  throw error; // Re-throw or handle
}

// Capture message (non-exception events)
Sentry.captureMessage('Unusual activity detected', {
  level: 'warning',
  extra: {
    userId: user.id,
    activityType: 'bulk_download',
    count: 1000,
  },
});
```

## User Context

```typescript
// Set user info for error context
Sentry.setUser({
  id: user.id,
  email: user.email,
  username: user.name,
  // Custom data
  subscription: user.plan,
});

// Clear user on logout
Sentry.setUser(null);
```

## Breadcrumbs

Breadcrumbs provide a trail of events leading up to an error:

```typescript
// Automatic breadcrumbs are captured for:
// - console.log/warn/error
// - fetch requests
// - DOM events (in browser)

// Manual breadcrumbs
Sentry.addBreadcrumb({
  category: 'auth',
  message: 'User logged in',
  level: 'info',
  data: {
    userId: user.id,
    method: 'password',
  },
});

Sentry.addBreadcrumb({
  category: 'payment',
  message: 'Payment initiated',
  level: 'info',
  data: {
    amount: 99.99,
    currency: 'USD',
  },
});

// When an error occurs, these breadcrumbs are included
```

## Tags and Extra Data

```typescript
// Tags: Indexed, searchable in Sentry UI
Sentry.setTag('customer_tier', 'enterprise');
Sentry.setTag('feature_flag', 'new_checkout');

// Extra: Not indexed, appears in event details
Sentry.setExtra('request_body', JSON.stringify(requestData));
Sentry.setExtra('response_time_ms', responseTime);

// Scoped to current request
Sentry.withScope((scope) => {
  scope.setTag('transaction_id', txId);
  scope.setExtra('cart_items', cartItems);
  
  Sentry.captureException(error);
});
```

## D1 Database Instrumentation

```typescript
import * as Sentry from '@sentry/cloudflare';

// Wrap D1 database for automatic tracing
const instrumentedDb = Sentry.instrumentD1WithSentry(env.DB);

// Queries are now traced
const users = await instrumentedDb
  .prepare('SELECT * FROM users WHERE status = ?')
  .bind('active')
  .all();
```

## Cron Monitoring

```typescript
import * as Sentry from '@sentry/cloudflare';

const monitorConfig = {
  schedule: {
    type: 'crontab' as const,
    value: '0 * * * *', // Every hour
  },
  checkinMargin: 5,    // Minutes before missed
  maxRuntime: 30,      // Max minutes
  timezone: 'UTC',
};

export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    // Sentry tracks if job runs on time and completes
    await Sentry.withMonitor(
      'hourly-cleanup',
      async () => {
        await performCleanup(env);
      },
      monitorConfig
    );
  },
};
```

## Source Maps

Upload source maps for readable stack traces:

### Setup (package.json)

```json
{
  "scripts": {
    "build": "wrangler deploy --dry-run --outdir=dist",
    "sentry:sourcemaps": "sentry-cli sourcemaps inject ./dist && sentry-cli sourcemaps upload ./dist",
    "deploy": "npm run build && npm run sentry:sourcemaps && wrangler deploy"
  },
  "devDependencies": {
    "@sentry/cli": "^2.0.0"
  }
}
```

### Sentry CLI Config (.sentryclirc)

```ini
[auth]
token=your-auth-token

[defaults]
org=your-org-slug
project=your-project-slug
```

### GitHub Actions

```yaml
- name: Deploy with Source Maps
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org
    SENTRY_PROJECT: your-project
  run: |
    npm run build
    npx sentry-cli sourcemaps inject ./dist
    npx sentry-cli sourcemaps upload --release=${{ github.sha }} ./dist
    npx wrangler deploy
```

## Error Boundaries (React/Remix)

For frontend code on Cloudflare Pages:

```tsx
// entry.client.tsx
import * as Sentry from '@sentry/remix';

Sentry.init({
  dsn: '__PUBLIC_DSN__',
  tracesSampleRate: 0.1,
  integrations: [
    Sentry.browserTracingIntegration({
      useEffect,
      useLocation,
      useMatches,
    }),
  ],
});

// ErrorBoundary component
export const ErrorBoundary = () => {
  const error = useRouteError();
  Sentry.captureRemixErrorBoundaryError(error);
  
  return (
    <div>
      <h1>Something went wrong</h1>
      <p>We've been notified and are working on a fix.</p>
    </div>
  );
};
```

## Alerting Configuration

### In Sentry Dashboard

1. **Issue Alerts**: Trigger on new issues or issue volume
   - New issue in Production → Slack + Email
   - Issue seen > 100 times in 1 hour → PagerDuty

2. **Metric Alerts**: Based on error rates or counts
   - Error rate > 5% → Warning
   - Error rate > 10% → Critical

3. **Integrations**:
   - Slack for notifications
   - PagerDuty for on-call
   - Jira for issue tracking

### Alert Rules Example

```
Name: High Error Rate
Conditions:
  - The number of events is more than 50 in 5 minutes
  - Event is from the production environment
Actions:
  - Send Slack notification to #alerts
  - Create Jira ticket
```

## Performance Monitoring

```typescript
// Automatic spans for fetch requests
const response = await fetch('https://api.stripe.com/v1/charges', {
  method: 'POST',
  body: data,
});
// ^ This creates a span automatically

// Manual spans for custom operations
const transaction = Sentry.startTransaction({
  name: 'process-payment',
  op: 'payment',
});

const dbSpan = transaction.startChild({
  op: 'db.query',
  description: 'SELECT user',
});
const user = await getUser(userId);
dbSpan.finish();

const apiSpan = transaction.startChild({
  op: 'http.client',
  description: 'POST /v1/charges',
});
await processStripePayment(user, amount);
apiSpan.finish();

transaction.finish();
```

## Best Practices

### 1. Set Appropriate Sample Rates

```typescript
{
  // Development: capture everything
  tracesSampleRate: env.ENVIRONMENT === 'production' ? 0.1 : 1.0,
  
  // Errors are always captured (100%)
}
```

### 2. Add Context Progressively

```typescript
// Early in request: set basic context
Sentry.setTag('endpoint', request.url);

// After auth: add user
Sentry.setUser({ id: user.id, email: user.email });

// Before risky operation: add specifics
Sentry.withScope((scope) => {
  scope.setExtra('payment_details', { amount, currency });
  // ... operation that might fail
});
```

### 3. Filter Noise

```typescript
{
  ignoreErrors: [
    // Known, non-actionable errors
    'ResizeObserver loop limit exceeded',
    'Network request failed',
    'Load failed',
  ],
  
  beforeSend: (event) => {
    // Don't report aborted requests
    if (event.exception?.values?.[0]?.value?.includes('AbortError')) {
      return null;
    }
    return event;
  },
}
```

### 4. Use Releases for Tracking

```typescript
{
  release: env.CF_VERSION_METADATA?.id || 'unknown',
}
```

This enables:
- Regression detection
- Release health tracking
- Suspect commits identification

## Troubleshooting

### Events Not Appearing

1. Check DSN is set correctly
2. Verify network access to Sentry (Workers can reach sentry.io)
3. Check beforeSend isn't filtering events
4. Review rate limits in Sentry dashboard

### Missing Stack Traces

1. Ensure source maps are uploaded
2. Check release version matches
3. Verify source map paths match production URLs

### Too Many Events

1. Increase sampling rate
2. Add error filtering
3. Use beforeSend to deduplicate
4. Check for infinite loops in error handlers
