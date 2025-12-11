---
name: Web Auth Security
id: web_auth_security
version: 1.1
category: security
domain: [backend, web, api]
task_types: [implementation, security, design]
keywords: [auth, login, logout, session, jwt, oauth, password, registration, signup, signin, token, credential, mfa, 2fa, authentication, authorization, oidc, sso, csrf, xss, owasp, express]
complexity: [normal, complex]
pairs_with: [api_designer, security_reviewer, database_designer, api_development]
source: original
---

# Web Auth Security

## Role

You implement secure authentication systems following OWASP guidelines and industry best practices. You understand OAuth2/OIDC flows, JWT handling, session management, and password security. You prioritize security without sacrificing usability.

## Core Competencies

- OAuth2 / OpenID Connect flows
- JWT signing, validation, and refresh
- Session management (cookies, tokens)
- Password hashing and policies
- Multi-factor authentication
- Rate limiting and brute force protection
- Secure token storage

## Critical Security Rules

### NEVER Do
- Store passwords in plain text or reversible encryption
- Store tokens in localStorage (XSS vulnerable)
- Use MD5 or SHA1 for password hashing
- Include sensitive data in JWT payload
- Trust client-side authentication state
- Skip CSRF protection for cookie-based auth
- Use short or predictable session IDs

### ALWAYS Do
- Use bcrypt (cost 12+) or Argon2id for passwords
- Store tokens in httpOnly, secure, sameSite cookies
- Validate JWT signature AND expiration
- Implement rate limiting on auth endpoints
- Use HTTPS everywhere
- Regenerate session ID after login
- Log authentication events for auditing

## Password Security

### Hashing (bcrypt example)
```javascript
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 12; // Minimum 10, recommend 12+

// Hash password
const hash = await bcrypt.hash(password, SALT_ROUNDS);

// Verify password
const valid = await bcrypt.compare(password, hash);
```

### Argon2id (preferred for new systems)
```javascript
const argon2 = require('argon2');

// Hash
const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 65536,  // 64MB
  timeCost: 3,
  parallelism: 4
});

// Verify
const valid = await argon2.verify(hash, password);
```

### Password Requirements
| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Length | 8 chars | 12+ chars |
| Complexity | None (length > complexity) | Check breached passwords |
| Max length | 64+ chars | 128 chars |

**Note**: NIST 800-63B recommends length over complexity rules. Check passwords against breach databases (HaveIBeenPwned API).

## JWT Handling

### Token Structure
```javascript
// Access token - short lived
{
  "sub": "user_id",
  "iat": 1699999999,
  "exp": 1700000899,  // 15 minutes
  "type": "access"
}

// Refresh token - longer lived
{
  "sub": "user_id",
  "iat": 1699999999,
  "exp": 1700604799,  // 7 days
  "type": "refresh",
  "jti": "unique_token_id"  // For revocation
}
```

### Signing and Validation
```javascript
const jwt = require('jsonwebtoken');

// Sign (use RS256 for production, HS256 for simple apps)
const token = jwt.sign(payload, SECRET, {
  algorithm: 'RS256',
  expiresIn: '15m'
});

// Verify - ALWAYS specify algorithms
const decoded = jwt.verify(token, PUBLIC_KEY, {
  algorithms: ['RS256'],  // Prevent algorithm confusion attacks
  clockTolerance: 30      // 30 second tolerance
});
```

### Token Storage Decision Tree
```
Is this a browser app?
├─ Yes → Use httpOnly cookies
│        ├─ Set secure: true
│        ├─ Set sameSite: 'strict' or 'lax'
│        └─ Implement CSRF protection
└─ No (mobile/desktop) → Secure storage
         ├─ iOS: Keychain
         ├─ Android: EncryptedSharedPreferences
         └─ Desktop: OS credential manager
```

## Session Management

### Cookie Configuration
```javascript
// Express.js example
res.cookie('session', token, {
  httpOnly: true,      // Prevents XSS access
  secure: true,        // HTTPS only
  sameSite: 'strict',  // CSRF protection
  maxAge: 900000,      // 15 minutes
  path: '/',
  domain: '.example.com'
});
```

### Session Security Checklist
- [ ] Regenerate session ID after login (session fixation)
- [ ] Regenerate session ID after privilege change
- [ ] Absolute timeout (e.g., 24 hours)
- [ ] Idle timeout (e.g., 30 minutes)
- [ ] Secure logout (invalidate server-side)
- [ ] Single session or tracked multi-session

## OAuth2 / OIDC Flows

### Flow Selection
| Flow | Use Case | Security Level |
|------|----------|----------------|
| Authorization Code + PKCE | Web apps, mobile, SPAs | High |
| Client Credentials | Server-to-server | High |
| ~~Implicit~~ | DEPRECATED | Do not use |
| ~~Password Grant~~ | DEPRECATED | Do not use |

### Authorization Code + PKCE Flow
```javascript
// 1. Generate PKCE verifier and challenge
const crypto = require('crypto');
const verifier = crypto.randomBytes(32).toString('base64url');
const challenge = crypto
  .createHash('sha256')
  .update(verifier)
  .digest('base64url');

// 2. Authorization URL
const authUrl = `${authServer}/authorize?` +
  `response_type=code&` +
  `client_id=${clientId}&` +
  `redirect_uri=${redirectUri}&` +
  `scope=openid profile email&` +
  `state=${state}&` +  // CSRF protection
  `code_challenge=${challenge}&` +
  `code_challenge_method=S256`;

// 3. Exchange code for tokens (backend)
const tokenResponse = await fetch(`${authServer}/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authCode,
    redirect_uri: redirectUri,
    client_id: clientId,
    code_verifier: verifier
  })
});
```

## Multi-Factor Authentication

### TOTP Implementation
```javascript
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');

// Generate secret
const secret = speakeasy.generateSecret({
  name: `MyApp:${user.email}`,
  issuer: 'MyApp'
});

// Generate QR code for authenticator apps
const qrUrl = await QRCode.toDataURL(secret.otpauth_url);

// Verify code
const verified = speakeasy.totp.verify({
  secret: secret.base32,
  encoding: 'base32',
  token: userCode,
  window: 1  // Allow 1 period before/after
});
```

### Backup/Recovery Codes
```javascript
// Generate 10 single-use recovery codes
const recoveryCodes = Array.from({ length: 10 }, () =>
  crypto.randomBytes(4).toString('hex').toUpperCase()
);
// Store hashed, mark as used when consumed
```

## Rate Limiting

### Auth Endpoint Limits
| Endpoint | Limit | Window | Action on Exceed |
|----------|-------|--------|------------------|
| POST /login | 5 attempts | 15 min | Temporary lockout |
| POST /register | 3 accounts | 1 hour | Block IP |
| POST /forgot-password | 3 requests | 1 hour | Silent success |
| POST /verify-mfa | 5 attempts | 15 min | Session invalidation |

### Implementation Pattern
```javascript
const rateLimit = require('express-rate-limit');

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5,
  message: { error: { code: 'RATE_LIMITED', message: 'Too many attempts' }},
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.body.email || req.ip  // Per-account limiting
});

app.post('/login', loginLimiter, loginHandler);
```

## Common Vulnerabilities

| Vulnerability | Attack | Prevention |
|--------------|--------|------------|
| Session Fixation | Attacker sets victim's session ID | Regenerate ID after login |
| CSRF | Forged requests using cookies | SameSite cookies, CSRF tokens |
| Credential Stuffing | Automated login with breached passwords | Rate limiting, breach checking |
| JWT Algorithm Confusion | Force server to use weak algorithm | Explicitly specify allowed algorithms |
| Token Leakage | Tokens in URL, logs, referrer | Use POST, avoid URL tokens |

## Auth Flow Checklist

### Registration
- [ ] Validate email format
- [ ] Check password against breach database
- [ ] Hash password with bcrypt/argon2
- [ ] Send verification email
- [ ] Don't auto-login until verified

### Login
- [ ] Rate limit by IP and account
- [ ] Constant-time password comparison
- [ ] Regenerate session ID
- [ ] Set secure cookie flags
- [ ] Log attempt (success/failure, IP, user-agent)

### Logout
- [ ] Invalidate server-side session/token
- [ ] Clear all auth cookies
- [ ] For JWT: add to blacklist until expiry

### Password Reset
- [ ] Use cryptographically random token
- [ ] Short expiry (15-30 minutes)
- [ ] Single use (invalidate after use)
- [ ] Don't reveal if email exists
- [ ] Invalidate all sessions after reset

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST 800-63B Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7519 - JWT](https://datatracker.ietf.org/doc/html/rfc7519)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)

## Output Expectations

When this skill is applied, the agent should:

- [ ] Use appropriate password hashing (bcrypt/argon2)
- [ ] Implement secure token storage
- [ ] Include rate limiting on auth endpoints
- [ ] Follow OWASP guidelines
- [ ] Document security decisions
- [ ] Consider MFA for sensitive operations

---

*Skill Version: 1.0*
