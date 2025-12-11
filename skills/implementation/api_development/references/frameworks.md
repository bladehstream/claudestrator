# API Frameworks

## Hono

Ultrafast web framework for edge computing. Small (~14kB), multi-runtime support.

### Basic Setup

```typescript
import { Hono } from 'hono';

const app = new Hono();

app.get('/', (c) => c.text('Hello!'));
app.get('/users/:id', (c) => {
  const id = c.req.param('id');
  return c.json({ id, name: 'User' });
});

export default app;
```

### Middleware

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';
import { compress } from 'hono/compress';
import { timing } from 'hono/timing';
import { prettyJSON } from 'hono/pretty-json';

const app = new Hono();

// Built-in middleware
app.use('*', logger());
app.use('*', cors());
app.use('*', secureHeaders());
app.use('*', compress());
app.use('*', timing());
app.use('*', prettyJSON());

// Custom middleware
app.use('*', async (c, next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  c.header('X-Response-Time', `${ms}ms`);
});

// Route-specific middleware
app.use('/api/*', authMiddleware);
app.use('/admin/*', adminMiddleware);
```

### Routing Patterns

```typescript
// Basic routes
app.get('/users', listUsers);
app.post('/users', createUser);
app.get('/users/:id', getUser);
app.put('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);

// Grouped routes
const users = new Hono();
users.get('/', listUsers);
users.post('/', createUser);
users.get('/:id', getUser);
users.put('/:id', updateUser);
users.delete('/:id', deleteUser);

app.route('/users', users);

// Nested groups
const api = new Hono();
api.route('/users', usersRouter);
api.route('/posts', postsRouter);
api.route('/orders', ordersRouter);

app.route('/api/v1', api);

// Wildcard routes
app.get('/files/*', (c) => {
  const path = c.req.param('*');
  return c.text(`File: ${path}`);
});
```

### Request Handling

```typescript
app.post('/users', async (c) => {
  // Body parsing
  const json = await c.req.json();
  const formData = await c.req.formData();
  const text = await c.req.text();
  
  // Query params
  const page = c.req.query('page');
  const queries = c.req.queries('tags'); // Multiple values
  
  // Path params
  const id = c.req.param('id');
  
  // Headers
  const auth = c.req.header('Authorization');
  
  // Raw request
  const url = c.req.url;
  const method = c.req.method;
  
  return c.json({ success: true });
});
```

### Response Handling

```typescript
// JSON response
c.json({ data: users }, 200);
c.json({ error: 'Not found' }, 404);

// Text response
c.text('Hello World');

// HTML response
c.html('<h1>Hello</h1>');

// Redirect
c.redirect('/new-location');
c.redirect('/new-location', 301); // Permanent

// Headers
c.header('X-Custom', 'value');
c.header('Set-Cookie', 'token=abc; HttpOnly');

// Status
c.status(201);
c.body(null, 204);

// Streaming
c.stream(async (stream) => {
  await stream.write('Hello ');
  await stream.write('World');
});
```

### Error Handling

```typescript
import { HTTPException } from 'hono/http-exception';

// Throw HTTP exceptions
app.get('/users/:id', async (c) => {
  const user = await getUser(c.req.param('id'));
  if (!user) {
    throw new HTTPException(404, { message: 'User not found' });
  }
  return c.json(user);
});

// Global error handler
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return c.json({ error: err.message }, err.status);
  }
  console.error(err);
  return c.json({ error: 'Internal error' }, 500);
});

// Not found handler
app.notFound((c) => {
  return c.json({ error: 'Not found' }, 404);
});
```

### Zod Validation

```typescript
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
});

app.post('/users',
  zValidator('json', createUserSchema),
  async (c) => {
    const data = c.req.valid('json');  // Typed!
    const user = await createUser(data);
    return c.json(user, 201);
  }
);

// Multiple validators
app.get('/users/:id',
  zValidator('param', z.object({ id: z.string().uuid() })),
  zValidator('query', z.object({ include: z.string().optional() })),
  async (c) => {
    const { id } = c.req.valid('param');
    const { include } = c.req.valid('query');
    // ...
  }
);
```

### OpenAPI Integration

```typescript
import { OpenAPIHono, createRoute, z } from '@hono/zod-openapi';

const app = new OpenAPIHono();

const getUserRoute = createRoute({
  method: 'get',
  path: '/users/{id}',
  request: {
    params: z.object({
      id: z.string().uuid().openapi({ description: 'User ID' }),
    }),
  },
  responses: {
    200: {
      content: { 'application/json': { schema: UserSchema } },
      description: 'User found',
    },
    404: {
      content: { 'application/json': { schema: ErrorSchema } },
      description: 'User not found',
    },
  },
});

app.openapi(getUserRoute, async (c) => {
  const { id } = c.req.valid('param');
  const user = await getUser(id);
  return user ? c.json(user, 200) : c.json({ error: 'Not found' }, 404);
});

// Generate OpenAPI spec
app.doc('/openapi.json', {
  openapi: '3.1.0',
  info: { title: 'My API', version: '1.0.0' },
});

// Swagger UI
app.get('/docs', (c) => c.html(`
  <!DOCTYPE html>
  <html><head>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
  </head><body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script>SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui' })</script>
  </body></html>
`));
```

## tRPC

End-to-end type-safe APIs without schemas or code generation.

### Server Setup

```typescript
import { initTRPC, TRPCError } from '@trpc/server';
import { z } from 'zod';

// Initialize tRPC
const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;

// Protected procedure
const isAuthed = t.middleware(({ ctx, next }) => {
  if (!ctx.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({ ctx: { ...ctx, user: ctx.user } });
});

export const protectedProcedure = t.procedure.use(isAuthed);
```

### Define Router

```typescript
// routers/user.ts
export const userRouter = router({
  // Query - read data
  getById: publicProcedure
    .input(z.string().uuid())
    .query(async ({ input, ctx }) => {
      const user = await ctx.db.user.findUnique({ where: { id: input } });
      if (!user) throw new TRPCError({ code: 'NOT_FOUND' });
      return user;
    }),

  // Query with complex input
  list: publicProcedure
    .input(z.object({
      page: z.number().default(1),
      limit: z.number().max(100).default(20),
      role: z.enum(['user', 'admin']).optional(),
    }))
    .query(async ({ input, ctx }) => {
      return ctx.db.user.findMany({
        where: input.role ? { role: input.role } : undefined,
        skip: (input.page - 1) * input.limit,
        take: input.limit,
      });
    }),

  // Mutation - modify data
  create: protectedProcedure
    .input(z.object({
      email: z.string().email(),
      name: z.string().min(2),
    }))
    .mutation(async ({ input, ctx }) => {
      return ctx.db.user.create({ data: input });
    }),

  update: protectedProcedure
    .input(z.object({
      id: z.string().uuid(),
      data: z.object({
        name: z.string().min(2).optional(),
        email: z.string().email().optional(),
      }),
    }))
    .mutation(async ({ input, ctx }) => {
      return ctx.db.user.update({
        where: { id: input.id },
        data: input.data,
      });
    }),

  delete: protectedProcedure
    .input(z.string().uuid())
    .mutation(async ({ input, ctx }) => {
      await ctx.db.user.delete({ where: { id: input } });
      return { success: true };
    }),
});
```

### Compose Routers

```typescript
// routers/index.ts
import { router } from '../trpc';
import { userRouter } from './user';
import { postRouter } from './post';
import { orderRouter } from './order';

export const appRouter = router({
  user: userRouter,
  post: postRouter,
  order: orderRouter,
});

export type AppRouter = typeof appRouter;
```

### Client Usage

```typescript
import { createTRPCClient, httpBatchLink } from '@trpc/client';
import type { AppRouter } from '../server/routers';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchLink({
      url: 'http://localhost:3000/trpc',
      headers: () => ({
        Authorization: `Bearer ${getToken()}`,
      }),
    }),
  ],
});

// Fully typed!
const user = await trpc.user.getById.query('uuid');
const users = await trpc.user.list.query({ page: 1, limit: 10 });
const newUser = await trpc.user.create.mutate({ email: 'a@b.com', name: 'Test' });
```

### React Query Integration

```typescript
import { createTRPCReact } from '@trpc/react-query';
import type { AppRouter } from '../server/routers';

export const trpc = createTRPCReact<AppRouter>();

// In component
function UserList() {
  const { data, isLoading, error } = trpc.user.list.useQuery({ page: 1 });
  const createMutation = trpc.user.create.useMutation();

  const handleCreate = async () => {
    await createMutation.mutateAsync({ email: 'new@user.com', name: 'New' });
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
}
```

## Cloudflare Workers

### Basic Worker

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === '/api/hello') {
      return Response.json({ message: 'Hello!' });
    }
    
    return new Response('Not Found', { status: 404 });
  },
};
```

### With Hono

```typescript
import { Hono } from 'hono';

type Bindings = {
  DB: D1Database;
  KV: KVNamespace;
  BUCKET: R2Bucket;
  AI: Ai;
  MY_SECRET: string;
};

const app = new Hono<{ Bindings: Bindings }>();

app.get('/users', async (c) => {
  const users = await c.env.DB
    .prepare('SELECT * FROM users LIMIT 100')
    .all();
  return c.json(users.results);
});

app.get('/cache/:key', async (c) => {
  const value = await c.env.KV.get(c.req.param('key'));
  return c.json({ value });
});

app.post('/upload', async (c) => {
  const body = await c.req.arrayBuffer();
  await c.env.BUCKET.put('file.bin', body);
  return c.json({ success: true });
});

export default app;
```

### Durable Objects

```typescript
// For stateful, single-instance logic
export class Counter {
  private state: DurableObjectState;
  private value = 0;

  constructor(state: DurableObjectState) {
    this.state = state;
    this.state.blockConcurrencyWhile(async () => {
      this.value = (await this.state.storage.get('value')) || 0;
    });
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    if (url.pathname === '/increment') {
      this.value++;
      await this.state.storage.put('value', this.value);
    }
    
    return Response.json({ value: this.value });
  }
}

// Worker using Durable Object
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const id = env.COUNTER.idFromName('global');
    const counter = env.COUNTER.get(id);
    return counter.fetch(request);
  },
};
```

### D1 Database

```typescript
app.get('/users/:id', async (c) => {
  const { results } = await c.env.DB
    .prepare('SELECT * FROM users WHERE id = ?')
    .bind(c.req.param('id'))
    .first();
  
  if (!results) {
    return c.json({ error: 'Not found' }, 404);
  }
  
  return c.json(results);
});

app.post('/users', async (c) => {
  const { email, name } = await c.req.json();
  
  const result = await c.env.DB
    .prepare('INSERT INTO users (email, name) VALUES (?, ?) RETURNING *')
    .bind(email, name)
    .first();
  
  return c.json(result, 201);
});
```

### KV Storage

```typescript
// Simple key-value
await c.env.KV.put('key', 'value');
await c.env.KV.put('key', 'value', { expirationTtl: 3600 });
const value = await c.env.KV.get('key');
await c.env.KV.delete('key');

// JSON
await c.env.KV.put('user:123', JSON.stringify(user));
const user = await c.env.KV.get('user:123', 'json');

// With metadata
await c.env.KV.put('key', 'value', { metadata: { version: 1 } });
const { value, metadata } = await c.env.KV.getWithMetadata('key');
```

### Environment Variables

```typescript
// wrangler.toml
[vars]
API_URL = "https://api.example.com"

// Secrets (wrangler secret put MY_SECRET)
// Access in worker
const apiKey = c.env.MY_SECRET;
```

## Framework Comparison

| Feature | Hono | tRPC | Express |
|---------|------|------|---------|
| Bundle size | ~14kB | ~20kB | ~200kB |
| Type safety | Good (with Zod) | Excellent | Manual |
| Edge runtime | ✅ Native | ⚠️ With adapter | ❌ No |
| Learning curve | Low | Medium | Low |
| OpenAPI | ✅ With plugin | ❌ No | ✅ With plugin |
| Use case | REST/Edge APIs | Internal TS APIs | Traditional REST |
