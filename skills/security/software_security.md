---
name: Software Security Expert
id: software_security
version: 1.1
category: security
domain: [backend, frontend, api, web, mobile]
task_types: [implementation, security]
keywords: [secure coding, input validation, parameterized query, output encoding, encryption, hashing, secrets management, defense in depth, least privilege]
complexity: [normal, complex]
pairs_with: [authentication, api_designer, security_reviewer]
source: Adapted from Project CodeGuard software-security framework
---

# Software Security Expert

## Role

You implement secure-by-default code during development. You apply OWASP guidelines, validate inputs, prevent injection attacks, and follow defense-in-depth principles. Use this skill when writing new code or modifying existing code. For reviewing code after it's written, use `security_reviewer` instead.

## Core Competencies

- Input validation and sanitization
- Injection prevention (SQL, XSS, command)
- Secure data handling
- Cryptography best practices
- Authentication/authorization patterns
- Secure configuration
- Secrets management

## Universal Security Rules

### ALWAYS Apply (Every Code Change)

#### 1. No Hardcoded Credentials
```javascript
// ❌ NEVER
const apiKey = "sk-1234567890abcdef";
const dbPassword = "secretpassword";

// ✅ ALWAYS
const apiKey = process.env.API_KEY;
const dbPassword = process.env.DB_PASSWORD;
```

#### 2. Modern Cryptography Only
```javascript
// ❌ NEVER - Broken/weak algorithms
crypto.createHash('md5');
crypto.createHash('sha1');
crypto.createCipher('des', key);

// ✅ ALWAYS - Modern algorithms
crypto.createHash('sha256');
crypto.createHash('sha3-256');
crypto.createCipheriv('aes-256-gcm', key, iv);
```

#### 3. Validate Certificates
```javascript
// ❌ NEVER - Disabling verification
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
{ rejectUnauthorized: false }

// ✅ ALWAYS - Proper certificate handling
// Use default verification, or pin specific certs
```

## Input Validation

### Validate at System Boundaries
```javascript
// API endpoint - validate everything from client
app.post('/api/transactions', (req, res) => {
  const { amount, category, date } = req.body;

  // Type validation
  if (typeof amount !== 'number' || isNaN(amount)) {
    return res.status(400).json({ error: 'Invalid amount' });
  }

  // Range validation
  if (amount < -1000000 || amount > 1000000) {
    return res.status(400).json({ error: 'Amount out of range' });
  }

  // Format validation
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return res.status(400).json({ error: 'Invalid date format' });
  }

  // Allowlist validation
  const validCategories = ['income', 'expense', 'transfer'];
  if (!validCategories.includes(category)) {
    return res.status(400).json({ error: 'Invalid category' });
  }

  // Proceed with validated data
});
```

### Schema Validation (Recommended)
```javascript
import { z } from 'zod';

const TransactionSchema = z.object({
  amount: z.number().min(-1000000).max(1000000),
  category: z.enum(['income', 'expense', 'transfer']),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  description: z.string().max(500).optional(),
});

// Usage
const result = TransactionSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ errors: result.error.issues });
}
const validatedData = result.data;
```

## Injection Prevention

### SQL Injection
```javascript
// ❌ NEVER - String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;
const query = `SELECT * FROM users WHERE name = '${name}'`;

// ✅ ALWAYS - Parameterized queries
// Node.js (pg)
const result = await db.query(
  'SELECT * FROM users WHERE id = $1',
  [userId]
);

// Node.js (mysql2)
const [rows] = await db.execute(
  'SELECT * FROM users WHERE name = ?',
  [name]
);

// Prisma (ORM)
const user = await prisma.user.findUnique({
  where: { id: userId }
});
```

### XSS (Cross-Site Scripting)
```javascript
// ❌ NEVER - Direct HTML insertion
element.innerHTML = userInput;
document.write(userInput);

// ✅ ALWAYS - Text content or sanitization
element.textContent = userInput;

// If HTML is required, sanitize
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);

// React auto-escapes, but avoid:
// ❌ dangerouslySetInnerHTML={{ __html: userInput }}
```

### Command Injection
```javascript
// ❌ NEVER - Shell execution with user input
exec(`convert ${userFilename} output.png`);
exec(`grep ${searchTerm} logfile.txt`);

// ✅ ALWAYS - Use arrays, avoid shell
import { execFile } from 'child_process';
execFile('convert', [userFilename, 'output.png']);

// Or validate strictly
const allowedPattern = /^[a-zA-Z0-9_-]+\.png$/;
if (!allowedPattern.test(userFilename)) {
  throw new Error('Invalid filename');
}
```

### Path Traversal
```javascript
// ❌ NEVER - Direct path concatenation
const filepath = `/uploads/${userInput}`;
fs.readFile(filepath);

// ✅ ALWAYS - Validate and resolve
import path from 'path';

const uploadsDir = '/var/app/uploads';
const requestedPath = path.join(uploadsDir, userInput);
const resolvedPath = path.resolve(requestedPath);

// Ensure path stays within allowed directory
if (!resolvedPath.startsWith(uploadsDir)) {
  throw new Error('Invalid path');
}
fs.readFile(resolvedPath);
```

## Secure Data Handling

### Sensitive Data in Logs
```javascript
// ❌ NEVER - Log sensitive data
console.log('User login:', { email, password });
console.log('Payment:', { cardNumber, cvv });

// ✅ ALWAYS - Redact sensitive fields
console.log('User login:', { email, password: '[REDACTED]' });
console.log('Payment:', { cardLast4: cardNumber.slice(-4) });

// Use structured logging with redaction
const logger = pino({
  redact: ['password', 'token', 'cardNumber', 'ssn']
});
```

### Sensitive Data in URLs
```javascript
// ❌ NEVER - Secrets in URL (logged, cached, referrer)
fetch(`/api/data?token=${apiToken}`);
redirect(`/reset?token=${resetToken}`);

// ✅ ALWAYS - Use headers or POST body
fetch('/api/data', {
  headers: { 'Authorization': `Bearer ${apiToken}` }
});

// For one-time tokens, POST immediately
fetch('/api/reset', {
  method: 'POST',
  body: JSON.stringify({ token: resetToken })
});
```

### Secure Comparison
```javascript
// ❌ NEVER - Timing attack vulnerable
if (userToken === storedToken) { }

// ✅ ALWAYS - Constant-time comparison
import { timingSafeEqual } from 'crypto';

const userBuffer = Buffer.from(userToken);
const storedBuffer = Buffer.from(storedToken);

if (userBuffer.length !== storedBuffer.length) {
  return false;
}
return timingSafeEqual(userBuffer, storedBuffer);
```

## Secrets Management

### Environment Variables
```bash
# .env (NEVER commit)
DATABASE_URL=postgres://user:pass@host:5432/db
API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
JWT_SECRET=your-256-bit-secret

# .env.example (commit this)
DATABASE_URL=postgres://user:pass@localhost:5432/myapp
API_KEY=your-api-key-here
JWT_SECRET=generate-a-secure-random-string
```

### Secret Rotation
```javascript
// Support multiple valid secrets during rotation
const validSecrets = [
  process.env.JWT_SECRET,
  process.env.JWT_SECRET_PREVIOUS, // During rotation period
].filter(Boolean);

function verifyToken(token) {
  for (const secret of validSecrets) {
    try {
      return jwt.verify(token, secret);
    } catch (e) {
      continue;
    }
  }
  throw new Error('Invalid token');
}
```

## HTTP Security Headers

```javascript
// Express.js with helmet
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Key headers:
// Content-Security-Policy - Prevent XSS
// Strict-Transport-Security - Force HTTPS
// X-Content-Type-Options: nosniff - Prevent MIME sniffing
// X-Frame-Options: DENY - Prevent clickjacking
// Referrer-Policy: strict-origin-when-cross-origin
```

## OWASP Top 10 Quick Reference

| Risk | Prevention |
|------|------------|
| A01 Broken Access Control | Check authorization on every request |
| A02 Cryptographic Failures | Use strong algorithms, protect data at rest/transit |
| A03 Injection | Parameterized queries, input validation |
| A04 Insecure Design | Threat modeling, secure design patterns |
| A05 Security Misconfiguration | Harden defaults, remove unnecessary features |
| A06 Vulnerable Components | Keep dependencies updated, audit regularly |
| A07 Auth Failures | See authentication skill |
| A08 Data Integrity Failures | Verify signatures, use integrity checks |
| A09 Logging Failures | Log security events, protect logs |
| A10 SSRF | Validate URLs, allowlist destinations |

## Security Review Checklist

### Before Code Review
- [ ] No hardcoded credentials
- [ ] All inputs validated at boundaries
- [ ] Parameterized queries for database
- [ ] Output encoding for user content
- [ ] Secrets from environment variables
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Dependencies audited (`npm audit`)

### For Sensitive Operations
- [ ] Authentication required
- [ ] Authorization checked
- [ ] Rate limiting applied
- [ ] Audit logging enabled
- [ ] Error messages don't leak info

## Output Expectations

When this skill is applied, the agent should:

- [ ] Validate all external inputs
- [ ] Use parameterized queries
- [ ] Prevent XSS in output
- [ ] Never hardcode secrets
- [ ] Use modern cryptography
- [ ] Apply principle of least privilege
- [ ] Add security-relevant comments

---

*Skill Version: 1.0*
*Adapted from: Project CodeGuard software-security framework*
