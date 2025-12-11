# Multi-Factor Authentication (MFA) with TOTP

## Overview

TOTP (Time-based One-Time Password) generates 6-digit codes that change every 30 seconds. Users scan a QR code with authenticator apps (Google Authenticator, Authy, 1Password) and provide codes during login.

## Libraries

| Library | Status | Notes |
|---------|--------|-------|
| `otpauth` | ✅ Active | Recommended, modern |
| `otplib` | ⚠️ Maintained | Good alternative |
| `speakeasy` | ❌ Deprecated | Do not use for new projects |

## Implementation with otpauth

### Setup

```bash
npm install otpauth qrcode
npm install -D @types/qrcode
```

### Generate Secret

```typescript
import * as OTPAuth from 'otpauth';
import * as QRCode from 'qrcode';

interface TOTPSetup {
  secret: string;        // Base32 encoded secret
  qrCodeUrl: string;     // Data URL for QR code image
  otpauthUrl: string;    // URL for manual entry
}

async function generateTOTPSetup(
  userEmail: string,
  issuer: string = 'MyApp'
): Promise<TOTPSetup> {
  // Generate random secret
  const secret = new OTPAuth.Secret({ size: 20 });

  // Create TOTP instance
  const totp = new OTPAuth.TOTP({
    issuer,
    label: userEmail,
    algorithm: 'SHA1',
    digits: 6,
    period: 30,
    secret,
  });

  // Generate otpauth URL
  const otpauthUrl = totp.toString();

  // Generate QR code as data URL
  const qrCodeUrl = await QRCode.toDataURL(otpauthUrl, {
    width: 200,
    margin: 2,
    color: {
      dark: '#000000',
      light: '#ffffff',
    },
  });

  return {
    secret: secret.base32,
    qrCodeUrl,
    otpauthUrl,
  };
}
```

### Verify TOTP Code

```typescript
function verifyTOTPCode(secret: string, token: string): boolean {
  const totp = new OTPAuth.TOTP({
    algorithm: 'SHA1',
    digits: 6,
    period: 30,
    secret: OTPAuth.Secret.fromBase32(secret),
  });

  // Validate with ±1 window (allows for clock drift)
  const delta = totp.validate({ token, window: 1 });

  // delta is null if invalid, or the time step difference if valid
  return delta !== null;
}

// More secure: track used tokens to prevent replay
async function verifyTOTPCodeSecure(
  userId: string,
  secret: string,
  token: string,
  db: Database
): Promise<boolean> {
  const totp = new OTPAuth.TOTP({
    algorithm: 'SHA1',
    digits: 6,
    period: 30,
    secret: OTPAuth.Secret.fromBase32(secret),
  });

  const delta = totp.validate({ token, window: 1 });
  if (delta === null) return false;

  // Calculate current time step
  const timeStep = Math.floor(Date.now() / 30000);
  const usedTimeStep = timeStep + delta;

  // Check if this time step was already used
  const lastUsedStep = await db.getLastUsedTOTPStep(userId);
  if (lastUsedStep && usedTimeStep <= lastUsedStep) {
    return false;  // Replay attack prevention
  }

  // Store this time step as used
  await db.setLastUsedTOTPStep(userId, usedTimeStep);

  return true;
}
```

## Backup/Recovery Codes

```typescript
import crypto from 'crypto';

// Generate backup codes (one-time use)
function generateBackupCodes(count: number = 10): string[] {
  return Array.from({ length: count }, () =>
    crypto.randomBytes(4).toString('hex').toUpperCase()
  );
}

// Format: XXXX-XXXX
function formatBackupCode(code: string): string {
  return `${code.slice(0, 4)}-${code.slice(4)}`;
}

// Store hashed backup codes
async function storeBackupCodes(
  userId: string,
  codes: string[],
  db: Database
): Promise<void> {
  const hashedCodes = await Promise.all(
    codes.map(async (code) => ({
      hash: crypto.createHash('sha256').update(code).digest('hex'),
      used: false,
    }))
  );

  await db.mfaBackupCodes.createMany({
    data: hashedCodes.map((c) => ({
      userId,
      codeHash: c.hash,
      used: false,
    })),
  });
}

// Verify and consume backup code
async function verifyBackupCode(
  userId: string,
  code: string,
  db: Database
): Promise<boolean> {
  const normalizedCode = code.replace(/-/g, '').toUpperCase();
  const hash = crypto.createHash('sha256').update(normalizedCode).digest('hex');

  const backupCode = await db.mfaBackupCodes.findFirst({
    where: { userId, codeHash: hash, used: false },
  });

  if (!backupCode) return false;

  // Mark as used
  await db.mfaBackupCodes.update({
    where: { id: backupCode.id },
    data: { used: true, usedAt: new Date() },
  });

  return true;
}
```

## Database Schema

```sql
-- MFA settings
CREATE TABLE mfa_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  totp_secret TEXT,  -- Encrypted in production
  totp_enabled BOOLEAN DEFAULT FALSE,
  totp_verified_at TIMESTAMP,
  last_used_step BIGINT,  -- For replay prevention
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Backup codes
CREATE TABLE mfa_backup_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  code_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash
  used BOOLEAN DEFAULT FALSE,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_backup_codes_user ON mfa_backup_codes(user_id, used);
```

## API Endpoints

```typescript
import { Hono } from 'hono';

const mfa = new Hono();

// Start TOTP setup
mfa.post('/setup/totp', async (c) => {
  const user = c.get('user');
  
  const setup = await generateTOTPSetup(user.email, 'MyApp');

  // Store secret temporarily (not enabled yet)
  await db.mfaSettings.upsert({
    where: { userId: user.id },
    create: {
      userId: user.id,
      totpSecret: encrypt(setup.secret),  // Encrypt secret!
      totpEnabled: false,
    },
    update: {
      totpSecret: encrypt(setup.secret),
      totpEnabled: false,
    },
  });

  return c.json({
    qrCode: setup.qrCodeUrl,
    secret: setup.secret,  // For manual entry
  });
});

// Verify and enable TOTP
mfa.post('/verify/totp', async (c) => {
  const user = c.get('user');
  const { code } = await c.req.json();

  const settings = await db.mfaSettings.findUnique({
    where: { userId: user.id },
  });

  if (!settings?.totpSecret) {
    return c.json({ error: 'TOTP not set up' }, 400);
  }

  const secret = decrypt(settings.totpSecret);
  const isValid = verifyTOTPCode(secret, code);

  if (!isValid) {
    return c.json({ error: 'Invalid code' }, 400);
  }

  // Enable TOTP
  await db.mfaSettings.update({
    where: { userId: user.id },
    data: {
      totpEnabled: true,
      totpVerifiedAt: new Date(),
    },
  });

  // Generate backup codes
  const backupCodes = generateBackupCodes(10);
  await storeBackupCodes(user.id, backupCodes, db);

  return c.json({
    enabled: true,
    backupCodes: backupCodes.map(formatBackupCode),
  });
});

// Disable TOTP (requires verification)
mfa.post('/disable/totp', async (c) => {
  const user = c.get('user');
  const { code, password } = await c.req.json();

  // Verify password first
  const passwordValid = await verifyPassword(user.passwordHash, password);
  if (!passwordValid) {
    return c.json({ error: 'Invalid password' }, 401);
  }

  const settings = await db.mfaSettings.findUnique({
    where: { userId: user.id },
  });

  if (!settings?.totpEnabled) {
    return c.json({ error: 'TOTP not enabled' }, 400);
  }

  // Verify TOTP code
  const secret = decrypt(settings.totpSecret);
  const isValid = verifyTOTPCode(secret, code);

  if (!isValid) {
    return c.json({ error: 'Invalid code' }, 400);
  }

  // Disable TOTP
  await db.mfaSettings.update({
    where: { userId: user.id },
    data: {
      totpEnabled: false,
      totpSecret: null,
    },
  });

  // Delete backup codes
  await db.mfaBackupCodes.deleteMany({
    where: { userId: user.id },
  });

  return c.json({ disabled: true });
});

export default mfa;
```

## Login Flow with MFA

```typescript
// Step 1: Initial login (returns MFA requirement)
app.post('/auth/login', async (c) => {
  const { email, password } = await c.req.json();

  const user = await db.users.findUnique({
    where: { email },
    include: { mfaSettings: true },
  });

  if (!user || !await verifyPassword(user.passwordHash, password)) {
    return c.json({ error: 'Invalid credentials' }, 401);
  }

  // Check if MFA is enabled
  if (user.mfaSettings?.totpEnabled) {
    // Create temporary MFA session
    const mfaToken = crypto.randomBytes(32).toString('hex');
    await db.mfaSession.create({
      data: {
        token: mfaToken,
        userId: user.id,
        expiresAt: new Date(Date.now() + 5 * 60 * 1000),  // 5 minutes
      },
    });

    return c.json({
      requiresMfa: true,
      mfaToken,
      mfaMethods: ['totp', 'backup'],
    });
  }

  // No MFA - issue tokens
  const tokens = generateTokens(user);
  return c.json({ tokens, user: sanitizeUser(user) });
});

// Step 2: Verify MFA
app.post('/auth/mfa/verify', async (c) => {
  const { mfaToken, code, method } = await c.req.json();

  const session = await db.mfaSession.findFirst({
    where: {
      token: mfaToken,
      expiresAt: { gt: new Date() },
    },
    include: {
      user: { include: { mfaSettings: true } },
    },
  });

  if (!session) {
    return c.json({ error: 'Invalid or expired MFA session' }, 401);
  }

  let isValid = false;

  if (method === 'totp') {
    const secret = decrypt(session.user.mfaSettings!.totpSecret!);
    isValid = await verifyTOTPCodeSecure(
      session.userId,
      secret,
      code,
      db
    );
  } else if (method === 'backup') {
    isValid = await verifyBackupCode(session.userId, code, db);
  }

  if (!isValid) {
    return c.json({ error: 'Invalid code' }, 401);
  }

  // Delete MFA session
  await db.mfaSession.delete({ where: { id: session.id } });

  // Issue tokens
  const tokens = generateTokens(session.user);
  return c.json({ tokens, user: sanitizeUser(session.user) });
});
```

## React Native TOTP Input

```typescript
import { useState, useRef } from 'react';
import { View, TextInput, StyleSheet } from 'react-native';

interface TOTPInputProps {
  length?: number;
  onComplete: (code: string) => void;
}

export function TOTPInput({ length = 6, onComplete }: TOTPInputProps) {
  const [code, setCode] = useState(Array(length).fill(''));
  const inputs = useRef<TextInput[]>([]);

  const handleChange = (text: string, index: number) => {
    if (!/^\d*$/.test(text)) return;

    const newCode = [...code];
    newCode[index] = text;
    setCode(newCode);

    // Auto-advance to next input
    if (text && index < length - 1) {
      inputs.current[index + 1]?.focus();
    }

    // Check if complete
    if (newCode.every((digit) => digit) && newCode.join('').length === length) {
      onComplete(newCode.join(''));
    }
  };

  const handleKeyPress = (e: any, index: number) => {
    if (e.nativeEvent.key === 'Backspace' && !code[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  return (
    <View style={styles.container}>
      {code.map((digit, index) => (
        <TextInput
          key={index}
          ref={(ref) => { if (ref) inputs.current[index] = ref; }}
          style={styles.input}
          value={digit}
          onChangeText={(text) => handleChange(text, index)}
          onKeyPress={(e) => handleKeyPress(e, index)}
          keyboardType="number-pad"
          maxLength={1}
          selectTextOnFocus
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  input: {
    width: 48,
    height: 56,
    borderWidth: 2,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    fontSize: 24,
    textAlign: 'center',
  },
});
```

## Security Considerations

1. **Encrypt secrets** at rest in database
2. **Rate limit** verification attempts (5 attempts per 5 minutes)
3. **Prevent replay** by tracking used time steps
4. **Time synchronization** - use ±1 window for clock drift
5. **Secure backup codes** - hash and one-time use
6. **MFA session timeout** - 5 minutes maximum
7. **Require password** to disable MFA
8. **Audit logging** for MFA events
