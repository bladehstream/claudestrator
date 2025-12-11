# Error Handling

## HTTP Status Codes

### Success (2xx)

| Code | Name | Use Case |
|------|------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST creating resource |
| 202 | Accepted | Request accepted, processing async |
| 204 | No Content | Successful DELETE, no body |

### Client Errors (4xx)

| Code | Name | Use Case |
|------|------|----------|
| 400 | Bad Request | Malformed syntax, invalid JSON |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Authenticated but not permitted |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method |
| 409 | Conflict | Resource conflict (duplicate) |
| 410 | Gone | Resource permanently deleted |
| 422 | Unprocessable Entity | Validation failed (semantic error) |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Errors (5xx)

| Code | Name | Use Case |
|------|------|----------|
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Temporarily down/maintenance |
| 504 | Gateway Timeout | Upstream timeout |

### Decision Guide

```
Is the request malformed (bad JSON, missing fields)?
  → 400 Bad Request

Is authentication missing or invalid?
  → 401 Unauthorized

Is the user authenticated but not allowed?
  → 403 Forbidden

Does the resource exist?
  → 404 Not Found

Is there a business rule violation (e.g., insufficient balance)?
  → 422 Unprocessable Entity

Does creating this conflict with existing data?
  → 409 Conflict

Is the user sending too many requests?
  → 429 Too Many Requests
```

## RFC 9457 Problem Details

Standard format for HTTP API error responses.

### Basic Structure

```typescript
interface ProblemDetails {
  type: string;      // URI identifying error type
  title: string;     // Short human-readable summary
  status: number;    // HTTP status code
  detail?: string;   // Human-readable explanation
  instance?: string; // URI identifying specific occurrence
  [key: string]: unknown;  // Extension fields
}
```

### Examples

**Validation Error:**
```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation",
  "instance": "/users",
  "errors": [
    {
      "field": "email",
      "message": "Must be a valid email address"
    },
    {
      "field": "password",
      "message": "Must be at least 8 characters"
    }
  ]
}
```

**Not Found:**
```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "User with id '123' was not found",
  "instance": "/users/123"
}
```

**Rate Limited:**
```json
{
  "type": "https://api.example.com/errors/rate-limit",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "instance": "/users",
  "retryAfter": 60,
  "limit": 100,
  "remaining": 0,
  "reset": "2025-01-15T12:00:00Z"
}
```

**Conflict:**
```json
{
  "type": "https://api.example.com/errors/conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "A user with this email already exists",
  "instance": "/users",
  "conflictingField": "email"
}
```

**Internal Error:**
```json
{
  "type": "https://api.example.com/errors/internal",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please try again later.",
  "instance": "/users/123",
  "traceId": "abc-123-def"
}
```

## Implementation

### Error Classes

```typescript
// Base error class
export class AppError extends Error {
  constructor(
    public readonly type: string,
    public readonly title: string,
    public readonly status: number,
    public readonly detail?: string,
    public readonly extensions?: Record<string, unknown>
  ) {
    super(detail || title);
    this.name = this.constructor.name;
  }

  toJSON(): ProblemDetails {
    return {
      type: this.type,
      title: this.title,
      status: this.status,
      detail: this.detail,
      ...this.extensions,
    };
  }
}

// Specific error types
export class ValidationError extends AppError {
  constructor(
    errors: Array<{ field: string; message: string }>,
    detail = 'One or more fields failed validation'
  ) {
    super(
      'https://api.example.com/errors/validation',
      'Validation Error',
      400,
      detail,
      { errors }
    );
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(
      'https://api.example.com/errors/not-found',
      'Not Found',
      404,
      `${resource} with id '${id}' was not found`
    );
  }
}

export class UnauthorizedError extends AppError {
  constructor(detail = 'Authentication required') {
    super(
      'https://api.example.com/errors/unauthorized',
      'Unauthorized',
      401,
      detail
    );
  }
}

export class ForbiddenError extends AppError {
  constructor(detail = 'You do not have permission to perform this action') {
    super(
      'https://api.example.com/errors/forbidden',
      'Forbidden',
      403,
      detail
    );
  }
}

export class ConflictError extends AppError {
  constructor(detail: string, conflictingField?: string) {
    super(
      'https://api.example.com/errors/conflict',
      'Conflict',
      409,
      detail,
      conflictingField ? { conflictingField } : undefined
    );
  }
}

export class RateLimitError extends AppError {
  constructor(retryAfter: number, limit: number, reset: Date) {
    super(
      'https://api.example.com/errors/rate-limit',
      'Too Many Requests',
      429,
      `Rate limit exceeded. Try again in ${retryAfter} seconds.`,
      {
        retryAfter,
        limit,
        remaining: 0,
        reset: reset.toISOString(),
      }
    );
  }
}
```

### Centralized Error Handler (Hono)

```typescript
import { Hono } from 'hono';
import { ZodError } from 'zod';

const app = new Hono();

app.onError((err, c) => {
  const instance = c.req.path;
  
  // App-specific errors
  if (err instanceof AppError) {
    return c.json(
      { ...err.toJSON(), instance },
      err.status as any
    );
  }
  
  // Zod validation errors
  if (err instanceof ZodError) {
    const errors = err.errors.map(e => ({
      field: e.path.join('.'),
      message: e.message,
    }));
    return c.json({
      type: 'https://api.example.com/errors/validation',
      title: 'Validation Error',
      status: 400,
      detail: 'Request validation failed',
      instance,
      errors,
    }, 400);
  }
  
  // JWT/Auth errors
  if (err.name === 'JsonWebTokenError' || err.name === 'TokenExpiredError') {
    return c.json({
      type: 'https://api.example.com/errors/unauthorized',
      title: 'Unauthorized',
      status: 401,
      detail: err.message,
      instance,
    }, 401);
  }
  
  // Log unexpected errors (don't expose details)
  console.error('Unexpected error:', err);
  
  return c.json({
    type: 'https://api.example.com/errors/internal',
    title: 'Internal Server Error',
    status: 500,
    detail: 'An unexpected error occurred',
    instance,
    traceId: c.get('requestId'),  // If using request ID middleware
  }, 500);
});
```

### Not Found Handler

```typescript
app.notFound((c) => {
  return c.json({
    type: 'https://api.example.com/errors/not-found',
    title: 'Not Found',
    status: 404,
    detail: `Route ${c.req.method} ${c.req.path} not found`,
    instance: c.req.path,
  }, 404);
});
```

## Error Handling Best Practices

### 1. Never Return 200 with Error Body

```typescript
// ❌ Bad
return c.json({ error: 'User not found' }, 200);

// ✅ Good
return c.json({
  type: 'https://api.example.com/errors/not-found',
  title: 'Not Found',
  status: 404,
  detail: 'User not found',
}, 404);
```

### 2. Don't Expose Internal Details

```typescript
// ❌ Bad - exposes stack trace and internal info
return c.json({
  error: err.message,
  stack: err.stack,
  query: 'SELECT * FROM users WHERE...',
}, 500);

// ✅ Good - generic message, log internally
console.error('Database error:', err);
return c.json({
  type: 'https://api.example.com/errors/internal',
  title: 'Internal Server Error',
  status: 500,
  detail: 'An unexpected error occurred',
  traceId: requestId,
}, 500);
```

### 3. Include Actionable Information

```typescript
// ❌ Bad - no guidance
return c.json({ error: 'Invalid request' }, 400);

// ✅ Good - tells user how to fix
return c.json({
  type: 'https://api.example.com/errors/validation',
  title: 'Validation Error',
  status: 400,
  detail: 'Email format is invalid',
  errors: [
    { 
      field: 'email', 
      message: 'Must be a valid email address (e.g., user@example.com)' 
    }
  ],
}, 400);
```

### 4. Use Appropriate Status Codes

```typescript
// ❌ Bad - using 400 for everything
if (!user) return c.json({ error: 'Not found' }, 400);
if (!authorized) return c.json({ error: 'Not allowed' }, 400);

// ✅ Good - specific status codes
if (!user) return c.json(new NotFoundError('User', id).toJSON(), 404);
if (!authorized) return c.json(new ForbiddenError().toJSON(), 403);
```

### 5. Handle Async Errors

```typescript
// ❌ Bad - unhandled promise rejection
app.get('/users/:id', async (c) => {
  const user = await userService.findById(c.req.param('id'));
  return c.json(user);
});

// ✅ Good - explicit error handling
app.get('/users/:id', async (c) => {
  try {
    const user = await userService.findById(c.req.param('id'));
    if (!user) {
      throw new NotFoundError('User', c.req.param('id'));
    }
    return c.json(user);
  } catch (err) {
    throw err;  // Let global handler process it
  }
});
```

### 6. Consistent Error Format

Always use the same structure across your API:

```typescript
// Create helper function
function errorResponse(
  c: Context,
  status: number,
  type: string,
  title: string,
  detail?: string,
  extensions?: Record<string, unknown>
) {
  return c.json({
    type: `https://api.example.com/errors/${type}`,
    title,
    status,
    detail,
    instance: c.req.path,
    ...extensions,
  }, status as any);
}

// Usage
return errorResponse(c, 404, 'not-found', 'Not Found', 'User not found');
return errorResponse(c, 400, 'validation', 'Validation Error', 'Invalid input', { errors });
```

## Error Logging

```typescript
import { logger } from './logger';

app.onError((err, c) => {
  const errorContext = {
    method: c.req.method,
    path: c.req.path,
    requestId: c.get('requestId'),
    userId: c.get('userId'),
    userAgent: c.req.header('user-agent'),
  };

  if (err instanceof AppError && err.status < 500) {
    // Client errors - log at info/warn level
    logger.warn('Client error', { ...errorContext, error: err.toJSON() });
  } else {
    // Server errors - log at error level with stack
    logger.error('Server error', { 
      ...errorContext, 
      error: err.message,
      stack: err.stack,
    });
  }

  // Return appropriate response...
});
```

## Content-Type for Errors

Always return errors as JSON with proper content type:

```typescript
return c.json(errorBody, status, {
  'Content-Type': 'application/problem+json',  // RFC 9457 media type
});
```
