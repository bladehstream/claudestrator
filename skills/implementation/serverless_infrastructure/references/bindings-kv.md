# Cloudflare KV Namespace Bindings

Key-value storage for low-latency reads with eventual consistency. Ideal for configuration, session data, and caching.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Read latency** | ~10-50ms globally |
| **Write propagation** | ~60 seconds globally |
| **Consistency** | Eventual (read-after-write in same location) |
| **Max value size** | 25 MB |
| **Max key size** | 512 bytes |
| **Write limit** | 1 write per second per key |

## Configuration

### wrangler.toml
```toml
[[kv_namespaces]]
binding = "CACHE"
id = "abc123def456"

# Preview namespace for local dev
[[kv_namespaces]]
binding = "CACHE"
id = "abc123def456"
preview_id = "xyz789"
```

### Create Namespace
```bash
# Create production namespace
npx wrangler kv:namespace create "CACHE"

# Create preview namespace for dev
npx wrangler kv:namespace create "CACHE" --preview
```

## Basic Operations

### TypeScript Types
```typescript
interface Env {
  CACHE: KVNamespace;
}
```

### Read Operations
```typescript
// Get string value
const value = await c.env.CACHE.get('key');

// Get with type
const value = await c.env.CACHE.get('key', 'text'); // string | null
const value = await c.env.CACHE.get('key', 'json'); // unknown | null
const value = await c.env.CACHE.get('key', 'arrayBuffer'); // ArrayBuffer | null
const value = await c.env.CACHE.get('key', 'stream'); // ReadableStream | null

// Get with metadata
const { value, metadata } = await c.env.CACHE.getWithMetadata<Metadata>('key');
```

### Write Operations
```typescript
// Simple put
await c.env.CACHE.put('key', 'value');

// Put with expiration (seconds from now)
await c.env.CACHE.put('key', 'value', { expirationTtl: 3600 }); // 1 hour

// Put with absolute expiration (Unix timestamp)
await c.env.CACHE.put('key', 'value', { expiration: 1735689600 });

// Put with metadata
await c.env.CACHE.put('key', 'value', {
  metadata: { userId: '123', createdAt: Date.now() },
});

// Put JSON (must stringify)
await c.env.CACHE.put('user:123', JSON.stringify(userData));
```

### Delete Operations
```typescript
await c.env.CACHE.delete('key');
```

### List Operations
```typescript
// List all keys
const { keys, list_complete, cursor } = await c.env.CACHE.list();

// List with prefix
const result = await c.env.CACHE.list({ prefix: 'user:' });

// Paginate through results
let cursor: string | undefined;
do {
  const result = await c.env.CACHE.list({ cursor, limit: 100 });
  for (const key of result.keys) {
    console.log(key.name, key.metadata);
  }
  cursor = result.list_complete ? undefined : result.cursor;
} while (cursor);
```

## Common Patterns

### Session Storage
```typescript
interface Session {
  userId: string;
  email: string;
  createdAt: number;
  expiresAt: number;
}

async function createSession(env: Env, userId: string, email: string): Promise<string> {
  const sessionId = crypto.randomUUID();
  const session: Session = {
    userId,
    email,
    createdAt: Date.now(),
    expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days
  };
  
  await env.CACHE.put(
    `session:${sessionId}`,
    JSON.stringify(session),
    { expirationTtl: 7 * 24 * 60 * 60 } // 7 days in seconds
  );
  
  return sessionId;
}

async function getSession(env: Env, sessionId: string): Promise<Session | null> {
  const data = await env.CACHE.get(`session:${sessionId}`, 'json');
  return data as Session | null;
}

async function deleteSession(env: Env, sessionId: string): Promise<void> {
  await env.CACHE.delete(`session:${sessionId}`);
}
```

### Caching with Stale-While-Revalidate
```typescript
interface CacheEntry<T> {
  data: T;
  cachedAt: number;
  ttl: number;
}

async function getWithCache<T>(
  env: Env,
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds: number = 300
): Promise<T> {
  const cached = await env.CACHE.get<CacheEntry<T>>(key, 'json');
  
  if (cached) {
    const age = (Date.now() - cached.cachedAt) / 1000;
    
    // Return cached data immediately
    if (age < cached.ttl) {
      return cached.data;
    }
    
    // Stale: return cached but refresh in background
    if (age < cached.ttl * 2) {
      // Don't await - refresh in background
      refreshCache(env, key, fetcher, ttlSeconds);
      return cached.data;
    }
  }
  
  // No cache or too stale - fetch fresh
  return refreshCache(env, key, fetcher, ttlSeconds);
}

async function refreshCache<T>(
  env: Env,
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds: number
): Promise<T> {
  const data = await fetcher();
  const entry: CacheEntry<T> = {
    data,
    cachedAt: Date.now(),
    ttl: ttlSeconds,
  };
  
  await env.CACHE.put(key, JSON.stringify(entry), {
    expirationTtl: ttlSeconds * 2, // Keep stale data for SWR
  });
  
  return data;
}
```

### Configuration Store
```typescript
interface AppConfig {
  featureFlags: Record<string, boolean>;
  rateLimits: Record<string, number>;
  maintenanceMode: boolean;
}

async function getConfig(env: Env): Promise<AppConfig> {
  const config = await env.CACHE.get<AppConfig>('config:app', 'json');
  
  if (!config) {
    // Return defaults if not configured
    return {
      featureFlags: {},
      rateLimits: { default: 100 },
      maintenanceMode: false,
    };
  }
  
  return config;
}

// Middleware to inject config
app.use('*', async (c, next) => {
  const config = await getConfig(c.env);
  c.set('config', config);
  
  if (config.maintenanceMode) {
    return c.json({ error: 'Service under maintenance' }, 503);
  }
  
  await next();
});
```

### Rate Limiting (Simple)
```typescript
// Note: For strict rate limiting, use Durable Objects instead
// KV's eventual consistency makes this approximate

interface RateLimitEntry {
  count: number;
  windowStart: number;
}

async function checkRateLimit(
  env: Env,
  identifier: string,
  limit: number,
  windowSeconds: number
): Promise<{ allowed: boolean; remaining: number }> {
  const key = `ratelimit:${identifier}`;
  const now = Date.now();
  const windowMs = windowSeconds * 1000;
  
  const entry = await env.CACHE.get<RateLimitEntry>(key, 'json');
  
  if (!entry || now - entry.windowStart > windowMs) {
    // New window
    await env.CACHE.put(key, JSON.stringify({
      count: 1,
      windowStart: now,
    }), { expirationTtl: windowSeconds });
    
    return { allowed: true, remaining: limit - 1 };
  }
  
  if (entry.count >= limit) {
    return { allowed: false, remaining: 0 };
  }
  
  // Increment (race condition possible - use DO for strict limits)
  await env.CACHE.put(key, JSON.stringify({
    count: entry.count + 1,
    windowStart: entry.windowStart,
  }), { expirationTtl: windowSeconds });
  
  return { allowed: true, remaining: limit - entry.count - 1 };
}
```

### User Preferences
```typescript
interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  notifications: boolean;
}

const DEFAULT_PREFS: UserPreferences = {
  theme: 'light',
  language: 'en',
  notifications: true,
};

async function getUserPrefs(env: Env, userId: string): Promise<UserPreferences> {
  const prefs = await env.CACHE.get<UserPreferences>(`prefs:${userId}`, 'json');
  return { ...DEFAULT_PREFS, ...prefs };
}

async function updateUserPrefs(
  env: Env,
  userId: string,
  updates: Partial<UserPreferences>
): Promise<UserPreferences> {
  const current = await getUserPrefs(env, userId);
  const updated = { ...current, ...updates };
  
  await env.CACHE.put(`prefs:${userId}`, JSON.stringify(updated));
  
  return updated;
}
```

## Performance Optimization

### Batch Reads (Not Native - Manual Pattern)
```typescript
// KV doesn't have native batch get, but you can parallelize
async function batchGet(env: Env, keys: string[]): Promise<Map<string, string | null>> {
  const results = await Promise.all(
    keys.map(async (key) => ({
      key,
      value: await env.CACHE.get(key),
    }))
  );
  
  return new Map(results.map(r => [r.key, r.value]));
}
```

### Minimize Writes
```typescript
// BAD: Multiple writes
await env.CACHE.put('user:123:name', 'John');
await env.CACHE.put('user:123:email', 'john@example.com');
await env.CACHE.put('user:123:role', 'admin');

// GOOD: Single write with JSON
await env.CACHE.put('user:123', JSON.stringify({
  name: 'John',
  email: 'john@example.com',
  role: 'admin',
}));
```

### Key Design
```typescript
// Good key patterns
const keys = {
  session: (id: string) => `session:${id}`,
  userPrefs: (userId: string) => `prefs:${userId}`,
  cache: (resource: string, id: string) => `cache:${resource}:${id}`,
  rateLimit: (ip: string, endpoint: string) => `rl:${endpoint}:${ip}`,
};

// Avoid: Long keys waste space
// Bad:  'user-preferences-for-user-id-12345'
// Good: 'prefs:12345'
```

## Error Handling

```typescript
async function safeGet<T>(env: Env, key: string): Promise<T | null> {
  try {
    return await env.CACHE.get<T>(key, 'json');
  } catch (error) {
    console.error(`KV get failed for ${key}:`, error);
    return null;
  }
}

async function safePut(env: Env, key: string, value: unknown): Promise<boolean> {
  try {
    await env.CACHE.put(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error(`KV put failed for ${key}:`, error);
    return false;
  }
}
```

## Testing

### Local Development
```bash
# Use --persist to keep KV data between dev sessions
npx wrangler dev --persist-to=.wrangler/state

# Or use remote KV (preview namespace)
npx wrangler dev --remote
```

### Seeding Data
```bash
# Put single value
npx wrangler kv:key put --binding=CACHE "config:app" '{"maintenanceMode":false}'

# Bulk upload from JSON file
npx wrangler kv:bulk put --binding=CACHE ./seed-data.json
```

### seed-data.json Format
```json
[
  {
    "key": "config:app",
    "value": "{\"maintenanceMode\":false}"
  },
  {
    "key": "user:123",
    "value": "{\"name\":\"Test User\"}",
    "expiration_ttl": 3600
  }
]
```

## Best Practices

1. **Design for eventual consistency** - Don't rely on immediate write visibility
2. **Use TTL for all cache entries** - Avoid stale data accumulation
3. **Batch data in single keys** - Minimize write operations
4. **Use meaningful key prefixes** - Enables listing and organization
5. **Handle missing keys gracefully** - Always have defaults
6. **Avoid hot keys** - 1 write/sec limit per key
7. **Use Durable Objects for strict consistency** - When KV's eventual consistency isn't enough
