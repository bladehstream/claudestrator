# JWT Authentication with Access & Refresh Tokens

## Overview

JWT (JSON Web Token) authentication uses cryptographically signed tokens to verify user identity. The access/refresh token pattern balances security (short-lived access tokens) with usability (longer-lived refresh tokens for session continuity).

## Token Structure

```typescript
// JWT consists of three parts: header.payload.signature

interface JWTHeader {
  alg: 'HS256' | 'RS256' | 'ES256' | 'EdDSA';  // Algorithm
  typ: 'JWT';
}

interface AccessTokenPayload {
  sub: string;      // Subject (user ID)
  email?: string;
  role: string;
  permissions?: string[];
  iat: number;      // Issued at (Unix timestamp)
  exp: number;      // Expiration (Unix timestamp)
  iss?: string;     // Issuer
  aud?: string;     // Audience
}

interface RefreshTokenPayload {
  sub: string;      // User ID
  jti: string;      // Unique token ID (for revocation)
  iat: number;
  exp: number;
  family?: string;  // Token family (for rotation tracking)
}
```

## Recommended Expiration Times

```typescript
const TOKEN_CONFIG = {
  accessToken: {
    expiresIn: '15m',      // 15 minutes - short-lived
    // Alternative: 5m for high-security apps
  },
  refreshToken: {
    expiresIn: '7d',       // 7 days
    // Mobile apps: up to 30d
    // High-security: 24h
  },
  rememberMe: {
    refreshExpiresIn: '30d',  // Extended refresh for "remember me"
  },
};
```

## Implementation with jsonwebtoken

### Setup

```typescript
import jwt, { JwtPayload, SignOptions } from 'jsonwebtoken';
import crypto from 'crypto';

// Environment variables
const JWT_SECRET = process.env.JWT_SECRET!;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!;

// Use different secrets for access and refresh tokens
// Minimum 256 bits (32 bytes) for HMAC-SHA256
```

### Token Generation

```typescript
interface User {
  id: string;
  email: string;
  role: string;
}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

function generateTokens(user: User): TokenPair {
  const accessToken = jwt.sign(
    {
      sub: user.id,
      email: user.email,
      role: user.role,
    },
    JWT_SECRET,
    { expiresIn: '15m' }
  );

  const refreshToken = jwt.sign(
    {
      sub: user.id,
      jti: crypto.randomUUID(),  // Unique ID for revocation
    },
    JWT_REFRESH_SECRET,
    { expiresIn: '7d' }
  );

  return {
    accessToken,
    refreshToken,
    expiresIn: 900,  // 15 minutes in seconds
  };
}
```

### Token Verification

```typescript
interface VerifiedToken extends JwtPayload {
  sub: string;
  email?: string;
  role?: string;
}

function verifyAccessToken(token: string): VerifiedToken {
  try {
    const payload = jwt.verify(token, JWT_SECRET) as VerifiedToken;
    return payload;
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new Error('TOKEN_EXPIRED');
    }
    if (error instanceof jwt.JsonWebTokenError) {
      throw new Error('TOKEN_INVALID');
    }
    throw error;
  }
}

function verifyRefreshToken(token: string): VerifiedToken {
  try {
    return jwt.verify(token, JWT_REFRESH_SECRET) as VerifiedToken;
  } catch (error) {
    throw new Error('REFRESH_TOKEN_INVALID');
  }
}
```

### Token Refresh Flow

```typescript
interface RefreshResult {
  accessToken: string;
  refreshToken?: string;  // New refresh token if rotating
}

async function refreshTokens(
  refreshToken: string,
  db: Database
): Promise<RefreshResult> {
  // 1. Verify refresh token
  const payload = verifyRefreshToken(refreshToken);
  
  // 2. Check if token is blacklisted/revoked
  const isRevoked = await db.isTokenRevoked(payload.jti!);
  if (isRevoked) {
    throw new Error('TOKEN_REVOKED');
  }
  
  // 3. Get user (ensure still exists and active)
  const user = await db.getUserById(payload.sub);
  if (!user || !user.isActive) {
    throw new Error('USER_NOT_FOUND');
  }
  
  // 4. Generate new tokens
  const tokens = generateTokens(user);
  
  // 5. Revoke old refresh token (rotation)
  await db.revokeToken(payload.jti!);
  
  return {
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken,
  };
}
```

## Token Storage Best Practices

### Access Token
```typescript
// ✅ Store in memory (JavaScript variable)
// Survives page navigation, lost on refresh
let accessToken: string | null = null;

// ✅ Or in sessionStorage (cleared on tab close)
// Vulnerable to XSS but scoped to tab
sessionStorage.setItem('accessToken', token);

// ❌ NEVER localStorage - persists and XSS vulnerable
```

### Refresh Token
```typescript
// ✅ httpOnly cookie (server-set)
// Not accessible to JavaScript, automatic on requests
res.cookie('refreshToken', token, {
  httpOnly: true,
  secure: true,           // HTTPS only
  sameSite: 'strict',     // CSRF protection
  maxAge: 7 * 24 * 60 * 60 * 1000,  // 7 days
  path: '/api/auth',      // Only sent to auth endpoints
});

// ✅ Clear on logout
res.clearCookie('refreshToken', {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/api/auth',
});
```

## Hono Implementation

```typescript
import { Hono } from 'hono';
import { jwt } from 'hono/jwt';
import { setCookie, getCookie, deleteCookie } from 'hono/cookie';

const app = new Hono();

// Login endpoint
app.post('/api/auth/login', async (c) => {
  const { email, password } = await c.req.json();
  
  // Validate credentials (see password-security.md)
  const user = await authenticateUser(email, password);
  if (!user) {
    return c.json({ error: 'Invalid credentials' }, 401);
  }
  
  const tokens = generateTokens(user);
  
  // Set refresh token as httpOnly cookie
  setCookie(c, 'refreshToken', tokens.refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'Strict',
    maxAge: 7 * 24 * 60 * 60,
    path: '/api/auth',
  });
  
  // Return access token in body
  return c.json({
    accessToken: tokens.accessToken,
    expiresIn: tokens.expiresIn,
    user: { id: user.id, email: user.email, role: user.role },
  });
});

// Refresh endpoint
app.post('/api/auth/refresh', async (c) => {
  const refreshToken = getCookie(c, 'refreshToken');
  
  if (!refreshToken) {
    return c.json({ error: 'No refresh token' }, 401);
  }
  
  try {
    const result = await refreshTokens(refreshToken, db);
    
    // Set new refresh token
    setCookie(c, 'refreshToken', result.refreshToken!, {
      httpOnly: true,
      secure: true,
      sameSite: 'Strict',
      maxAge: 7 * 24 * 60 * 60,
      path: '/api/auth',
    });
    
    return c.json({ accessToken: result.accessToken });
  } catch (error) {
    deleteCookie(c, 'refreshToken');
    return c.json({ error: 'Invalid refresh token' }, 401);
  }
});

// Protected routes
app.use('/api/*', jwt({ secret: JWT_SECRET }));

app.get('/api/profile', (c) => {
  const payload = c.get('jwtPayload');
  return c.json({ userId: payload.sub });
});

// Logout
app.post('/api/auth/logout', async (c) => {
  const refreshToken = getCookie(c, 'refreshToken');
  
  if (refreshToken) {
    // Optionally blacklist the refresh token
    try {
      const payload = verifyRefreshToken(refreshToken);
      await db.revokeToken(payload.jti!);
    } catch {
      // Token already invalid, continue
    }
  }
  
  deleteCookie(c, 'refreshToken', { path: '/api/auth' });
  return c.json({ success: true });
});
```

## Token Revocation Strategies

### Blacklist (Recommended for Refresh Tokens)
```typescript
// Store revoked token JTIs
interface RevokedToken {
  jti: string;
  expiresAt: Date;  // Auto-cleanup after expiry
}

// Check on every refresh
async function isTokenRevoked(jti: string): Promise<boolean> {
  const revoked = await db.revokedTokens.findUnique({ where: { jti } });
  return !!revoked;
}
```

### Token Versioning (For Invalidating All Tokens)
```typescript
// Store token version per user
interface User {
  id: string;
  tokenVersion: number;  // Increment to invalidate all tokens
}

// Include version in token
const token = jwt.sign(
  { sub: user.id, version: user.tokenVersion },
  secret
);

// Verify version matches
function verifyWithVersion(token: string, user: User): boolean {
  const payload = jwt.verify(token, secret);
  return payload.version === user.tokenVersion;
}

// Invalidate all user tokens
async function invalidateAllTokens(userId: string): Promise<void> {
  await db.user.update({
    where: { id: userId },
    data: { tokenVersion: { increment: 1 } },
  });
}
```

## Algorithm Recommendations (2025)

| Algorithm | Use Case | Key Size |
|-----------|----------|----------|
| EdDSA | Best security + performance | Ed25519 |
| ES256 | Good security, smaller signatures | P-256 |
| RS256 | Wide compatibility, asymmetric | 2048-bit |
| HS256 | Simple symmetric, single service | 256-bit |

```typescript
// EdDSA example (requires jose library)
import { SignJWT, jwtVerify } from 'jose';
import { generateKeyPair } from 'jose';

const { publicKey, privateKey } = await generateKeyPair('EdDSA');

const token = await new SignJWT({ sub: user.id })
  .setProtectedHeader({ alg: 'EdDSA' })
  .setExpirationTime('15m')
  .sign(privateKey);

const { payload } = await jwtVerify(token, publicKey);
```

## Security Considerations

1. **Different Secrets**: Use separate secrets for access and refresh tokens
2. **Short Expiry**: Access tokens should expire quickly (5-15 minutes)
3. **Token Rotation**: Generate new refresh token on each refresh
4. **Secure Transport**: Always use HTTPS
5. **Minimal Claims**: Don't store sensitive data in tokens
6. **JTI for Refresh**: Always include unique ID for revocation
7. **Audience Validation**: Verify `aud` claim matches expected service
