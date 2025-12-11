# Input Validation and Sanitization

Comprehensive guide to validating user input and preventing injection attacks.

## Core Principle

**Never trust user input.** All data from users, query parameters, headers, and external sources must be validated before use.

## Validation vs Sanitization

| Approach | Purpose | When to Use |
|----------|---------|-------------|
| **Validation** | Reject invalid input | Always - first line of defense |
| **Sanitization** | Clean/transform input | When storing user-generated content |
| **Encoding** | Escape for output context | When rendering user data |

## Zod Validation

Zod provides TypeScript-first schema validation with runtime type checking.

### Installation
```bash
npm install zod @hono/zod-validator
```

### Basic Schemas
```typescript
import { z } from 'zod';

// Primitives
const StringSchema = z.string();
const NumberSchema = z.number();
const BooleanSchema = z.boolean();
const DateSchema = z.date();

// String validations
const EmailSchema = z.string().email();
const UrlSchema = z.string().url();
const UuidSchema = z.string().uuid();
const MinMaxSchema = z.string().min(1).max(100);
const RegexSchema = z.string().regex(/^[a-zA-Z0-9]+$/);

// Number validations
const PositiveSchema = z.number().positive();
const IntegerSchema = z.number().int();
const RangeSchema = z.number().min(0).max(100);

// Enums
const StatusSchema = z.enum(['pending', 'active', 'completed']);
```

### Object Schemas
```typescript
const UserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100),
  age: z.number().int().positive().max(150).optional(),
  role: z.enum(['user', 'admin']).default('user'),
  tags: z.array(z.string()).max(10).optional(),
  metadata: z.record(z.string()).optional(),
});

type User = z.infer<typeof UserSchema>;
// { email: string; name: string; age?: number; role: 'user' | 'admin'; ... }
```

### Hono Integration
```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const app = new Hono();

// Validate JSON body
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

app.post('/users',
  zValidator('json', CreateUserSchema),
  async (c) => {
    const data = c.req.valid('json');
    // data is typed and validated
    return c.json({ created: data });
  }
);

// Validate path parameters
const UserIdSchema = z.object({
  id: z.string().uuid(),
});

app.get('/users/:id',
  zValidator('param', UserIdSchema),
  async (c) => {
    const { id } = c.req.valid('param');
    return c.json({ id });
  }
);

// Validate query parameters
const PaginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.enum(['asc', 'desc']).optional(),
});

app.get('/users',
  zValidator('query', PaginationSchema),
  async (c) => {
    const { page, limit, sort } = c.req.valid('query');
    return c.json({ page, limit, sort });
  }
);

// Validate headers
const AuthHeaderSchema = z.object({
  authorization: z.string().startsWith('Bearer '),
});

app.get('/protected',
  zValidator('header', AuthHeaderSchema),
  async (c) => {
    const { authorization } = c.req.valid('header');
    const token = authorization.replace('Bearer ', '');
    return c.json({ token });
  }
);
```

### Custom Error Responses
```typescript
const validateJson = <T extends z.ZodType>(schema: T) =>
  zValidator('json', schema, (result, c) => {
    if (!result.success) {
      return c.json({
        error: 'Validation failed',
        details: result.error.issues.map(issue => ({
          field: issue.path.join('.'),
          message: issue.message,
          code: issue.code,
        })),
      }, 400);
    }
  });

app.post('/users', validateJson(CreateUserSchema), handler);
```

### Advanced Schemas
```typescript
// Conditional fields
const PaymentSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('card'),
    cardNumber: z.string().regex(/^\d{16}$/),
    expiry: z.string().regex(/^\d{2}\/\d{2}$/),
    cvv: z.string().regex(/^\d{3,4}$/),
  }),
  z.object({
    type: z.literal('bank'),
    accountNumber: z.string(),
    routingNumber: z.string(),
  }),
]);

// Transform on parse
const PhoneSchema = z.string()
  .transform(val => val.replace(/[^\d]/g, ''))
  .pipe(z.string().length(10));

// Custom validation
const PasswordSchema = z.string()
  .min(8)
  .max(100)
  .refine(
    (val) => /[A-Z]/.test(val),
    { message: 'Must contain uppercase letter' }
  )
  .refine(
    (val) => /[a-z]/.test(val),
    { message: 'Must contain lowercase letter' }
  )
  .refine(
    (val) => /[0-9]/.test(val),
    { message: 'Must contain number' }
  );

// Async validation
const UniqueEmailSchema = z.string().email().refine(
  async (email) => {
    const existing = await findUserByEmail(email);
    return !existing;
  },
  { message: 'Email already in use' }
);
```

## XSS Prevention

Cross-Site Scripting attacks inject malicious scripts into web pages.

### HTML Escaping
```typescript
import { escape } from 'html-escaper';

// Escape user input before rendering in HTML
const userInput = '<script>alert("XSS")</script>';
const safe = escape(userInput);
// &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;

app.get('/search', (c) => {
  const q = escape(c.req.query('q') || '');
  return c.html(`<h1>Results for: ${q}</h1>`);
});
```

### HTML Sanitization (for Rich Content)
```typescript
import DOMPurify from 'dompurify';
import { JSDOM } from 'jsdom';

const window = new JSDOM('').window;
const purify = DOMPurify(window);

// Allow only safe HTML tags
const userHtml = '<p>Hello</p><script>alert("XSS")</script>';
const clean = purify.sanitize(userHtml);
// <p>Hello</p>

// Custom allowed tags
const cleanCustom = purify.sanitize(userHtml, {
  ALLOWED_TAGS: ['p', 'b', 'i', 'em', 'strong', 'a'],
  ALLOWED_ATTR: ['href', 'title'],
});
```

### Content Security Policy
```typescript
// Add CSP header to prevent inline scripts
app.use('*', async (c, next) => {
  c.header('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self'; " +
    "object-src 'none'; " +
    "frame-ancestors 'self';"
  );
  await next();
});
```

## Common Validation Patterns

### API Key Validation
```typescript
const ApiKeySchema = z.string()
  .min(32)
  .max(64)
  .regex(/^[a-zA-Z0-9_-]+$/);
```

### File Upload Validation
```typescript
const FileUploadSchema = z.object({
  filename: z.string()
    .max(255)
    .regex(/^[\w\-. ]+$/)
    .refine(
      (name) => !name.includes('..'),
      'Invalid filename'
    ),
  contentType: z.enum([
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
  ]),
  size: z.number().max(10 * 1024 * 1024), // 10MB
});

app.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File | null;
  
  if (!file) {
    return c.json({ error: 'No file provided' }, 400);
  }
  
  const validation = FileUploadSchema.safeParse({
    filename: file.name,
    contentType: file.type,
    size: file.size,
  });
  
  if (!validation.success) {
    return c.json({ 
      error: 'Invalid file',
      details: validation.error.issues 
    }, 400);
  }
  
  // File is validated, proceed with upload
});
```

### URL Validation (SSRF Prevention)
```typescript
const SafeUrlSchema = z.string().url().refine(
  (url) => {
    try {
      const parsed = new URL(url);
      // Only allow HTTPS
      if (parsed.protocol !== 'https:') return false;
      // Block private IPs and localhost
      const host = parsed.hostname;
      if (host === 'localhost') return false;
      if (host.startsWith('127.')) return false;
      if (host.startsWith('10.')) return false;
      if (host.startsWith('192.168.')) return false;
      if (host.startsWith('172.') && parseInt(host.split('.')[1]) >= 16 && parseInt(host.split('.')[1]) <= 31) return false;
      // Block internal domains
      if (host.endsWith('.internal') || host.endsWith('.local')) return false;
      return true;
    } catch {
      return false;
    }
  },
  { message: 'Invalid or unsafe URL' }
);
```

### Search Query Sanitization
```typescript
const SearchQuerySchema = z.string()
  .max(200)
  .transform((val) => {
    // Remove special characters that could cause issues
    return val.replace(/[<>"'&;]/g, '');
  });
```

### Pagination Parameters
```typescript
const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().regex(/^[a-zA-Z_]+$/).optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc'),
});
```

## Validation Middleware Factory

```typescript
import { z } from 'zod';
import { zValidator } from '@hono/zod-validator';
import { createMiddleware } from 'hono/factory';

// Generic validation middleware with custom error handling
function validate<T extends z.ZodType>(
  target: 'json' | 'query' | 'param' | 'header',
  schema: T
) {
  return zValidator(target, schema, (result, c) => {
    if (!result.success) {
      const isProd = c.env?.ENVIRONMENT === 'production';
      
      return c.json({
        error: 'Validation Error',
        message: isProd ? 'Invalid request data' : undefined,
        details: isProd ? undefined : result.error.issues.map(i => ({
          field: i.path.join('.'),
          message: i.message,
        })),
      }, 400);
    }
  });
}

// Usage
app.post('/users', validate('json', CreateUserSchema), handler);
app.get('/users/:id', validate('param', UserIdSchema), handler);
app.get('/search', validate('query', SearchQuerySchema), handler);
```

## Best Practices

1. **Validate early** - Validate at the API boundary before any processing
2. **Use allowlists** - Specify what IS allowed, not what ISN'T
3. **Type coercion** - Use `z.coerce` for query/path params that should be numbers
4. **Reasonable limits** - Set max lengths on all strings and arrays
5. **Custom errors** - Provide helpful (but not exploitable) error messages
6. **Escape for context** - HTML escape for HTML, SQL escape for SQL
7. **Defense in depth** - Validate even if frontend validates
8. **Test edge cases** - Empty strings, nulls, very long inputs, special characters
9. **Log validation failures** - May indicate attack attempts
10. **Keep schemas DRY** - Reuse common schemas across endpoints
