# Authentication Libraries

## Overview

Choosing the right authentication library depends on your framework, requirements, and whether you need managed auth or want full control.

## Library Comparison (2025)

| Library | Type | Best For | Framework Support |
|---------|------|----------|-------------------|
| **Better Auth** | Full-featured | New projects, TypeScript-first | Framework-agnostic |
| **Auth.js** | Full-featured | Next.js projects | Next.js, SvelteKit, others |
| **Lucia** | Educational | Learning, custom solutions | Framework-agnostic |
| **Passport** | Middleware | Express.js, strategy pattern | Express, Koa |
| **Arctic** | OAuth client | OAuth-only needs | Framework-agnostic |

## Better Auth (Recommended 2025)

Better Auth is the most comprehensive TypeScript auth framework, created to address pain points in the ecosystem.

### Features
- Email/password, OAuth, Passkeys, MFA
- Multi-tenant, organization support
- Session management
- Plugin ecosystem
- TypeScript-first with full type inference
- Framework-agnostic

### Installation

```bash
npm install better-auth
```

### Basic Setup

```typescript
// auth.ts
import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { db } from './db';

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: 'pg',  // or 'mysql', 'sqlite'
  }),
  emailAndPassword: {
    enabled: true,
  },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    },
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
  },
});
```

### Hono Integration

```typescript
import { Hono } from 'hono';
import { auth } from './auth';
import { cors } from 'hono/cors';

const app = new Hono();

// CORS for auth endpoints
app.use(
  '/api/auth/*',
  cors({
    origin: ['http://localhost:3000'],
    credentials: true,
  })
);

// Mount auth handler
app.on(['POST', 'GET'], '/api/auth/*', (c) => {
  return auth.handler(c.req.raw);
});

// Session middleware
app.use('*', async (c, next) => {
  const session = await auth.api.getSession({
    headers: c.req.raw.headers,
  });
  c.set('user', session?.user ?? null);
  c.set('session', session?.session ?? null);
  await next();
});

// Protected route
app.get('/api/me', (c) => {
  const user = c.get('user');
  if (!user) return c.json({ error: 'Unauthorized' }, 401);
  return c.json(user);
});
```

### Client SDK

```typescript
import { createAuthClient } from 'better-auth/client';

export const authClient = createAuthClient({
  baseURL: 'http://localhost:3000',
});

// Sign up
await authClient.signUp.email({
  email: 'user@example.com',
  password: 'password123',
  name: 'John Doe',
});

// Sign in
await authClient.signIn.email({
  email: 'user@example.com',
  password: 'password123',
});

// OAuth
await authClient.signIn.social({
  provider: 'google',
  callbackURL: '/dashboard',
});

// Get session
const session = await authClient.getSession();

// Sign out
await authClient.signOut();
```

### Plugins

```typescript
import { betterAuth } from 'better-auth';
import { twoFactor } from 'better-auth/plugins';
import { organization } from 'better-auth/plugins';

export const auth = betterAuth({
  // ... base config
  plugins: [
    twoFactor({
      issuer: 'MyApp',
    }),
    organization({
      allowInvitations: true,
    }),
  ],
});
```

## Auth.js (NextAuth.js)

Auth.js is the successor to NextAuth.js, now framework-agnostic but still best for Next.js.

### Installation

```bash
npm install next-auth@beta
```

### Next.js Setup

```typescript
// auth.ts
import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Google from 'next-auth/providers/google';
import Credentials from 'next-auth/providers/credentials';

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.GITHUB_ID,
      clientSecret: process.env.GITHUB_SECRET,
    }),
    Google({
      clientId: process.env.GOOGLE_ID,
      clientSecret: process.env.GOOGLE_SECRET,
    }),
    Credentials({
      credentials: {
        email: {},
        password: {},
      },
      authorize: async (credentials) => {
        const user = await validateCredentials(
          credentials.email,
          credentials.password
        );
        return user;
      },
    }),
  ],
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    session: async ({ session, token }) => {
      if (token) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    },
  },
});

// app/api/auth/[...nextauth]/route.ts
export const { GET, POST } = handlers;
```

### Usage in Components

```typescript
// Server Component
import { auth } from '@/auth';

export default async function Page() {
  const session = await auth();
  
  if (!session) {
    return <div>Not authenticated</div>;
  }
  
  return <div>Hello {session.user.name}</div>;
}

// Client Component
'use client';
import { useSession, signIn, signOut } from 'next-auth/react';

export function AuthButton() {
  const { data: session } = useSession();
  
  if (session) {
    return (
      <button onClick={() => signOut()}>Sign out</button>
    );
  }
  
  return (
    <button onClick={() => signIn('google')}>Sign in</button>
  );
}
```

## Lucia (Learning Resource)

Lucia v3 was deprecated in March 2025 and is now a learning resource for implementing auth from scratch.

### Use Lucia When
- Learning authentication concepts
- Building custom auth without library overhead
- Following Copenhagen Book principles

### Lucia Approach (Without Library)

```typescript
// Session management from scratch
import { sha256 } from '@oslojs/crypto/sha2';
import { encodeHexLowerCase } from '@oslojs/encoding';

function generateSessionToken(): string {
  const bytes = new Uint8Array(20);
  crypto.getRandomValues(bytes);
  return encodeBase32LowerCaseNoPadding(bytes);
}

async function createSession(
  token: string,
  userId: string
): Promise<Session> {
  const sessionId = encodeHexLowerCase(
    sha256(new TextEncoder().encode(token))
  );
  
  const session: Session = {
    id: sessionId,
    userId,
    expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
  };
  
  await db.insert(sessionTable).values(session);
  return session;
}

async function validateSession(
  token: string
): Promise<SessionValidationResult> {
  const sessionId = encodeHexLowerCase(
    sha256(new TextEncoder().encode(token))
  );
  
  const session = await db
    .select()
    .from(sessionTable)
    .where(eq(sessionTable.id, sessionId))
    .get();
  
  if (!session || session.expiresAt < new Date()) {
    return { session: null, user: null };
  }
  
  const user = await db
    .select()
    .from(userTable)
    .where(eq(userTable.id, session.userId))
    .get();
  
  return { session, user };
}
```

### Related Oslo Libraries

```bash
npm install @oslojs/crypto @oslojs/encoding
npm install arctic  # OAuth 2.0 client
```

## Arctic (OAuth Client)

Lightweight OAuth 2.0 client with 50+ provider support.

### Installation

```bash
npm install arctic
```

### Usage

```typescript
import { Google, GitHub, Apple } from 'arctic';

// Initialize providers
const google = new Google(
  process.env.GOOGLE_CLIENT_ID!,
  process.env.GOOGLE_CLIENT_SECRET!,
  'http://localhost:3000/auth/google/callback'
);

const github = new GitHub(
  process.env.GITHUB_CLIENT_ID!,
  process.env.GITHUB_CLIENT_SECRET!,
  null // No explicit redirect URI
);

// Generate authorization URL
const state = generateState();
const codeVerifier = generateCodeVerifier();
const url = google.createAuthorizationURL(state, codeVerifier, [
  'openid',
  'profile',
  'email',
]);

// Exchange code for tokens
const tokens = await google.validateAuthorizationCode(code, codeVerifier);
// tokens: { accessToken, refreshToken, accessTokenExpiresAt, idToken }

// Refresh access token
const newTokens = await google.refreshAccessToken(tokens.refreshToken);
```

## Passport (Express Middleware)

Traditional choice for Express.js with strategy pattern.

### Installation

```bash
npm install passport passport-local passport-google-oauth20
```

### Setup

```typescript
import passport from 'passport';
import { Strategy as LocalStrategy } from 'passport-local';
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';

// Local strategy
passport.use(
  new LocalStrategy(
    { usernameField: 'email' },
    async (email, password, done) => {
      try {
        const user = await findUserByEmail(email);
        if (!user || !await verifyPassword(password, user.passwordHash)) {
          return done(null, false, { message: 'Invalid credentials' });
        }
        return done(null, user);
      } catch (error) {
        return done(error);
      }
    }
  )
);

// Google strategy
passport.use(
  new GoogleStrategy(
    {
      clientID: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      callbackURL: '/auth/google/callback',
    },
    async (accessToken, refreshToken, profile, done) => {
      const user = await findOrCreateUser(profile);
      return done(null, user);
    }
  )
);

// Serialization
passport.serializeUser((user, done) => done(null, user.id));
passport.deserializeUser(async (id, done) => {
  const user = await findUserById(id);
  done(null, user);
});
```

### Express Routes

```typescript
import express from 'express';
import passport from 'passport';

const app = express();

app.use(passport.initialize());
app.use(passport.session());

// Local login
app.post(
  '/auth/login',
  passport.authenticate('local', {
    successRedirect: '/dashboard',
    failureRedirect: '/login',
  })
);

// Google OAuth
app.get(
  '/auth/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

app.get(
  '/auth/google/callback',
  passport.authenticate('google', { failureRedirect: '/login' }),
  (req, res) => res.redirect('/dashboard')
);
```

## Decision Matrix

| Requirement | Recommended Library |
|-------------|---------------------|
| New TypeScript project | Better Auth |
| Next.js application | Auth.js or Better Auth |
| Learning auth concepts | Lucia (docs) |
| OAuth only | Arctic |
| Express.js existing | Passport |
| Full control, no library | Oslo + Arctic |
| Enterprise SSO | Better Auth (plugins) or Auth0 |

## Migration Guide

### From Auth.js to Better Auth

```typescript
// Old Auth.js
import NextAuth from 'next-auth';
export const { auth } = NextAuth({ providers: [...] });

// New Better Auth
import { betterAuth } from 'better-auth';
export const auth = betterAuth({
  emailAndPassword: { enabled: true },
  socialProviders: { google: {...} },
});
```

### From Lucia to Better Auth

```typescript
// Lucia concepts map to Better Auth:
// - lucia.createSession() → auth.api.signIn.email()
// - lucia.validateSession() → auth.api.getSession()
// - lucia.invalidateSession() → auth.api.signOut()
```

## Managed Auth Services

For projects requiring managed authentication:

| Service | Best For | Features |
|---------|----------|----------|
| **Clerk** | Startups, quick setup | UI components, organizations |
| **Auth0** | Enterprise | SSO, compliance, scaling |
| **Supabase Auth** | Supabase users | Integrated with Supabase |
| **Firebase Auth** | Firebase ecosystem | Google integration |
