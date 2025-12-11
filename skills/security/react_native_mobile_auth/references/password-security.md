# Password Security

## Overview

Password hashing transforms passwords into irreversible cryptographic hashes for secure storage. Modern algorithms (Argon2, bcrypt, scrypt) are designed to be computationally expensive, making brute-force attacks impractical.

## Algorithm Comparison (2025)

| Algorithm | Recommendation | Memory-Hard | GPU Resistant | Notes |
|-----------|----------------|-------------|---------------|-------|
| Argon2id | ✅ Best choice | Yes | Yes | PHC winner, OWASP recommended |
| bcrypt | ✅ Good | No | Moderate | Widely supported, proven |
| scrypt | ✅ Good | Yes | Yes | Memory-hard alternative |
| PBKDF2 | ⚠️ Legacy | No | No | Only if others unavailable |
| SHA-256 | ❌ Never | No | No | Not designed for passwords |
| MD5 | ❌ Never | No | No | Cryptographically broken |

## Argon2 (Recommended)

### Types
- **Argon2id**: Hybrid, best for password hashing (recommended)
- **Argon2i**: Data-independent, side-channel resistant
- **Argon2d**: Data-dependent, faster but side-channel vulnerable

### Installation

```bash
npm install argon2
```

### Implementation

```typescript
import argon2 from 'argon2';

// Recommended configuration for 2025
const ARGON2_CONFIG = {
  type: argon2.argon2id,
  memoryCost: 65536,    // 64 MB (2^16 KB)
  timeCost: 3,          // 3 iterations
  parallelism: 4,       // 4 threads
  hashLength: 32,       // 32 bytes output
};

// Hash password
async function hashPassword(password: string): Promise<string> {
  return argon2.hash(password, ARGON2_CONFIG);
}

// Verify password
async function verifyPassword(
  hash: string,
  password: string
): Promise<boolean> {
  try {
    return await argon2.verify(hash, password);
  } catch {
    return false;
  }
}

// Check if rehash needed (config changed)
function needsRehash(hash: string): boolean {
  return argon2.needsRehash(hash, ARGON2_CONFIG);
}

// Usage
const hash = await hashPassword('user-password');
// $argon2id$v=19$m=65536,t=3,p=4$randomsalt$hashedvalue

const isValid = await verifyPassword(hash, 'user-password');
// true
```

### Configuration Guidelines

```typescript
// Adjust based on your server capacity
// Target: 0.5-1 second hash time

// Low-end server
const LOW_CONFIG = {
  type: argon2.argon2id,
  memoryCost: 19456,   // 19 MB
  timeCost: 2,
  parallelism: 1,
};

// Standard server (recommended)
const STANDARD_CONFIG = {
  type: argon2.argon2id,
  memoryCost: 65536,   // 64 MB
  timeCost: 3,
  parallelism: 4,
};

// High-security
const HIGH_CONFIG = {
  type: argon2.argon2id,
  memoryCost: 262144,  // 256 MB
  timeCost: 4,
  parallelism: 8,
};
```

## bcrypt (Alternative)

### Installation

```bash
npm install bcrypt
```

### Implementation

```typescript
import bcrypt from 'bcrypt';

// Cost factor: 10-12 for most apps, 12+ for high security
const SALT_ROUNDS = 12;

// Hash password
async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

// Verify password
async function verifyPassword(
  hash: string,
  password: string
): Promise<boolean> {
  try {
    return await bcrypt.compare(password, hash);
  } catch {
    return false;
  }
}

// Usage
const hash = await hashPassword('user-password');
// $2b$12$saltsaltsal.hashedhashedhashedhashed

const isValid = await verifyPassword(hash, 'user-password');
```

### Cost Factor Guidelines

```
Cost 10: ~100ms (minimum recommended)
Cost 11: ~200ms
Cost 12: ~400ms (good balance)
Cost 13: ~800ms
Cost 14: ~1.6s (high security)
```

## Password Validation

### Requirements

```typescript
interface PasswordRequirements {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecial: boolean;
  preventCommon: boolean;
  preventUserInfo: boolean;
}

const DEFAULT_REQUIREMENTS: PasswordRequirements = {
  minLength: 8,          // NIST recommends 8+ (12+ for high security)
  maxLength: 128,        // Prevent DoS with very long passwords
  requireUppercase: false,  // NIST no longer recommends
  requireLowercase: false,
  requireNumbers: false,
  requireSpecial: false,
  preventCommon: true,   // Block common passwords
  preventUserInfo: true, // Block email/username in password
};
```

### Validation Implementation

```typescript
// Common passwords to block (use larger list in production)
const COMMON_PASSWORDS = new Set([
  'password', '123456', '12345678', 'qwerty', 'abc123',
  'password1', '111111', '123123', 'admin', 'letmein',
  'welcome', 'monkey', 'dragon', 'master', 'sunshine',
]);

interface ValidationResult {
  valid: boolean;
  errors: string[];
  strength: 'weak' | 'fair' | 'strong' | 'very-strong';
}

function validatePassword(
  password: string,
  userInfo?: { email?: string; username?: string },
  requirements = DEFAULT_REQUIREMENTS
): ValidationResult {
  const errors: string[] = [];

  // Length checks
  if (password.length < requirements.minLength) {
    errors.push(`Password must be at least ${requirements.minLength} characters`);
  }
  if (password.length > requirements.maxLength) {
    errors.push(`Password must be at most ${requirements.maxLength} characters`);
  }

  // Character type checks (if required)
  if (requirements.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain an uppercase letter');
  }
  if (requirements.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain a lowercase letter');
  }
  if (requirements.requireNumbers && !/\d/.test(password)) {
    errors.push('Password must contain a number');
  }
  if (requirements.requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain a special character');
  }

  // Common password check
  if (requirements.preventCommon) {
    const normalized = password.toLowerCase();
    if (COMMON_PASSWORDS.has(normalized)) {
      errors.push('Password is too common');
    }
  }

  // User info check
  if (requirements.preventUserInfo && userInfo) {
    const lower = password.toLowerCase();
    if (userInfo.email && lower.includes(userInfo.email.split('@')[0].toLowerCase())) {
      errors.push('Password cannot contain your email');
    }
    if (userInfo.username && lower.includes(userInfo.username.toLowerCase())) {
      errors.push('Password cannot contain your username');
    }
  }

  // Calculate strength
  const strength = calculateStrength(password);

  return {
    valid: errors.length === 0,
    errors,
    strength,
  };
}

function calculateStrength(password: string): 'weak' | 'fair' | 'strong' | 'very-strong' {
  let score = 0;

  // Length
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;

  // Character variety
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  // Patterns (deductions)
  if (/(.)\1{2,}/.test(password)) score--;  // Repeated chars
  if (/^[a-zA-Z]+$/.test(password)) score--; // Only letters
  if (/^\d+$/.test(password)) score--;       // Only numbers

  if (score <= 2) return 'weak';
  if (score <= 4) return 'fair';
  if (score <= 6) return 'strong';
  return 'very-strong';
}
```

### Using zxcvbn for Strength Estimation

```typescript
import zxcvbn from 'zxcvbn';

function validatePasswordStrength(
  password: string,
  userInputs: string[] = []  // Email, name, etc.
): { score: number; feedback: string[] } {
  const result = zxcvbn(password, userInputs);

  return {
    score: result.score,  // 0-4 (0=weak, 4=very strong)
    feedback: [
      ...(result.feedback.warning ? [result.feedback.warning] : []),
      ...result.feedback.suggestions,
    ],
  };
}

// Require minimum score
const MIN_SCORE = 2;  // At least "fair"

function isPasswordAcceptable(password: string): boolean {
  const { score } = validatePasswordStrength(password);
  return score >= MIN_SCORE;
}
```

## Secure Password Reset

```typescript
import crypto from 'crypto';

// Generate reset token
function generateResetToken(): { token: string; hash: string; expiresAt: Date } {
  const token = crypto.randomBytes(32).toString('hex');
  const hash = crypto.createHash('sha256').update(token).digest('hex');
  const expiresAt = new Date(Date.now() + 60 * 60 * 1000); // 1 hour

  return { token, hash, expiresAt };
}

// Store hash in database, send token to user
async function initiatePasswordReset(email: string): Promise<void> {
  const user = await db.users.findUnique({ where: { email } });
  
  // Always return success to prevent email enumeration
  if (!user) return;

  const { token, hash, expiresAt } = generateResetToken();

  await db.passwordResets.upsert({
    where: { userId: user.id },
    create: { userId: user.id, tokenHash: hash, expiresAt },
    update: { tokenHash: hash, expiresAt },
  });

  // Send email with token (not hash)
  await sendEmail(email, 'Password Reset', {
    resetUrl: `https://app.example.com/reset?token=${token}`,
  });
}

// Verify token and reset password
async function resetPassword(
  token: string,
  newPassword: string
): Promise<boolean> {
  const hash = crypto.createHash('sha256').update(token).digest('hex');

  const reset = await db.passwordResets.findFirst({
    where: {
      tokenHash: hash,
      expiresAt: { gt: new Date() },
      used: false,
    },
    include: { user: true },
  });

  if (!reset) {
    return false;
  }

  // Validate new password
  const validation = validatePassword(newPassword);
  if (!validation.valid) {
    throw new Error(validation.errors.join(', '));
  }

  // Hash and update password
  const passwordHash = await hashPassword(newPassword);

  await db.$transaction([
    db.users.update({
      where: { id: reset.userId },
      data: { passwordHash },
    }),
    db.passwordResets.update({
      where: { id: reset.id },
      data: { used: true },
    }),
    // Invalidate all sessions
    db.sessions.deleteMany({
      where: { userId: reset.userId },
    }),
  ]);

  return true;
}
```

## Migration from Weaker Algorithms

```typescript
// Gradual migration strategy
async function verifyAndMigrate(
  userId: string,
  password: string,
  storedHash: string
): Promise<boolean> {
  // Detect algorithm from hash format
  const algorithm = detectHashAlgorithm(storedHash);

  let isValid = false;

  switch (algorithm) {
    case 'argon2':
      isValid = await argon2.verify(storedHash, password);
      // Check if needs rehash (config changed)
      if (isValid && argon2.needsRehash(storedHash, ARGON2_CONFIG)) {
        const newHash = await argon2.hash(password, ARGON2_CONFIG);
        await updatePasswordHash(userId, newHash);
      }
      break;

    case 'bcrypt':
      isValid = await bcrypt.compare(password, storedHash);
      // Migrate to Argon2
      if (isValid) {
        const newHash = await argon2.hash(password, ARGON2_CONFIG);
        await updatePasswordHash(userId, newHash);
      }
      break;

    case 'sha256':
      // Legacy - migrate immediately
      const legacyHash = crypto.createHash('sha256').update(password).digest('hex');
      isValid = crypto.timingSafeEqual(
        Buffer.from(storedHash),
        Buffer.from(legacyHash)
      );
      if (isValid) {
        const newHash = await argon2.hash(password, ARGON2_CONFIG);
        await updatePasswordHash(userId, newHash);
      }
      break;
  }

  return isValid;
}

function detectHashAlgorithm(hash: string): string {
  if (hash.startsWith('$argon2')) return 'argon2';
  if (hash.startsWith('$2a$') || hash.startsWith('$2b$')) return 'bcrypt';
  if (hash.length === 64 && /^[a-f0-9]+$/.test(hash)) return 'sha256';
  return 'unknown';
}
```

## OWASP Recommendations (2025)

1. **Use Argon2id** as first choice
2. **bcrypt** with cost ≥ 10 as alternative
3. **Minimum 8 characters**, recommend 12+
4. **No complexity requirements** (NIST guidance)
5. **Block common passwords**
6. **Secure password reset** with time-limited tokens
7. **Rate limit** authentication attempts
8. **Account lockout** after failed attempts
