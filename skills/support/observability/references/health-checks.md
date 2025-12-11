# Health Checks

Implement liveness and readiness probes for monitoring application health and enabling graceful orchestration.

## Two Types of Health Checks

| Type | Purpose | Endpoint | Failure Action |
|------|---------|----------|----------------|
| **Liveness** | Is the process alive? | `/livez` | Restart container |
| **Readiness** | Can it accept traffic? | `/readyz` | Remove from load balancer |

### Key Difference
- Liveness failing = restart the application
- Readiness failing = stop sending traffic but don't restart

## Basic Implementation

### Liveness Probe (Simple)
```typescript
// Liveness should be simple - no external dependencies
app.get('/livez', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
  });
});
```

### Readiness Probe (With Dependencies)
```typescript
app.get('/readyz', async (c) => {
  const checks: Record<string, boolean> = {};
  let allHealthy = true;

  // Check database
  try {
    await c.env.DB.prepare('SELECT 1').first();
    checks.database = true;
  } catch {
    checks.database = false;
    allHealthy = false;
  }

  // Check KV (if critical)
  try {
    await c.env.KV.get('health-check-key');
    checks.kv = true;
  } catch {
    checks.kv = false;
    allHealthy = false;
  }

  return c.json({
    status: allHealthy ? 'ok' : 'error',
    checks,
    timestamp: new Date().toISOString(),
  }, allHealthy ? 200 : 503);
});
```

## Comprehensive Health Check Service

```typescript
interface HealthCheckResult {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  duration_ms: number;
  message?: string;
}

interface HealthStatus {
  status: 'pass' | 'fail' | 'warn';
  version?: string;
  checks: Record<string, HealthCheckResult>;
  timestamp: string;
}

type HealthChecker = () => Promise<void>;

class HealthCheckService {
  private checks: Map<string, HealthChecker> = new Map();

  addCheck(name: string, checker: HealthChecker) {
    this.checks.set(name, checker);
  }

  async runChecks(): Promise<HealthStatus> {
    const results: Record<string, HealthCheckResult> = {};
    let overallStatus: 'pass' | 'fail' | 'warn' = 'pass';

    for (const [name, checker] of this.checks) {
      const startTime = Date.now();
      try {
        await checker();
        results[name] = {
          name,
          status: 'pass',
          duration_ms: Date.now() - startTime,
        };
      } catch (error) {
        results[name] = {
          name,
          status: 'fail',
          duration_ms: Date.now() - startTime,
          message: error instanceof Error ? error.message : 'Unknown error',
        };
        overallStatus = 'fail';
      }
    }

    return {
      status: overallStatus,
      checks: results,
      timestamp: new Date().toISOString(),
    };
  }
}

// Usage
const healthService = new HealthCheckService();

healthService.addCheck('database', async () => {
  const result = await env.DB.prepare('SELECT 1').first();
  if (!result) throw new Error('Database query failed');
});

healthService.addCheck('external-api', async () => {
  const response = await fetch('https://api.example.com/health', {
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`API returned ${response.status}`);
});

app.get('/readyz', async (c) => {
  const status = await healthService.runChecks();
  return c.json(status, status.status === 'pass' ? 200 : 503);
});
```

## Hono Health Check Middleware

```typescript
import { createMiddleware } from 'hono/factory';

interface HealthOptions {
  path?: string;
  checker?: (env: Env) => Promise<boolean>;
}

export const livenessProbe = (options: HealthOptions = {}) => {
  const path = options.path || '/livez';
  
  return createMiddleware(async (c, next) => {
    if (c.req.path === path && c.req.method === 'GET') {
      return c.json({ status: 'ok', timestamp: new Date().toISOString() });
    }
    await next();
  });
};

export const readinessProbe = (options: HealthOptions = {}) => {
  const path = options.path || '/readyz';
  
  return createMiddleware(async (c, next) => {
    if (c.req.path === path && c.req.method === 'GET') {
      try {
        const healthy = options.checker 
          ? await options.checker(c.env)
          : true;
        
        return c.json(
          { status: healthy ? 'ok' : 'error', timestamp: new Date().toISOString() },
          healthy ? 200 : 503
        );
      } catch (error) {
        return c.json(
          { status: 'error', error: 'Health check failed' },
          503
        );
      }
    }
    await next();
  });
};

// Usage
app.use(livenessProbe());
app.use(readinessProbe({
  checker: async (env) => {
    await env.DB.prepare('SELECT 1').first();
    return true;
  },
}));
```

## Dependency-Specific Checks

### D1 Database Check
```typescript
async function checkD1(db: D1Database): Promise<boolean> {
  try {
    const result = await db.prepare('SELECT 1 as health').first<{ health: number }>();
    return result?.health === 1;
  } catch {
    return false;
  }
}
```

### KV Check
```typescript
async function checkKV(kv: KVNamespace): Promise<boolean> {
  try {
    // Use a dedicated health check key
    await kv.put('__health__', Date.now().toString());
    const value = await kv.get('__health__');
    return value !== null;
  } catch {
    return false;
  }
}
```

### External API Check
```typescript
async function checkExternalAPI(url: string, timeoutMs = 5000): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    const response = await fetch(url, {
      method: 'HEAD',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}
```

### R2 Check
```typescript
async function checkR2(bucket: R2Bucket): Promise<boolean> {
  try {
    // List a single object to verify connectivity
    await bucket.list({ limit: 1 });
    return true;
  } catch {
    return false;
  }
}
```

## Caching Expensive Checks

```typescript
interface CachedCheck {
  result: boolean;
  timestamp: number;
}

const checkCache = new Map<string, CachedCheck>();
const CACHE_TTL_MS = 10000; // 10 seconds

async function cachedCheck(
  name: string,
  checker: () => Promise<boolean>
): Promise<boolean> {
  const cached = checkCache.get(name);
  const now = Date.now();
  
  if (cached && now - cached.timestamp < CACHE_TTL_MS) {
    return cached.result;
  }
  
  const result = await checker();
  checkCache.set(name, { result, timestamp: now });
  return result;
}

// Usage in readiness check
app.get('/readyz', async (c) => {
  const dbHealthy = await cachedCheck('database', () => checkD1(c.env.DB));
  
  return c.json({
    status: dbHealthy ? 'ok' : 'error',
    checks: { database: dbHealthy },
  }, dbHealthy ? 200 : 503);
});
```

## Health Response Formats

### Simple Format
```json
{
  "status": "ok"
}
```

### Detailed Format (RFC Health Check Draft)
```json
{
  "status": "pass",
  "version": "1.0.0",
  "releaseId": "abc123",
  "notes": [],
  "output": "",
  "checks": {
    "database:responseTime": {
      "componentType": "datastore",
      "observedValue": 25,
      "observedUnit": "ms",
      "status": "pass",
      "time": "2024-01-15T12:00:00Z"
    },
    "memory:utilization": {
      "componentType": "system",
      "observedValue": 65,
      "observedUnit": "percent",
      "status": "warn",
      "time": "2024-01-15T12:00:00Z"
    }
  }
}
```

## Best Practices

### Do's
```typescript
// ✅ Keep liveness simple - no external deps
app.get('/livez', (c) => c.json({ status: 'ok' }));

// ✅ Add timeouts to readiness checks
const checkWithTimeout = async (checker: () => Promise<boolean>, ms = 5000) => {
  const timeout = new Promise<boolean>((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), ms)
  );
  return Promise.race([checker(), timeout]);
};

// ✅ Return appropriate status codes
// 200 = healthy, 503 = unhealthy

// ✅ Include timestamps for debugging
{
  status: 'ok',
  timestamp: new Date().toISOString()
}
```

### Don'ts
```typescript
// ❌ Don't include external deps in liveness
app.get('/livez', async (c) => {
  await c.env.DB.prepare('SELECT 1').first(); // Wrong!
  return c.json({ status: 'ok' });
});

// ❌ Don't expose sensitive info
app.get('/readyz', async (c) => {
  return c.json({
    status: 'ok',
    dbConnectionString: c.env.DATABASE_URL, // Never!
  });
});

// ❌ Don't make checks too expensive
// Cache results for expensive operations
```

## Kubernetes Configuration (Reference)

```yaml
# For when deploying to Kubernetes
spec:
  containers:
    - name: api
      livenessProbe:
        httpGet:
          path: /livez
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /readyz
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        timeoutSeconds: 3
        failureThreshold: 3
```

## Cloudflare Workers Specifics

Workers are ephemeral - health checks work differently:

```typescript
// Workers don't need traditional liveness/readiness
// But these endpoints are useful for:
// 1. External monitoring services
// 2. Load balancer health checks
// 3. Debugging connectivity issues

app.get('/health', async (c) => {
  // Simple health check
  return c.json({
    status: 'ok',
    environment: c.env.ENVIRONMENT,
    region: c.req.header('cf-ray')?.split('-')[1] || 'unknown',
  });
});

// Deep health check for debugging
app.get('/health/deep', async (c) => {
  const checks: Record<string, unknown> = {};
  
  // D1
  try {
    const start = Date.now();
    await c.env.DB.prepare('SELECT 1').first();
    checks.d1 = { status: 'ok', latency_ms: Date.now() - start };
  } catch (e) {
    checks.d1 = { status: 'error', error: (e as Error).message };
  }
  
  // KV
  try {
    const start = Date.now();
    await c.env.KV.get('__health__');
    checks.kv = { status: 'ok', latency_ms: Date.now() - start };
  } catch (e) {
    checks.kv = { status: 'error', error: (e as Error).message };
  }
  
  const allOk = Object.values(checks).every(
    (c: any) => c.status === 'ok'
  );
  
  return c.json({
    status: allOk ? 'ok' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
  }, allOk ? 200 : 503);
});
```

## Monitoring Integration

```typescript
// Log health check results for monitoring
app.get('/readyz', async (c) => {
  const status = await runHealthChecks(c.env);
  
  // Log for monitoring systems to pick up
  console.log(JSON.stringify({
    type: 'health_check',
    status: status.status,
    checks: status.checks,
    timestamp: new Date().toISOString(),
  }));
  
  return c.json(status, status.status === 'pass' ? 200 : 503);
});
```
