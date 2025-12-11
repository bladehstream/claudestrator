# Cloudflare Durable Objects

Stateful serverless compute with strong consistency, coordination, and WebSocket support. Ideal for real-time applications, rate limiting, and distributed state.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Consistency** | Strong (single-threaded per ID) |
| **State** | Persistent key-value storage |
| **WebSockets** | Native support with hibernation |
| **Location** | Single location per ID (co-located) |
| **Execution** | Single concurrent request per ID |

## When to Use Durable Objects

| Use Case | Why Durable Objects |
|----------|---------------------|
| **Rate limiting** | Accurate counts, no race conditions |
| **WebSocket server** | State persists across connections |
| **Collaboration** | Real-time sync, conflict resolution |
| **Session state** | Strong consistency, atomic updates |
| **Coordination** | Distributed locks, leader election |
| **Counters/sequences** | Accurate increments |

## Configuration

### wrangler.toml
```toml
[[durable_objects.bindings]]
name = "RATE_LIMITER"
class_name = "RateLimiter"

[[durable_objects.bindings]]
name = "ROOM"
class_name = "ChatRoom"

[[migrations]]
tag = "v1"
new_classes = ["RateLimiter", "ChatRoom"]
```

### Export Classes
```typescript
// src/index.ts
export { RateLimiter } from './durable-objects/rate-limiter';
export { ChatRoom } from './durable-objects/chat-room';

export default app;
```

## Basic Durable Object

### Simple Counter Example
```typescript
// src/durable-objects/counter.ts
export class Counter implements DurableObject {
  private state: DurableObjectState;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    switch (url.pathname) {
      case '/increment': {
        let count = (await this.state.storage.get<number>('count')) || 0;
        count++;
        await this.state.storage.put('count', count);
        return new Response(JSON.stringify({ count }));
      }
      
      case '/get': {
        const count = (await this.state.storage.get<number>('count')) || 0;
        return new Response(JSON.stringify({ count }));
      }
      
      case '/reset': {
        await this.state.storage.delete('count');
        return new Response(JSON.stringify({ count: 0 }));
      }
      
      default:
        return new Response('Not found', { status: 404 });
    }
  }
}
```

### Calling from Worker
```typescript
// src/index.ts
interface Env {
  COUNTER: DurableObjectNamespace;
}

app.post('/counters/:id/increment', async (c) => {
  const id = c.env.COUNTER.idFromName(c.req.param('id'));
  const stub = c.env.COUNTER.get(id);
  
  const response = await stub.fetch(
    new Request('http://do/increment', { method: 'POST' })
  );
  
  return response;
});
```

## Rate Limiter

```typescript
// src/durable-objects/rate-limiter.ts
interface RateLimitConfig {
  limit: number;
  windowMs: number;
}

export class RateLimiter implements DurableObject {
  private state: DurableObjectState;
  private requests: number[] = [];

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const config: RateLimitConfig = {
      limit: parseInt(url.searchParams.get('limit') || '100'),
      windowMs: parseInt(url.searchParams.get('window') || '60000'),
    };
    
    const now = Date.now();
    const windowStart = now - config.windowMs;
    
    // Load requests from storage if not in memory
    if (this.requests.length === 0) {
      this.requests = (await this.state.storage.get<number[]>('requests')) || [];
    }
    
    // Remove old requests
    this.requests = this.requests.filter(ts => ts > windowStart);
    
    if (this.requests.length >= config.limit) {
      const oldestRequest = Math.min(...this.requests);
      const resetAt = oldestRequest + config.windowMs;
      
      return Response.json({
        allowed: false,
        remaining: 0,
        resetAt,
        retryAfter: Math.ceil((resetAt - now) / 1000),
      }, { status: 429 });
    }
    
    // Add new request
    this.requests.push(now);
    await this.state.storage.put('requests', this.requests);
    
    return Response.json({
      allowed: true,
      remaining: config.limit - this.requests.length,
      resetAt: now + config.windowMs,
    });
  }
}
```

### Rate Limit Middleware
```typescript
// src/middleware/rate-limit.ts
import { createMiddleware } from 'hono/factory';

export const rateLimit = (options: {
  limit: number;
  windowMs: number;
  keyGenerator?: (c: Context) => string;
}) => createMiddleware(async (c, next) => {
  const key = options.keyGenerator?.(c) || c.req.header('cf-connecting-ip') || 'anonymous';
  
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
  
  c.header('X-RateLimit-Limit', String(options.limit));
  c.header('X-RateLimit-Remaining', String(result.remaining));
  c.header('X-RateLimit-Reset', String(result.resetAt));
  
  if (!result.allowed) {
    c.header('Retry-After', String(result.retryAfter));
    return c.json({ error: 'Rate limit exceeded' }, 429);
  }
  
  await next();
});

// Usage
app.use('/api/*', rateLimit({ limit: 100, windowMs: 60000 }));
```

## WebSocket Chat Room

```typescript
// src/durable-objects/chat-room.ts
interface ChatMessage {
  type: 'message' | 'join' | 'leave';
  user: string;
  content?: string;
  timestamp: number;
}

export class ChatRoom implements DurableObject {
  private state: DurableObjectState;
  private sessions: Map<WebSocket, { user: string }> = new Map();

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === '/websocket') {
      if (request.headers.get('Upgrade') !== 'websocket') {
        return new Response('Expected WebSocket', { status: 426 });
      }
      
      const user = url.searchParams.get('user') || 'anonymous';
      const { 0: client, 1: server } = new WebSocketPair();
      
      await this.handleWebSocket(server, user);
      
      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }
    
    if (url.pathname === '/history') {
      const history = await this.state.storage.get<ChatMessage[]>('history') || [];
      return Response.json(history.slice(-100)); // Last 100 messages
    }
    
    return new Response('Not found', { status: 404 });
  }

  async handleWebSocket(ws: WebSocket, user: string): Promise<void> {
    // Accept the WebSocket
    this.state.acceptWebSocket(ws);
    this.sessions.set(ws, { user });
    
    // Broadcast join
    await this.broadcast({
      type: 'join',
      user,
      timestamp: Date.now(),
    });
    
    // Send recent history
    const history = await this.state.storage.get<ChatMessage[]>('history') || [];
    ws.send(JSON.stringify({ type: 'history', messages: history.slice(-50) }));
  }

  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer): Promise<void> {
    const session = this.sessions.get(ws);
    if (!session) return;
    
    try {
      const data = JSON.parse(message as string);
      
      if (data.type === 'message' && data.content) {
        const chatMessage: ChatMessage = {
          type: 'message',
          user: session.user,
          content: data.content,
          timestamp: Date.now(),
        };
        
        // Save to history
        const history = await this.state.storage.get<ChatMessage[]>('history') || [];
        history.push(chatMessage);
        
        // Keep only last 1000 messages
        if (history.length > 1000) {
          history.splice(0, history.length - 1000);
        }
        
        await this.state.storage.put('history', history);
        
        // Broadcast to all
        await this.broadcast(chatMessage);
      }
    } catch (e) {
      console.error('Invalid message:', e);
    }
  }

  async webSocketClose(ws: WebSocket, code: number, reason: string): Promise<void> {
    const session = this.sessions.get(ws);
    if (session) {
      this.sessions.delete(ws);
      await this.broadcast({
        type: 'leave',
        user: session.user,
        timestamp: Date.now(),
      });
    }
  }

  async webSocketError(ws: WebSocket, error: unknown): Promise<void> {
    console.error('WebSocket error:', error);
    ws.close(1011, 'Internal error');
  }

  private async broadcast(message: ChatMessage): Promise<void> {
    const payload = JSON.stringify(message);
    
    for (const ws of this.state.getWebSockets()) {
      try {
        ws.send(payload);
      } catch (e) {
        // WebSocket might be closed
      }
    }
  }
}
```

### WebSocket Route
```typescript
// src/index.ts
app.get('/rooms/:roomId/websocket', async (c) => {
  const roomId = c.req.param('roomId');
  const user = c.req.query('user') || 'anonymous';
  
  const id = c.env.ROOM.idFromName(roomId);
  const stub = c.env.ROOM.get(id);
  
  return stub.fetch(
    new Request(`http://do/websocket?user=${user}`, {
      headers: c.req.raw.headers,
    })
  );
});
```

## WebSocket Hibernation

For cost optimization with many idle connections:

```typescript
export class HibernatingRoom implements DurableObject {
  private state: DurableObjectState;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    if (request.headers.get('Upgrade') === 'websocket') {
      const { 0: client, 1: server } = new WebSocketPair();
      
      // Accept with tags for identification
      this.state.acceptWebSocket(server, ['user-123']);
      
      return new Response(null, { status: 101, webSocket: client });
    }
    
    return new Response('Not found', { status: 404 });
  }

  // Called when message received (wakes from hibernation)
  async webSocketMessage(ws: WebSocket, message: string): Promise<void> {
    // Get tags to identify connection
    const tags = this.state.getTags(ws);
    console.log('Message from:', tags);
    
    // Broadcast to all connected WebSockets
    for (const socket of this.state.getWebSockets()) {
      socket.send(message);
    }
  }

  async webSocketClose(ws: WebSocket): Promise<void> {
    // Cleanup
  }
}
```

## Storage API

### Basic Operations
```typescript
// Get single value
const value = await this.state.storage.get<User>('user');

// Get multiple values
const values = await this.state.storage.get<string>(['key1', 'key2', 'key3']);
// Returns Map<string, string>

// Put single value
await this.state.storage.put('key', value);

// Put multiple values (atomic)
await this.state.storage.put({
  user: userData,
  settings: settingsData,
  lastUpdated: Date.now(),
});

// Delete
await this.state.storage.delete('key');
await this.state.storage.delete(['key1', 'key2']);

// Delete all
await this.state.storage.deleteAll();

// List keys
const entries = await this.state.storage.list();
const prefixed = await this.state.storage.list({ prefix: 'user:' });
```

### Transactions
```typescript
// Atomic transaction
await this.state.storage.transaction(async (txn) => {
  const balance = await txn.get<number>('balance') || 0;
  
  if (balance < amount) {
    throw new Error('Insufficient funds');
  }
  
  await txn.put('balance', balance - amount);
  await txn.put('lastTransaction', Date.now());
});
```

### Alarms
```typescript
export class ScheduledTask implements DurableObject {
  private state: DurableObjectState;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === '/schedule') {
      // Schedule alarm for 1 hour from now
      const scheduledTime = Date.now() + 60 * 60 * 1000;
      await this.state.storage.setAlarm(scheduledTime);
      
      return Response.json({ scheduledTime });
    }
    
    if (url.pathname === '/cancel') {
      await this.state.storage.deleteAlarm();
      return Response.json({ cancelled: true });
    }
    
    return new Response('Not found', { status: 404 });
  }

  // Called when alarm fires
  async alarm(): Promise<void> {
    console.log('Alarm fired!');
    
    // Do scheduled work...
    const task = await this.state.storage.get('pendingTask');
    if (task) {
      // Process task
      await this.state.storage.delete('pendingTask');
    }
    
    // Optionally schedule next alarm
    // await this.state.storage.setAlarm(Date.now() + 24 * 60 * 60 * 1000);
  }
}
```

## ID Strategies

```typescript
// Name-based ID (deterministic)
// Same name always gives same DO instance
const id = c.env.DO.idFromName('user-123');
const id = c.env.DO.idFromName(`room:${roomId}`);

// Random ID (unique per call)
const id = c.env.DO.newUniqueId();

// From string (restore existing)
const id = c.env.DO.idFromString(savedIdString);
const idString = id.toString(); // For storage

// Location hints
const id = c.env.DO.newUniqueId({ jurisdiction: 'eu' });
```

## Error Handling

```typescript
export class SafeDO implements DurableObject {
  async fetch(request: Request): Promise<Response> {
    try {
      // DO logic
      return Response.json({ success: true });
    } catch (error) {
      console.error('DO error:', error);
      
      if (error instanceof Error) {
        return Response.json(
          { error: error.message },
          { status: 500 }
        );
      }
      
      return Response.json(
        { error: 'Internal error' },
        { status: 500 }
      );
    }
  }
}

// Caller-side error handling
async function callDO(env: Env, name: string): Promise<Result> {
  const id = env.DO.idFromName(name);
  const stub = env.DO.get(id);
  
  try {
    const response = await stub.fetch(new Request('http://do/action'));
    
    if (!response.ok) {
      const error = await response.json<{ error: string }>();
      throw new Error(error.error);
    }
    
    return response.json();
  } catch (error) {
    // Network error or DO unavailable
    console.error('DO call failed:', error);
    throw error;
  }
}
```

## Testing

### Local Development
```bash
# DOs work locally with persist
npx wrangler dev --persist-to=.wrangler/state
```

### Unit Testing Pattern
```typescript
import { describe, it, expect } from 'vitest';

describe('Counter DO', () => {
  it('should increment', async () => {
    // Create mock state
    const storage = new Map();
    const mockState = {
      storage: {
        get: async (key) => storage.get(key),
        put: async (key, value) => storage.set(key, value),
      },
    };
    
    const counter = new Counter(mockState as any, {} as Env);
    
    // Test increment
    const response = await counter.fetch(
      new Request('http://do/increment', { method: 'POST' })
    );
    
    const result = await response.json();
    expect(result.count).toBe(1);
  });
});
```

## Best Practices

1. **Single responsibility** - One DO class per concern
2. **Use name-based IDs** - For predictable routing (user IDs, room names)
3. **Keep state minimal** - DOs are single-threaded, optimize for speed
4. **Use hibernation** - For WebSocket apps with idle connections
5. **Handle errors gracefully** - DOs can fail, callers should retry
6. **Use alarms for scheduling** - Not cron (per-DO scheduling)
7. **Batch storage operations** - Use put(object) for multiple writes
8. **Consider location** - DOs are single-location, latency varies
