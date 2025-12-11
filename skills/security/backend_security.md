---
name: Backend Security
id: backend_security
version: 1.0
category: security
domain: [security, api, backend]
task_types: [implementation, security, review]
keywords: [security, owasp, injection, xss, csrf, validation, zod, headers, secrets, cors, rate limiting, sql injection]
complexity: [normal, complex]
pairs_with: [api_development, web_auth_security, databases]
source: backend-skills/backend-security/SKILL-backend-security.md
---

# Backend Security Skill

Secure APIs and backend services against common vulnerabilities including OWASP API Top 10, injection attacks, and misconfigurations.

## Quick Reference

### Essential Security Middleware (Hono)
```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { csrf } from 'hono/csrf';
import { secureHeaders } from 'hono/secure-headers';

const app = new Hono<{ Bindings: Env }>();

// Security headers
app.use('*', secureHeaders());

// CORS - configure for your domains
app.use('/api/*', cors({
  origin: ['https://app.example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}));

// CSRF protection for state-changing operations
app.use('/api/*', csrf());
```

### Input Validation with Zod
```typescript
import { z } from 'zod';
import { zValidator } from '@hono/zod-validator';

const UserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[\w\s-]+$/),
  age: z.number().int().positive().max(150).optional(),
});

app.post('/users',
  zValidator('json', UserSchema),
  async (c) => {
    const data = c.req.valid('json'); // Validated and typed
    // Safe to use
  }
);
```

### Secrets Management (Cloudflare Workers)
```bash
# Set secrets (never in wrangler.toml)
npx wrangler secret put API_KEY
npx wrangler secret put DATABASE_URL --env production

# Local development (.dev.vars - gitignored)
echo "API_KEY=dev-key-here" >> .dev.vars
```

## OWASP API Top 10 (2023) Overview

| Risk | Description | Primary Mitigation |
|------|-------------|-------------------|
| **API1** | Broken Object Level Authorization | Verify user owns resource on every request |
| **API2** | Broken Authentication | Strong auth, rate limit login, MFA |
| **API3** | Broken Object Property Level Authorization | Control exposed fields, validate inputs |
| **API4** | Unrestricted Resource Consumption | Rate limiting, payload size limits |
| **API5** | Broken Function Level Authorization | RBAC, verify permissions per endpoint |
| **API6** | Unrestricted Access to Sensitive Business Flows | Rate limit, CAPTCHA, anomaly detection |
| **API7** | Server Side Request Forgery | Validate URLs, allowlist domains |
| **API8** | Security Misconfiguration | Secure defaults, remove debug endpoints |
| **API9** | Improper Inventory Management | API versioning, deprecate old versions |
| **API10** | Unsafe Consumption of APIs | Validate third-party responses |

## Security Checklist

### Authentication & Authorization
- [ ] Use strong password hashing (Argon2id or bcrypt)
- [ ] Implement proper JWT validation (signature, expiration, issuer)
- [ ] Store tokens securely (httpOnly cookies for refresh tokens)
- [ ] Check authorization on every request (not just authentication)
- [ ] Implement rate limiting on login endpoints
- [ ] Use MFA for sensitive operations

### Input Validation
- [ ] Validate all user input with schemas (Zod)
- [ ] Sanitize HTML content before storage/display
- [ ] Use parameterized queries for all database operations
- [ ] Limit request body size and array lengths
- [ ] Validate file uploads (type, size, content)

### Security Headers
- [ ] Set Content-Security-Policy
- [ ] Enable Strict-Transport-Security (HSTS)
- [ ] Set X-Content-Type-Options: nosniff
- [ ] Set X-Frame-Options or frame-ancestors CSP
- [ ] Remove X-Powered-By header

### Secrets & Configuration
- [ ] Never commit secrets to version control
- [ ] Use environment-specific secret storage
- [ ] Rotate secrets regularly
- [ ] Use least-privilege database credentials
- [ ] Disable debug mode in production

### API Design
- [ ] Use HTTPS everywhere
- [ ] Version APIs properly
- [ ] Return minimal error details in production
- [ ] Log security events (failed auth, permission denied)
- [ ] Implement proper CORS configuration

## Reference Documents

| Document | Contents |
|----------|----------|
| [input-validation.md](./references/input-validation.md) | Zod schemas, sanitization, XSS prevention |
| [sql-injection.md](./references/sql-injection.md) | Parameterized queries, ORM security |
| [security-headers.md](./references/security-headers.md) | CSP, HSTS, CORS, Helmet equivalent for Hono |
| [rate-limiting.md](./references/rate-limiting.md) | Algorithms, Durable Objects implementation |
| [secrets-management.md](./references/secrets-management.md) | Environment variables, Cloudflare secrets |
| [owasp-api-security.md](./references/owasp-api-security.md) | Detailed OWASP API Top 10 mitigations |

## Common Vulnerability Patterns

### SQL Injection - WRONG
```typescript
// NEVER do this - SQL injection vulnerability
const query = `SELECT * FROM users WHERE email = '${email}'`;
```

### SQL Injection - CORRECT
```typescript
// Always use parameterized queries
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = ?'
).bind(email).first();
```

### XSS - WRONG
```typescript
// NEVER trust user input in HTML
app.get('/search', (c) => {
  const q = c.req.query('q');
  return c.html(`<h1>Results for: ${q}</h1>`); // XSS!
});
```

### XSS - CORRECT
```typescript
import { escape } from 'html-escaper';

app.get('/search', (c) => {
  const q = escape(c.req.query('q') || '');
  return c.html(`<h1>Results for: ${q}</h1>`);
});
```

### Authorization - WRONG
```typescript
// Only checks authentication, not authorization
app.get('/users/:id', authMiddleware, async (c) => {
  const user = await getUser(c.req.param('id'));
  return c.json(user); // Any authenticated user can view any user!
});
```

### Authorization - CORRECT
```typescript
// Checks that user owns the resource
app.get('/users/:id', authMiddleware, async (c) => {
  const requestedId = c.req.param('id');
  const currentUser = c.get('user');

  if (requestedId !== currentUser.id && currentUser.role !== 'admin') {
    return c.json({ error: 'Forbidden' }, 403);
  }

  const user = await getUser(requestedId);
  return c.json(user);
});
```

## Error Handling

### Production-Safe Errors
```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  const isProd = c.env.ENVIRONMENT === 'production';

  // Log full error internally
  console.error({
    error: err.message,
    stack: err.stack,
    path: c.req.path,
    method: c.req.method,
  });

  if (err instanceof HTTPException) {
    return err.getResponse();
  }

  // Never expose internal details in production
  return c.json({
    error: isProd ? 'Internal Server Error' : err.message,
  }, 500);
});
```

## Security Testing

### Tools
- **OWASP ZAP** - Dynamic security scanner
- **Burp Suite** - Proxy and security testing
- **sqlmap** - SQL injection detection
- **npm audit** - Dependency vulnerabilities

### Manual Testing Checklist
1. Try SQL injection in all input fields
2. Test IDOR (change IDs in requests)
3. Test privilege escalation (access admin endpoints)
4. Check for sensitive data in responses
5. Verify rate limiting works
6. Test CORS with unauthorized origins
7. Check error messages don't leak info

## Best Practices

1. **Defense in depth** - Multiple layers of security
2. **Fail securely** - Deny by default on errors
3. **Least privilege** - Minimal permissions needed
4. **Input validation** - Validate everything, trust nothing
5. **Output encoding** - Encode data for context (HTML, SQL, JSON)
6. **Secure defaults** - Safe configuration out of the box
7. **Keep secrets secret** - Never log or expose sensitive data
8. **Update dependencies** - Regular security updates
9. **Monitor and log** - Detect and respond to attacks
10. **Test regularly** - Security testing in CI/CD

---

*Skill Version: 1.0*
