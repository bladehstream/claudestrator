# Secrets Management

Securely store, access, and manage sensitive configuration like API keys, database credentials, and encryption keys.

## Core Principles

1. **Never commit secrets to version control**
2. **Use environment-specific secrets**
3. **Rotate secrets regularly**
4. **Principle of least privilege**
5. **Audit secret access**

## Cloudflare Workers Secrets

### Setting Secrets

```bash
# Interactive (prompts for value - recommended)
npx wrangler secret put API_KEY

# From stdin (for scripts)
echo "secret-value" | npx wrangler secret put API_KEY

# Per environment
npx wrangler secret put API_KEY --env staging
npx wrangler secret put API_KEY --env production

# List secrets (values not shown)
npx wrangler secret list

# Delete secret
npx wrangler secret delete API_KEY
```

### Bulk Secrets
```bash
# Create .env.production (never commit!)
# Add to .gitignore first
echo ".env.production" >> .gitignore

# Upload all secrets at once
npx wrangler secret bulk .env.production --env production
```

### Accessing Secrets in Code

```typescript
interface Env {
  // Environment variables (from wrangler.toml [vars])
  ENVIRONMENT: string;
  API_URL: string;
  
  // Secrets (from wrangler secret put)
  API_KEY: string;
  DATABASE_URL: string;
  JWT_SECRET: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Secrets available just like env vars
    const apiKey = env.API_KEY;
    
    // Use in API calls
    const response = await fetch('https://api.example.com/data', {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
    });
    
    return new Response('OK');
  },
};
```

### With Hono

```typescript
import { Hono } from 'hono';

interface Env {
  API_KEY: string;
  DATABASE_URL: string;
}

const app = new Hono<{ Bindings: Env }>();

app.get('/data', async (c) => {
  // Access via c.env
  const apiKey = c.env.API_KEY;
  
  // Never log secrets!
  // console.log(apiKey); // DON'T DO THIS
  
  return c.json({ status: 'ok' });
});
```

## Local Development

### .dev.vars File

```bash
# .dev.vars (in project root, gitignored)
API_KEY=dev-api-key-12345
DATABASE_URL=postgresql://localhost:5432/dev
JWT_SECRET=dev-jwt-secret-not-for-production
STRIPE_SECRET_KEY=sk_test_xxxxx
```

### .gitignore Setup

```gitignore
# Secrets files
.dev.vars
.dev.vars.*
.env
.env.*
!.env.example

# Wrangler state
.wrangler/
```

### Environment-Specific Secrets

```bash
# .dev.vars.staging
API_KEY=staging-api-key
DATABASE_URL=postgresql://staging-db:5432/app

# .dev.vars.production
API_KEY=production-api-key
DATABASE_URL=postgresql://prod-db:5432/app
```

```bash
# Use specific environment locally
npx wrangler dev --env staging
```

## wrangler.toml Configuration

```toml
name = "my-api"
main = "src/index.ts"

# NON-SENSITIVE configuration only
[vars]
ENVIRONMENT = "development"
API_URL = "https://api.example.com"
LOG_LEVEL = "debug"

# NEVER put secrets here!
# API_KEY = "secret"  # WRONG!

# Per-environment config
[env.staging.vars]
ENVIRONMENT = "staging"
API_URL = "https://staging-api.example.com"
LOG_LEVEL = "info"

[env.production.vars]
ENVIRONMENT = "production"
API_URL = "https://api.example.com"
LOG_LEVEL = "warn"
```

## Secret Rotation

### Strategy

1. **Add new secret** alongside old one
2. **Update code** to use new secret
3. **Deploy changes**
4. **Remove old secret**

### Implementation

```typescript
interface Env {
  // Support both during rotation
  API_KEY: string;
  API_KEY_NEW?: string;  // Optional during rotation
}

async function callExternalApi(env: Env): Promise<Response> {
  // Try new key first if available
  const apiKey = env.API_KEY_NEW || env.API_KEY;
  
  return fetch('https://api.example.com', {
    headers: { 'Authorization': `Bearer ${apiKey}` },
  });
}
```

### Rotation Script

```bash
#!/bin/bash
# rotate-secret.sh

# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Add as new secret
echo "$NEW_SECRET" | npx wrangler secret put API_KEY_NEW --env production

# 3. After deployment and verification
# npx wrangler secret delete API_KEY_NEW --env production
# echo "$NEW_SECRET" | npx wrangler secret put API_KEY --env production
```

## Secret Validation at Startup

```typescript
import { z } from 'zod';

const EnvSchema = z.object({
  // Required secrets
  API_KEY: z.string().min(32, 'API_KEY must be at least 32 characters'),
  JWT_SECRET: z.string().min(64, 'JWT_SECRET must be at least 64 characters'),
  DATABASE_URL: z.string().url('DATABASE_URL must be a valid URL'),
  
  // Optional with defaults
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

function validateEnv(env: unknown): z.infer<typeof EnvSchema> {
  const result = EnvSchema.safeParse(env);
  
  if (!result.success) {
    console.error('Environment validation failed:', result.error.format());
    throw new Error('Invalid environment configuration');
  }
  
  return result.data;
}

// Use in handler
export default {
  async fetch(request: Request, env: unknown): Promise<Response> {
    const validEnv = validateEnv(env);
    // Now use validEnv with type safety
  },
};
```

## Secrets in CI/CD (GitHub Actions)

### Setting Secrets

1. Go to Repository → Settings → Secrets and variables → Actions
2. Add secrets: `CF_API_TOKEN`, `PRODUCTION_API_KEY`, etc.

### Using in Workflows

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - run: npm ci
      
      # Set secrets before deploy
      - name: Set Production Secrets
        run: |
          echo "${{ secrets.PRODUCTION_API_KEY }}" | npx wrangler secret put API_KEY --env production
          echo "${{ secrets.PRODUCTION_JWT_SECRET }}" | npx wrangler secret put JWT_SECRET --env production
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
      
      - name: Deploy
        run: npx wrangler deploy --env production
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
```

## Secrets Store (Account-Level)

For secrets shared across multiple Workers:

```toml
# wrangler.toml
[[secrets_store_bindings]]
binding = "SHARED_SECRETS"
store_id = "your-store-id"
```

```typescript
interface Env {
  SHARED_SECRETS: SecretsStore;
}

app.get('/data', async (c) => {
  const apiKey = await c.env.SHARED_SECRETS.get('SHARED_API_KEY');
  // Use shared secret
});
```

## Security Best Practices

### Do's

```typescript
// ✅ Use environment variables
const apiKey = env.API_KEY;

// ✅ Validate secrets exist
if (!env.API_KEY) {
  throw new Error('API_KEY not configured');
}

// ✅ Use secrets for authentication
const authHeader = `Bearer ${env.API_KEY}`;

// ✅ Use strong secrets
// Generate with: openssl rand -base64 32
```

### Don'ts

```typescript
// ❌ Never hardcode secrets
const apiKey = 'sk_live_xxxxx';  // WRONG!

// ❌ Never log secrets
console.log('API Key:', env.API_KEY);  // WRONG!

// ❌ Never include in error messages
throw new Error(`Auth failed with key ${apiKey}`);  // WRONG!

// ❌ Never expose in responses
return c.json({ apiKey: env.API_KEY });  // WRONG!

// ❌ Never commit to git
// Even in "private" repos
```

### Error Handling Without Leaking Secrets

```typescript
async function callExternalApi(env: Env): Promise<Data> {
  try {
    const response = await fetch('https://api.example.com', {
      headers: { 'Authorization': `Bearer ${env.API_KEY}` },
    });
    
    if (!response.ok) {
      // Log without secret
      console.error('External API error:', response.status);
      throw new Error('External API unavailable');
    }
    
    return response.json();
  } catch (error) {
    // Never include secret in error
    console.error('API call failed:', error);
    throw new Error('Failed to fetch data');
  }
}
```

## Audit and Monitoring

### Log Secret Access (Not Values)

```typescript
function useSecret(secretName: string, env: Record<string, string>): string {
  const value = env[secretName];
  
  if (!value) {
    console.error(`Secret ${secretName} not found`);
    throw new Error('Configuration error');
  }
  
  // Log access, not value
  console.log(`Accessed secret: ${secretName}`);
  
  return value;
}
```

### Monitor Failed Auth Attempts

```typescript
app.use('*', async (c, next) => {
  try {
    await next();
  } catch (error) {
    if (error instanceof HTTPException && error.status === 401) {
      console.log({
        event: 'auth_failure',
        ip: c.req.header('cf-connecting-ip'),
        path: c.req.path,
        timestamp: new Date().toISOString(),
      });
    }
    throw error;
  }
});
```

## Summary Checklist

- [ ] Secrets in `wrangler secret put`, never in wrangler.toml
- [ ] `.dev.vars` for local development, in `.gitignore`
- [ ] Different secrets per environment
- [ ] Secrets validated at startup
- [ ] No secrets in logs or error messages
- [ ] CI/CD uses GitHub Secrets
- [ ] Regular secret rotation schedule
- [ ] Audit trail for secret access
- [ ] Strong secret values (32+ characters)
- [ ] Least privilege principle applied
