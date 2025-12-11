# Cloudflare Workers TypeScript Configuration

Comprehensive guide to TypeScript setup for Cloudflare Workers with type generation, module formats, and Node.js compatibility.

## Type Generation (Recommended Approach)

Since wrangler 3.x, the recommended approach is generating types from your wrangler.toml rather than manually installing type packages.

### Generate Runtime Types
```bash
# Generates worker-configuration.d.ts based on wrangler.toml
npx wrangler types
```

This creates types for:
- All bindings (KV, D1, R2, Durable Objects, etc.)
- Environment variables defined in `[vars]`
- Compatibility flags and date features

### Generated File Structure
```typescript
// worker-configuration.d.ts (auto-generated)
interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
  STORAGE: R2Bucket;
  API_KEY: string;
}
```

### tsconfig.json Setup
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["@cloudflare/workers-types"],
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true
  },
  "include": ["src/**/*", "worker-configuration.d.ts"],
  "exclude": ["node_modules"]
}
```

## Module Worker Format

Workers use ES Module format (not Service Worker format):

### Correct: Module Worker
```typescript
// src/index.ts
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response('Hello World');
  },
  
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    // Cron handler
  },
};
```

### Incorrect: Service Worker Format (Legacy)
```typescript
// DON'T USE - legacy format
addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});
```

## Node.js Compatibility

Enable Node.js APIs with the compatibility flag:

### wrangler.toml
```toml
compatibility_flags = ["nodejs_compat"]
```

### Install Node Types
```bash
npm install -D @types/node
```

### Update tsconfig.json
```json
{
  "compilerOptions": {
    "types": ["@cloudflare/workers-types", "node"]
  }
}
```

### Available Node.js APIs
```typescript
// These work with nodejs_compat
import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';
import { EventEmitter } from 'node:events';
import { Readable, Writable } from 'node:stream';
import { URL, URLSearchParams } from 'node:url';
import { TextEncoder, TextDecoder } from 'node:util';
```

### Not Available (Requires Polyfills)
```typescript
// These DON'T work - need alternatives
import fs from 'node:fs';      // Use R2/KV instead
import net from 'node:net';    // Use fetch/WebSockets
import child_process from 'node:child_process'; // Not available
```

## Typing Patterns

### Typed Env Object
```typescript
// types.ts
export interface Env {
  // Bindings
  DB: D1Database;
  CACHE: KVNamespace;
  STORAGE: R2Bucket;
  MY_DO: DurableObjectNamespace;
  QUEUE: Queue<QueueMessage>;
  
  // Environment variables
  ENVIRONMENT: 'development' | 'staging' | 'production';
  API_SECRET: string;
}

export interface QueueMessage {
  type: 'email' | 'webhook';
  payload: unknown;
}
```

### Typed with Hono
```typescript
import { Hono } from 'hono';
import type { Env } from './types';

// Type the app with bindings
const app = new Hono<{ Bindings: Env }>();

app.get('/', (c) => {
  // c.env is fully typed
  const db = c.env.DB;
  const isProd = c.env.ENVIRONMENT === 'production';
  return c.json({ status: 'ok' });
});

export default app;
```

### Typed Request Context
```typescript
import { Hono, Context } from 'hono';

interface Variables {
  user: { id: string; email: string };
  requestId: string;
}

const app = new Hono<{ 
  Bindings: Env; 
  Variables: Variables;
}>();

// Middleware sets typed variables
app.use('*', async (c, next) => {
  c.set('requestId', crypto.randomUUID());
  await next();
});

// Route accesses typed variables
app.get('/me', (c) => {
  const user = c.get('user'); // Typed as { id: string; email: string }
  return c.json(user);
});
```

## Compatibility Dates

The compatibility_date controls which runtime features are available:

### wrangler.toml
```toml
# Use a recent date for latest features
compatibility_date = "2024-12-01"
```

### Feature Availability by Date

| Date | Feature |
|------|---------|
| 2024-09-02 | `nodejs_compat_v2` - Enhanced Node.js compatibility |
| 2024-03-04 | `unwrap_custom_thenables` - Better Promise handling |
| 2023-08-01 | `strict_crypto_checks` - Stricter WebCrypto validation |

### Check Available Features
```bash
# List compatibility flags
npx wrangler types --help
```

## Development vs Production Types

### Conditional Typing
```typescript
// Different behavior per environment
interface DevEnv extends BaseEnv {
  DEBUG: 'true';
}

interface ProdEnv extends BaseEnv {
  DEBUG?: never;
}

type Env = DevEnv | ProdEnv;
```

### Type Guards
```typescript
function isDev(env: Env): env is DevEnv {
  return env.ENVIRONMENT === 'development';
}

app.use('*', async (c, next) => {
  if (isDev(c.env)) {
    console.log('Debug mode enabled');
  }
  await next();
});
```

## Type-Safe Environment Variables

### Runtime Validation with Zod
```typescript
import { z } from 'zod';

const EnvSchema = z.object({
  DB: z.custom<D1Database>(),
  CACHE: z.custom<KVNamespace>(),
  API_SECRET: z.string().min(32),
  ENVIRONMENT: z.enum(['development', 'staging', 'production']),
});

export type Env = z.infer<typeof EnvSchema>;

// Validate at startup
function validateEnv(env: unknown): Env {
  return EnvSchema.parse(env);
}
```

## Common Type Issues

### Issue: Property doesn't exist on Env
```typescript
// Problem: Env not typed
app.get('/', (c) => {
  c.env.DB; // Error: Property 'DB' does not exist
});

// Solution: Type the Hono app
const app = new Hono<{ Bindings: Env }>();
```

### Issue: Cannot find module '@cloudflare/workers-types'
```bash
# Solution: Install types package
npm install -D @cloudflare/workers-types
```

### Issue: Types don't match runtime
```bash
# Solution: Regenerate types from wrangler.toml
npx wrangler types
```

### Issue: Node API not available
```typescript
// Problem: Using Node API without flag
import { Buffer } from 'buffer'; // Might not work

// Solution 1: Add compatibility flag to wrangler.toml
// compatibility_flags = ["nodejs_compat"]

// Solution 2: Use node: prefix
import { Buffer } from 'node:buffer';
```

## Project Template

### package.json
```json
{
  "name": "my-worker",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "types": "wrangler types",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20241205.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.5.0",
    "wrangler": "^3.99.0"
  },
  "dependencies": {
    "hono": "^4.6.0"
  }
}
```

### Pre-commit Type Check
```bash
# Add to CI or pre-commit hook
npm run types && npm run typecheck
```

## Best Practices

1. **Always run `wrangler types`** after modifying wrangler.toml
2. **Use Module Worker format** - Service Worker format is legacy
3. **Enable `nodejs_compat`** if using any Node.js APIs
4. **Type your Hono app** with `Bindings` and `Variables`
5. **Validate env at runtime** with Zod for extra safety
6. **Keep compatibility_date recent** for latest features
7. **Include worker-configuration.d.ts** in tsconfig includes
