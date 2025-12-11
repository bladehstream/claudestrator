# Session Security

## Overview

Session management is critical for maintaining authenticated state. This covers cookie security, CSRF protection, session handling, and security headers.

## Cookie Security

### Secure Cookie Configuration

```typescript
interface CookieOptions {
  httpOnly: boolean;    // Prevent JavaScript access (XSS protection)
  secure: boolean;      // HTTPS only
  sameSite: 'strict' | 'lax' | 'none';  // CSRF protection
  maxAge: number;       // Expiration in seconds
  path: string;         // Cookie path
  domain?: string;      // Cookie domain
}

// Production cookie settings
const SECURE_COOKIE_OPTIONS: CookieOptions = {
  httpOnly: true,
  secure: true,           // Always true in production
  sameSite: 'strict',     // Most restrictive
  maxAge: 7 * 24 * 60 * 60,  // 7 days
  path: '/',
};

// Session cookie (shorter lifetime)
const SESSION_COOKIE_OPTIONS: CookieOptions = {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',        // Allow navigation requests
  maxAge: 24 * 60 * 60,   // 24 hours
  path: '/',
};

// Auth endpoint cookie (restricted path)
const AUTH_COOKIE_OPTIONS: CookieOptions = {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: 7 * 24 * 60 * 60,
  path: '/api/auth',      // Only sent to auth endpoints
};
```

### SameSite Attribute

```
Strict: Cookie only sent on same-site requests
        - Best CSRF protection
        - Breaks some legitimate cross-site flows

Lax:    Cookie sent on same-site + top-level navigation
        - Good balance of security and usability
        - Default for most browsers

None:   Cookie sent on all requests (requires Secure)
        - Required for cross-site embedded content
        - Must be used with care
```

### Hono Cookie Handling

```typescript
import { Hono } from 'hono';
import { setCookie, getCookie, deleteCookie } from 'hono/cookie';

const app = new Hono();

// Set secure cookie
app.post('/auth/login', async (c) => {
  const { refreshToken, accessToken } = await authenticate(c);

  setCookie(c, 'refreshToken', refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'Strict',
    maxAge: 7 * 24 * 60 * 60,
    path: '/api/auth',
  });

  return c.json({ accessToken });
});

// Read cookie
app.get('/api/auth/session', (c) => {
  const sessionId = getCookie(c, 'sessionId');
  // ...
});

// Delete cookie (set same options)
app.post('/auth/logout', (c) => {
  deleteCookie(c, 'refreshToken', {
    path: '/api/auth',
  });
  return c.json({ success: true });
});
```

## CSRF Protection

### Hono CSRF Middleware

```typescript
import { csrf } from 'hono/csrf';

const app = new Hono();

// Basic CSRF protection
app.use('*', csrf());

// With specific origins
app.use(
  '*',
  csrf({
    origin: [
      'https://myapp.example.com',
      'https://app.example.com',
    ],
  })
);

// Dynamic origin validation
app.use(
  '*',
  csrf({
    origin: (origin) => {
      // Must match exactly to prevent subdomain attacks
      return /^https:\/\/(www\.)?example\.com$/.test(origin);
    },
  })
);
```

### Double Submit Cookie Pattern

```typescript
import crypto from 'crypto';

// Generate CSRF token
function generateCSRFToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

// Middleware to set CSRF cookie
app.use('*', async (c, next) => {
  let csrfToken = getCookie(c, 'csrf-token');
  
  if (!csrfToken) {
    csrfToken = generateCSRFToken();
    setCookie(c, 'csrf-token', csrfToken, {
      httpOnly: false,  // Must be readable by JavaScript
      secure: true,
      sameSite: 'Strict',
      maxAge: 24 * 60 * 60,
    });
  }
  
  c.set('csrfToken', csrfToken);
  await next();
});

// Validate CSRF on state-changing requests
app.use('/api/*', async (c, next) => {
  const method = c.req.method;
  
  // Skip safe methods
  if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    return next();
  }
  
  const cookieToken = getCookie(c, 'csrf-token');
  const headerToken = c.req.header('X-CSRF-Token');
  
  if (!cookieToken || !headerToken || cookieToken !== headerToken) {
    return c.json({ error: 'Invalid CSRF token' }, 403);
  }
  
  await next();
});

// Endpoint to get token for client
app.get('/api/csrf-token', (c) => {
  return c.json({ token: c.get('csrfToken') });
});
```

### Client-Side CSRF Handling

```typescript
// API client with CSRF token
class ApiClient {
  private csrfToken: string | null = null;

  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    // Get CSRF token if not cached
    if (!this.csrfToken) {
      await this.refreshCSRFToken();
    }

    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'X-CSRF-Token': this.csrfToken!,
      },
      credentials: 'include',  // Send cookies
    });
  }

  private async refreshCSRFToken(): Promise<void> {
    const response = await fetch('/api/csrf-token', {
      credentials: 'include',
    });
    const { token } = await response.json();
    this.csrfToken = token;
  }
}
```

## Security Headers

### Hono Secure Headers

```typescript
import { secureHeaders } from 'hono/secure-headers';

app.use(
  '*',
  secureHeaders({
    contentSecurityPolicy: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", 'https://api.example.com'],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      frameAncestors: ["'none'"],
    },
    crossOriginEmbedderPolicy: 'require-corp',
    crossOriginOpenerPolicy: 'same-origin',
    crossOriginResourcePolicy: 'same-origin',
    referrerPolicy: 'strict-origin-when-cross-origin',
    strictTransportSecurity: 'max-age=31536000; includeSubDomains',
    xContentTypeOptions: 'nosniff',
    xFrameOptions: 'DENY',
    xXssProtection: '1; mode=block',
  })
);
```

### Manual Header Setting

```typescript
app.use('*', async (c, next) => {
  await next();

  // Security headers
  c.header('X-Content-Type-Options', 'nosniff');
  c.header('X-Frame-Options', 'DENY');
  c.header('X-XSS-Protection', '1; mode=block');
  c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
  c.header(
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains; preload'
  );
  c.header(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
  );
});
```

## Session Management

### Database Session Store

```typescript
interface Session {
  id: string;
  userId: string;
  data: Record<string, unknown>;
  userAgent: string;
  ipAddress: string;
  createdAt: Date;
  expiresAt: Date;
  lastActivityAt: Date;
}

class SessionStore {
  constructor(private db: Database) {}

  async create(
    userId: string,
    context: { userAgent: string; ipAddress: string }
  ): Promise<Session> {
    const session = {
      id: crypto.randomUUID(),
      userId,
      data: {},
      userAgent: context.userAgent,
      ipAddress: context.ipAddress,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
      lastActivityAt: new Date(),
    };

    await this.db.sessions.create({ data: session });
    return session;
  }

  async get(sessionId: string): Promise<Session | null> {
    const session = await this.db.sessions.findUnique({
      where: { id: sessionId },
    });

    if (!session || session.expiresAt < new Date()) {
      return null;
    }

    return session;
  }

  async touch(sessionId: string): Promise<void> {
    await this.db.sessions.update({
      where: { id: sessionId },
      data: { lastActivityAt: new Date() },
    });
  }

  async destroy(sessionId: string): Promise<void> {
    await this.db.sessions.delete({ where: { id: sessionId } });
  }

  async destroyAllForUser(userId: string): Promise<void> {
    await this.db.sessions.deleteMany({ where: { userId } });
  }

  async cleanup(): Promise<void> {
    await this.db.sessions.deleteMany({
      where: { expiresAt: { lt: new Date() } },
    });
  }
}
```

### Session Middleware

```typescript
const sessionStore = new SessionStore(db);

app.use('*', async (c, next) => {
  const sessionId = getCookie(c, 'sessionId');

  if (sessionId) {
    const session = await sessionStore.get(sessionId);
    
    if (session) {
      c.set('session', session);
      c.set('user', await db.users.findUnique({
        where: { id: session.userId },
      }));
      
      // Update last activity
      await sessionStore.touch(sessionId);
    }
  }

  await next();
});
```

### Active Sessions Management

```typescript
// Get all active sessions for user
app.get('/api/sessions', async (c) => {
  const user = c.get('user');
  const currentSession = c.get('session');

  const sessions = await db.sessions.findMany({
    where: { userId: user.id },
    orderBy: { lastActivityAt: 'desc' },
  });

  return c.json(
    sessions.map((s) => ({
      id: s.id,
      userAgent: s.userAgent,
      ipAddress: s.ipAddress,
      createdAt: s.createdAt,
      lastActivityAt: s.lastActivityAt,
      isCurrent: s.id === currentSession.id,
    }))
  );
});

// Revoke specific session
app.delete('/api/sessions/:id', async (c) => {
  const user = c.get('user');
  const sessionId = c.req.param('id');

  const session = await db.sessions.findFirst({
    where: { id: sessionId, userId: user.id },
  });

  if (!session) {
    return c.json({ error: 'Session not found' }, 404);
  }

  await sessionStore.destroy(sessionId);
  return c.json({ success: true });
});

// Revoke all other sessions
app.post('/api/sessions/revoke-others', async (c) => {
  const user = c.get('user');
  const currentSession = c.get('session');

  await db.sessions.deleteMany({
    where: {
      userId: user.id,
      id: { not: currentSession.id },
    },
  });

  return c.json({ success: true });
});
```

## Rate Limiting

```typescript
// Simple in-memory rate limiter
const rateLimits = new Map<string, { count: number; resetAt: number }>();

function rateLimit(
  key: string,
  limit: number,
  windowMs: number
): { allowed: boolean; remaining: number; resetAt: number } {
  const now = Date.now();
  const record = rateLimits.get(key);

  if (!record || now > record.resetAt) {
    rateLimits.set(key, { count: 1, resetAt: now + windowMs });
    return { allowed: true, remaining: limit - 1, resetAt: now + windowMs };
  }

  if (record.count >= limit) {
    return { allowed: false, remaining: 0, resetAt: record.resetAt };
  }

  record.count++;
  return { allowed: true, remaining: limit - record.count, resetAt: record.resetAt };
}

// Rate limit middleware for auth endpoints
app.use('/api/auth/*', async (c, next) => {
  const ip = c.req.header('CF-Connecting-IP') || 
             c.req.header('X-Forwarded-For')?.split(',')[0] ||
             'unknown';
  
  const { allowed, remaining, resetAt } = rateLimit(
    `auth:${ip}`,
    10,        // 10 requests
    60 * 1000  // per minute
  );

  c.header('X-RateLimit-Remaining', remaining.toString());
  c.header('X-RateLimit-Reset', Math.ceil(resetAt / 1000).toString());

  if (!allowed) {
    return c.json({ error: 'Too many requests' }, 429);
  }

  await next();
});
```

## Security Checklist

### Cookies
- [ ] httpOnly for all auth cookies
- [ ] Secure flag (HTTPS only)
- [ ] SameSite attribute set
- [ ] Appropriate expiration
- [ ] Path restriction where possible

### CSRF
- [ ] Token validation on state-changing requests
- [ ] Origin header validation
- [ ] SameSite cookies as additional protection

### Headers
- [ ] Content-Security-Policy
- [ ] Strict-Transport-Security
- [ ] X-Frame-Options
- [ ] X-Content-Type-Options
- [ ] X-XSS-Protection

### Sessions
- [ ] Secure session ID generation
- [ ] Session expiration
- [ ] Session invalidation on logout
- [ ] Multiple session management
- [ ] IP/User-Agent tracking

### Rate Limiting
- [ ] Authentication endpoints
- [ ] Password reset
- [ ] API endpoints
- [ ] Progressive delays for failures
