# Rate Limit Handling

Handle API rate limits gracefully with backoff strategies, request throttling, and queue-based approaches.

## Understanding Rate Limits

### Common Rate Limit Headers
```typescript
interface RateLimitInfo {
  limit: number;       // Max requests allowed
  remaining: number;   // Requests remaining
  reset: number;       // Unix timestamp when limit resets
  retryAfter?: number; // Seconds to wait (on 429)
}

function parseRateLimitHeaders(headers: Headers): RateLimitInfo | null {
  const limit = headers.get('X-RateLimit-Limit');
  const remaining = headers.get('X-RateLimit-Remaining');
  const reset = headers.get('X-RateLimit-Reset');
  const retryAfter = headers.get('Retry-After');

  if (!limit || !remaining) return null;

  return {
    limit: parseInt(limit, 10),
    remaining: parseInt(remaining, 10),
    reset: parseInt(reset || '0', 10),
    retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
  };
}
```

### Rate Limit Response (429)
```typescript
interface RateLimitError {
  status: 429;
  retryAfter: number; // seconds
  message: string;
}

function isRateLimited(response: Response): boolean {
  return response.status === 429;
}

function getRetryDelay(response: Response): number {
  // Check Retry-After header (could be seconds or date)
  const retryAfter = response.headers.get('Retry-After');
  
  if (!retryAfter) {
    return 60000; // Default 60 seconds
  }
  
  // If it's a number, it's seconds
  const seconds = parseInt(retryAfter, 10);
  if (!isNaN(seconds)) {
    return seconds * 1000;
  }
  
  // If it's a date string
  const date = new Date(retryAfter);
  if (!isNaN(date.getTime())) {
    return Math.max(0, date.getTime() - Date.now());
  }
  
  return 60000; // Default fallback
}
```

## Exponential Backoff with Jitter

```typescript
interface BackoffOptions {
  initialDelay?: number;  // ms
  maxDelay?: number;      // ms
  factor?: number;        // multiplier
  jitter?: boolean;       // add randomness
}

function calculateBackoff(
  attempt: number,
  options: BackoffOptions = {}
): number {
  const {
    initialDelay = 1000,
    maxDelay = 60000,
    factor = 2,
    jitter = true,
  } = options;

  // Exponential: initialDelay * factor^attempt
  let delay = initialDelay * Math.pow(factor, attempt);
  
  // Cap at maxDelay
  delay = Math.min(delay, maxDelay);
  
  // Add jitter (±30%)
  if (jitter) {
    const jitterFactor = 0.7 + Math.random() * 0.6; // 0.7 to 1.3
    delay = delay * jitterFactor;
  }
  
  return Math.round(delay);
}

// Usage
async function fetchWithBackoff<T>(
  url: string,
  options: RequestInit = {},
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, options);
    
    if (response.ok) {
      return response.json();
    }
    
    if (response.status === 429) {
      // Use server's Retry-After if provided
      const serverDelay = getRetryDelay(response);
      const backoffDelay = calculateBackoff(attempt);
      const delay = Math.max(serverDelay, backoffDelay);
      
      console.log(`Rate limited, waiting ${delay}ms before retry`);
      await sleep(delay);
      continue;
    }
    
    // Non-retryable error
    throw new Error(`HTTP ${response.status}`);
  }
  
  throw new Error('Max retries exceeded');
}
```

## Request Throttling

### Token Bucket Algorithm
```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private capacity: number,      // Max tokens
    private refillRate: number,    // Tokens per second
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(
      this.capacity,
      this.tokens + elapsed * this.refillRate
    );
    this.lastRefill = now;
  }

  async acquire(tokens = 1): Promise<void> {
    this.refill();
    
    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return;
    }
    
    // Wait for tokens to be available
    const waitTime = ((tokens - this.tokens) / this.refillRate) * 1000;
    await sleep(waitTime);
    this.refill();
    this.tokens -= tokens;
  }

  canAcquire(tokens = 1): boolean {
    this.refill();
    return this.tokens >= tokens;
  }
}

// Usage: 10 requests per second
const rateLimiter = new TokenBucket(10, 10);

async function throttledFetch(url: string): Promise<Response> {
  await rateLimiter.acquire();
  return fetch(url);
}
```

### Sliding Window Counter (Durable Object)
```typescript
export class RateLimiterDO {
  private requests: number[] = [];

  constructor(
    private state: DurableObjectState,
    private windowMs = 60000,  // 1 minute window
    private maxRequests = 100  // 100 requests per minute
  ) {}

  async fetch(request: Request): Promise<Response> {
    const now = Date.now();
    
    // Load state
    this.requests = await this.state.storage.get('requests') || [];
    
    // Remove old requests outside window
    this.requests = this.requests.filter(t => now - t < this.windowMs);
    
    // Check limit
    if (this.requests.length >= this.maxRequests) {
      const oldestInWindow = this.requests[0];
      const retryAfter = Math.ceil((oldestInWindow + this.windowMs - now) / 1000);
      
      return new Response(JSON.stringify({ error: 'Rate limited' }), {
        status: 429,
        headers: {
          'Retry-After': String(retryAfter),
          'X-RateLimit-Limit': String(this.maxRequests),
          'X-RateLimit-Remaining': '0',
        },
      });
    }
    
    // Add this request
    this.requests.push(now);
    await this.state.storage.put('requests', this.requests);
    
    return new Response(JSON.stringify({ allowed: true }), {
      headers: {
        'X-RateLimit-Limit': String(this.maxRequests),
        'X-RateLimit-Remaining': String(this.maxRequests - this.requests.length),
      },
    });
  }
}
```

## Queue-Based Rate Limiting

For high-volume scenarios, use a queue to smooth out requests:

```typescript
interface Env {
  API_QUEUE: Queue;
  RATE_LIMIT: DurableObjectNamespace;
}

interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
  callback?: string; // Webhook URL for result
}

// Producer: Enqueue requests
app.post('/api-proxy', async (c) => {
  const request: QueuedRequest = {
    id: crypto.randomUUID(),
    url: c.req.query('url')!,
    method: c.req.method,
    headers: Object.fromEntries(c.req.header().entries()),
    body: await c.req.text(),
    callback: c.req.header('x-callback-url'),
  };
  
  await c.env.API_QUEUE.send(request);
  
  return c.json({
    queued: true,
    requestId: request.id,
    message: 'Request queued for processing',
  }, 202);
});

// Consumer: Process at controlled rate
export default {
  async queue(
    batch: MessageBatch<QueuedRequest>,
    env: Env
  ): Promise<void> {
    // Process one at a time with delay
    for (const message of batch.messages) {
      try {
        const response = await fetch(message.body.url, {
          method: message.body.method,
          headers: message.body.headers,
          body: message.body.body,
        });
        
        // Send result to callback if provided
        if (message.body.callback) {
          await fetch(message.body.callback, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              requestId: message.body.id,
              status: response.status,
              body: await response.text(),
            }),
          });
        }
        
        message.ack();
        
        // Rate limit: wait between requests
        await sleep(100); // 10 requests/second
      } catch (error) {
        message.retry();
      }
    }
  },
};
```

## Pre-emptive Rate Limiting

Check remaining quota before making requests:

```typescript
interface Env {
  RATE_LIMIT_CACHE: KVNamespace;
}

interface CachedRateLimit {
  remaining: number;
  reset: number;
  updatedAt: number;
}

async function checkRateLimit(
  apiName: string,
  env: Env
): Promise<{ allowed: boolean; waitMs?: number }> {
  const cached = await env.RATE_LIMIT_CACHE.get(`ratelimit:${apiName}`, 'json') as CachedRateLimit | null;
  
  if (!cached) {
    return { allowed: true };
  }
  
  // If we know we're out of quota
  if (cached.remaining <= 0) {
    const waitMs = cached.reset * 1000 - Date.now();
    if (waitMs > 0) {
      return { allowed: false, waitMs };
    }
  }
  
  return { allowed: true };
}

async function updateRateLimit(
  apiName: string,
  headers: Headers,
  env: Env
): Promise<void> {
  const info = parseRateLimitHeaders(headers);
  if (!info) return;
  
  await env.RATE_LIMIT_CACHE.put(
    `ratelimit:${apiName}`,
    JSON.stringify({
      remaining: info.remaining,
      reset: info.reset,
      updatedAt: Date.now(),
    }),
    { expirationTtl: 300 } // 5 minutes
  );
}

// Usage
async function callApi(url: string, env: Env): Promise<Response> {
  const { allowed, waitMs } = await checkRateLimit('stripe', env);
  
  if (!allowed && waitMs) {
    throw new Error(`Rate limited, retry in ${waitMs}ms`);
  }
  
  const response = await fetch(url);
  
  // Update our cache with latest rate limit info
  await updateRateLimit('stripe', response.headers, env);
  
  return response;
}
```

## Circuit Breaker for Rate Limits

```typescript
interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half-open';
  failures: number;
  rateLimitHits: number;
  lastRateLimitAt: number;
  resetAt: number;
}

class RateLimitCircuitBreaker {
  private state: CircuitBreakerState = {
    state: 'closed',
    failures: 0,
    rateLimitHits: 0,
    lastRateLimitAt: 0,
    resetAt: 0,
  };

  constructor(
    private rateLimitThreshold = 3,  // Opens after 3 rate limits
    private resetTimeout = 60000      // Try again after 60s
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Check if circuit is open
    if (this.state.state === 'open') {
      if (Date.now() < this.state.resetAt) {
        throw new Error('Circuit breaker is open');
      }
      this.state.state = 'half-open';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error);
      throw error;
    }
  }

  private onSuccess(): void {
    this.state.failures = 0;
    this.state.rateLimitHits = 0;
    this.state.state = 'closed';
  }

  private onFailure(error: unknown): void {
    // Check if it's a rate limit error
    if (error instanceof ApiError && error.status === 429) {
      this.state.rateLimitHits++;
      this.state.lastRateLimitAt = Date.now();
      
      if (this.state.rateLimitHits >= this.rateLimitThreshold) {
        this.state.state = 'open';
        this.state.resetAt = Date.now() + this.resetTimeout;
      }
    }
  }
}
```

## Best Practices

### Do's
```typescript
// ✅ Always handle 429 responses
if (response.status === 429) {
  const retryAfter = getRetryDelay(response);
  await sleep(retryAfter);
  // Retry
}

// ✅ Use exponential backoff with jitter
const delay = calculateBackoff(attempt, { jitter: true });

// ✅ Track rate limit headers proactively
const rateLimit = parseRateLimitHeaders(response.headers);
if (rateLimit.remaining < 10) {
  console.warn('Approaching rate limit');
}

// ✅ Queue non-urgent requests
await env.LOW_PRIORITY_QUEUE.send(request);
```

### Don'ts
```typescript
// ❌ Don't hammer the API after a 429
while (true) {
  const response = await fetch(url);
  if (response.ok) break;
  // No delay!
}

// ❌ Don't ignore Retry-After headers
if (response.status === 429) {
  await sleep(1000); // Should use Retry-After
}

// ❌ Don't retry immediately on all failures
catch (error) {
  return fetch(url); // Immediate retry
}
```

## Common API Rate Limits Reference

| API | Rate Limit | Window |
|-----|------------|--------|
| Stripe | 100/sec (test), 100/sec (live) | Per second |
| SendGrid | 3000/sec | Per second |
| Twilio | Varies by product | Per second |
| GitHub | 5000/hour (authenticated) | Per hour |
| OpenAI | Varies by model | Per minute |
