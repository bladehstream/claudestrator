---
name: Serverless Infrastructure
id: serverless_infrastructure
version: 1.0
category: implementation
domain: [cloudflare, serverless, backend, typescript]
task_types: [implementation, deployment, design]
keywords: [cloudflare, workers, serverless, hono, kv, d1, r2, durable objects, wrangler, edge, cron, deployment]
complexity: [normal, complex]
pairs_with: [api_development, databases, backend_security]
source: backend-skills/serverless-infrastructure/SKILL-serverless-infrastructure.md
---

# Serverless Infrastructure Skill

Build and deploy serverless applications on Cloudflare Workers with TypeScript, Hono framework, and platform bindings.

## Quick Reference

### Project Setup
```bash
# Create new Workers project
npm create cloudflare@latest my-api -- --template hono

# Or add to existing project
npm install hono wrangler --save-dev
npx wrangler init
```

### Essential wrangler.toml
```toml
name = "my-api"
main = "src/index.ts"
compatibility_date = "2024-12-01"
compatibility_flags = ["nodejs_compat"]

[vars]
ENVIRONMENT = "development"

[[kv_namespaces]]
binding = "CACHE"
id = "abc123"

[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "def456"

[[r2_buckets]]
binding = "STORAGE"
bucket_name = "my-bucket"

[triggers]
crons = ["0 */6 * * *"]
```

### Basic Hono App with Bindings
```typescript
import { Hono } from 'hono';

type Bindings = {
  DB: D1Database;
  CACHE: KVNamespace;
  STORAGE: R2Bucket;
  ENVIRONMENT: string;
};

const app = new Hono<{ Bindings: Bindings }>();

app.get('/health', (c) => c.json({ status: 'ok' }));

export default app;
```

## When to Use Each Binding

| Binding | Use Case | Limits | Cost Model |
|---------|----------|--------|------------|
| **KV** | Session data, config, cache | 1 write/sec per key, 25MB value | Reads cheap, writes cost more |
| **D1** | Relational data, queries | 10GB per DB, 10M rows | Row reads/writes |
| **R2** | Files, media, backups | 5TB per object | Storage + operations, zero egress |
| **Durable Objects** | Real-time, WebSockets, coordination | Single-threaded per ID | Duration + requests |
| **Queues** | Background jobs, webhooks | 100 messages/batch | Messages processed |

## Decision Guide

### Framework Choice
- **Hono** → Default choice for Workers (fast, typed, middleware ecosystem)
- **itty-router** → Minimal routing only (smaller bundle)
- **Raw Workers** → Maximum control, no dependencies

### Database Choice
- **D1** → Primary relational data (SQLite, familiar SQL)
- **KV** → High-read, low-write data (config, sessions, cache)
- **R2** → Binary/large objects (files, images, exports)
- **Durable Objects** → Real-time state, WebSockets, rate limiting

### When NOT to Use Workers
- Long-running processes (>30s CPU time)
- Heavy compute (ML inference, video processing)
- Large memory requirements (>128MB)
- Need for persistent connections to traditional databases

## File Structure
```
project/
├── src/
│   ├── index.ts           # Entry point, app export
│   ├── routes/            # Route handlers
│   ├── middleware/        # Custom middleware
│   ├── services/          # Business logic
│   └── lib/               # Utilities
├── wrangler.toml          # Workers configuration
├── worker-configuration.d.ts  # Generated types
└── migrations/            # D1 migrations
```

## Reference Documents

| Document | Contents |
|----------|----------|
| [workers-typescript.md](./references/workers-typescript.md) | TypeScript setup, type generation, module format |
| [bindings-kv.md](./references/bindings-kv.md) | KV namespace patterns, caching, sessions |
| [bindings-d1.md](./references/bindings-d1.md) | D1 database, migrations, query patterns |
| [bindings-r2.md](./references/bindings-r2.md) | R2 object storage, uploads, presigned URLs |
| [bindings-durable-objects.md](./references/bindings-durable-objects.md) | Stateful Workers, WebSockets, coordination |
| [hono-workers.md](./references/hono-workers.md) | Hono setup, middleware, routing patterns |
| [cron-triggers.md](./references/cron-triggers.md) | Scheduled tasks, Workflows, background jobs |
| [deployment.md](./references/deployment.md) | CI/CD, environments, secrets management |

## Common Patterns

### Environment-Based Configuration
```typescript
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Bindings }>();

app.use('*', async (c, next) => {
  // Access env vars through bindings
  const isProd = c.env.ENVIRONMENT === 'production';
  c.set('isProd', isProd);
  await next();
});
```

### Error Handling
```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return err.getResponse();
  }
  console.error(err);
  return c.json({ error: 'Internal Server Error' }, 500);
});
```

### Request Validation with Zod
```typescript
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

app.post('/users',
  zValidator('json', CreateUserSchema),
  async (c) => {
    const data = c.req.valid('json');
    // data is typed as { email: string; name: string }
  }
);
```

## Development Commands

```bash
# Generate types from wrangler.toml
npx wrangler types

# Local development with remote bindings
npx wrangler dev --remote

# Test cron triggers locally
npx wrangler dev --test-scheduled
# Then visit: http://localhost:8787/__scheduled

# Deploy to production
npx wrangler deploy

# Deploy to staging
npx wrangler deploy --env staging

# Tail production logs
npx wrangler tail
```

## Security Checklist

- [ ] Secrets in `wrangler secret put`, never in wrangler.toml
- [ ] CORS configured for specific origins in production
- [ ] Rate limiting on public endpoints (use Durable Objects or external service)
- [ ] Input validation on all user data (Zod + zValidator)
- [ ] Error messages don't leak internal details
- [ ] Sensitive headers stripped from responses
- [ ] D1 queries use parameterized statements (never string concatenation)

---

*Skill Version: 1.0*
