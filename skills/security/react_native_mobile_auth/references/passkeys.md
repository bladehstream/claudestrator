# Passkeys and WebAuthn Authentication

## Overview

Passkeys are cryptographic credentials that replace passwords. They use public-key cryptography where the private key never leaves the user's device. WebAuthn is the W3C standard that enables passkey support in browsers and applications.

## Key Concepts

```
Passkey = Discoverable FIDO credential
WebAuthn = Browser API for passkey operations
FIDO2 = Umbrella standard (WebAuthn + CTAP2)
CTAP2 = Protocol for external authenticators (YubiKey, etc.)
```

## Benefits

- **Phishing resistant**: Credentials bound to origin, can't be phished
- **No shared secrets**: Private key never transmitted
- **Biometric-friendly**: Uses Face ID, Touch ID, Windows Hello
- **Synced across devices**: iCloud Keychain, Google Password Manager
- **No password fatigue**: Users don't create/remember passwords

## Registration Flow

```
1. User initiates registration
2. Server generates challenge + creation options
3. Browser calls navigator.credentials.create()
4. User authenticates (biometrics/PIN)
5. Authenticator creates key pair
6. Browser returns public key + attestation to server
7. Server stores credential (public key, credential ID)
```

## Authentication Flow

```
1. User initiates login (optionally with username)
2. Server generates challenge + request options
3. Browser calls navigator.credentials.get()
4. User authenticates (biometrics/PIN)
5. Authenticator signs challenge with private key
6. Browser returns signature to server
7. Server verifies signature with stored public key
```

## Server Implementation with SimpleWebAuthn

### Setup

```bash
npm install @simplewebauthn/server @simplewebauthn/types
```

### Registration

```typescript
import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  type VerifiedRegistrationResponse,
} from '@simplewebauthn/server';
import type {
  PublicKeyCredentialCreationOptionsJSON,
  RegistrationResponseJSON,
} from '@simplewebauthn/types';

const RP_NAME = 'My App';
const RP_ID = 'example.com';  // Your domain
const ORIGIN = `https://${RP_ID}`;

// Store challenges temporarily (use Redis in production)
const challengeStore = new Map<string, string>();

// Step 1: Generate registration options
async function getRegistrationOptions(
  userId: string,
  userName: string,
  userDisplayName: string,
  existingCredentials: { id: string; transports?: AuthenticatorTransport[] }[]
): Promise<PublicKeyCredentialCreationOptionsJSON> {
  const options = await generateRegistrationOptions({
    rpName: RP_NAME,
    rpID: RP_ID,
    userID: userId,
    userName,
    userDisplayName,
    // Prevent re-registration of existing credentials
    excludeCredentials: existingCredentials.map(cred => ({
      id: cred.id,
      type: 'public-key',
      transports: cred.transports,
    })),
    authenticatorSelection: {
      residentKey: 'required',      // Discoverable credential (passkey)
      userVerification: 'required', // Require biometrics/PIN
      authenticatorAttachment: 'platform', // Built-in authenticator
    },
    attestationType: 'none', // Don't require attestation
    supportedAlgorithmIDs: [-7, -257], // ES256, RS256
  });

  // Store challenge for verification
  challengeStore.set(userId, options.challenge);

  return options;
}

// Step 2: Verify registration response
async function verifyRegistration(
  userId: string,
  response: RegistrationResponseJSON
): Promise<{
  credentialId: string;
  publicKey: string;
  counter: number;
  transports?: AuthenticatorTransport[];
}> {
  const expectedChallenge = challengeStore.get(userId);
  if (!expectedChallenge) {
    throw new Error('Challenge not found');
  }

  const verification = await verifyRegistrationResponse({
    response,
    expectedChallenge,
    expectedOrigin: ORIGIN,
    expectedRPID: RP_ID,
    requireUserVerification: true,
  });

  if (!verification.verified || !verification.registrationInfo) {
    throw new Error('Registration verification failed');
  }

  // Clean up challenge
  challengeStore.delete(userId);

  const { credentialID, credentialPublicKey, counter } = 
    verification.registrationInfo;

  return {
    credentialId: Buffer.from(credentialID).toString('base64url'),
    publicKey: Buffer.from(credentialPublicKey).toString('base64url'),
    counter,
    transports: response.response.transports,
  };
}
```

### Authentication

```typescript
import {
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';
import type {
  PublicKeyCredentialRequestOptionsJSON,
  AuthenticationResponseJSON,
} from '@simplewebauthn/types';

// Step 1: Generate authentication options
async function getAuthenticationOptions(
  userId?: string  // Optional for discoverable credentials
): Promise<PublicKeyCredentialRequestOptionsJSON> {
  let allowCredentials: { id: string; type: 'public-key'; transports?: AuthenticatorTransport[] }[] = [];

  // If userId provided, limit to their credentials
  if (userId) {
    const userCredentials = await db.credentials.findMany({
      where: { userId },
    });
    allowCredentials = userCredentials.map(cred => ({
      id: cred.credentialId,
      type: 'public-key',
      transports: cred.transports,
    }));
  }

  const options = await generateAuthenticationOptions({
    rpID: RP_ID,
    allowCredentials: allowCredentials.length > 0 ? allowCredentials : undefined,
    userVerification: 'required',
  });

  // Store challenge (key by challenge for discoverable flow)
  const challengeKey = userId || options.challenge;
  challengeStore.set(challengeKey, options.challenge);

  return options;
}

// Step 2: Verify authentication response
async function verifyAuthentication(
  response: AuthenticationResponseJSON,
  challengeKey: string
): Promise<{ userId: string; verified: boolean }> {
  const expectedChallenge = challengeStore.get(challengeKey);
  if (!expectedChallenge) {
    throw new Error('Challenge not found');
  }

  // Find credential in database
  const credential = await db.credentials.findUnique({
    where: { credentialId: response.id },
    include: { user: true },
  });

  if (!credential) {
    throw new Error('Credential not found');
  }

  const verification = await verifyAuthenticationResponse({
    response,
    expectedChallenge,
    expectedOrigin: ORIGIN,
    expectedRPID: RP_ID,
    authenticator: {
      credentialID: Buffer.from(credential.credentialId, 'base64url'),
      credentialPublicKey: Buffer.from(credential.publicKey, 'base64url'),
      counter: credential.counter,
      transports: credential.transports,
    },
    requireUserVerification: true,
  });

  if (!verification.verified) {
    throw new Error('Authentication verification failed');
  }

  // Update counter to prevent replay attacks
  await db.credentials.update({
    where: { credentialId: response.id },
    data: { counter: verification.authenticationInfo.newCounter },
  });

  // Clean up challenge
  challengeStore.delete(challengeKey);

  return {
    userId: credential.userId,
    verified: true,
  };
}
```

## Client Implementation

### Browser Registration

```typescript
import {
  startRegistration,
  browserSupportsWebAuthn,
} from '@simplewebauthn/browser';

async function registerPasskey() {
  // Check support
  if (!browserSupportsWebAuthn()) {
    throw new Error('WebAuthn not supported');
  }

  // Get options from server
  const optionsRes = await fetch('/api/auth/passkey/register/options', {
    method: 'POST',
    credentials: 'include',
  });
  const options = await optionsRes.json();

  // Start registration (prompts user)
  const registrationResponse = await startRegistration(options);

  // Send response to server for verification
  const verifyRes = await fetch('/api/auth/passkey/register/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(registrationResponse),
  });

  return verifyRes.json();
}
```

### Browser Authentication

```typescript
import {
  startAuthentication,
  browserSupportsWebAuthnAutofill,
} from '@simplewebauthn/browser';

// Standard authentication
async function authenticateWithPasskey() {
  const optionsRes = await fetch('/api/auth/passkey/authenticate/options');
  const options = await optionsRes.json();

  const authResponse = await startAuthentication(options);

  const verifyRes = await fetch('/api/auth/passkey/authenticate/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(authResponse),
  });

  return verifyRes.json();
}

// Conditional UI (autofill-style)
async function setupConditionalUI() {
  if (!await browserSupportsWebAuthnAutofill()) {
    return;
  }

  const optionsRes = await fetch('/api/auth/passkey/authenticate/options');
  const options = await optionsRes.json();

  try {
    // This shows passkeys in browser autofill
    const authResponse = await startAuthentication(options, true);
    
    // User selected a passkey from autofill
    const verifyRes = await fetch('/api/auth/passkey/authenticate/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(authResponse),
    });

    return verifyRes.json();
  } catch (error) {
    // User cancelled or no passkeys available
    console.log('Conditional UI cancelled');
  }
}
```

## React Native Implementation

```typescript
// Using react-native-passkeys
import { Passkeys } from 'react-native-passkeys';

// Check availability
const isSupported = Passkeys.isSupported();

// Registration
async function registerPasskey(options: any) {
  try {
    const result = await Passkeys.create(options);
    return result;
  } catch (error) {
    if (error.code === 'ERR_USER_CANCELLED') {
      return null;
    }
    throw error;
  }
}

// Authentication
async function authenticateWithPasskey(options: any) {
  try {
    const result = await Passkeys.get(options);
    return result;
  } catch (error) {
    if (error.code === 'ERR_USER_CANCELLED') {
      return null;
    }
    throw error;
  }
}
```

## Database Schema

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Passkey credentials table
CREATE TABLE credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  credential_id VARCHAR(512) UNIQUE NOT NULL,
  public_key TEXT NOT NULL,
  counter BIGINT DEFAULT 0,
  transports TEXT[], -- Array of transport types
  device_type VARCHAR(50), -- 'singleDevice' or 'multiDevice'
  backed_up BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  last_used_at TIMESTAMP
);

CREATE INDEX idx_credentials_user_id ON credentials(user_id);
CREATE INDEX idx_credentials_credential_id ON credentials(credential_id);
```

## Hono API Routes

```typescript
import { Hono } from 'hono';

const passkeys = new Hono();

// Registration
passkeys.post('/register/options', async (c) => {
  const user = c.get('user');  // From auth middleware
  if (!user) return c.json({ error: 'Unauthorized' }, 401);

  const existingCredentials = await db.credentials.findMany({
    where: { userId: user.id },
    select: { credentialId: true, transports: true },
  });

  const options = await getRegistrationOptions(
    user.id,
    user.email,
    user.name,
    existingCredentials.map(c => ({
      id: c.credentialId,
      transports: c.transports,
    }))
  );

  return c.json(options);
});

passkeys.post('/register/verify', async (c) => {
  const user = c.get('user');
  if (!user) return c.json({ error: 'Unauthorized' }, 401);

  const body = await c.req.json();
  
  const credential = await verifyRegistration(user.id, body);

  await db.credentials.create({
    data: {
      userId: user.id,
      credentialId: credential.credentialId,
      publicKey: credential.publicKey,
      counter: credential.counter,
      transports: credential.transports,
    },
  });

  return c.json({ success: true });
});

// Authentication
passkeys.post('/authenticate/options', async (c) => {
  const options = await getAuthenticationOptions();
  return c.json(options);
});

passkeys.post('/authenticate/verify', async (c) => {
  const body = await c.req.json();
  
  const result = await verifyAuthentication(body, body.response.clientDataJSON);

  // Create session or JWT
  const tokens = generateTokens({ id: result.userId });

  return c.json({
    success: true,
    accessToken: tokens.accessToken,
  });
});

export default passkeys;
```

## Security Considerations

1. **Challenge expiration**: Expire challenges after 1-5 minutes
2. **Counter validation**: Always update and verify counter
3. **Origin validation**: Strictly validate expected origin
4. **User verification**: Require biometrics/PIN for sensitive operations
5. **Backup status**: Track backed_up flag for security policies
6. **Credential revocation**: Allow users to revoke compromised credentials
7. **Fallback methods**: Provide recovery options (email, backup codes)

## Migration Strategy

```
Phase 1: Add passkeys as additional auth method
         - Users with password can add passkey
         - Either method works for login

Phase 2: Encourage passkey adoption
         - Prompt users to add passkey after password login
         - Show security benefits

Phase 3: Optional passwordless
         - Allow new users to register with passkey only
         - Existing users can remove password

Phase 4: Password deprecation (optional)
         - Strongly encourage migration
         - Keep password as recovery fallback
```
