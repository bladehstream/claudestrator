# Validation with Zod

## Core Concepts

Zod is a TypeScript-first schema validation library with zero dependencies.

### Basic Usage

```typescript
import { z } from 'zod';

// Define schema
const userSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  age: z.number().int().positive().optional(),
});

// Infer TypeScript type
type User = z.infer<typeof userSchema>;
// { email: string; name: string; age?: number }

// Parse (throws on error)
const user = userSchema.parse(data);

// Safe parse (returns result object)
const result = userSchema.safeParse(data);
if (result.success) {
  console.log(result.data);
} else {
  console.log(result.error.issues);
}
```

## Primitive Types

```typescript
// Strings
z.string()
z.string().min(1)              // Non-empty
z.string().max(100)
z.string().length(10)
z.string().email()
z.string().url()
z.string().uuid()
z.string().cuid()
z.string().regex(/^[a-z]+$/)
z.string().startsWith('prefix')
z.string().endsWith('suffix')
z.string().trim()              // Transforms whitespace
z.string().toLowerCase()
z.string().toUpperCase()

// Numbers
z.number()
z.number().int()
z.number().positive()
z.number().negative()
z.number().nonnegative()
z.number().min(0)
z.number().max(100)
z.number().multipleOf(5)
z.number().finite()
z.number().safe()              // Safe integers

// Coercion (convert strings to numbers)
z.coerce.number()              // "123" → 123
z.coerce.boolean()             // "true" → true
z.coerce.date()                // "2025-01-01" → Date

// Booleans
z.boolean()

// Dates
z.date()
z.date().min(new Date('2020-01-01'))
z.date().max(new Date())
z.coerce.date()                // Parse date strings

// Enums
z.enum(['pending', 'active', 'inactive'])
z.nativeEnum(UserRole)         // TypeScript enum

// Literals
z.literal('active')
z.literal(42)
z.literal(true)
```

## Objects

```typescript
// Basic object
const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string(),
  role: z.enum(['user', 'admin']),
});

// Optional and nullable
z.object({
  required: z.string(),
  optional: z.string().optional(),      // string | undefined
  nullable: z.string().nullable(),      // string | null
  nullish: z.string().nullish(),        // string | null | undefined
  withDefault: z.string().default(''),  // Defaults to '' if undefined
});

// Strict mode (reject unknown keys)
const strictSchema = z.object({
  name: z.string(),
}).strict();

// Passthrough (keep unknown keys)
const passthroughSchema = z.object({
  name: z.string(),
}).passthrough();

// Strip unknown keys (default behavior)
const stripSchema = z.object({
  name: z.string(),
}).strip();

// Extend schemas
const baseSchema = z.object({ id: z.string() });
const extendedSchema = baseSchema.extend({
  name: z.string(),
  email: z.string().email(),
});

// Merge schemas
const merged = schema1.merge(schema2);

// Pick/Omit
const pickedSchema = userSchema.pick({ email: true, name: true });
const omittedSchema = userSchema.omit({ id: true });

// Partial (all optional)
const partialSchema = userSchema.partial();

// Required (all required)
const requiredSchema = partialSchema.required();

// DeepPartial
const deepPartialSchema = userSchema.deepPartial();
```

## Arrays and Tuples

```typescript
// Arrays
z.array(z.string())
z.string().array()             // Equivalent
z.array(z.number()).min(1)     // At least 1 element
z.array(z.number()).max(10)    // At most 10 elements
z.array(z.number()).length(5)  // Exactly 5 elements
z.array(z.number()).nonempty() // At least 1 element

// Tuples (fixed-length, typed positions)
z.tuple([z.string(), z.number()])  // [string, number]
z.tuple([z.string(), z.number()]).rest(z.boolean())  // [string, number, ...boolean[]]
```

## Unions and Discriminated Unions

```typescript
// Union
const stringOrNumber = z.union([z.string(), z.number()]);
// Shorthand
const stringOrNumber2 = z.string().or(z.number());

// Discriminated union (more efficient)
const eventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('user.created'),
    userId: z.string(),
    email: z.string().email(),
  }),
  z.object({
    type: z.literal('user.deleted'),
    userId: z.string(),
  }),
  z.object({
    type: z.literal('order.placed'),
    orderId: z.string(),
    amount: z.number(),
  }),
]);
```

## Records and Maps

```typescript
// Record (object with dynamic keys)
z.record(z.string(), z.number())  // { [key: string]: number }
z.record(z.enum(['a', 'b']), z.number())  // { a?: number, b?: number }

// Map
z.map(z.string(), z.number())

// Set
z.set(z.string())
z.set(z.number()).min(1).max(10)
```

## Transforms and Refinements

### Transforms

```typescript
// Transform input to different output
const trimmedString = z.string().transform(val => val.trim());

const userInput = z.object({
  email: z.string().email().toLowerCase(),
  name: z.string().trim(),
  birthDate: z.string().transform(val => new Date(val)),
});

// Complex transform
const parseJson = z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch (e) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Invalid JSON',
    });
    return z.NEVER;
  }
});

// Preprocess (before validation)
const numberFromString = z.preprocess(
  (val) => (typeof val === 'string' ? parseInt(val, 10) : val),
  z.number()
);
```

### Refinements

```typescript
// Simple refinement
const positiveNumber = z.number().refine(n => n > 0, {
  message: 'Must be positive',
});

// With path for nested errors
const passwordSchema = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine(data => data.password === data.confirmPassword, {
  message: 'Passwords must match',
  path: ['confirmPassword'],
});

// Async refinement
const uniqueEmailSchema = z.string().email().refine(
  async (email) => {
    const exists = await checkEmailExists(email);
    return !exists;
  },
  { message: 'Email already exists' }
);

// Superrefine for multiple issues
const complexSchema = z.object({
  items: z.array(z.string()),
  maxItems: z.number(),
}).superRefine((data, ctx) => {
  if (data.items.length > data.maxItems) {
    ctx.addIssue({
      code: z.ZodIssueCode.too_big,
      maximum: data.maxItems,
      type: 'array',
      inclusive: true,
      message: `Cannot have more than ${data.maxItems} items`,
    });
  }
});
```

## Error Handling

### Error Format

```typescript
const result = schema.safeParse(data);
if (!result.success) {
  console.log(result.error.issues);
  // [
  //   {
  //     code: 'invalid_type',
  //     expected: 'string',
  //     received: 'number',
  //     path: ['email'],
  //     message: 'Expected string, received number'
  //   }
  // ]
  
  // Flatten errors
  console.log(result.error.flatten());
  // {
  //   formErrors: [],
  //   fieldErrors: {
  //     email: ['Expected string, received number']
  //   }
  // }
  
  // Format errors
  console.log(result.error.format());
  // {
  //   email: { _errors: ['Expected string, received number'] }
  // }
}
```

### Custom Error Messages

```typescript
const schema = z.object({
  email: z.string({
    required_error: 'Email is required',
    invalid_type_error: 'Email must be a string',
  }).email({ message: 'Invalid email format' }),
  
  age: z.number()
    .min(18, { message: 'Must be 18 or older' })
    .max(120, { message: 'Invalid age' }),
});
```

### Error Map

```typescript
// Global error customization
z.setErrorMap((issue, ctx) => {
  if (issue.code === z.ZodIssueCode.invalid_type) {
    if (issue.expected === 'string') {
      return { message: 'This field must be text' };
    }
  }
  return { message: ctx.defaultError };
});
```

## API Request/Response Schemas

### Request Validation

```typescript
// Create user request
export const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  password: z.string().min(8).regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    'Must contain uppercase, lowercase, and number'
  ),
  role: z.enum(['user', 'admin']).default('user'),
});

export type CreateUserInput = z.infer<typeof createUserSchema>;

// Update user request (partial)
export const updateUserSchema = createUserSchema
  .omit({ password: true })
  .partial();

export type UpdateUserInput = z.infer<typeof updateUserSchema>;

// Query params
export const listUsersQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  role: z.enum(['user', 'admin']).optional(),
  sort: z.enum(['createdAt', 'name', 'email']).default('createdAt'),
  order: z.enum(['asc', 'desc']).default('desc'),
});

// Path params
export const userIdParamSchema = z.object({
  id: z.string().uuid(),
});
```

### Response Schemas

```typescript
// User response (excludes password)
export const userResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string(),
  role: z.enum(['user', 'admin']),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export type UserResponse = z.infer<typeof userResponseSchema>;

// Paginated response
export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    data: z.array(itemSchema),
    meta: z.object({
      total: z.number(),
      page: z.number(),
      limit: z.number(),
      totalPages: z.number(),
    }),
  });

export const userListResponseSchema = paginatedResponseSchema(userResponseSchema);
```

## Hono Integration

```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';

const app = new Hono();

app.post(
  '/users',
  zValidator('json', createUserSchema),
  async (c) => {
    const data = c.req.valid('json');  // Fully typed CreateUserInput
    const user = await userService.create(data);
    return c.json(user, 201);
  }
);

app.get(
  '/users',
  zValidator('query', listUsersQuerySchema),
  async (c) => {
    const { page, limit, role, sort, order } = c.req.valid('query');
    const users = await userService.list({ page, limit, role, sort, order });
    return c.json(users);
  }
);

app.get(
  '/users/:id',
  zValidator('param', userIdParamSchema),
  async (c) => {
    const { id } = c.req.valid('param');
    const user = await userService.findById(id);
    if (!user) {
      return c.json({ error: 'Not found' }, 404);
    }
    return c.json(user);
  }
);

// Custom error handling
app.post(
  '/users',
  zValidator('json', createUserSchema, (result, c) => {
    if (!result.success) {
      return c.json({
        type: 'validation_error',
        errors: result.error.flatten().fieldErrors,
      }, 400);
    }
  }),
  handler
);
```

## Schema Composition Patterns

### Base + Variants

```typescript
// Base schema
const baseEventSchema = z.object({
  id: z.string().uuid(),
  timestamp: z.date(),
  source: z.string(),
});

// Specific event schemas
const userEventSchema = baseEventSchema.extend({
  type: z.literal('user'),
  userId: z.string().uuid(),
  action: z.enum(['created', 'updated', 'deleted']),
});

const orderEventSchema = baseEventSchema.extend({
  type: z.literal('order'),
  orderId: z.string().uuid(),
  action: z.enum(['placed', 'shipped', 'delivered']),
});

// Union of all events
const eventSchema = z.discriminatedUnion('type', [
  userEventSchema,
  orderEventSchema,
]);
```

### Input/Output Pairs

```typescript
// Shared base
const userBase = {
  email: z.string().email(),
  name: z.string().min(2).max(100),
  role: z.enum(['user', 'admin']),
};

// Input (what client sends)
export const createUserInput = z.object({
  ...userBase,
  password: z.string().min(8),
});

// Output (what API returns)
export const userOutput = z.object({
  id: z.string().uuid(),
  ...userBase,
  createdAt: z.date(),
  updatedAt: z.date(),
});
```

## Best Practices

1. **Validate at boundaries** - All external input (requests, env vars, config)
2. **Infer types** - Use `z.infer<>` instead of manual types
3. **Coerce query params** - Use `z.coerce` for URL params
4. **Use `.safeParse()`** - For controlled error handling
5. **Compose schemas** - Build complex from simple with extend/merge
6. **Transform early** - Normalize data during validation
7. **Custom messages** - User-friendly error messages
8. **Schema as source of truth** - Generate types, docs from schemas
