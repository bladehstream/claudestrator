# OAuth 2.0 and PKCE Authentication

## Overview

OAuth 2.0 is the industry standard for authorization. PKCE (Proof Key for Code Exchange) is a security extension required for mobile apps and SPAs where client secrets cannot be safely stored.

## When to Use PKCE

```
✅ Mobile apps (React Native, iOS, Android)
✅ Single-page applications (React, Vue, Angular)
✅ Desktop applications
✅ Any public client that can't store secrets

❌ Server-side applications with secure secret storage
   (can use standard Authorization Code flow)
```

## PKCE Flow

```
1. Client generates code_verifier (random string)
2. Client creates code_challenge = SHA256(code_verifier)
3. Client redirects to authorization server with code_challenge
4. User authenticates and approves
5. Authorization server redirects back with authorization code
6. Client exchanges code + code_verifier for tokens
7. Server verifies SHA256(code_verifier) === stored code_challenge
8. Server issues access token and refresh token
```

## Implementation

### Code Verifier and Challenge Generation

```typescript
import crypto from 'crypto';

// Generate cryptographically random code verifier
function generateCodeVerifier(): string {
  // 43-128 characters, URL-safe base64
  return crypto.randomBytes(32)
    .toString('base64url')
    .slice(0, 128);
}

// Create code challenge from verifier
async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Node.js alternative
function generateCodeChallengeNode(verifier: string): string {
  return crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
}
```

### Authorization Request

```typescript
interface AuthorizationParams {
  clientId: string;
  redirectUri: string;
  scope: string;
  state: string;
  codeChallenge: string;
}

function buildAuthorizationUrl(
  baseUrl: string,
  params: AuthorizationParams
): string {
  const url = new URL(baseUrl);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('client_id', params.clientId);
  url.searchParams.set('redirect_uri', params.redirectUri);
  url.searchParams.set('scope', params.scope);
  url.searchParams.set('state', params.state);
  url.searchParams.set('code_challenge', params.codeChallenge);
  url.searchParams.set('code_challenge_method', 'S256');
  return url.toString();
}

// Example usage
const codeVerifier = generateCodeVerifier();
const codeChallenge = await generateCodeChallenge(codeVerifier);
const state = crypto.randomUUID();

// Store codeVerifier and state securely (e.g., sessionStorage)
sessionStorage.setItem('pkce_code_verifier', codeVerifier);
sessionStorage.setItem('oauth_state', state);

const authUrl = buildAuthorizationUrl(
  'https://auth.example.com/authorize',
  {
    clientId: 'your-client-id',
    redirectUri: 'https://app.example.com/callback',
    scope: 'openid profile email',
    state,
    codeChallenge,
  }
);

// Redirect user
window.location.href = authUrl;
```

### Token Exchange

```typescript
interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  id_token?: string;  // If using OpenID Connect
}

async function exchangeCodeForTokens(
  code: string,
  codeVerifier: string
): Promise<TokenResponse> {
  const response = await fetch('https://auth.example.com/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: 'your-client-id',
      code,
      redirect_uri: 'https://app.example.com/callback',
      code_verifier: codeVerifier,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error_description || 'Token exchange failed');
  }

  return response.json();
}
```

### Callback Handler

```typescript
async function handleCallback(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const error = params.get('error');

  // Check for errors
  if (error) {
    throw new Error(params.get('error_description') || error);
  }

  // Validate state to prevent CSRF
  const storedState = sessionStorage.getItem('oauth_state');
  if (state !== storedState) {
    throw new Error('Invalid state parameter');
  }

  // Get stored code verifier
  const codeVerifier = sessionStorage.getItem('pkce_code_verifier');
  if (!codeVerifier) {
    throw new Error('Missing code verifier');
  }

  // Exchange code for tokens
  const tokens = await exchangeCodeForTokens(code!, codeVerifier);

  // Clean up
  sessionStorage.removeItem('oauth_state');
  sessionStorage.removeItem('pkce_code_verifier');

  // Store tokens appropriately
  // Access token in memory, refresh token via httpOnly cookie
  return tokens;
}
```

## React Native / Expo Implementation

### Using expo-auth-session

```typescript
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';

// Required for web browser redirect
WebBrowser.maybeCompleteAuthSession();

// Discovery document for provider
const discovery = {
  authorizationEndpoint: 'https://auth.example.com/authorize',
  tokenEndpoint: 'https://auth.example.com/token',
  revocationEndpoint: 'https://auth.example.com/revoke',
};

export function useOAuthLogin() {
  const redirectUri = AuthSession.makeRedirectUri({
    scheme: 'your-app-scheme',
    path: 'callback',
  });

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: 'your-client-id',
      scopes: ['openid', 'profile', 'email'],
      redirectUri,
      usePKCE: true,  // Automatically handles PKCE
    },
    discovery
  );

  useEffect(() => {
    if (response?.type === 'success') {
      const { code } = response.params;
      exchangeCodeForTokens(code, request?.codeVerifier!);
    }
  }, [response]);

  const login = async () => {
    const result = await promptAsync();
    return result;
  };

  return { login, isLoading: !request };
}
```

### Manual PKCE in React Native

```typescript
import * as Crypto from 'expo-crypto';
import * as Linking from 'expo-linking';
import * as SecureStore from 'expo-secure-store';

async function generatePKCE() {
  // Generate random bytes
  const randomBytes = await Crypto.getRandomBytesAsync(32);
  const codeVerifier = btoa(String.fromCharCode(...randomBytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

  // Create challenge
  const digest = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    codeVerifier,
    { encoding: Crypto.CryptoEncoding.BASE64 }
  );
  
  const codeChallenge = digest
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

  return { codeVerifier, codeChallenge };
}

async function initiateOAuthFlow() {
  const { codeVerifier, codeChallenge } = await generatePKCE();
  const state = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    Date.now().toString()
  );

  // Store for later verification
  await SecureStore.setItemAsync('oauth_code_verifier', codeVerifier);
  await SecureStore.setItemAsync('oauth_state', state);

  const authUrl = new URL('https://auth.example.com/authorize');
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('client_id', 'your-client-id');
  authUrl.searchParams.set('redirect_uri', Linking.createURL('callback'));
  authUrl.searchParams.set('scope', 'openid profile email');
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('code_challenge', codeChallenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');

  await Linking.openURL(authUrl.toString());
}
```

## Social Login Providers

### Google OAuth

```typescript
const GOOGLE_CONFIG = {
  clientId: process.env.GOOGLE_CLIENT_ID!,
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  scopes: ['openid', 'profile', 'email'],
};

// Additional params for Google
const googleAuthUrl = buildAuthorizationUrl(
  GOOGLE_CONFIG.authorizationEndpoint,
  {
    ...params,
    // Google-specific
    access_type: 'offline',  // Get refresh token
    prompt: 'consent',       // Force consent screen
  }
);
```

### Apple Sign In

```typescript
// Apple requires special handling
import * as AppleAuthentication from 'expo-apple-authentication';

async function signInWithApple() {
  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });

    // Send credential.identityToken to your backend
    const response = await fetch('/api/auth/apple', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identityToken: credential.identityToken,
        authorizationCode: credential.authorizationCode,
        user: credential.user,
      }),
    });

    return response.json();
  } catch (error) {
    if (error.code === 'ERR_CANCELED') {
      // User cancelled
      return null;
    }
    throw error;
  }
}
```

## Server-Side Token Validation

```typescript
import { Hono } from 'hono';

const app = new Hono();

// Store PKCE data (use Redis or database in production)
const pkceStore = new Map<string, { codeVerifier: string; expiresAt: number }>();

app.post('/api/auth/token', async (c) => {
  const body = await c.req.parseBody();
  
  const {
    grant_type,
    code,
    redirect_uri,
    code_verifier,
    client_id,
  } = body;

  if (grant_type !== 'authorization_code') {
    return c.json({ error: 'unsupported_grant_type' }, 400);
  }

  // Verify authorization code and get stored challenge
  const authCode = await db.authCodes.findUnique({
    where: { code, clientId: client_id },
  });

  if (!authCode || authCode.expiresAt < Date.now()) {
    return c.json({ error: 'invalid_grant' }, 400);
  }

  // Verify PKCE
  const computedChallenge = crypto
    .createHash('sha256')
    .update(code_verifier as string)
    .digest('base64url');

  if (computedChallenge !== authCode.codeChallenge) {
    return c.json({ error: 'invalid_grant' }, 400);
  }

  // Generate tokens
  const tokens = generateTokens(authCode.user);

  // Delete used authorization code
  await db.authCodes.delete({ where: { code } });

  return c.json({
    access_token: tokens.accessToken,
    refresh_token: tokens.refreshToken,
    token_type: 'Bearer',
    expires_in: 900,
  });
});
```

## Using Arctic Library

Arctic is a lightweight OAuth 2.0 client library with 50+ provider support.

```typescript
import { Google, Apple, GitHub } from 'arctic';

// Initialize providers
const google = new Google(
  process.env.GOOGLE_CLIENT_ID!,
  process.env.GOOGLE_CLIENT_SECRET!,
  'https://app.example.com/callback/google'
);

// Generate authorization URL
const state = crypto.randomUUID();
const codeVerifier = crypto.randomBytes(32).toString('base64url');
const scopes = ['openid', 'profile', 'email'];

const url = google.createAuthorizationURL(state, codeVerifier, scopes);

// Exchange code for tokens
const tokens = await google.validateAuthorizationCode(code, codeVerifier);
// Returns: { accessToken, refreshToken, accessTokenExpiresAt, idToken }
```

## Security Best Practices

1. **Always use PKCE** for public clients
2. **Validate state parameter** to prevent CSRF
3. **Use S256 challenge method** (not plain)
4. **Store code_verifier securely** (SecureStore on mobile)
5. **Validate redirect_uri** exactly (no wildcards)
6. **Use short-lived authorization codes** (< 10 minutes)
7. **One-time use codes** - delete after exchange
8. **HTTPS only** for all OAuth endpoints
