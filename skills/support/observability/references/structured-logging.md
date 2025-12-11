# Structured Logging

Implement consistent, machine-parseable logging for your Cloudflare Workers applications.

## Why JSON Logging?

Traditional text logs are hard to parse and query:
```
2024-01-15 10:30:45 INFO User john@example.com logged in from 192.168.1.1
```

JSON logs are automatically indexed and queryable:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "event": "user_login",
  "email": "john@example.com",
  "ip": "192.168.1.1"
}
```

## Logger Implementation

### Basic Logger

```typescript
// utils/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

interface LoggerOptions {
  service: string;
  environment: string;
  minLevel?: LogLevel;
}

interface LogContext {
  requestId?: string;
  userId?: string;
  traceId?: string;
  [key: string]: unknown;
}

export class Logger {
  private service: string;
  private environment: string;
  private minLevel: number;
  private context: LogContext;

  constructor(options: LoggerOptions, context: LogContext = {}) {
    this.service = options.service;
    this.environment = options.environment;
    this.minLevel = LOG_LEVELS[options.minLevel || 'info'];
    this.context = context;
  }

  private log(level: LogLevel, message: string, data?: Record<string, unknown>) {
    if (LOG_LEVELS[level] < this.minLevel) return;

    const entry = {
      timestamp: new Date().toISOString(),
      level,
      service: this.service,
      environment: this.environment,
      message,
      ...this.context,
      ...data,
    };

    console.log(JSON.stringify(entry));
  }

  debug(message: string, data?: Record<string, unknown>) {
    this.log('debug', message, data);
  }

  info(message: string, data?: Record<string, unknown>) {
    this.log('info', message, data);
  }

  warn(message: string, data?: Record<string, unknown>) {
    this.log('warn', message, data);
  }

  error(message: string, data?: Record<string, unknown>) {
    this.log('error', message, data);
  }

  // Create child logger with additional context
  child(additionalContext: LogContext): Logger {
    const childLogger = new Logger(
      { service: this.service, environment: this.environment },
      { ...this.context, ...additionalContext }
    );
    childLogger.minLevel = this.minLevel;
    return childLogger;
  }
}

// Factory function
export function createLogger(env: Env, requestId?: string): Logger {
  return new Logger(
    {
      service: 'my-api',
      environment: env.ENVIRONMENT || 'development',
      minLevel: (env.LOG_LEVEL as LogLevel) || 'info',
    },
    { requestId }
  );
}
```

### Usage with Hono

```typescript
import { Hono } from 'hono';
import { createMiddleware } from 'hono/factory';
import { createLogger, Logger } from './utils/logger';

// Extend Hono's Variables type
type Variables = {
  requestId: string;
  logger: Logger;
};

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

// Logging middleware
const loggingMiddleware = createMiddleware(async (c, next) => {
  const requestId = c.req.header('x-request-id') || crypto.randomUUID();
  const logger = createLogger(c.env, requestId);
  
  c.set('requestId', requestId);
  c.set('logger', logger);
  c.header('x-request-id', requestId);

  const start = performance.now();
  const method = c.req.method;
  const path = c.req.path;

  logger.info('Request started', { method, path });

  try {
    await next();
    
    const duration_ms = Math.round(performance.now() - start);
    const status = c.res.status;
    
    logger.info('Request completed', { method, path, status, duration_ms });
  } catch (error) {
    const duration_ms = Math.round(performance.now() - start);
    
    logger.error('Request failed', {
      method,
      path,
      duration_ms,
      error: {
        name: error.name,
        message: error.message,
      },
    });
    
    throw error;
  }
});

app.use('*', loggingMiddleware);

// Access logger in handlers
app.post('/users', async (c) => {
  const logger = c.get('logger');
  const data = await c.req.json();
  
  logger.info('Creating user', { email: data.email });
  
  const user = await createUser(data, c.env);
  
  logger.info('User created', { userId: user.id });
  
  return c.json(user, 201);
});
```

## Log Schema Standards

### Standard Fields

```typescript
interface StandardLog {
  // Always present
  timestamp: string;      // ISO 8601: 2024-01-15T10:30:45.123Z
  level: string;          // debug, info, warn, error
  message: string;        // Human-readable description
  
  // Service identification
  service: string;        // Service name: 'user-api', 'payment-worker'
  environment: string;    // dev, staging, production
  
  // Request correlation
  requestId?: string;     // UUID for request correlation
  traceId?: string;       // Distributed trace ID
  spanId?: string;        // Current span ID
  
  // User context
  userId?: string;        // Authenticated user
  sessionId?: string;     // Session identifier
  
  // Performance
  duration_ms?: number;   // Operation duration
  
  // Error details
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: string;
  };
}
```

### Event-Specific Fields

```typescript
// HTTP request logs
interface HttpRequestLog extends StandardLog {
  http: {
    method: string;
    path: string;
    status: number;
    userAgent?: string;
    ip?: string;
  };
}

// Database operation logs
interface DatabaseLog extends StandardLog {
  db: {
    operation: 'query' | 'insert' | 'update' | 'delete';
    table: string;
    rowsAffected?: number;
  };
}

// External API call logs
interface ExternalApiLog extends StandardLog {
  external: {
    service: string;
    endpoint: string;
    status: number;
    duration_ms: number;
  };
}
```

## Logging Best Practices

### 1. Use Consistent Event Names

```typescript
// Define event names as constants
const EVENTS = {
  // Authentication
  AUTH_LOGIN_SUCCESS: 'auth.login.success',
  AUTH_LOGIN_FAILED: 'auth.login.failed',
  AUTH_LOGOUT: 'auth.logout',
  
  // Users
  USER_CREATED: 'user.created',
  USER_UPDATED: 'user.updated',
  USER_DELETED: 'user.deleted',
  
  // Payments
  PAYMENT_INITIATED: 'payment.initiated',
  PAYMENT_COMPLETED: 'payment.completed',
  PAYMENT_FAILED: 'payment.failed',
} as const;

// Usage
logger.info(EVENTS.USER_CREATED, { userId: user.id, email: user.email });
```

### 2. Sanitize Sensitive Data

```typescript
const SENSITIVE_FIELDS = [
  'password',
  'token',
  'apiKey',
  'secret',
  'authorization',
  'cookie',
  'ssn',
  'creditCard',
];

function sanitize(obj: Record<string, unknown>): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_FIELDS.some(field => 
      key.toLowerCase().includes(field.toLowerCase())
    )) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitize(value as Record<string, unknown>);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

// Usage in logger
private log(level: LogLevel, message: string, data?: Record<string, unknown>) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...this.context,
    ...(data ? sanitize(data) : {}),
  };
  console.log(JSON.stringify(entry));
}
```

### 3. Log Error Context

```typescript
// Bad - no context
logger.error('Payment failed');

// Good - full context
logger.error('Payment failed', {
  error: {
    name: error.name,
    message: error.message,
    code: error.code,
    stack: error.stack,
  },
  payment: {
    id: paymentId,
    amount: amount,
    currency: currency,
  },
  user: {
    id: userId,
    email: userEmail,
  },
  external: {
    provider: 'stripe',
    requestId: stripeRequestId,
  },
});
```

### 4. Log at Boundaries

Log when crossing boundaries (API calls, database queries, external services):

```typescript
// API boundary
app.post('/api/orders', async (c) => {
  const logger = c.get('logger');
  
  // Log entry
  logger.info('Order creation started', { 
    customerId: data.customerId,
    itemCount: data.items.length,
  });
  
  // ... processing ...
  
  // Log exit
  logger.info('Order creation completed', { 
    orderId: order.id,
    total: order.total,
  });
});

// Database boundary
async function createOrder(data: OrderData, logger: Logger): Promise<Order> {
  const start = performance.now();
  
  try {
    const order = await db.insert(orders).values(data).returning();
    
    logger.debug('Database insert completed', {
      table: 'orders',
      duration_ms: Math.round(performance.now() - start),
    });
    
    return order;
  } catch (error) {
    logger.error('Database insert failed', {
      table: 'orders',
      error: { name: error.name, message: error.message },
      duration_ms: Math.round(performance.now() - start),
    });
    throw error;
  }
}
```

### 5. Avoid Excessive Logging

```typescript
// Bad - logging in loops
for (const item of items) {
  await processItem(item);
  logger.info('Item processed', { itemId: item.id }); // Too much!
}

// Good - log summary
const results = await Promise.all(items.map(processItem));
const successful = results.filter(r => r.success).length;
const failed = results.filter(r => !r.success).length;

logger.info('Batch processing completed', {
  total: items.length,
  successful,
  failed,
  duration_ms: elapsed,
});
```

## Contextual Logging

### Request Context Propagation

```typescript
// Middleware sets up context
app.use('*', async (c, next) => {
  const requestId = c.req.header('x-request-id') || crypto.randomUUID();
  const traceId = c.req.header('x-trace-id') || crypto.randomUUID();
  
  const logger = createLogger(c.env).child({
    requestId,
    traceId,
    path: c.req.path,
    method: c.req.method,
  });
  
  c.set('logger', logger);
  await next();
});

// Child loggers for specific operations
app.post('/orders', async (c) => {
  const logger = c.get('logger');
  const userId = c.get('userId');
  
  // Add user context
  const userLogger = logger.child({ userId });
  
  userLogger.info('Creating order');
  
  // Pass to services
  const order = await orderService.create(data, userLogger);
});

// Services receive logger with context
class OrderService {
  async create(data: OrderData, logger: Logger): Promise<Order> {
    logger.info('Validating order data');
    
    // Create child for payment operation
    const paymentLogger = logger.child({ operation: 'payment' });
    await this.processPayment(data, paymentLogger);
    
    logger.info('Order created');
  }
}
```

## Log Sampling

For high-traffic applications, sample logs to reduce volume:

```typescript
interface SamplingConfig {
  debug: number;  // 0.01 = 1%
  info: number;   // 0.1 = 10%
  warn: number;   // 1 = 100%
  error: number;  // 1 = 100%
}

const SAMPLING: SamplingConfig = {
  debug: 0.01,
  info: 0.1,
  warn: 1,
  error: 1,
};

function shouldSample(level: LogLevel): boolean {
  return Math.random() < SAMPLING[level];
}

// In logger
private log(level: LogLevel, message: string, data?: Record<string, unknown>) {
  if (LOG_LEVELS[level] < this.minLevel) return;
  if (!shouldSample(level)) return;
  
  // ... rest of logging
}
```

## Testing Logs

```typescript
import { describe, it, expect, vi } from 'vitest';
import { createLogger } from './logger';

describe('Logger', () => {
  it('logs JSON to console', () => {
    const consoleSpy = vi.spyOn(console, 'log');
    const logger = createLogger({ ENVIRONMENT: 'test' }, 'req-123');
    
    logger.info('Test message', { key: 'value' });
    
    expect(consoleSpy).toHaveBeenCalledTimes(1);
    
    const logged = JSON.parse(consoleSpy.mock.calls[0][0]);
    expect(logged).toMatchObject({
      level: 'info',
      message: 'Test message',
      requestId: 'req-123',
      key: 'value',
    });
    expect(logged.timestamp).toBeDefined();
  });
  
  it('redacts sensitive fields', () => {
    const consoleSpy = vi.spyOn(console, 'log');
    const logger = createLogger({ ENVIRONMENT: 'test' });
    
    logger.info('User auth', { password: 'secret123', email: 'test@test.com' });
    
    const logged = JSON.parse(consoleSpy.mock.calls[0][0]);
    expect(logged.password).toBe('[REDACTED]');
    expect(logged.email).toBe('test@test.com');
  });
});
```
