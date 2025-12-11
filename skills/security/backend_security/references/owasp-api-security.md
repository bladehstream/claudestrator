# OWASP API Security Top 10

Detailed mitigations for the OWASP API Security Top 10 (2023) vulnerabilities.

## API1:2023 - Broken Object Level Authorization (BOLA)

Users can access objects they don't own by manipulating IDs.

### Vulnerability Example
```typescript
// VULNERABLE: No ownership check
app.get('/api/orders/:orderId', async (c) => {
  const order = await getOrder(c.req.param('orderId'));
  return c.json(order); // Any user can view any order!
});
```

### Mitigation
```typescript
// SECURE: Verify ownership on every request
app.get('/api/orders/:orderId', authMiddleware, async (c) => {
  const user = c.get('user');
  const orderId = c.req.param('orderId');
  
  const order = await getOrder(orderId);
  
  if (!order) {
    return c.json({ error: 'Order not found' }, 404);
  }
  
  // Check ownership
  if (order.userId !== user.id && user.role !== 'admin') {
    return c.json({ error: 'Forbidden' }, 403);
  }
  
  return c.json(order);
});
```

### Authorization Middleware Pattern
```typescript
function ownershipCheck<T extends { userId: string }>(
  getResource: (id: string, env: Env) => Promise<T | null>
) {
  return createMiddleware(async (c, next) => {
    const user = c.get('user');
    const resourceId = c.req.param('id');
    
    const resource = await getResource(resourceId, c.env);
    
    if (!resource) {
      return c.json({ error: 'Not found' }, 404);
    }
    
    if (resource.userId !== user.id && user.role !== 'admin') {
      // Log potential attack
      console.warn({
        event: 'authorization_failure',
        userId: user.id,
        resourceId,
        type: 'BOLA',
      });
      return c.json({ error: 'Forbidden' }, 403);
    }
    
    c.set('resource', resource);
    await next();
  });
}

// Usage
app.get('/orders/:id', 
  authMiddleware, 
  ownershipCheck(getOrder),
  (c) => c.json(c.get('resource'))
);
```

## API2:2023 - Broken Authentication

Weak authentication mechanisms or improper token handling.

### Common Vulnerabilities
- Weak passwords allowed
- No rate limiting on login
- Tokens don't expire
- Secrets in URLs

### Mitigation
```typescript
import { z } from 'zod';

// Strong password validation
const PasswordSchema = z.string()
  .min(12, 'Password must be at least 12 characters')
  .regex(/[A-Z]/, 'Must contain uppercase')
  .regex(/[a-z]/, 'Must contain lowercase')
  .regex(/[0-9]/, 'Must contain number')
  .regex(/[^A-Za-z0-9]/, 'Must contain special character');

// Rate limit login attempts
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  keyGenerator: (c) => c.req.json().then(b => b.email),
});

app.post('/auth/login', loginLimiter, async (c) => {
  const { email, password } = await c.req.json();
  
  const user = await getUserByEmail(email);
  
  // Constant-time comparison to prevent timing attacks
  if (!user || !await verifyPassword(password, user.passwordHash)) {
    // Generic error message
    return c.json({ error: 'Invalid credentials' }, 401);
  }
  
  // Short-lived access token
  const accessToken = await createJwt(user, { expiresIn: '15m' });
  
  // Longer refresh token in httpOnly cookie
  const refreshToken = await createRefreshToken(user);
  
  setCookie(c, 'refresh_token', refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'Strict',
    maxAge: 7 * 24 * 60 * 60, // 7 days
  });
  
  return c.json({ accessToken });
});
```

## API3:2023 - Broken Object Property Level Authorization

Exposing sensitive object properties or allowing unauthorized property updates.

### Vulnerability Example
```typescript
// VULNERABLE: Exposes all properties
app.get('/api/users/:id', async (c) => {
  const user = await getUser(c.req.param('id'));
  return c.json(user); // Includes passwordHash, internalNotes, etc.!
});

// VULNERABLE: Accepts any property
app.patch('/api/users/:id', async (c) => {
  const updates = await c.req.json();
  await updateUser(c.req.param('id'), updates); // Can set role, isAdmin, etc.!
});
```

### Mitigation
```typescript
// Define allowed output fields per role
const UserOutputSchema = {
  public: z.object({
    id: z.string(),
    name: z.string(),
    avatar: z.string().nullable(),
  }),
  owner: z.object({
    id: z.string(),
    name: z.string(),
    email: z.string(),
    avatar: z.string().nullable(),
    createdAt: z.string(),
  }),
  admin: z.object({
    id: z.string(),
    name: z.string(),
    email: z.string(),
    avatar: z.string().nullable(),
    role: z.string(),
    status: z.string(),
    createdAt: z.string(),
    lastLoginAt: z.string().nullable(),
  }),
};

function filterUserOutput(user: User, role: 'public' | 'owner' | 'admin') {
  const schema = UserOutputSchema[role];
  return schema.parse(user);
}

app.get('/api/users/:id', authMiddleware, async (c) => {
  const currentUser = c.get('user');
  const user = await getUser(c.req.param('id'));
  
  if (!user) return c.notFound();
  
  // Determine access level
  const role = currentUser.role === 'admin' ? 'admin'
    : currentUser.id === user.id ? 'owner'
    : 'public';
  
  return c.json(filterUserOutput(user, role));
});

// Define allowed update fields
const UserUpdateSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  avatar: z.string().url().optional(),
  // role, status, etc. NOT allowed here
});

app.patch('/api/users/:id', authMiddleware, async (c) => {
  const updates = UserUpdateSchema.parse(await c.req.json());
  // Only validated fields can be updated
  await updateUser(c.req.param('id'), updates);
});
```

## API4:2023 - Unrestricted Resource Consumption

No limits on request size, rate, or resource usage.

### Mitigation
```typescript
// Rate limiting
app.use('/api/*', rateLimit({
  windowMs: 60 * 1000,
  max: 100,
}));

// Request size limits
app.use('/api/*', async (c, next) => {
  const contentLength = parseInt(c.req.header('content-length') || '0');
  if (contentLength > 1024 * 1024) { // 1MB
    return c.json({ error: 'Request too large' }, 413);
  }
  await next();
});

// Pagination limits
const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

// Array limits in input
const BulkOperationSchema = z.object({
  ids: z.array(z.string().uuid()).max(100),
});

// Query complexity limits (for GraphQL)
// Use libraries like graphql-depth-limit
```

## API5:2023 - Broken Function Level Authorization

Users can access admin functions.

### Vulnerability Example
```typescript
// VULNERABLE: Only checks authentication, not authorization
app.delete('/api/users/:id', authMiddleware, async (c) => {
  await deleteUser(c.req.param('id')); // Any user can delete any user!
});
```

### Mitigation
```typescript
// Role-based middleware
function requireRole(...roles: string[]) {
  return createMiddleware(async (c, next) => {
    const user = c.get('user');
    
    if (!roles.includes(user.role)) {
      console.warn({
        event: 'authorization_failure',
        userId: user.id,
        requiredRoles: roles,
        userRole: user.role,
        path: c.req.path,
      });
      return c.json({ error: 'Forbidden' }, 403);
    }
    
    await next();
  });
}

// Admin-only routes
app.delete('/api/users/:id', 
  authMiddleware, 
  requireRole('admin'), 
  async (c) => {
    await deleteUser(c.req.param('id'));
    return c.json({ deleted: true });
  }
);

// Multiple roles
app.get('/api/reports', 
  authMiddleware, 
  requireRole('admin', 'manager'),
  async (c) => {
    const reports = await getReports();
    return c.json(reports);
  }
);
```

## API6:2023 - Unrestricted Access to Sensitive Business Flows

Automated abuse of business functionality (e.g., ticket scalping, credential stuffing).

### Mitigation
```typescript
// Rate limit by user + action
const purchaseLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // 3 purchases per hour
  keyGenerator: (c) => `purchase:${c.get('user').id}`,
  message: { error: 'Purchase limit exceeded. Try again later.' },
});

// CAPTCHA for sensitive operations
app.post('/api/tickets/purchase',
  authMiddleware,
  purchaseLimiter,
  verifyCaptcha,
  async (c) => {
    // Process purchase
  }
);

// Detect automated behavior
app.use('/api/*', async (c, next) => {
  const ua = c.req.header('user-agent');
  
  // Flag suspicious patterns
  if (!ua || ua.length < 10 || /bot|crawler|spider/i.test(ua)) {
    c.set('suspicious', true);
  }
  
  await next();
});
```

## API7:2023 - Server Side Request Forgery (SSRF)

API fetches URLs provided by users without validation.

### Vulnerability Example
```typescript
// VULNERABLE: Fetches any URL user provides
app.post('/api/fetch-url', async (c) => {
  const { url } = await c.req.json();
  const response = await fetch(url); // Can access internal services!
  return c.json(await response.json());
});
```

### Mitigation
```typescript
const ALLOWED_DOMAINS = [
  'api.github.com',
  'api.twitter.com',
  'graph.facebook.com',
];

function isUrlAllowed(urlString: string): boolean {
  try {
    const url = new URL(urlString);
    
    // Must be HTTPS
    if (url.protocol !== 'https:') return false;
    
    // Check against allowlist
    if (!ALLOWED_DOMAINS.includes(url.hostname)) return false;
    
    // Block private IPs
    const host = url.hostname;
    if (host === 'localhost' || host === '127.0.0.1') return false;
    if (/^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host)) return false;
    
    // Block internal domains
    if (host.endsWith('.internal') || host.endsWith('.local')) return false;
    
    return true;
  } catch {
    return false;
  }
}

app.post('/api/fetch-url', async (c) => {
  const { url } = await c.req.json();
  
  if (!isUrlAllowed(url)) {
    return c.json({ error: 'URL not allowed' }, 400);
  }
  
  const response = await fetch(url, {
    redirect: 'error', // Don't follow redirects
  });
  
  return c.json(await response.json());
});
```

## API8:2023 - Security Misconfiguration

Insecure default configurations, exposed debug endpoints, missing headers.

### Checklist
```typescript
// Remove debug endpoints in production
if (process.env.NODE_ENV !== 'development') {
  // Don't register debug routes
} else {
  app.get('/debug/env', (c) => c.json(process.env));
}

// Secure headers (see security-headers.md)
app.use('*', secureHeaders());

// Proper CORS
app.use('/api/*', cors({
  origin: ['https://app.example.com'], // Not '*' in production
  credentials: true,
}));

// Don't expose stack traces
app.onError((err, c) => {
  console.error(err);
  return c.json({
    error: c.env.ENVIRONMENT === 'production' 
      ? 'Internal error' 
      : err.message,
  }, 500);
});

// Disable X-Powered-By equivalent
// (Workers don't expose this by default)
```

## API9:2023 - Improper Inventory Management

Running outdated API versions, shadow APIs, undocumented endpoints.

### Mitigation
```typescript
// Explicit versioning
const v1 = new Hono();
const v2 = new Hono();

v1.get('/users', handleV1Users);
v2.get('/users', handleV2Users);

app.route('/api/v1', v1);
app.route('/api/v2', v2);

// Deprecation headers
v1.use('*', async (c, next) => {
  c.header('Deprecation', 'true');
  c.header('Sunset', 'Sat, 31 Dec 2024 23:59:59 GMT');
  c.header('Link', '</api/v2>; rel="successor-version"');
  await next();
});

// Document all endpoints
// Use OpenAPI/Swagger
```

## API10:2023 - Unsafe Consumption of APIs

Trusting third-party API responses without validation.

### Vulnerability Example
```typescript
// VULNERABLE: Trusts third-party data
app.get('/weather', async (c) => {
  const data = await fetch('https://weather-api.com/data').then(r => r.json());
  // Directly uses data.location in SQL query
  await db.query(`INSERT INTO logs (location) VALUES ('${data.location}')`);
});
```

### Mitigation
```typescript
// Validate third-party responses
const WeatherResponseSchema = z.object({
  location: z.string().max(100),
  temperature: z.number(),
  conditions: z.string(),
});

app.get('/weather', async (c) => {
  const response = await fetch('https://weather-api.com/data');
  
  if (!response.ok) {
    return c.json({ error: 'Weather service unavailable' }, 503);
  }
  
  const raw = await response.json();
  
  // Validate and sanitize
  const result = WeatherResponseSchema.safeParse(raw);
  
  if (!result.success) {
    console.error('Invalid weather API response:', result.error);
    return c.json({ error: 'Weather data unavailable' }, 503);
  }
  
  const data = result.data;
  
  // Now safe to use
  await env.DB.prepare(
    'INSERT INTO logs (location, temperature) VALUES (?, ?)'
  ).bind(data.location, data.temperature).run();
  
  return c.json(data);
});
```

## Security Testing Checklist

| Test | OWASP Risk |
|------|------------|
| Try accessing other users' resources by changing IDs | API1 (BOLA) |
| Test login without rate limiting | API2 |
| Check if sensitive fields are exposed | API3 |
| Send very large requests, many concurrent requests | API4 |
| Access admin endpoints as regular user | API5 |
| Automate business-critical flows | API6 |
| Submit URLs pointing to internal services | API7 |
| Look for debug endpoints, verbose errors | API8 |
| Test old API versions still accessible | API9 |
| Check validation of third-party data | API10 |
