---
name: Service Integrations
id: service_integrations
version: 1.0
category: implementation
domain: [api, backend, payments, webhooks]
task_types: [implementation, integration]
keywords: [api client, webhooks, retry, circuit breaker, rate limiting, airwallex, stripe, sendgrid, http, fetch, integration]
complexity: [normal, complex]
pairs_with: [api_development, backend_security, observability]
source: backend-skills/service-integrations/SKILL-service-integrations.md
---

# Service Integrations Skill

Integrate external APIs and services into your Cloudflare Workers applications with reliability, error handling, and observability.

## Quick Reference

### Type-Safe API Client Pattern

```typescript
// clients/base.ts
interface ApiClientOptions {
  baseUrl: string;
  apiKey: string;
  timeout?: number;
}

interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: unknown;
}

export class ApiClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl;
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 30000;
  }

  async request<T>(
    method: string,
    path: string,
    options: { body?: unknown; headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          ...options.headers,
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw {
          status: response.status,
          code: error.code || 'UNKNOWN_ERROR',
          message: error.message || response.statusText,
          details: error,
        } as ApiError;
      }

      return {
        data: await response.json() as T,
        status: response.status,
        headers: response.headers,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw { status: 408, code: 'TIMEOUT', message: 'Request timeout' };
      }
      throw error;
    }
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body: unknown) { return this.request<T>('POST', path, { body }); }
  put<T>(path: string, body: unknown) { return this.request<T>('PUT', path, { body }); }
  delete<T>(path: string) { return this.request<T>('DELETE', path); }
}
```

### Webhook Handler Pattern

```typescript
// webhooks/handler.ts
import { Hono } from 'hono';
import { verifyWebhookSignature } from './verify';

const app = new Hono<{ Bindings: Env }>();

app.post('/webhooks/payment', async (c) => {
  const signature = c.req.header('x-signature');
  const timestamp = c.req.header('x-timestamp');
  const body = await c.req.text();

  // Verify signature
  const isValid = await verifyWebhookSignature({
    signature,
    timestamp,
    body,
    secret: c.env.WEBHOOK_SECRET,
  });

  if (!isValid) {
    return c.json({ error: 'Invalid signature' }, 401);
  }

  // Parse and process
  const event = JSON.parse(body);

  // Idempotency check
  const processed = await c.env.KV.get(`webhook:${event.id}`);
  if (processed) {
    return c.json({ status: 'already_processed' }, 200);
  }

  // Process event
  await processWebhookEvent(event, c.env);

  // Mark as processed
  await c.env.KV.put(`webhook:${event.id}`, 'true', { expirationTtl: 86400 * 7 });

  return c.json({ status: 'processed' }, 200);
});
```

## Integration Checklist

### Before Integration
- [ ] Review API documentation and rate limits
- [ ] Obtain API credentials (store as secrets)
- [ ] Understand authentication method (API key, OAuth, JWT)
- [ ] Identify required webhook events
- [ ] Plan error handling strategy

### Implementation
- [ ] Create type-safe API client
- [ ] Implement request/response validation
- [ ] Add timeout handling
- [ ] Implement retry logic with exponential backoff
- [ ] Set up webhook endpoint with signature verification
- [ ] Add idempotency for webhook processing

### Observability
- [ ] Log all external API calls with timing
- [ ] Track error rates and response times
- [ ] Set up alerts for API failures
- [ ] Monitor webhook delivery success

## Common Patterns

### 1. Retry with Exponential Backoff

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; baseDelay?: number } = {}
): Promise<T> {
  const { maxAttempts = 3, baseDelay = 1000 } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;

      // Only retry on transient errors
      if (!isRetryable(error)) throw error;

      const delay = baseDelay * Math.pow(2, attempt - 1);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

function isRetryable(error: unknown): boolean {
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const status = (error as { status: number }).status;
    return status === 429 || status >= 500;
  }
  return true; // Network errors are retryable
}
```

### 2. Circuit Breaker

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold = 5,
    private resetTimeout = 60000
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }
}
```

### 3. Request Caching

```typescript
async function cachedRequest<T>(
  key: string,
  fn: () => Promise<T>,
  env: Env,
  ttl: number = 300 // 5 minutes
): Promise<T> {
  // Check cache
  const cached = await env.KV.get(key, 'json');
  if (cached) return cached as T;

  // Make request
  const result = await fn();

  // Cache result
  await env.KV.put(key, JSON.stringify(result), { expirationTtl: ttl });

  return result;
}

// Usage
const rates = await cachedRequest(
  'fx:USD:AUD',
  () => airwallex.getFxRates('USD', 'AUD'),
  env,
  60 // Cache for 1 minute
);
```

## Reference Documents

| Document | Topics |
|----------|--------|
| [api-clients.md](references/api-clients.md) | Type-safe clients, authentication, error handling |
| [http-client.md](references/http-client.md) | Fetch patterns, retry, timeout, interceptors |
| [webhooks.md](references/webhooks.md) | Signature verification, idempotency, event processing |
| [async-processing.md](references/async-processing.md) | Queues, background jobs, reliable delivery |
| [rate-limit-handling.md](references/rate-limit-handling.md) | Backoff, 429 handling, throttling |
| [airwallex.md](references/airwallex.md) | Payment intents, payouts, FX, webhook events |

## Service-Specific Quick Start

### Airwallex (Payments)

```typescript
// Initialize client
const airwallex = new AirwallexClient({
  clientId: env.AIRWALLEX_CLIENT_ID,
  apiKey: env.AIRWALLEX_API_KEY,
  environment: env.ENVIRONMENT === 'production' ? 'prod' : 'demo',
});

// Create payment intent
const intent = await airwallex.createPaymentIntent({
  amount: 99.99,
  currency: 'USD',
  merchantOrderId: order.id,
});

// Return client secret for frontend
return c.json({ clientSecret: intent.client_secret });
```

### Stripe (Alternative)

```typescript
const stripe = new Stripe(env.STRIPE_SECRET_KEY, {
  apiVersion: '2023-10-16',
  httpClient: Stripe.createFetchHttpClient(),
});

const paymentIntent = await stripe.paymentIntents.create({
  amount: 9999, // cents
  currency: 'usd',
  metadata: { orderId: order.id },
});
```

### SendGrid (Email)

```typescript
await fetch('https://api.sendgrid.com/v3/mail/send', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${env.SENDGRID_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    personalizations: [{ to: [{ email: user.email }] }],
    from: { email: 'noreply@example.com' },
    subject: 'Order Confirmation',
    content: [{ type: 'text/html', value: emailHtml }],
  }),
});
```

## Anti-Patterns to Avoid

```typescript
// ❌ Don't hardcode credentials
const apiKey = 'sk_live_xxxxx';

// ❌ Don't ignore errors
await fetch(url).catch(() => {});

// ❌ Don't trust webhook payloads without verification
app.post('/webhook', async (c) => {
  const data = await c.req.json();
  await processPayment(data); // No signature check!
});

// ❌ Don't make unbounded retries
while (true) {
  try { return await apiCall(); } catch { /* retry forever */ }
}

// ❌ Don't log sensitive data
console.log('API response:', JSON.stringify(response)); // May contain PII

// ✅ Do use secrets from environment
const apiKey = env.API_KEY;

// ✅ Do handle errors explicitly
const response = await fetch(url);
if (!response.ok) {
  logger.error('API call failed', { status: response.status });
  throw new ApiError(response.status);
}

// ✅ Do verify webhook signatures
if (!verifySignature(signature, body, secret)) {
  return c.json({ error: 'Invalid signature' }, 401);
}
```

## Rate Limiting Strategies

### Token Bucket (Client-Side)

```typescript
class RateLimiter {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private maxTokens: number = 10,
    private refillRate: number = 1 // tokens per second
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();

    if (this.tokens < 1) {
      const waitTime = (1 - this.tokens) / this.refillRate * 1000;
      await new Promise(r => setTimeout(r, waitTime));
      this.refill();
    }

    this.tokens--;
  }

  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }
}

// Usage
const limiter = new RateLimiter(10, 2); // 10 max, 2/sec refill

async function rateLimitedCall<T>(fn: () => Promise<T>): Promise<T> {
  await limiter.acquire();
  return fn();
}
```

### Handle 429 Responses

```typescript
async function handleRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  const response = await fn();

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return handleRateLimit(fn);
  }

  return response;
}
```

---

*Skill Version: 1.0*
