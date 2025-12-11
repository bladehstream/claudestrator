# HTTP Client Patterns

Robust patterns for making HTTP requests to external APIs with proper error handling, retries, and timeouts.

## Basic Fetch with Timeout

```typescript
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = 10000
): Promise<Response> {
  // Use AbortSignal.timeout() for cleaner timeout handling
  const response = await fetch(url, {
    ...options,
    signal: AbortSignal.timeout(timeoutMs),
  });
  
  return response;
}

// Usage
try {
  const response = await fetchWithTimeout('https://api.example.com/data', {
    method: 'GET',
    headers: { 'Authorization': 'Bearer token' },
  }, 5000);
  
  const data = await response.json();
} catch (error) {
  if (error.name === 'TimeoutError') {
    console.error('Request timed out');
  } else {
    console.error('Request failed:', error);
  }
}
```

## Retry with Exponential Backoff

```typescript
interface RetryOptions {
  retries?: number;
  initialDelay?: number;
  maxDelay?: number;
  retryableStatuses?: number[];
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryOptions: RetryOptions = {}
): Promise<Response> {
  const {
    retries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    retryableStatuses = [408, 429, 500, 502, 503, 504],
  } = retryOptions;

  let lastError: Error | undefined;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(30000),
      });

      // Success or non-retryable error
      if (response.ok || !retryableStatuses.includes(response.status)) {
        return response;
      }

      // Check for Retry-After header on 429
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        if (retryAfter) {
          delay = parseInt(retryAfter, 10) * 1000 || delay;
        }
      }

      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      // Network errors are retryable
      lastError = error as Error;
    }

    // Don't wait after last attempt
    if (attempt < retries) {
      // Add jitter to prevent thundering herd
      const jitter = Math.random() * 0.3 * delay;
      await sleep(delay + jitter);
      delay = Math.min(delay * 2, maxDelay);
    }
  }

  throw lastError || new Error('Request failed');
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

## Typed Response Handling

```typescript
interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

interface ApiErrorResponse {
  status: number;
  statusText: string;
  body: string;
}

class ApiRequestError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiRequestError';
  }

  get isRetryable(): boolean {
    return [408, 429, 500, 502, 503, 504].includes(this.status);
  }
}

async function typedFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const response = await fetch(url, options);

  if (!response.ok) {
    const body = await response.text();
    throw new ApiRequestError(response.status, response.statusText, body);
  }

  const data = await response.json() as T;
  
  return {
    data,
    status: response.status,
    headers: response.headers,
  };
}
```

## Request Interceptors Pattern

```typescript
type RequestInterceptor = (
  url: string,
  options: RequestInit
) => Promise<[string, RequestInit]> | [string, RequestInit];

type ResponseInterceptor = (
  response: Response
) => Promise<Response> | Response;

class HttpClient {
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  addRequestInterceptor(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor);
  }

  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    // Apply request interceptors
    let finalUrl = url;
    let finalOptions = options;
    
    for (const interceptor of this.requestInterceptors) {
      [finalUrl, finalOptions] = await interceptor(finalUrl, finalOptions);
    }

    // Make request
    let response = await fetch(finalUrl, finalOptions);

    // Apply response interceptors
    for (const interceptor of this.responseInterceptors) {
      response = await interceptor(response);
    }

    return response;
  }
}

// Usage: Add authentication
const client = new HttpClient();

client.addRequestInterceptor((url, options) => {
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${apiKey}`);
  return [url, { ...options, headers }];
});

// Usage: Add logging
client.addRequestInterceptor((url, options) => {
  console.log(`Request: ${options.method || 'GET'} ${url}`);
  return [url, options];
});

client.addResponseInterceptor((response) => {
  console.log(`Response: ${response.status} ${response.url}`);
  return response;
});
```

## Concurrent Requests with Limit

```typescript
async function fetchAllWithLimit<T>(
  urls: string[],
  limit: number,
  fetcher: (url: string) => Promise<T>
): Promise<T[]> {
  const results: T[] = [];
  const executing: Promise<void>[] = [];

  for (const url of urls) {
    const promise = fetcher(url).then(result => {
      results.push(result);
    });

    executing.push(promise);

    if (executing.length >= limit) {
      await Promise.race(executing);
      // Remove completed promises
      executing.splice(
        executing.findIndex(p => p === promise),
        1
      );
    }
  }

  await Promise.all(executing);
  return results;
}

// Usage: Fetch 100 URLs with max 5 concurrent requests
const urls = ['https://api.example.com/item/1', /* ... */];
const results = await fetchAllWithLimit(urls, 5, async (url) => {
  const response = await fetchWithRetry(url);
  return response.json();
});
```

## Request Deduplication

```typescript
class RequestDeduplicator {
  private pending = new Map<string, Promise<Response>>();

  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    // Create cache key from URL and relevant options
    const key = this.createKey(url, options);

    // Return existing promise if request is in flight
    const existing = this.pending.get(key);
    if (existing) {
      return existing.then(r => r.clone());
    }

    // Make new request
    const promise = fetch(url, options);
    this.pending.set(key, promise);

    try {
      const response = await promise;
      return response;
    } finally {
      this.pending.delete(key);
    }
  }

  private createKey(url: string, options: RequestInit): string {
    return `${options.method || 'GET'}:${url}`;
  }
}
```

## Cloudflare Workers-Specific Patterns

### Using Service Bindings
```typescript
// Call another Worker directly (faster than HTTP)
interface Env {
  AUTH_SERVICE: Fetcher;
}

app.get('/data', async (c) => {
  // Service binding - internal call, no network
  const authResponse = await c.env.AUTH_SERVICE.fetch(
    'https://auth/verify',
    { headers: c.req.header() }
  );
  
  if (!authResponse.ok) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  
  // Continue with main logic
});
```

### Caching External API Responses
```typescript
interface Env {
  CACHE: KVNamespace;
}

async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds: number,
  env: Env
): Promise<T> {
  // Check cache
  const cached = await env.CACHE.get(key, 'json');
  if (cached) {
    return cached as T;
  }

  // Fetch fresh data
  const data = await fetcher();

  // Cache in background (don't await)
  env.CACHE.put(key, JSON.stringify(data), {
    expirationTtl: ttlSeconds,
  });

  return data;
}

// Usage
const user = await cachedFetch(
  `user:${userId}`,
  () => fetchUser(userId),
  300, // 5 minutes
  c.env
);
```

## Best Practices

### Do's
```typescript
// ✅ Always set timeouts
signal: AbortSignal.timeout(30000)

// ✅ Handle specific error types
try {
  const response = await fetch(url);
} catch (error) {
  if (error.name === 'TimeoutError') {
    // Handle timeout
  } else if (error.name === 'TypeError') {
    // Network error
  }
}

// ✅ Log requests for debugging
console.log(JSON.stringify({
  event: 'api_request',
  url,
  method,
  duration_ms: Date.now() - start,
  status: response.status,
}));

// ✅ Use structured error responses
throw new ApiRequestError(response.status, response.statusText, body);
```

### Don'ts
```typescript
// ❌ Don't forget timeouts
await fetch(url); // Could hang forever

// ❌ Don't retry non-idempotent requests without care
if (method === 'POST') {
  // Be careful - might create duplicates
}

// ❌ Don't log sensitive data
console.log({ apiKey }); // Never!

// ❌ Don't ignore rate limits
if (response.status === 429) {
  // MUST handle this
}
```

## Complete HTTP Client Class

```typescript
export class HttpClient {
  constructor(
    private baseUrl: string,
    private options: {
      apiKey?: string;
      timeout?: number;
      retries?: number;
    } = {}
  ) {}

  async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.options.apiKey) {
      headers['Authorization'] = `Bearer ${this.options.apiKey}`;
    }

    const response = await fetchWithRetry(
      url,
      {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      },
      { retries: this.options.retries }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      throw new ApiRequestError(response.status, response.statusText, errorBody);
    }

    return response.json();
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body: unknown) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body: unknown) { return this.request<T>('PUT', path, body); }
  patch<T>(path: string, body: unknown) { return this.request<T>('PATCH', path, body); }
  delete<T>(path: string) { return this.request<T>('DELETE', path); }
}
```
