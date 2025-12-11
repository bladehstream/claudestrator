---
name: API Development
id: api_development
version: 1.0
category: implementation
domain: [api, backend, typescript, web]
task_types: [design, implementation, documentation]
keywords: [api, rest, graphql, trpc, hono, endpoint, validation, zod, openapi, http, request, response, pagination, rate-limiting, versioning]
complexity: [normal, complex]
pairs_with: [database_designer, security_reviewer, web_auth_security]
source: backend-skills/api-development/SKILL-api-development.md
---

# API Development

Build production-ready APIs with modern TypeScript patterns.

## Quick Reference: When to Use What

| Need | Solution | Reference |
|------|----------|-----------|
| Public REST API | OpenAPI 3.1 + Hono/Express | [rest-design.md](references/rest-design.md), [openapi.md](references/openapi.md) |
| Internal TypeScript API | tRPC | [frameworks.md](references/frameworks.md) |
| Flexible queries | GraphQL | [graphql.md](references/graphql.md) |
| Edge/serverless | Hono + Cloudflare Workers | [frameworks.md](references/frameworks.md) |
| Input validation | Zod | [validation.md](references/validation.md) |

## Core Workflow

### 1. Design Phase

**Choose API style:**
- REST: Resource-oriented, HTTP semantics, broad client support
- GraphQL: Flexible queries, single endpoint, typed schema
- tRPC: End-to-end TypeScript type safety, internal APIs

**Design-first approach (recommended for REST):**
1. Write OpenAPI spec defining endpoints, schemas, responses
2. Generate types/stubs from spec
3. Implement handlers matching contract
4. Generate documentation automatically

### 2. Implementation Essentials

**Request validation pattern (Zod + Hono):**
```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  role: z.enum(['user', 'admin']).default('user'),
});

app.post('/users',
  zValidator('json', createUserSchema),
  async (c) => {
    const data = c.req.valid('json'); // Fully typed
    const user = await userService.create(data);
    return c.json(user, 201);
  }
);
```

**Error response format (RFC 9457):**
```typescript
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Email format is invalid",
  "instance": "/users",
  "errors": [
    { "field": "email", "message": "Must be valid email" }
  ]
}
```

**HTTP status code quick reference:**
- 200 OK, 201 Created, 204 No Content
- 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable, 429 Too Many Requests
- 500 Internal Error, 503 Service Unavailable

### 3. Key Patterns

**Pagination** - Choose based on use case:
| Type | Use When | Params |
|------|----------|--------|
| Offset | Small datasets, random page access | `?page=2&limit=20` |
| Cursor | Large/changing data, infinite scroll | `?cursor=abc&limit=20` |
| Keyset | High performance, real-time feeds | `?after_id=123&limit=20` |

**Versioning** - Pick one strategy consistently:
| Strategy | Example | Best For |
|----------|---------|----------|
| URL path | `/v1/users` | Public APIs, clear separation |
| Header | `Accept: application/vnd.api.v2+json` | Clean URLs, internal APIs |
| Query | `?version=2` | Simple implementation |

**Rate limiting headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699574400
Retry-After: 60
```

## Reference Files

Read these for detailed implementation guidance:

| File | Contents |
|------|----------|
| [rest-design.md](references/rest-design.md) | REST principles, URL design, HTTP methods, resource modeling |
| [graphql.md](references/graphql.md) | Schema design, queries, mutations, resolvers, N+1 prevention |
| [openapi.md](references/openapi.md) | OpenAPI 3.1/3.2 spec, components, security schemes, tooling |
| [validation.md](references/validation.md) | Zod patterns, transforms, error handling, schema composition |
| [error-handling.md](references/error-handling.md) | Status codes, error formats, centralized handlers |
| [versioning.md](references/versioning.md) | Strategies, deprecation, migration paths |
| [pagination.md](references/pagination.md) | Offset, cursor, keyset implementation with code |
| [rate-limiting.md](references/rate-limiting.md) | Algorithms, middleware, distributed limiting |
| [frameworks.md](references/frameworks.md) | Hono, tRPC, Cloudflare Workers patterns |
| [testing.md](references/testing.md) | Contract testing, integration testing, mocking |

## Framework Quick Start

### Hono (Recommended for Edge/Serverless)

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';

const app = new Hono();

app.use('*', cors());
app.use('*', logger());

// Routes
app.route('/users', usersRouter);
app.route('/posts', postsRouter);

export default app;
```

### tRPC (Type-Safe Internal APIs)

```typescript
// server
const appRouter = router({
  users: router({
    getById: publicProcedure
      .input(z.string().uuid())
      .query(({ input }) => userService.findById(input)),
    create: publicProcedure
      .input(createUserSchema)
      .mutation(({ input }) => userService.create(input)),
  }),
});

// client - fully typed, no codegen
const user = await trpc.users.getById.query('uuid');
```

## Common Patterns

**Centralized error handler:**
```typescript
app.onError((err, c) => {
  if (err instanceof ZodError) {
    return c.json({
      type: 'validation_error',
      errors: err.errors
    }, 400);
  }
  if (err instanceof NotFoundError) {
    return c.json({ type: 'not_found', detail: err.message }, 404);
  }
  console.error(err);
  return c.json({ type: 'internal_error' }, 500);
});
```

**Response envelope (optional):**
```typescript
// Paginated response
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "hasMore": true
  },
  "links": {
    "next": "/users?cursor=abc",
    "prev": null
  }
}
```

## Cloudflare Workers Specifics

```typescript
// wrangler.jsonc bindings
export interface Env {
  DB: D1Database;
  KV: KVNamespace;
  CACHE: Cache;
}

// Hono with bindings
const app = new Hono<{ Bindings: Env }>();

app.get('/users/:id', async (c) => {
  // Access bindings via c.env
  const user = await c.env.DB
    .prepare('SELECT * FROM users WHERE id = ?')
    .bind(c.req.param('id'))
    .first();
  return c.json(user);
});
```

## Best Practices Summary

1. **Design first** - Write OpenAPI spec before code for public APIs
2. **Validate at boundaries** - Use Zod for all external input
3. **Consistent errors** - Follow RFC 9457 format, include actionable details
4. **Version from day one** - URL path versioning is simplest
5. **Cursor pagination** - Use for any dataset that may grow
6. **Rate limit everything** - Protect both public and internal endpoints
7. **Type everything** - Zod schemas are single source of truth
8. **Test contracts** - Consumer-driven contract tests prevent breaking changes

---

*Skill Version: 1.0*
