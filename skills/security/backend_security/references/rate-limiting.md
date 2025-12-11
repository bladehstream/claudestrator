# Rate Limiting

Protect APIs from abuse, DoS attacks, and ensure fair resource allocation.

## Why Rate Limit?

| Purpose | Benefit |
|---------|---------|
| **Prevent abuse** | Stop scraping, brute force, spam |
| **Ensure availability** | Protect server from overload |
| **Fair usage** | Prevent one user from monopolizing |
| **Cost control** | Limit expensive operations |
| **Security** | Slow down credential stuffing attacks |

## Rate Limiting Algorithms

### Fixed Window
Simple counter that resets at fixed intervals.

```typescript
// Fixed Window - In-memory (single instance only)
const windowMs = 60_000; // 1 minute
const maxRequests = 100;
const store = new Map<string, { count: number; windowStart: number }>();

function fixedWindowLimit(key: string): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const record = store.get(key);
  
  // New window or expired
  if (!record || now - record.windowStart >= windowMs) {
    store.set(key, { count: 1, windowStart: now });
    return { allowed: true, remaining: maxRequests - 1 };
  }
  
  // Within window
  if (record.count >= maxRequests) {
    return { allowed: false, remaining: 0 };
  }
  
  record.count++;
  return { allowed: true, remaining: maxRequests - record.count };
}
```

**Pros:** Simple, low memory
**Cons:** Burst at window boundaries (can get 2x requests at boundary)

### Sliding Window
Smoother rate limiting using weighted counts.

```typescript
// Sliding Window Counter
function slidingWindowLimit(key: string): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const currentWindow = Math.floor(now / windowMs);
  const previousWindow = currentWindow - 1;
  const positionInWindow = (now % windowMs) / windowMs;
  
  const currentCount = getCount(key, currentWindow);
  const previousCount = getCount(key, previousWindow);
  
  // Weighted count from previous window
  const estimatedCount = previousCount * (1 - positionInWindow) + currentCount;
  
  if (estimatedCount >= maxRequests) {
    return { allowed: false, remaining: 0 };
  }
  
  incrementCount(key, currentWindow);
  return { allowed: true, remaining: Math.floor(maxRequests - estimatedCount - 1) };
}
```

**Pros:** Smoother than fixed window, prevents boundary bursts
**Cons:** More complex, needs two counters

### Token Bucket
Allows bursts while enforcing average rate.

```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;
  
  constructor(
    private capacity: number,    // Max tokens (burst size)
    private refillRate: number,  // Tokens per second
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }
  
  take(count: number = 1): boolean {
    this.refill();
    
    if (this.tokens >= count) {
      this.tokens -= count;
      return true;
    }
    
    return false;
  }
  
  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.refillRate;
    
    this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }
  
  getTokens(): number {
    this.refill();
    return this.tokens;
  }
}
```

**Pros:** Allows controlled bursts, flexible
**Cons:** More state to track

### Leaky Bucket
Processes requests at a constant rate.

```typescript
class LeakyBucket {
  private queue: (() => void)[] = [];
  private processing = false;
  
  constructor(
    private capacity: number,      // Max queue size
    private leakRateMs: number,    // Ms between processing
  ) {}
  
  add(callback: () => void): boolean {
    if (this.queue.length >= this.capacity) {
      return false; // Bucket full, reject
    }
    
    this.queue.push(callback);
    this.startLeaking();
    return true;
  }
  
  private startLeaking(): void {
    if (this.processing) return;
    this.processing = true;
    
    const leak = () => {
      const callback = this.queue.shift();
      if (callback) {
        callback();
        setTimeout(leak, this.leakRateMs);
      } else {
        this.processing = false;
      }
    };
    
    leak();
  }
}
```

**Pros:** Smooths traffic, predictable processing rate
**Cons:** Adds latency, queue management complexity

## Cloudflare Workers Implementation

### Using KV (Approximate)
```typescript
// Rate limiting with KV - eventually consistent
// Good for soft limits, not strict enforcement

interface RateLimitRecord {
  count: number;
  windowStart: number;
}

async function kvRateLimit(
  kv: KVNamespace,
  key: string,
  limit: number,
  windowSeconds: number
): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
  const now = Date.now();
  const recordKey = `ratelimit:${key}`;
  
  const record = await kv.get<RateLimitRecord>(recordKey, 'json');
  
  // New window
  if (!record || now - record.windowStart > windowSeconds * 1000) {
    await kv.put(recordKey, JSON.stringify({
      count: 1,
      windowStart: now,
    }), { expirationTtl: windowSeconds });
    
    return {
      allowed: true,
      remaining: limit - 1,
      resetAt: now + windowSeconds * 1000,
    };
  }
  
  // Check limit
  if (record.count >= limit) {
    return {
      allowed: false,
      remaining: 0,
      resetAt: record.windowStart + windowSeconds * 1000,
    };
  }
  
  // Increment (race condition possible)
  await kv.put(recordKey, JSON.stringify({
    count: record.count + 1,
    windowStart: record.windowStart,
  }), { expirationTtl: windowSeconds });
  
  return {
    allowed: true,
    remaining: limit - record.count - 1,
    resetAt: record.windowStart + windowSeconds * 1000,
  };
}
```

### Using Durable Objects (Accurate)
```typescript
// Durable Object for accurate rate limiting
export class RateLimiter implements DurableObject {
  private state: DurableObjectState;
  private requests: number[] = [];

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '100');
    const windowMs = parseInt(url.searchParams.get('window') || '60000');
    
    // Load from storage if empty
    if (this.requests.length === 0) {
      this.requests = await this.state.storage.get('requests') || [];
    }
    
    const now = Date.now();
    const windowStart = now - windowMs;
    
    // Remove old requests
    this.requests = this.requests.filter(ts => ts > windowStart);
    
    // Check limit
    if (this.requests.length >= limit) {
      const oldestInWindow = Math.min(...this.requests);
      const resetAt = oldestInWindow + windowMs;
      
      return Response.json({
        allowed: false,
        remaining: 0,
        resetAt,
        retryAfter: Math.ceil((resetAt - now) / 1000),
      }, { status: 429 });
    }
    
    // Add request
    this.requests.push(now);
    await this.state.storage.put('requests', this.requests);
    
    return Response.json({
      allowed: true,
      remaining: limit - this.requests.length,
      resetAt: now + windowMs,
    });
  }
}
```

### Rate Limit Middleware
```typescript
import { createMiddleware } from 'hono/factory';

interface RateLimitOptions {
  limit: number;
  windowMs: number;
  keyGenerator?: (c: Context) => string;
  skip?: (c: Context) => boolean;
}

export const rateLimit = (options: RateLimitOptions) => 
  createMiddleware(async (c, next) => {
    // Skip if specified
    if (options.skip?.(c)) {
      await next();
      return;
    }
    
    // Generate key (default: IP address)
    const key = options.keyGenerator?.(c) 
      || c.req.header('cf-connecting-ip') 
      || c.req.header('x-forwarded-for')?.split(',')[0]
      || 'anonymous';
    
    // Get rate limiter DO
    const id = c.env.RATE_LIMITER.idFromName(key);
    const stub = c.env.RATE_LIMITER.get(id);
    
    const response = await stub.fetch(
      new Request(`http://do/check?limit=${options.limit}&window=${options.windowMs}`)
    );
    
    const result = await response.json<{
      allowed: boolean;
      remaining: number;
      resetAt: number;
      retryAfter?: number;
    }>();
    
    // Set rate limit headers
    c.header('X-RateLimit-Limit', String(options.limit));
    c.header('X-RateLimit-Remaining', String(result.remaining));
    c.header('X-RateLimit-Reset', String(Math.ceil(result.resetAt / 1000)));
    
    if (!result.allowed) {
      c.header('Retry-After', String(result.retryAfter));
      return c.json({ 
        error: 'Too Many Requests',
        message: `Rate limit exceeded. Try again in ${result.retryAfter} seconds.`
      }, 429);
    }
    
    await next();
  });

// Usage
app.use('/api/*', rateLimit({
  limit: 100,
  windowMs: 60_000, // 1 minute
}));

// Stricter limit for auth endpoints
app.use('/api/auth/*', rateLimit({
  limit: 5,
  windowMs: 60_000,
  keyGenerator: (c) => `auth:${c.req.header('cf-connecting-ip')}`,
}));
```

## Rate Limit Response Headers

Standard headers to include:

| Header | Purpose |
|--------|---------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in window |
| `X-RateLimit-Reset` | Unix timestamp when window resets |
| `Retry-After` | Seconds until client should retry (on 429) |

## Different Limits for Different Endpoints

```typescript
// Tiered rate limiting
const rateLimits = {
  // Very strict for login attempts
  login: { limit: 5, windowMs: 300_000 },  // 5 per 5 minutes
  
  // Strict for writes
  write: { limit: 30, windowMs: 60_000 },  // 30 per minute
  
  // Standard for reads
  read: { limit: 100, windowMs: 60_000 },  // 100 per minute
  
  // Generous for static resources
  static: { limit: 1000, windowMs: 60_000 },
};

app.use('/api/auth/login', rateLimit(rateLimits.login));
app.use('/api/*/create', rateLimit(rateLimits.write));
app.use('/api/*/update', rateLimit(rateLimits.write));
app.use('/api/*/delete', rateLimit(rateLimits.write));
app.use('/api/*', rateLimit(rateLimits.read));
```

## User-Based vs IP-Based

```typescript
// IP-based (default, for unauthenticated)
const ipKey = (c: Context) => c.req.header('cf-connecting-ip') || 'unknown';

// User-based (for authenticated users)
const userKey = (c: Context) => {
  const user = c.get('user');
  return user ? `user:${user.id}` : ipKey(c);
};

// API key based
const apiKeyKey = (c: Context) => {
  const apiKey = c.req.header('x-api-key');
  return apiKey ? `apikey:${apiKey}` : ipKey(c);
};

// Combined (user if auth'd, else IP)
const combinedKey = (c: Context) => {
  const user = c.get('user');
  if (user) return `user:${user.id}`;
  return ipKey(c);
};
```

## Handling 429 Responses (Client Side)

```typescript
// Exponential backoff with retry
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries = 3
): Promise<Response> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, options);
    
    if (response.status !== 429) {
      return response;
    }
    
    if (attempt === maxRetries) {
      throw new Error('Max retries exceeded');
    }
    
    // Get retry delay from header or use exponential backoff
    const retryAfter = response.headers.get('Retry-After');
    const delay = retryAfter 
      ? parseInt(retryAfter) * 1000 
      : Math.pow(2, attempt) * 1000;
    
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  throw new Error('Unexpected end of retry loop');
}
```

## Best Practices

1. **Choose the right algorithm** - Token bucket for APIs, leaky bucket for queues
2. **Use Durable Objects for accuracy** - KV has eventual consistency issues
3. **Set appropriate limits** - Too strict hurts UX, too loose allows abuse
4. **Different limits per endpoint** - Strict for login, generous for reads
5. **Include rate limit headers** - Help clients implement proper backoff
6. **Return 429 with Retry-After** - Standard response for rate limiting
7. **Log rate limit hits** - Monitor for abuse patterns
8. **Skip internal requests** - Don't rate limit internal service calls
9. **Consider burst allowance** - Let users burst occasionally
10. **Test under load** - Verify limits work correctly
