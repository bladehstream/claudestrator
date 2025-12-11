# Hono Framework for Cloudflare Workers

Ultra-fast, lightweight web framework with TypeScript-first design. The recommended framework for Cloudflare Workers.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Bundle size** | ~12KB (hono/tiny) |
| **TypeScript** | First-class support |
| **Runtimes** | Workers, Deno, Bun, Node.js, AWS Lambda |
| **Middleware** | Rich built-in ecosystem |
| **Used by** | Cloudflare (Workers Logs, KV, Queues) |

## Getting Started

### Create New Project
```bash
npm create cloudflare@latest my-api -- --template hono
```

### Add to Existing Project
```bash
npm install hono
```

### Basic Application
```typescript
// src/index.ts
import { Hono } from 'hono';

interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
  API_KEY: string;
}

const app = new Hono<{ Bindings: Env }>();

app.get('/', (c) => c.text('Hello World'));

app.get('/json', (c) => c.json({ message: 'Hello' }));

export default app;
```

## Routing

### Basic Routes
```typescript
// HTTP methods
app.get('/users', handler);
app.post('/users', handler);
app.put('/users/:id', handler);
app.patch('/users/:id', handler);
app.delete('/users/:id', handler);

// All methods
app.all('/webhook', handler);

// Multiple methods
app.on(['GET', 'POST'], '/endpoint', handler);
```

### Path Parameters
```typescript
// Single parameter
app.get('/users/:id', (c) => {
  const id = c.req.param('id');
  return c.json({ id });
});

// Multiple parameters
app.get('/users/:userId/posts/:postId', (c) => {
  const { userId, postId } = c.req.param();
  return c.json({ userId, postId });
});

// Wildcard (catch remaining path)
app.get('/files/*', (c) => {
  const path = c.req.param('*'); // 'path/to/file.txt'
  return c.text(`File: ${path}`);
});

// Optional parameter
app.get('/posts/:id?', (c) => {
  const id = c.req.param('id'); // undefined if not provided
  return c.json({ id });
});

// Regex constraint
app.get('/users/:id{[0-9]+}', (c) => {
  const id = c.req.param('id'); // Only matches numeric IDs
  return c.json({ id });
});
```

### Route Groups
```typescript
// Group routes with base path
const users = new Hono<{ Bindings: Env }>();

users.get('/', (c) => c.json({ users: [] }));
users.get('/:id', (c) => c.json({ id: c.req.param('id') }));
users.post('/', (c) => c.json({ created: true }));

app.route('/users', users);

// Or use basePath
const api = new Hono().basePath('/api/v1');
api.get('/health', (c) => c.json({ status: 'ok' }));
```

## Request Handling

### Query Parameters
```typescript
app.get('/search', (c) => {
  // Single parameter
  const q = c.req.query('q');
  
  // All parameters
  const { page, limit } = c.req.query();
  
  // Multiple values (array)
  const tags = c.req.queries('tag'); // ['a', 'b', 'c']
  
  return c.json({ q, page, limit, tags });
});
```

### Request Body
```typescript
// JSON body
app.post('/users', async (c) => {
  const body = await c.req.json<{ name: string; email: string }>();
  return c.json(body);
});

// Form data
app.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File;
  const name = formData.get('name') as string;
  return c.json({ fileName: file.name });
});

// Raw body
app.post('/raw', async (c) => {
  const text = await c.req.text();
  const buffer = await c.req.arrayBuffer();
  return c.text('Received');
});
```

### Headers
```typescript
app.get('/headers', (c) => {
  // Single header
  const auth = c.req.header('Authorization');
  
  // All headers
  const headers = c.req.raw.headers;
  
  return c.json({ auth });
});
```

## Response Helpers

### Response Types
```typescript
// Text
c.text('Hello World');
c.text('Not found', 404);

// JSON
c.json({ data: 'value' });
c.json({ error: 'Not found' }, 404);

// HTML
c.html('<h1>Hello</h1>');

// Redirect
c.redirect('/new-location');
c.redirect('/new-location', 301); // Permanent

// Not found
c.notFound();

// Empty response
c.body(null, 204);

// Stream
c.stream(async (stream) => {
  await stream.write('Hello');
  await stream.write(' World');
});
```

### Response Headers
```typescript
app.get('/download', (c) => {
  // Set single header
  c.header('Content-Type', 'application/pdf');
  c.header('Content-Disposition', 'attachment; filename="doc.pdf"');
  
  return c.body(pdfData);
});

// With Response object
app.get('/custom', (c) => {
  return new Response('Hello', {
    status: 200,
    headers: {
      'Content-Type': 'text/plain',
      'X-Custom-Header': 'value',
    },
  });
});
```

## Middleware

### Built-in Middleware
```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';
import { csrf } from 'hono/csrf';
import { compress } from 'hono/compress';
import { etag } from 'hono/etag';
import { cache } from 'hono/cache';
import { timing } from 'hono/timing';

const app = new Hono();

// Apply to all routes
app.use(logger());
app.use(secureHeaders());
app.use(compress());

// Apply to specific paths
app.use('/api/*', cors());
app.use('/api/*', csrf());
```

### CORS Configuration
```typescript
import { cors } from 'hono/cors';

app.use('/api/*', cors({
  origin: ['https://example.com', 'https://app.example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['X-Request-Id'],
  maxAge: 86400,
  credentials: true,
}));

// Dynamic origin
app.use('/api/*', cors({
  origin: (origin) => {
    return origin.endsWith('.example.com') ? origin : null;
  },
}));
```

### Custom Middleware
```typescript
import { createMiddleware } from 'hono/factory';

// Simple middleware
const requestId = createMiddleware(async (c, next) => {
  const id = crypto.randomUUID();
  c.header('X-Request-Id', id);
  c.set('requestId', id);
  await next();
});

// Middleware with options
const auth = (options: { required: boolean }) => 
  createMiddleware(async (c, next) => {
    const token = c.req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token && options.required) {
      return c.json({ error: 'Unauthorized' }, 401);
    }
    
    if (token) {
      // Verify token...
      c.set('user', { id: '123', email: 'user@example.com' });
    }
    
    await next();
  });

// Usage
app.use('*', requestId);
app.use('/api/*', auth({ required: true }));
```

### Middleware Order
```typescript
// Middleware runs in order defined
app.use(logger());        // 1st: logs request
app.use(cors());          // 2nd: handles CORS
app.use(auth());          // 3rd: authenticates

// Specific path middleware runs before route handler
app.use('/admin/*', adminOnly());
app.get('/admin/dashboard', (c) => { /* ... */ });
```

## Validation with Zod

### Setup
```bash
npm install zod @hono/zod-validator
```

### Request Validation
```typescript
import { z } from 'zod';
import { zValidator } from '@hono/zod-validator';

// Schema definitions
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().positive().optional(),
});

const UserIdSchema = z.object({
  id: z.string().uuid(),
});

const QuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

// Validate JSON body
app.post('/users',
  zValidator('json', CreateUserSchema),
  async (c) => {
    const data = c.req.valid('json');
    // data is typed as { email: string; name: string; age?: number }
    return c.json(data);
  }
);

// Validate path params
app.get('/users/:id',
  zValidator('param', UserIdSchema),
  async (c) => {
    const { id } = c.req.valid('param');
    return c.json({ id });
  }
);

// Validate query params
app.get('/users',
  zValidator('query', QuerySchema),
  async (c) => {
    const { page, limit } = c.req.valid('query');
    return c.json({ page, limit });
  }
);

// Multiple validators
app.put('/users/:id',
  zValidator('param', UserIdSchema),
  zValidator('json', CreateUserSchema.partial()),
  async (c) => {
    const { id } = c.req.valid('param');
    const updates = c.req.valid('json');
    return c.json({ id, updates });
  }
);
```

### Custom Error Handling
```typescript
import { zValidator } from '@hono/zod-validator';

const validate = <T extends z.ZodType>(schema: T) =>
  zValidator('json', schema, (result, c) => {
    if (!result.success) {
      return c.json({
        error: 'Validation failed',
        details: result.error.issues.map(issue => ({
          path: issue.path.join('.'),
          message: issue.message,
        })),
      }, 400);
    }
  });

app.post('/users', validate(CreateUserSchema), handler);
```

## Error Handling

### HTTPException
```typescript
import { HTTPException } from 'hono/http-exception';

app.get('/users/:id', async (c) => {
  const user = await getUser(c.req.param('id'));
  
  if (!user) {
    throw new HTTPException(404, { message: 'User not found' });
  }
  
  return c.json(user);
});
```

### Global Error Handler
```typescript
app.onError((err, c) => {
  console.error(`Error: ${err.message}`);
  
  if (err instanceof HTTPException) {
    return err.getResponse();
  }
  
  // Custom error types
  if (err instanceof ValidationError) {
    return c.json({ error: err.message, details: err.details }, 400);
  }
  
  // Default error response
  return c.json({
    error: 'Internal Server Error',
    message: c.env.ENVIRONMENT === 'development' ? err.message : undefined,
  }, 500);
});
```

### Not Found Handler
```typescript
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    path: c.req.path,
  }, 404);
});
```

## Context Variables

### Setting and Getting Variables
```typescript
interface Variables {
  user: { id: string; email: string };
  requestId: string;
  startTime: number;
}

const app = new Hono<{ 
  Bindings: Env; 
  Variables: Variables;
}>();

// Set in middleware
app.use('*', async (c, next) => {
  c.set('requestId', crypto.randomUUID());
  c.set('startTime', Date.now());
  await next();
});

// Get in handler
app.get('/me', (c) => {
  const user = c.get('user');
  const requestId = c.get('requestId');
  return c.json({ user, requestId });
});
```

## Cloudflare-Specific Features

### Accessing Bindings
```typescript
app.get('/data', async (c) => {
  // All bindings available via c.env
  const db = c.env.DB;
  const kv = c.env.CACHE;
  const r2 = c.env.STORAGE;
  const apiKey = c.env.API_KEY;
  
  return c.json({ status: 'ok' });
});
```

### Execution Context
```typescript
app.get('/background', async (c) => {
  // Access execution context for background tasks
  c.executionCtx.waitUntil(
    logAnalytics(c.req.raw)
  );
  
  return c.json({ status: 'ok' });
});
```

### Cache API
```typescript
import { cache } from 'hono/cache';

app.use('/static/*', cache({
  cacheName: 'my-app',
  cacheControl: 'max-age=3600',
}));

// Manual caching
app.get('/expensive', async (c) => {
  const cacheKey = new Request(c.req.url);
  const cached = await caches.default.match(cacheKey);
  
  if (cached) {
    return cached;
  }
  
  const response = c.json(await expensiveOperation());
  
  c.executionCtx.waitUntil(
    caches.default.put(cacheKey, response.clone())
  );
  
  return response;
});
```

## Testing

### With Hono Test Helpers
```typescript
import { Hono } from 'hono';
import { describe, it, expect } from 'vitest';

const app = new Hono();
app.get('/hello', (c) => c.text('Hello'));

describe('API', () => {
  it('returns hello', async () => {
    const res = await app.request('/hello');
    expect(res.status).toBe(200);
    expect(await res.text()).toBe('Hello');
  });
  
  it('handles POST', async () => {
    const res = await app.request('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Test' }),
    });
    expect(res.status).toBe(201);
  });
});
```

### With Mock Bindings
```typescript
const mockEnv = {
  DB: createMockD1(),
  CACHE: createMockKV(),
  API_KEY: 'test-key',
};

it('uses bindings', async () => {
  const res = await app.request('/data', {}, mockEnv);
  expect(res.status).toBe(200);
});
```

## Project Structure

```
src/
├── index.ts              # App entry, exports default
├── routes/
│   ├── index.ts          # Route aggregator
│   ├── users.ts          # User routes
│   └── posts.ts          # Post routes
├── middleware/
│   ├── auth.ts           # Authentication
│   ├── rate-limit.ts     # Rate limiting
│   └── validate.ts       # Validation helpers
├── services/
│   ├── user-service.ts   # Business logic
│   └── post-service.ts
├── repositories/
│   ├── user-repo.ts      # Data access
│   └── post-repo.ts
├── schemas/
│   ├── user.ts           # Zod schemas
│   └── post.ts
└── types.ts              # Shared types
```

### Modular Routes
```typescript
// src/routes/users.ts
import { Hono } from 'hono';
import type { Env } from '../types';

const users = new Hono<{ Bindings: Env }>();

users.get('/', async (c) => { /* ... */ });
users.post('/', async (c) => { /* ... */ });
users.get('/:id', async (c) => { /* ... */ });

export { users };

// src/routes/index.ts
import { Hono } from 'hono';
import { users } from './users';
import { posts } from './posts';

const routes = new Hono();

routes.route('/users', users);
routes.route('/posts', posts);

export { routes };

// src/index.ts
import { Hono } from 'hono';
import { routes } from './routes';

const app = new Hono();
app.route('/api/v1', routes);

export default app;
```

## Best Practices

1. **Type your app** - Always specify `Bindings` and `Variables`
2. **Use validation** - zValidator for all user input
3. **Modular routes** - Split into separate files
4. **Error handling** - Global handler + HTTPException
5. **Middleware order** - Logger first, auth before routes
6. **Test with app.request()** - No server needed
7. **Use waitUntil** - For background tasks
8. **Keep handlers thin** - Business logic in services
