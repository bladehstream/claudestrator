# Cloudflare Workers Deployment and CI/CD

Deploy Workers to production with environments, secrets management, and automated pipelines.

## Deployment Basics

### Manual Deployment
```bash
# Deploy to production
npx wrangler deploy

# Deploy to specific environment
npx wrangler deploy --env staging
npx wrangler deploy --env production

# Dry run (show what would be deployed)
npx wrangler deploy --dry-run

# Deploy specific file
npx wrangler deploy src/index.ts
```

### Version Information
```bash
# View deployment details
npx wrangler deployments list

# View specific deployment
npx wrangler deployments view <deployment-id>

# Rollback to previous version
npx wrangler rollback
```

## Environments

### wrangler.toml Configuration
```toml
# Base configuration (development)
name = "my-api"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[vars]
ENVIRONMENT = "development"
LOG_LEVEL = "debug"

[[kv_namespaces]]
binding = "CACHE"
id = "dev-kv-id"

[[d1_databases]]
binding = "DB"
database_name = "my-db-dev"
database_id = "dev-db-id"

# Staging environment
[env.staging]
name = "my-api-staging"

[env.staging.vars]
ENVIRONMENT = "staging"
LOG_LEVEL = "info"

[[env.staging.kv_namespaces]]
binding = "CACHE"
id = "staging-kv-id"

[[env.staging.d1_databases]]
binding = "DB"
database_name = "my-db-staging"
database_id = "staging-db-id"

# Production environment
[env.production]
name = "my-api-production"
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" }
]

[env.production.vars]
ENVIRONMENT = "production"
LOG_LEVEL = "warn"

[[env.production.kv_namespaces]]
binding = "CACHE"
id = "production-kv-id"

[[env.production.d1_databases]]
binding = "DB"
database_name = "my-db-production"
database_id = "production-db-id"
```

### Environment-Specific Commands
```bash
# Deploy to environments
npx wrangler deploy --env staging
npx wrangler deploy --env production

# Run locally with environment config
npx wrangler dev --env staging

# Execute D1 migrations per environment
npx wrangler d1 migrations apply my-db-dev --local
npx wrangler d1 migrations apply my-db-staging --env staging --remote
npx wrangler d1 migrations apply my-db-production --env production --remote

# Tail logs per environment
npx wrangler tail --env production
```

## Secrets Management

### Setting Secrets
```bash
# Interactive (prompts for value)
npx wrangler secret put API_KEY

# From stdin
echo "my-secret-value" | npx wrangler secret put API_KEY

# Per environment
npx wrangler secret put API_KEY --env staging
npx wrangler secret put API_KEY --env production

# List secrets
npx wrangler secret list
npx wrangler secret list --env production

# Delete secret
npx wrangler secret delete API_KEY
```

### Bulk Secrets (from .env)
```bash
# Create .env file (never commit!)
# .env.production
API_KEY=secret-api-key
DATABASE_URL=postgres://...
STRIPE_SECRET=sk_live_...

# Bulk upload
npx wrangler secret bulk .env.production --env production
```

### Accessing Secrets
```typescript
// Secrets are available in env just like vars
interface Env {
  // From [vars]
  ENVIRONMENT: string;
  
  // From secrets
  API_KEY: string;
  DATABASE_URL: string;
}

app.get('/test', (c) => {
  const apiKey = c.env.API_KEY;  // Secret value
  return c.json({ hasKey: !!apiKey });
});
```

### Secret Best Practices
```toml
# wrangler.toml - NEVER put secrets here!
[vars]
ENVIRONMENT = "production"    # OK - not sensitive
API_URL = "https://api.com"   # OK - not sensitive
# API_KEY = "secret"          # NEVER - use wrangler secret put
```

## Routes and Custom Domains

### Route Configuration
```toml
# Single route
route = "api.example.com/*"

# Multiple routes
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" },
  { pattern = "api.example.org/*", zone_name = "example.org" },
]

# Zone ID instead of name
routes = [
  { pattern = "api.example.com/*", zone_id = "abc123" }
]

# Custom domain (requires DNS setup)
routes = [
  { pattern = "api.example.com", custom_domain = true }
]
```

### workers.dev Subdomain
```toml
# Enable workers.dev URL
workers_dev = true  # Available at my-api.username.workers.dev

# Disable in production
[env.production]
workers_dev = false
routes = [{ pattern = "api.example.com/*", zone_name = "example.com" }]
```

## GitHub Actions CI/CD

### Basic Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - run: npm ci
      
      - run: npm run typecheck
      
      - run: npm test
      
      # Deploy to staging on PR
      - name: Deploy to Staging
        if: github.event_name == 'pull_request'
        run: npx wrangler deploy --env staging
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
      
      # Deploy to production on main
      - name: Deploy to Production
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: npx wrangler deploy --env production
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
```

### With D1 Migrations
```yaml
# .github/workflows/deploy.yml
name: Deploy with Migrations

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
          cache: 'npm'
      
      - run: npm ci
      
      # Run migrations first
      - name: Run D1 Migrations
        run: npx wrangler d1 migrations apply my-db-production --env production --remote
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
      
      # Then deploy
      - name: Deploy
        run: npx wrangler deploy --env production
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
```

### Multi-Environment Pipeline
```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run typecheck
      - run: npm test

  deploy-preview:
    needs: test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Deploy Preview
        run: |
          npx wrangler deploy --env preview \
            --var GIT_SHA:${{ github.sha }} \
            --var PR_NUMBER:${{ github.event.pull_request.number }}
      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚀 Preview deployed to https://my-api-preview.username.workers.dev'
            })

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npx wrangler d1 migrations apply my-db-staging --env staging --remote
      - run: npx wrangler deploy --env staging

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npx wrangler d1 migrations apply my-db-production --env production --remote
      - run: npx wrangler deploy --env production
```

### Creating API Token

1. Go to Cloudflare Dashboard → My Profile → API Tokens
2. Create Token → Use template "Edit Cloudflare Workers"
3. Permissions needed:
   - Account: Workers Scripts (Edit)
   - Account: Workers KV Storage (Edit)
   - Account: Workers R2 Storage (Edit)
   - Account: D1 (Edit)
   - Zone: Workers Routes (Edit) - if using custom domains
4. Copy token and add to GitHub Secrets as `CF_API_TOKEN`

## Wrangler Configuration Reference

### Complete wrangler.toml
```toml
# Required
name = "my-api"
main = "src/index.ts"
compatibility_date = "2024-12-01"

# Optional - runtime configuration
compatibility_flags = ["nodejs_compat"]
node_compat = true  # Deprecated, use nodejs_compat flag
workers_dev = true
account_id = "your-account-id"

# Build configuration
[build]
command = "npm run build"
cwd = "."
watch_dir = "src"

# Variables (non-sensitive)
[vars]
ENVIRONMENT = "development"
API_VERSION = "v1"

# KV Namespaces
[[kv_namespaces]]
binding = "CACHE"
id = "abc123"
preview_id = "def456"

# D1 Databases
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "xyz789"

# R2 Buckets
[[r2_buckets]]
binding = "STORAGE"
bucket_name = "my-bucket"
preview_bucket_name = "my-bucket-preview"

# Durable Objects
[[durable_objects.bindings]]
name = "RATE_LIMITER"
class_name = "RateLimiter"

[[migrations]]
tag = "v1"
new_classes = ["RateLimiter"]

# Queues
[[queues.producers]]
binding = "MY_QUEUE"
queue = "my-queue"

[[queues.consumers]]
queue = "my-queue"
max_batch_size = 10
max_batch_timeout = 30
max_retries = 3
dead_letter_queue = "my-dlq"

# Cron Triggers
[triggers]
crons = ["0 * * * *", "0 0 * * *"]

# Routes
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" }
]

# Limits
[limits]
cpu_ms = 50

# Placement
[placement]
mode = "smart"

# Observability
[observability]
enabled = true

# Tail consumers
[[tail_consumers]]
service = "log-collector"
```

## Deployment Strategies

### Blue-Green Deployment
```bash
# Deploy new version with different name
npx wrangler deploy --name my-api-blue --env production

# Test the new deployment
curl https://my-api-blue.username.workers.dev/health

# Switch routes
# Update wrangler.toml routes or use dashboard

# Rollback if needed
npx wrangler deploy --name my-api-green --env production
```

### Gradual Rollout
```typescript
// Use weighted routing in Worker
export default {
  async fetch(request: Request, env: Env) {
    // 10% to new version
    if (Math.random() < 0.1) {
      return handleNewVersion(request, env);
    }
    return handleCurrentVersion(request, env);
  },
};
```

### Feature Flags
```typescript
interface Env {
  CACHE: KVNamespace;
}

async function getFeatureFlags(env: Env): Promise<Record<string, boolean>> {
  const flags = await env.CACHE.get('feature-flags', 'json');
  return flags || {};
}

app.use('*', async (c, next) => {
  const flags = await getFeatureFlags(c.env);
  c.set('features', flags);
  await next();
});

app.get('/new-feature', async (c) => {
  const features = c.get('features');
  
  if (!features.newFeatureEnabled) {
    return c.json({ error: 'Feature not available' }, 404);
  }
  
  return c.json({ data: 'New feature response' });
});
```

## Monitoring Deployments

### Tail Logs
```bash
# Follow all logs
npx wrangler tail

# Filter by status
npx wrangler tail --status error

# Filter by IP
npx wrangler tail --ip-address 1.2.3.4

# JSON format for parsing
npx wrangler tail --format json

# Specific environment
npx wrangler tail --env production
```

### Health Checks
```typescript
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    version: c.env.GIT_SHA || 'unknown',
    environment: c.env.ENVIRONMENT,
    timestamp: new Date().toISOString(),
  });
});

app.get('/ready', async (c) => {
  try {
    // Check dependencies
    await c.env.DB.prepare('SELECT 1').first();
    await c.env.CACHE.get('health-check');
    
    return c.json({ status: 'ready' });
  } catch (error) {
    return c.json({ status: 'not ready', error: String(error) }, 503);
  }
});
```

## Best Practices

1. **Use environments** - Separate dev/staging/production configs
2. **Never commit secrets** - Use `wrangler secret put`
3. **Run migrations first** - Before deploying new code
4. **Test in staging** - Mirror production environment
5. **Use version info** - Include GIT_SHA in deployments
6. **Monitor after deploy** - Tail logs, check metrics
7. **Automate everything** - CI/CD for all environments
8. **Have rollback plan** - Use `wrangler rollback` or blue-green
9. **Use environment protection** - GitHub environment approvals for prod
10. **Document routes** - Keep DNS and route configs in sync
