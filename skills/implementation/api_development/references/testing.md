# API Testing

## Testing Pyramid for APIs

```
        /\
       /  \     End-to-End Tests (few)
      /----\    - Full system, real dependencies
     /      \   - Slow, flaky, expensive
    /--------\  
   /          \ Integration Tests (some)
  /------------\- Real DB, mocked externals
 /              \- API contract verification
/----------------\
|   Unit Tests   | (many)
| - Fast, isolated|
| - Business logic|
------------------
```

## Unit Testing

Test business logic in isolation.

```typescript
// services/user.test.ts
import { describe, it, expect, vi } from 'vitest';
import { UserService } from './user';

describe('UserService', () => {
  const mockDb = {
    user: {
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
  };

  const userService = new UserService(mockDb as any);

  describe('create', () => {
    it('should create user with valid data', async () => {
      const input = { email: 'test@example.com', name: 'Test' };
      mockDb.user.create.mockResolvedValue({ id: '123', ...input });

      const result = await userService.create(input);

      expect(result).toEqual({ id: '123', ...input });
      expect(mockDb.user.create).toHaveBeenCalledWith({ data: input });
    });

    it('should throw on duplicate email', async () => {
      mockDb.user.create.mockRejectedValue({ code: 'P2002' });

      await expect(
        userService.create({ email: 'exists@example.com', name: 'Test' })
      ).rejects.toThrow('Email already exists');
    });
  });
});
```

## Integration Testing

Test API endpoints with real/test database.

### Hono Integration Tests

```typescript
// routes/users.test.ts
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import app from '../app';
import { db } from '../db';

describe('Users API', () => {
  beforeAll(async () => {
    await db.$connect();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  beforeEach(async () => {
    await db.user.deleteMany();
  });

  describe('POST /users', () => {
    it('should create a user', async () => {
      const res = await app.request('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test@example.com',
          name: 'Test User',
        }),
      });

      expect(res.status).toBe(201);
      const body = await res.json();
      expect(body).toMatchObject({
        email: 'test@example.com',
        name: 'Test User',
      });
      expect(body.id).toBeDefined();
    });

    it('should return 400 for invalid email', async () => {
      const res = await app.request('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'invalid',
          name: 'Test',
        }),
      });

      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.errors).toBeDefined();
    });

    it('should return 409 for duplicate email', async () => {
      // Create first user
      await db.user.create({
        data: { email: 'test@example.com', name: 'First' },
      });

      // Try to create duplicate
      const res = await app.request('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test@example.com',
          name: 'Second',
        }),
      });

      expect(res.status).toBe(409);
    });
  });

  describe('GET /users/:id', () => {
    it('should return user by id', async () => {
      const user = await db.user.create({
        data: { email: 'test@example.com', name: 'Test' },
      });

      const res = await app.request(`/users/${user.id}`);

      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.id).toBe(user.id);
    });

    it('should return 404 for non-existent user', async () => {
      const res = await app.request('/users/00000000-0000-0000-0000-000000000000');

      expect(res.status).toBe(404);
    });
  });

  describe('GET /users', () => {
    it('should return paginated users', async () => {
      // Create test users
      await db.user.createMany({
        data: Array.from({ length: 25 }, (_, i) => ({
          email: `user${i}@example.com`,
          name: `User ${i}`,
        })),
      });

      const res = await app.request('/users?page=1&limit=10');

      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data).toHaveLength(10);
      expect(body.meta.total).toBe(25);
      expect(body.meta.totalPages).toBe(3);
    });
  });
});
```

### With Authentication

```typescript
describe('Protected Routes', () => {
  const validToken = 'valid-jwt-token';
  
  it('should return 401 without token', async () => {
    const res = await app.request('/api/profile');
    expect(res.status).toBe(401);
  });

  it('should return 401 with invalid token', async () => {
    const res = await app.request('/api/profile', {
      headers: { Authorization: 'Bearer invalid' },
    });
    expect(res.status).toBe(401);
  });

  it('should return user profile with valid token', async () => {
    const res = await app.request('/api/profile', {
      headers: { Authorization: `Bearer ${validToken}` },
    });
    expect(res.status).toBe(200);
  });
});
```

## Contract Testing

Verify API contracts between services.

### Consumer-Driven Contract Testing (Pact)

```typescript
// consumer.test.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';

const { like, eachLike, string, integer } = MatchersV3;

const provider = new PactV3({
  consumer: 'Frontend',
  provider: 'UserAPI',
});

describe('User API Contract', () => {
  it('should return user by id', async () => {
    await provider
      .given('user 123 exists')
      .uponReceiving('a request for user 123')
      .withRequest({
        method: 'GET',
        path: '/users/123',
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: string('123'),
          email: string('user@example.com'),
          name: string('Test User'),
          createdAt: string('2025-01-15T10:00:00Z'),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const response = await fetch(`${mockServer.url}/users/123`);
      const user = await response.json();
      
      expect(user.id).toBe('123');
      expect(user.email).toBeDefined();
    });
  });

  it('should return 404 for non-existent user', async () => {
    await provider
      .given('user 999 does not exist')
      .uponReceiving('a request for non-existent user')
      .withRequest({
        method: 'GET',
        path: '/users/999',
      })
      .willRespondWith({
        status: 404,
        headers: { 'Content-Type': 'application/json' },
        body: {
          type: string(),
          title: string('Not Found'),
          status: integer(404),
          detail: string(),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const response = await fetch(`${mockServer.url}/users/999`);
      expect(response.status).toBe(404);
    });
  });
});
```

### Provider Verification

```typescript
// provider.test.ts
import { Verifier } from '@pact-foundation/pact';

describe('Pact Verification', () => {
  it('should validate the expectations of the consumer', async () => {
    const verifier = new Verifier({
      providerBaseUrl: 'http://localhost:3000',
      pactUrls: ['./pacts/frontend-userapi.json'],
      stateHandlers: {
        'user 123 exists': async () => {
          await db.user.create({
            data: { id: '123', email: 'user@example.com', name: 'Test User' },
          });
        },
        'user 999 does not exist': async () => {
          await db.user.deleteMany({ where: { id: '999' } });
        },
      },
    });

    await verifier.verifyProvider();
  });
});
```

### OpenAPI Contract Testing

```typescript
// Validate responses against OpenAPI spec
import OpenAPIResponseValidator from 'openapi-response-validator';
import spec from './openapi.json';

const validator = new OpenAPIResponseValidator({ responses: spec.paths['/users/{id}'].get.responses });

describe('Response Contract', () => {
  it('should match OpenAPI schema', async () => {
    const res = await app.request('/users/123');
    const body = await res.json();

    const errors = validator.validateResponse(200, body);
    expect(errors).toBeUndefined();
  });
});
```

## Load Testing

```typescript
// k6 load test (k6.io)
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up
    { duration: '1m', target: 20 },    // Stay at 20 users
    { duration: '10s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% requests under 500ms
    http_req_failed: ['rate<0.01'],    // <1% failure rate
  },
};

export default function () {
  const res = http.get('http://localhost:3000/users');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  sleep(1);
}
```

## Mocking External Services

```typescript
import { vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// MSW server for mocking HTTP requests
const server = setupServer(
  http.get('https://api.stripe.com/v1/customers/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      email: 'customer@example.com',
    });
  }),
  
  http.post('https://api.stripe.com/v1/charges', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: 'ch_123',
      amount: body.amount,
      status: 'succeeded',
    });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Payment Service', () => {
  it('should create charge', async () => {
    const result = await paymentService.charge({
      customerId: 'cus_123',
      amount: 1000,
    });
    
    expect(result.status).toBe('succeeded');
  });

  it('should handle Stripe errors', async () => {
    // Override handler for this test
    server.use(
      http.post('https://api.stripe.com/v1/charges', () => {
        return HttpResponse.json(
          { error: { message: 'Card declined' } },
          { status: 402 }
        );
      })
    );

    await expect(
      paymentService.charge({ customerId: 'cus_123', amount: 1000 })
    ).rejects.toThrow('Card declined');
  });
});
```

## Test Utilities

```typescript
// test/utils.ts
import { db } from '../db';

// Factory functions
export function createTestUser(overrides = {}) {
  return db.user.create({
    data: {
      email: `test-${Date.now()}@example.com`,
      name: 'Test User',
      ...overrides,
    },
  });
}

// Authenticated request helper
export function authRequest(app: any, token: string) {
  return {
    get: (path: string) =>
      app.request(path, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    post: (path: string, body: any) =>
      app.request(path, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      }),
  };
}

// Database cleanup
export async function cleanDatabase() {
  const tablenames = await db.$queryRaw<
    Array<{ tablename: string }>
  >`SELECT tablename FROM pg_tables WHERE schemaname='public'`;

  for (const { tablename } of tablenames) {
    if (tablename !== '_prisma_migrations') {
      await db.$executeRawUnsafe(`TRUNCATE TABLE "public"."${tablename}" CASCADE;`);
    }
  }
}
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - run: npm ci
      
      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
      
      - name: Run tests
        run: npm test -- --coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

1. **Test behavior, not implementation** - Focus on inputs/outputs
2. **Use factories** for test data creation
3. **Isolate tests** - Clean state between tests
4. **Mock external services** - Don't hit real APIs in tests
5. **Test error cases** - 4xx, 5xx, edge cases
6. **Use contract tests** - Verify API compatibility
7. **Run tests in CI** - Every PR, every push
8. **Test authentication** - Valid, invalid, missing tokens
9. **Test pagination** - Empty, partial, full pages
10. **Keep tests fast** - Mock slow operations
