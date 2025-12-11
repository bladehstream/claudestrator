# Rate Limiting

## Core Concepts

Rate limiting restricts how many requests a client can make within a time window. Essential for:
- Preventing abuse and DDoS attacks
- Fair resource allocation
- Cost control
- Service stability

## Algorithms

### 1. Fixed Window

Count requests in fixed time intervals (e.g., per minute).

```typescript
// Simple fixed window implementation
class FixedWindowRateLimiter {
  private counts = new Map<string, { count: number; windowStart: number }>();
  
  constructor(
    private limit: number,
    private windowMs: number
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = Math.floor(now / this.windowMs) * this.windowMs;
    
    const current = this.counts.get(key);
    
    if (!current || current.windowStart !== windowStart) {
      this.counts.set(key, { count: 1, windowStart });
      return true;
    }
    
    if (current.count >= this.limit) {
      return false;
    }
    
    current.count++;
    return true;
  }
}
```

**Pros:** Simple, memory efficient
**Cons:** Burst at window boundaries (2x rate possible)

### 2. Sliding Window Log

Track exact timestamps of requests.

```typescript
class SlidingWindowLogLimiter {
  private logs = new Map<string, number[]>();
  
  constructor(
    private limit: number,
    private windowMs: number
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    let timestamps = this.logs.get(key) || [];
    timestamps = timestamps.filter(t => t > windowStart);
    
    if (timestamps.length >= this.limit) {
      return false;
    }
    
    timestamps.push(now);
    this.logs.set(key, timestamps);
    return true;
  }
}
```

**Pros:** Most accurate, no boundary issues
**Cons:** High memory usage for high-volume keys

### 3. Sliding Window Counter

Weighted average of current and previous window.

```typescript
class SlidingWindowCounterLimiter {
  private windows = new Map<string, { current: number; previous: number; currentStart: number }>();
  
  constructor(
    private limit: number,
    private windowMs: number
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    const currentWindowStart = Math.floor(now / this.windowMs) * this.windowMs;
    const previousWindowStart = currentWindowStart - this.windowMs;
    
    let data = this.windows.get(key);
    
    if (!data || data.currentStart < previousWindowStart) {
      data = { current: 0, previous: 0, currentStart: currentWindowStart };
    } else if (data.currentStart === previousWindowStart) {
      data = { current: 0, previous: data.current, currentStart: currentWindowStart };
    }
    
    // Weight based on position in current window
    const elapsedInWindow = now - currentWindowStart;
    const weight = (this.windowMs - elapsedInWindow) / this.windowMs;
    const weightedCount = data.current + (data.previous * weight);
    
    if (weightedCount >= this.limit) {
      return false;
    }
    
    data.current++;
    this.windows.set(key, data);
    return true;
  }
}
```

**Pros:** Low memory, smooth rate enforcement
**Cons:** Slightly more complex

### 4. Token Bucket

Tokens replenish at fixed rate, requests consume tokens.

```typescript
class TokenBucketLimiter {
  private buckets = new Map<string, { tokens: number; lastRefill: number }>();
  
  constructor(
    private bucketSize: number,  // Max tokens (burst capacity)
    private refillRate: number,  // Tokens per second
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    let bucket = this.buckets.get(key);
    
    if (!bucket) {
      bucket = { tokens: this.bucketSize - 1, lastRefill: now };
      this.buckets.set(key, bucket);
      return true;
    }
    
    // Refill tokens
    const elapsed = (now - bucket.lastRefill) / 1000;
    bucket.tokens = Math.min(
      this.bucketSize,
      bucket.tokens + (elapsed * this.refillRate)
    );
    bucket.lastRefill = now;
    
    if (bucket.tokens < 1) {
      return false;
    }
    
    bucket.tokens--;
    return true;
  }
}
```

**Pros:** Allows controlled bursts, smooth traffic
**Cons:** More complex to configure

### 5. Leaky Bucket

Requests processed at constant rate, excess queued/dropped.

```typescript
class LeakyBucketLimiter {
  private buckets = new Map<string, { queue: number; lastLeak: number }>();
  
  constructor(
    private bucketSize: number,  // Max queue size
    private leakRate: number,    // Requests processed per second
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    let bucket = this.buckets.get(key);
    
    if (!bucket) {
      bucket = { queue: 0, lastLeak: now };
    }
    
    // Leak (process) requests
    const elapsed = (now - bucket.lastLeak) / 1000;
    bucket.queue = Math.max(0, bucket.queue - (elapsed * this.leakRate));
    bucket.lastLeak = now;
    
    if (bucket.queue >= this.bucketSize) {
      return false;
    }
    
    bucket.queue++;
    this.buckets.set(key, bucket);
    return true;
  }
}
```

**Pros:** Smooth output rate, prevents bursts
**Cons:** May delay requests, complex implementation

## Response Headers

Standard headers for rate limit info:

```typescript
// Add to response
c.header('X-RateLimit-Limit', '100');        // Max requests per window
c.header('X-RateLimit-Remaining', '95');     // Requests remaining
c.header('X-RateLimit-Reset', '1699574400'); // Unix timestamp when window resets
c.header('Retry-After', '60');               // Seconds until retry (when limited)
```

## Hono Middleware Implementation

```typescript
import { Hono, Context, Next } from 'hono';

interface RateLimitConfig {
  limit: number;           // Max requests
  windowMs: number;        // Time window in ms
  keyGenerator?: (c: Context) => string;
  handler?: (c: Context) => Response;
  skipFailedRequests?: boolean;
  skipSuccessfulRequests?: boolean;
}

function rateLimiter(config: RateLimitConfig) {
  const {
    limit,
    windowMs,
    keyGenerator = (c) => c.req.header('x-forwarded-for') || 'unknown',
    handler,
    skipFailedRequests = false,
    skipSuccessfulRequests = false,
  } = config;
  
  const store = new Map<string, { count: number; resetTime: number }>();
  
  return async (c: Context, next: Next) => {
    const key = keyGenerator(c);
    const now = Date.now();
    
    let record = store.get(key);
    
    if (!record || now > record.resetTime) {
      record = { count: 0, resetTime: now + windowMs };
      store.set(key, record);
    }
    
    // Set headers
    const remaining = Math.max(0, limit - record.count - 1);
    const reset = Math.ceil(record.resetTime / 1000);
    
    c.header('X-RateLimit-Limit', String(limit));
    c.header('X-RateLimit-Remaining', String(remaining));
    c.header('X-RateLimit-Reset', String(reset));
    
    if (record.count >= limit) {
      const retryAfter = Math.ceil((record.resetTime - now) / 1000);
      c.header('Retry-After', String(retryAfter));
      
      if (handler) {
        return handler(c);
      }
      
      return c.json({
        type: 'https://api.example.com/errors/rate-limit',
        title: 'Too Many Requests',
        status: 429,
        detail: `Rate limit exceeded. Try again in ${retryAfter} seconds.`,
        retryAfter,
      }, 429);
    }
    
    record.count++;
    
    await next();
    
    // Optionally skip counting based on response
    if (skipFailedRequests && c.res.status >= 400) {
      record.count--;
    }
    if (skipSuccessfulRequests && c.res.status < 400) {
      record.count--;
    }
  };
}

// Usage
const app = new Hono();

// Global rate limit
app.use('*', rateLimiter({
  limit: 100,
  windowMs: 60 * 1000, // 1 minute
}));

// Stricter limit for auth endpoints
app.use('/auth/*', rateLimiter({
  limit: 5,
  windowMs: 15 * 60 * 1000, // 15 minutes
  keyGenerator: (c) => `auth:${c.req.header('x-forwarded-for')}`,
}));

// Per-user limit for authenticated routes
app.use('/api/*', rateLimiter({
  limit: 1000,
  windowMs: 60 * 60 * 1000, // 1 hour
  keyGenerator: (c) => `user:${c.get('userId')}`,
}));
```

## Distributed Rate Limiting (Redis)

For multi-instance deployments:

```typescript
import { Redis } from '@upstash/redis';

const redis = new Redis({ url: env.REDIS_URL, token: env.REDIS_TOKEN });

async function checkRateLimit(
  key: string,
  limit: number,
  windowSeconds: number
): Promise<{ allowed: boolean; remaining: number; reset: number }> {
  const now = Math.floor(Date.now() / 1000);
  const windowKey = `ratelimit:${key}:${Math.floor(now / windowSeconds)}`;
  
  const multi = redis.multi();
  multi.incr(windowKey);
  multi.expire(windowKey, windowSeconds);
  
  const results = await multi.exec();
  const count = results[0] as number;
  
  const remaining = Math.max(0, limit - count);
  const reset = (Math.floor(now / windowSeconds) + 1) * windowSeconds;
  
  return {
    allowed: count <= limit,
    remaining,
    reset,
  };
}

// Sliding window with Redis
async function slidingWindowRateLimit(
  key: string,
  limit: number,
  windowMs: number
): Promise<{ allowed: boolean; remaining: number }> {
  const now = Date.now();
  const windowStart = now - windowMs;
  const zsetKey = `ratelimit:sliding:${key}`;
  
  const multi = redis.multi();
  // Remove old entries
  multi.zremrangebyscore(zsetKey, 0, windowStart);
  // Add current request
  multi.zadd(zsetKey, { score: now, member: `${now}:${Math.random()}` });
  // Count requests in window
  multi.zcard(zsetKey);
  // Set expiry
  multi.expire(zsetKey, Math.ceil(windowMs / 1000));
  
  const results = await multi.exec();
  const count = results[2] as number;
  
  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
  };
}
```

## Cloudflare Workers Rate Limiting

Using Durable Objects for distributed state:

```typescript
// rate-limiter.ts (Durable Object)
export class RateLimiter {
  private state: DurableObjectState;
  private count = 0;
  private resetTime = 0;
  
  constructor(state: DurableObjectState) {
    this.state = state;
  }
  
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '100');
    const windowMs = parseInt(url.searchParams.get('window') || '60000');
    
    const now = Date.now();
    
    if (now > this.resetTime) {
      this.count = 0;
      this.resetTime = now + windowMs;
    }
    
    if (this.count >= limit) {
      return Response.json({
        allowed: false,
        remaining: 0,
        reset: this.resetTime,
      });
    }
    
    this.count++;
    
    return Response.json({
      allowed: true,
      remaining: limit - this.count,
      reset: this.resetTime,
    });
  }
}

// worker.ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const ip = request.headers.get('cf-connecting-ip') || 'unknown';
    const id = env.RATE_LIMITER.idFromName(ip);
    const limiter = env.RATE_LIMITER.get(id);
    
    const result = await limiter.fetch(
      `http://internal/?limit=100&window=60000`
    ).then(r => r.json());
    
    if (!result.allowed) {
      return new Response('Too Many Requests', { status: 429 });
    }
    
    // Process request...
  }
};
```

## Rate Limit by Tier

```typescript
const tierLimits = {
  free: { limit: 100, windowMs: 60 * 60 * 1000 },      // 100/hour
  basic: { limit: 1000, windowMs: 60 * 60 * 1000 },   // 1000/hour
  pro: { limit: 10000, windowMs: 60 * 60 * 1000 },    // 10000/hour
  enterprise: { limit: 100000, windowMs: 60 * 60 * 1000 },
};

app.use('/api/*', async (c, next) => {
  const user = c.get('user');
  const tier = user?.tier || 'free';
  const limits = tierLimits[tier];
  
  const { allowed, remaining, reset } = await checkRateLimit(
    `user:${user?.id || c.req.header('x-forwarded-for')}`,
    limits.limit,
    limits.windowMs / 1000
  );
  
  c.header('X-RateLimit-Limit', String(limits.limit));
  c.header('X-RateLimit-Remaining', String(remaining));
  c.header('X-RateLimit-Reset', String(reset));
  
  if (!allowed) {
    return c.json({ error: 'Rate limit exceeded' }, 429);
  }
  
  await next();
});
```

## Best Practices

1. **Use appropriate algorithm** - Token bucket for APIs, sliding window for auth
2. **Set different limits** per endpoint sensitivity
3. **Include rate limit headers** in all responses
4. **Provide clear error messages** with retry-after
5. **Use distributed store** for multi-instance deployments
6. **Monitor and alert** on rate limit hits
7. **Allow bursts** for legitimate traffic patterns
8. **Consider user tiers** with different limits
9. **Rate limit by multiple keys** (IP + user + endpoint)
10. **Don't rate limit health checks** and internal endpoints
