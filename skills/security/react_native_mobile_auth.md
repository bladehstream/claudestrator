---
name: React Native Auth
id: react_native_mobile_auth
version: 1.0
category: security
domain: [mobile, react-native, expo, api]
task_types: [implementation, security, design]
keywords: [auth, biometrics, face id, touch id, passkeys, webauthn, expo, react native, secure storage, oauth, pkce, mobile, hono, better auth, rbac]
complexity: [normal, complex]
pairs_with: [web_auth_security, api_development, device_hardware]
source: backend-skills/authentication/SKILL-authentication.md
---

# React Native Auth

Quick reference for implementing authentication and authorization in TypeScript applications, with focus on React Native/Expo mobile apps and serverless backends.

## When to Use This Skill

- Implementing user authentication (login, signup, password reset)
- JWT access/refresh token flows
- OAuth 2.0 / PKCE for mobile and SPAs
- Passkeys/WebAuthn passwordless authentication
- Biometric authentication in React Native
- Multi-factor authentication (TOTP)
- Role-based access control (RBAC)
- Session management and security

## Reference Files

| File | Use When |
|------|----------|
| `references/jwt-tokens.md` | Implementing JWT authentication with access/refresh tokens |
| `references/oauth-pkce.md` | OAuth 2.0 flows, PKCE for mobile apps, social login |
| `references/passkeys.md` | WebAuthn/passkeys passwordless authentication |
| `references/password-security.md` | Password hashing (Argon2/bcrypt), validation rules |
| `references/mobile-auth.md` | React Native/Expo biometrics, secure storage |
| `references/mfa-totp.md` | Two-factor authentication with TOTP |
| `references/rbac.md` | Role-based access control patterns |
| `references/session-security.md` | Session management, CSRF, cookie security |
| `references/auth-libraries.md` | Better Auth, Auth.js, library comparison |

## Quick Decision Guide

### Which Auth Method?

```
New Project → Better Auth (comprehensive, modern)
Existing Next.js → Auth.js (mature ecosystem)
Full Control Needed → Build with JWT + libraries
Mobile App → OAuth PKCE + Secure Storage + Biometrics
Enterprise/SSO → SAML/OIDC providers
```

### Token Strategy

```typescript
// Standard token lifetimes
const TOKEN_EXPIRY = {
  accessToken: '15m',    // Short-lived, in memory
  refreshToken: '7d',    // Longer, httpOnly cookie
  sessionToken: '24h',   // For session-based auth
  apiToken: '1h',        // For API access
};
```

### Password Hashing Quick Reference

```typescript
// RECOMMENDED: Argon2id (2025 best practice)
import argon2 from 'argon2';

const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 65536,  // 64 MB
  timeCost: 3,
  parallelism: 4,
});

const isValid = await argon2.verify(hash, password);

// ALTERNATIVE: bcrypt (widely supported)
import bcrypt from 'bcrypt';
const hash = await bcrypt.hash(password, 12);
const isValid = await bcrypt.compare(password, hash);
```

### JWT Token Generation

```typescript
import jwt from 'jsonwebtoken';

interface TokenPayload {
  sub: string;      // User ID
  email?: string;
  role: string;
  iat: number;
  exp: number;
  jti?: string;     // Unique token ID for revocation
}

function generateAccessToken(user: User): string {
  return jwt.sign(
    { sub: user.id, email: user.email, role: user.role },
    process.env.JWT_SECRET!,
    { expiresIn: '15m' }
  );
}

function generateRefreshToken(userId: string): string {
  return jwt.sign(
    { sub: userId, jti: crypto.randomUUID() },
    process.env.JWT_REFRESH_SECRET!,
    { expiresIn: '7d' }
  );
}
```

### Secure Cookie Settings

```typescript
// Production cookie configuration
const secureCookie = {
  httpOnly: true,      // Prevent XSS access
  secure: true,        // HTTPS only
  sameSite: 'strict',  // CSRF protection
  maxAge: 7 * 24 * 60 * 60 * 1000,  // 7 days
  path: '/',
};
```

### RBAC Quick Pattern

```typescript
type Role = 'admin' | 'manager' | 'user' | 'guest';
type Permission = 'create' | 'read' | 'update' | 'delete';
type Resource = 'users' | 'posts' | 'settings';

const permissions: Record<Role, Record<Resource, Permission[]>> = {
  admin: {
    users: ['create', 'read', 'update', 'delete'],
    posts: ['create', 'read', 'update', 'delete'],
    settings: ['create', 'read', 'update', 'delete'],
  },
  manager: {
    users: ['read'],
    posts: ['create', 'read', 'update', 'delete'],
    settings: ['read'],
  },
  user: {
    users: [],
    posts: ['create', 'read', 'update'],
    settings: [],
  },
  guest: {
    users: [],
    posts: ['read'],
    settings: [],
  },
};

function hasPermission(
  role: Role,
  resource: Resource,
  action: Permission
): boolean {
  return permissions[role]?.[resource]?.includes(action) ?? false;
}
```

### Hono Auth Middleware

```typescript
import { Hono } from 'hono';
import { jwt } from 'hono/jwt';
import { csrf } from 'hono/csrf';

const app = new Hono();

// CSRF protection
app.use('*', csrf());

// JWT middleware
app.use('/api/*', jwt({ secret: process.env.JWT_SECRET! }));

// Get user from token
app.get('/api/profile', (c) => {
  const payload = c.get('jwtPayload');
  return c.json({ userId: payload.sub });
});
```

### React Native Biometric Auth

```typescript
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

async function authenticateWithBiometrics(): Promise<boolean> {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();

  if (!hasHardware || !isEnrolled) return false;

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to continue',
    disableDeviceFallback: false,
  });

  return result.success;
}

// Store tokens securely
await SecureStore.setItemAsync('accessToken', token, {
  requireAuthentication: true,  // Require biometrics to access
});
```

### Biometric-Protected Token Flow

```typescript
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';

class SecureAuthStorage {
  private static readonly ACCESS_TOKEN_KEY = 'auth_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'auth_refresh_token';

  static async storeTokens(accessToken: string, refreshToken: string): Promise<void> {
    await Promise.all([
      SecureStore.setItemAsync(this.ACCESS_TOKEN_KEY, accessToken),
      SecureStore.setItemAsync(this.REFRESH_TOKEN_KEY, refreshToken, {
        requireAuthentication: true, // Biometric required to read
      }),
    ]);
  }

  static async getAccessToken(): Promise<string | null> {
    return SecureStore.getItemAsync(this.ACCESS_TOKEN_KEY);
  }

  static async getRefreshToken(): Promise<string | null> {
    // This will trigger biometric prompt
    const authenticated = await this.authenticateUser();
    if (!authenticated) return null;

    return SecureStore.getItemAsync(this.REFRESH_TOKEN_KEY);
  }

  static async authenticateUser(): Promise<boolean> {
    const { success } = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Verify your identity',
      cancelLabel: 'Cancel',
      disableDeviceFallback: false,
    });
    return success;
  }

  static async clearTokens(): Promise<void> {
    await Promise.all([
      SecureStore.deleteItemAsync(this.ACCESS_TOKEN_KEY),
      SecureStore.deleteItemAsync(this.REFRESH_TOKEN_KEY),
    ]);
  }
}
```

## Security Checklist

### Authentication
- [ ] Use Argon2id or bcrypt (cost ≥ 12) for password hashing
- [ ] Implement rate limiting on auth endpoints
- [ ] Use secure random tokens (crypto.randomBytes)
- [ ] Validate password strength (min 8 chars, complexity)
- [ ] Implement account lockout after failed attempts

### Tokens & Sessions
- [ ] Short-lived access tokens (15 min)
- [ ] Refresh tokens in httpOnly cookies (web) or SecureStore (mobile)
- [ ] Token rotation on refresh
- [ ] Implement token revocation (blacklist/whitelist)
- [ ] Use JTI for token uniqueness

### Transport & Storage
- [ ] HTTPS everywhere (no exceptions)
- [ ] Secure cookie flags (httpOnly, secure, sameSite)
- [ ] Never store tokens in localStorage (XSS vulnerable)
- [ ] Use Secure Storage on mobile (Keychain/Keystore)

### Protection
- [ ] CSRF protection on state-changing endpoints
- [ ] Validate Origin and Referer headers
- [ ] Implement CORS properly
- [ ] Content Security Policy headers

## Common Patterns

### Login Flow
1. User submits credentials
2. Validate credentials against stored hash
3. Generate access + refresh tokens
4. Set refresh token as httpOnly cookie (web) or SecureStore (mobile)
5. Return access token in response body
6. Client stores access token in memory

### Token Refresh Flow
1. Access token expires
2. Client sends request to refresh endpoint
3. Server validates refresh token from cookie/SecureStore
4. Generate new access + refresh tokens
5. Rotate refresh token (invalidate old)
6. Return new access token

### Logout Flow
1. Clear access token from client memory
2. Clear refresh token cookie/SecureStore
3. Add refresh token to blacklist (if using)
4. Optionally invalidate all user sessions

## Error Handling

```typescript
// Consistent auth error responses
const AuthErrors = {
  INVALID_CREDENTIALS: { code: 'AUTH001', status: 401 },
  TOKEN_EXPIRED: { code: 'AUTH002', status: 401 },
  TOKEN_INVALID: { code: 'AUTH003', status: 401 },
  INSUFFICIENT_PERMISSIONS: { code: 'AUTH004', status: 403 },
  ACCOUNT_LOCKED: { code: 'AUTH005', status: 423 },
  MFA_REQUIRED: { code: 'AUTH006', status: 403 },
  BIOMETRIC_FAILED: { code: 'AUTH007', status: 401 },
  BIOMETRIC_NOT_AVAILABLE: { code: 'AUTH008', status: 400 },
} as const;
```

## Related Skills

- `web_auth_security` - Server-side auth, OWASP guidelines, vulnerability prevention
- `api_development` - API security patterns
- `databases` - User/session schema design
- `backend_security` - Comprehensive security hardening
- `device_hardware` - Additional mobile hardware integrations

---

*Skill Version: 1.0*
