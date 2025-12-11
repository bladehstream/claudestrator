# API Clients

Build type-safe, reliable API clients for external service integration.

## Base Client Architecture

### Generic HTTP Client

```typescript
// clients/http-client.ts
import { z } from 'zod';

interface HttpClientConfig {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout?: number;
}

interface RequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
  query?: Record<string, string | number | boolean>;
}

export class HttpClient {
  private config: Required<HttpClientConfig>;

  constructor(config: HttpClientConfig) {
    this.config = {
      baseUrl: config.baseUrl,
      headers: config.headers || {},
      timeout: config.timeout || 30000,
    };
  }

  async request<T>(options: RequestOptions, schema?: z.ZodSchema<T>): Promise<T> {
    const url = this.buildUrl(options.path, options.query);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        method: options.method,
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers,
          ...options.headers,
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw await this.handleErrorResponse(response);
      }

      const data = await response.json();
      
      // Validate response against schema if provided
      if (schema) {
        const result = schema.safeParse(data);
        if (!result.success) {
          throw new ApiError(
            'VALIDATION_ERROR',
            'Response validation failed',
            response.status,
            result.error.errors
          );
        }
        return result.data;
      }

      return data as T;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError) throw error;
      
      if (error.name === 'AbortError') {
        throw new ApiError('TIMEOUT', 'Request timeout', 408);
      }
      
      throw new ApiError('NETWORK_ERROR', error.message, 0);
    }
  }

  private buildUrl(path: string, query?: Record<string, string | number | boolean>): string {
    const url = new URL(path, this.config.baseUrl);
    
    if (query) {
      for (const [key, value] of Object.entries(query)) {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, String(value));
        }
      }
    }
    
    return url.toString();
  }

  private async handleErrorResponse(response: Response): Promise<ApiError> {
    try {
      const body = await response.json();
      return new ApiError(
        body.code || 'API_ERROR',
        body.message || response.statusText,
        response.status,
        body
      );
    } catch {
      return new ApiError(
        'API_ERROR',
        response.statusText,
        response.status
      );
    }
  }
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }

  isRetryable(): boolean {
    return this.status === 429 || this.status >= 500;
  }
}
```

## Authentication Patterns

### API Key Authentication

```typescript
class ApiKeyClient extends HttpClient {
  constructor(config: { baseUrl: string; apiKey: string }) {
    super({
      baseUrl: config.baseUrl,
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
      },
    });
  }
}

// Usage
const client = new ApiKeyClient({
  baseUrl: 'https://api.example.com',
  apiKey: env.API_KEY,
});
```

### Basic Authentication

```typescript
class BasicAuthClient extends HttpClient {
  constructor(config: { baseUrl: string; username: string; password: string }) {
    const credentials = btoa(`${config.username}:${config.password}`);
    super({
      baseUrl: config.baseUrl,
      headers: {
        'Authorization': `Basic ${credentials}`,
      },
    });
  }
}
```

### OAuth Client Credentials

```typescript
class OAuthClient extends HttpClient {
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor(
    private oauthConfig: {
      baseUrl: string;
      tokenUrl: string;
      clientId: string;
      clientSecret: string;
    }
  ) {
    super({ baseUrl: oauthConfig.baseUrl });
  }

  async request<T>(options: RequestOptions, schema?: z.ZodSchema<T>): Promise<T> {
    // Ensure we have a valid token
    await this.ensureAccessToken();

    // Add token to headers
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`,
    };

    try {
      return await super.request({ ...options, headers }, schema);
    } catch (error) {
      // Refresh token on 401 and retry once
      if (error instanceof ApiError && error.status === 401) {
        this.accessToken = null;
        await this.ensureAccessToken();
        return super.request({
          ...options,
          headers: { ...options.headers, 'Authorization': `Bearer ${this.accessToken}` },
        }, schema);
      }
      throw error;
    }
  }

  private async ensureAccessToken(): Promise<void> {
    if (this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return; // Token still valid (with 1 min buffer)
    }

    const response = await fetch(this.oauthConfig.tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: this.oauthConfig.clientId,
        client_secret: this.oauthConfig.clientSecret,
      }),
    });

    if (!response.ok) {
      throw new ApiError('AUTH_ERROR', 'Failed to obtain access token', response.status);
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.tokenExpiry = Date.now() + (data.expires_in * 1000);
  }
}
```

### JWT with Refresh Token

```typescript
class JwtClient extends HttpClient {
  private accessToken: string | null = null;
  private refreshToken: string;
  private tokenExpiry: number = 0;

  constructor(
    private config: {
      baseUrl: string;
      refreshUrl: string;
      refreshToken: string;
    }
  ) {
    super({ baseUrl: config.baseUrl });
    this.refreshToken = config.refreshToken;
  }

  async request<T>(options: RequestOptions, schema?: z.ZodSchema<T>): Promise<T> {
    await this.ensureAccessToken();
    
    return super.request({
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`,
      },
    }, schema);
  }

  private async ensureAccessToken(): Promise<void> {
    if (this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return;
    }

    const response = await fetch(this.config.refreshUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      throw new ApiError('AUTH_ERROR', 'Token refresh failed', response.status);
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.tokenExpiry = Date.now() + (data.expires_in * 1000);
    
    if (data.refresh_token) {
      this.refreshToken = data.refresh_token;
    }
  }
}
```

## Type-Safe Service Client

### Example: Payment Service Client

```typescript
// clients/payment-service.ts
import { z } from 'zod';
import { HttpClient, ApiError } from './http-client';

// Response schemas
const PaymentIntentSchema = z.object({
  id: z.string(),
  amount: z.number(),
  currency: z.string(),
  status: z.enum(['pending', 'processing', 'succeeded', 'failed']),
  client_secret: z.string(),
  created_at: z.string(),
});

const PaymentIntentListSchema = z.object({
  data: z.array(PaymentIntentSchema),
  has_more: z.boolean(),
});

type PaymentIntent = z.infer<typeof PaymentIntentSchema>;
type PaymentIntentList = z.infer<typeof PaymentIntentListSchema>;

// Request types
interface CreatePaymentIntentRequest {
  amount: number;
  currency: string;
  customer_id?: string;
  metadata?: Record<string, string>;
}

// Client implementation
export class PaymentServiceClient {
  private http: HttpClient;

  constructor(config: { baseUrl: string; apiKey: string }) {
    this.http = new HttpClient({
      baseUrl: config.baseUrl,
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'X-Api-Version': '2024-01-01',
      },
    });
  }

  async createPaymentIntent(data: CreatePaymentIntentRequest): Promise<PaymentIntent> {
    return this.http.request(
      {
        method: 'POST',
        path: '/v1/payment_intents',
        body: data,
      },
      PaymentIntentSchema
    );
  }

  async getPaymentIntent(id: string): Promise<PaymentIntent> {
    return this.http.request(
      {
        method: 'GET',
        path: `/v1/payment_intents/${id}`,
      },
      PaymentIntentSchema
    );
  }

  async listPaymentIntents(options?: {
    limit?: number;
    starting_after?: string;
    customer_id?: string;
  }): Promise<PaymentIntentList> {
    return this.http.request(
      {
        method: 'GET',
        path: '/v1/payment_intents',
        query: options as Record<string, string | number>,
      },
      PaymentIntentListSchema
    );
  }

  async confirmPaymentIntent(id: string): Promise<PaymentIntent> {
    return this.http.request(
      {
        method: 'POST',
        path: `/v1/payment_intents/${id}/confirm`,
      },
      PaymentIntentSchema
    );
  }

  async cancelPaymentIntent(id: string): Promise<PaymentIntent> {
    return this.http.request(
      {
        method: 'POST',
        path: `/v1/payment_intents/${id}/cancel`,
      },
      PaymentIntentSchema
    );
  }
}
```

## Client with Logging

```typescript
import { Logger } from '../utils/logger';

class LoggedHttpClient extends HttpClient {
  constructor(
    config: HttpClientConfig,
    private logger: Logger,
    private serviceName: string
  ) {
    super(config);
  }

  async request<T>(options: RequestOptions, schema?: z.ZodSchema<T>): Promise<T> {
    const start = performance.now();
    const requestId = crypto.randomUUID().slice(0, 8);

    this.logger.debug(`[${this.serviceName}] Request started`, {
      requestId,
      method: options.method,
      path: options.path,
    });

    try {
      const result = await super.request(options, schema);
      const duration = Math.round(performance.now() - start);

      this.logger.info(`[${this.serviceName}] Request completed`, {
        requestId,
        method: options.method,
        path: options.path,
        duration_ms: duration,
      });

      return result;
    } catch (error) {
      const duration = Math.round(performance.now() - start);

      this.logger.error(`[${this.serviceName}] Request failed`, {
        requestId,
        method: options.method,
        path: options.path,
        duration_ms: duration,
        error: error instanceof ApiError ? {
          code: error.code,
          status: error.status,
          message: error.message,
        } : { message: String(error) },
      });

      throw error;
    }
  }
}
```

## Client Factory Pattern

```typescript
// clients/factory.ts
interface ServiceClients {
  payment: PaymentServiceClient;
  email: EmailServiceClient;
  analytics: AnalyticsClient;
}

export function createServiceClients(env: Env, logger: Logger): ServiceClients {
  return {
    payment: new PaymentServiceClient({
      baseUrl: env.PAYMENT_API_URL,
      apiKey: env.PAYMENT_API_KEY,
    }),
    email: new EmailServiceClient({
      baseUrl: 'https://api.sendgrid.com',
      apiKey: env.SENDGRID_API_KEY,
    }),
    analytics: new AnalyticsClient({
      baseUrl: env.ANALYTICS_API_URL,
      apiKey: env.ANALYTICS_API_KEY,
    }),
  };
}

// Usage in Hono
app.use('*', async (c, next) => {
  const logger = c.get('logger');
  c.set('services', createServiceClients(c.env, logger));
  await next();
});

app.post('/orders', async (c) => {
  const services = c.get('services');
  const intent = await services.payment.createPaymentIntent({
    amount: 9999,
    currency: 'usd',
  });
  // ...
});
```

## Testing API Clients

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PaymentServiceClient } from './payment-service';

describe('PaymentServiceClient', () => {
  let client: PaymentServiceClient;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    global.fetch = fetchMock;
    
    client = new PaymentServiceClient({
      baseUrl: 'https://api.test.com',
      apiKey: 'test_key',
    });
  });

  it('creates payment intent', async () => {
    const mockResponse = {
      id: 'pi_123',
      amount: 9999,
      currency: 'usd',
      status: 'pending',
      client_secret: 'secret_123',
      created_at: '2024-01-01T00:00:00Z',
    };

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await client.createPaymentIntent({
      amount: 9999,
      currency: 'usd',
    });

    expect(result).toEqual(mockResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.test.com/v1/payment_intents',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test_key',
        }),
      })
    );
  });

  it('handles API errors', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({
        code: 'invalid_amount',
        message: 'Amount must be positive',
      }),
    });

    await expect(client.createPaymentIntent({
      amount: -100,
      currency: 'usd',
    })).rejects.toThrow('Amount must be positive');
  });
});
```
