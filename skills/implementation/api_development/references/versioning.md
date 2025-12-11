# API Versioning

## Versioning Strategies

### 1. URL Path Versioning (Recommended)

Version in the URL path:
```
https://api.example.com/v1/users
https://api.example.com/v2/users
```

**Pros:**
- Highly visible and explicit
- Easy to implement and test
- Clear routing
- Browser/curl friendly
- Cached separately by version

**Cons:**
- Not "pure" REST (version isn't a resource)
- URL changes between versions

**Implementation (Hono):**
```typescript
import { Hono } from 'hono';

const app = new Hono();

// Version 1 routes
const v1 = new Hono();
v1.get('/users', getUsersV1);
v1.get('/users/:id', getUserV1);

// Version 2 routes
const v2 = new Hono();
v2.get('/users', getUsersV2);
v2.get('/users/:id', getUserV2);

// Mount versioned routes
app.route('/v1', v1);
app.route('/v2', v2);

// Optional: redirect unversioned to latest
app.get('/users', (c) => c.redirect('/v2/users'));
```

### 2. Header Versioning

Version in request header:
```
GET /users HTTP/1.1
Accept-Version: 2
```
or
```
GET /users HTTP/1.1
X-API-Version: 2.0
```

**Pros:**
- Clean URLs
- Follows HTTP semantics
- URLs don't change

**Cons:**
- Hidden from URL
- Harder to test in browser
- Requires header inspection

**Implementation:**
```typescript
const app = new Hono();

app.use('*', async (c, next) => {
  const version = c.req.header('Accept-Version') || 
                  c.req.header('X-API-Version') || 
                  '2';  // Default to latest
  c.set('apiVersion', version);
  await next();
});

app.get('/users', async (c) => {
  const version = c.get('apiVersion');
  
  if (version === '1') {
    return getUsersV1(c);
  }
  return getUsersV2(c);
});
```

### 3. Query Parameter Versioning

Version as query parameter:
```
https://api.example.com/users?version=2
https://api.example.com/users?api-version=2021-01-01
```

**Pros:**
- Easy to implement
- Visible in URL
- Easy to test

**Cons:**
- Clutters URLs
- Can be accidentally omitted
- Caching complications

**Implementation:**
```typescript
app.get('/users', async (c) => {
  const version = c.req.query('version') || '2';
  
  switch (version) {
    case '1':
      return getUsersV1(c);
    case '2':
    default:
      return getUsersV2(c);
  }
});
```

### 4. Content Negotiation (Accept Header)

Version in Accept header media type:
```
GET /users HTTP/1.1
Accept: application/vnd.myapi.v2+json
```

**Pros:**
- RESTful approach
- URLs don't change
- Follows HTTP standards

**Cons:**
- Complex to implement
- Hard to test in browser
- Not widely understood

**Implementation:**
```typescript
app.get('/users', async (c) => {
  const accept = c.req.header('Accept') || 'application/json';
  
  if (accept.includes('vnd.myapi.v1')) {
    return c.json(await getUsersV1(), 200, {
      'Content-Type': 'application/vnd.myapi.v1+json',
    });
  }
  
  // Default to v2
  return c.json(await getUsersV2(), 200, {
    'Content-Type': 'application/vnd.myapi.v2+json',
  });
});
```

## Comparison

| Strategy | Example | Visibility | Complexity | Use Case |
|----------|---------|------------|------------|----------|
| URL Path | `/v1/users` | High | Low | Public APIs |
| Header | `X-API-Version: 1` | Low | Medium | Internal APIs |
| Query | `?version=1` | Medium | Low | Simple APIs |
| Accept | `vnd.api.v1+json` | Low | High | Enterprise APIs |

**Recommendation:** Use URL path versioning for most cases. It's the most explicit and widely understood approach.

## Semantic Versioning for APIs

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (incompatible)
MINOR: Backward-compatible additions
PATCH: Backward-compatible fixes
```

**URL versioning:** Include only MAJOR version in URL
```
/v1/users  → 1.x.x
/v2/users  → 2.x.x
```

**Header versioning:** Can include MINOR version
```
X-API-Version: 1.2
```

## What Constitutes a Breaking Change?

**Breaking (requires new major version):**
- Removing an endpoint
- Removing a required request field
- Removing a response field
- Changing field type (string → number)
- Renaming fields
- Changing authentication method
- Changing error response structure
- Removing supported HTTP method

**Non-breaking (minor version):**
- Adding new endpoints
- Adding optional request fields
- Adding response fields
- Adding new enum values (with care)
- Adding new optional query parameters
- Performance improvements

## Deprecation Strategy

### 1. Announce Deprecation

```json
// Response headers
{
  "Deprecation": "true",
  "Sunset": "2025-06-01T00:00:00Z",
  "Link": "<https://api.example.com/docs/migration>; rel=\"deprecation\""
}
```

### 2. Response Warning

```json
{
  "data": { ... },
  "warnings": [
    {
      "code": "DEPRECATED_ENDPOINT",
      "message": "This endpoint is deprecated and will be removed on 2025-06-01. Please migrate to /v2/users"
    }
  ]
}
```

### 3. Documentation

```yaml
# OpenAPI
paths:
  /v1/users:
    get:
      deprecated: true
      description: |
        **DEPRECATED** - Use /v2/users instead.
        This endpoint will be removed on 2025-06-01.
```

### 4. Deprecation Timeline

```
1. Announce: 6+ months before removal
2. Warn: Add deprecation headers/warnings
3. Monitor: Track usage of deprecated endpoints
4. Contact: Reach out to heavy users
5. Remove: After sunset date
```

## Version Lifecycle

```
Development → Beta → Stable → Deprecated → Retired

Development: Active development, breaking changes expected
Beta: Feature complete, API may change
Stable: Production ready, backward compatible only
Deprecated: Still works, but migration recommended
Retired: Endpoint removed
```

## Implementation Patterns

### Versioned Controllers

```typescript
// controllers/v1/users.ts
export const getUsersV1 = async (c: Context) => {
  const users = await userService.findAll();
  // V1 format: flat structure
  return c.json(users.map(u => ({
    id: u.id,
    email: u.email,
    name: `${u.firstName} ${u.lastName}`,  // Combined name
  })));
};

// controllers/v2/users.ts
export const getUsersV2 = async (c: Context) => {
  const users = await userService.findAll();
  // V2 format: structured
  return c.json({
    data: users.map(u => ({
      id: u.id,
      email: u.email,
      firstName: u.firstName,
      lastName: u.lastName,
      profile: {
        avatarUrl: u.avatarUrl,
        bio: u.bio,
      },
    })),
    meta: { ... },
  });
};
```

### Shared Business Logic

```typescript
// services/userService.ts
// Business logic is shared across versions

// Transformation layer for versions
// transformers/v1/user.ts
export const transformUserV1 = (user: User): UserV1Response => ({
  id: user.id,
  email: user.email,
  name: `${user.firstName} ${user.lastName}`,
});

// transformers/v2/user.ts
export const transformUserV2 = (user: User): UserV2Response => ({
  id: user.id,
  email: user.email,
  firstName: user.firstName,
  lastName: user.lastName,
  profile: {
    avatarUrl: user.avatarUrl,
    bio: user.bio,
  },
});
```

### Version Middleware

```typescript
const versionMiddleware = () => {
  return async (c: Context, next: Next) => {
    // Determine version from URL, header, or query
    const pathMatch = c.req.path.match(/^\/v(\d+)/);
    const version = pathMatch?.[1] || 
                    c.req.header('X-API-Version') ||
                    c.req.query('version') ||
                    '2';  // Default
    
    c.set('apiVersion', parseInt(version));
    
    // Add deprecation warning for v1
    if (version === '1') {
      c.header('Deprecation', 'true');
      c.header('Sunset', '2025-06-01T00:00:00Z');
    }
    
    await next();
  };
};

app.use('*', versionMiddleware());
```

## Best Practices

1. **Version from day one** - Even if you think you won't need it
2. **Use URL versioning** for public APIs - Most explicit and understood
3. **Keep business logic unversioned** - Only transform at API boundaries
4. **Support 2-3 versions max** - Maintenance burden grows quickly
5. **Provide migration guides** - Document changes between versions
6. **Announce deprecation early** - Give users 6+ months notice
7. **Monitor version usage** - Know who's using what
8. **Default to latest stable** - But allow explicit version selection
9. **Version response schemas** - Document exactly what each version returns
10. **Test all supported versions** - Include in CI/CD pipeline
