# Async Processing

Handle long-running external operations reliably using Cloudflare Queues, background processing, and reliable delivery patterns.

## Why Async Processing?

External API calls can:
- Be slow (> 30 second timeout)
- Fail transiently
- Hit rate limits
- Need retries

Process them asynchronously to:
- Respond quickly to users
- Retry failed operations
- Handle rate limits gracefully
- Maintain reliability

## Cloudflare Queues Setup

### Configuration
```toml
# wrangler.toml
[[queues.producers]]
queue = "external-api-queue"
binding = "EXTERNAL_API_QUEUE"

[[queues.consumers]]
queue = "external-api-queue"
max_batch_size = 10
max_batch_timeout = 30
max_retries = 3
dead_letter_queue = "external-api-dlq"

# Dead letter queue for failed messages
[[queues.producers]]
queue = "external-api-dlq"
binding = "EXTERNAL_API_DLQ"
```

### Producer: Enqueue Work
```typescript
interface Env {
  EXTERNAL_API_QUEUE: Queue;
}

interface ExternalApiJob {
  type: 'send_email' | 'process_payment' | 'sync_data';
  payload: unknown;
  metadata: {
    correlationId: string;
    createdAt: string;
    userId?: string;
  };
}

// Enqueue a job
app.post('/orders', async (c) => {
  const order = await createOrder(c.req.json());
  
  // Queue payment processing
  await c.env.EXTERNAL_API_QUEUE.send({
    type: 'process_payment',
    payload: {
      orderId: order.id,
      amount: order.total,
      currency: 'USD',
    },
    metadata: {
      correlationId: c.get('requestId'),
      createdAt: new Date().toISOString(),
      userId: c.get('user').id,
    },
  } satisfies ExternalApiJob);
  
  return c.json({ order, status: 'processing' });
});
```

### Consumer: Process Work
```typescript
interface Env {
  EXTERNAL_API_QUEUE: Queue;
  EXTERNAL_API_DLQ: Queue;
}

export default {
  async queue(
    batch: MessageBatch<ExternalApiJob>,
    env: Env
  ): Promise<void> {
    for (const message of batch.messages) {
      try {
        await processJob(message.body, env);
        message.ack();
      } catch (error) {
        console.error('Job failed:', {
          type: message.body.type,
          correlationId: message.body.metadata.correlationId,
          error: (error as Error).message,
          attempt: message.attempts,
        });
        
        // Retry or send to DLQ
        if (message.attempts >= 3) {
          await env.EXTERNAL_API_DLQ.send({
            ...message.body,
            error: (error as Error).message,
            failedAt: new Date().toISOString(),
          });
          message.ack(); // Acknowledge to remove from main queue
        } else {
          message.retry(); // Will be retried
        }
      }
    }
  },
};

async function processJob(job: ExternalApiJob, env: Env): Promise<void> {
  switch (job.type) {
    case 'send_email':
      await sendEmail(job.payload as EmailPayload, env);
      break;
    case 'process_payment':
      await processPayment(job.payload as PaymentPayload, env);
      break;
    case 'sync_data':
      await syncData(job.payload as SyncPayload, env);
      break;
    default:
      throw new Error(`Unknown job type: ${job.type}`);
  }
}
```

## Webhook Async Processing

Process webhooks asynchronously to respond quickly:

```typescript
app.post('/webhooks/stripe', async (c) => {
  const rawBody = await c.req.text();
  const signature = c.req.header('stripe-signature');
  
  // Verify signature synchronously (fast)
  if (!verifyStripeSignature(rawBody, signature, c.env.STRIPE_WEBHOOK_SECRET)) {
    return c.json({ error: 'Invalid signature' }, 401);
  }
  
  const event = JSON.parse(rawBody);
  
  // Queue for async processing (respond immediately)
  await c.env.WEBHOOK_QUEUE.send({
    provider: 'stripe',
    eventId: event.id,
    eventType: event.type,
    payload: event,
    receivedAt: new Date().toISOString(),
  });
  
  // Respond within 5 seconds (Stripe requirement)
  return c.json({ received: true });
});
```

## Idempotency for External Calls

Ensure operations only execute once:

```typescript
interface Env {
  IDEMPOTENCY_KEYS: KVNamespace;
}

async function executeIdempotent<T>(
  key: string,
  operation: () => Promise<T>,
  env: Env,
  ttlSeconds = 86400 // 24 hours
): Promise<{ result: T; cached: boolean }> {
  // Check if already processed
  const existing = await env.IDEMPOTENCY_KEYS.get(key, 'json');
  if (existing) {
    return { result: existing as T, cached: true };
  }
  
  // Execute operation
  const result = await operation();
  
  // Store result
  await env.IDEMPOTENCY_KEYS.put(key, JSON.stringify(result), {
    expirationTtl: ttlSeconds,
  });
  
  return { result, cached: false };
}

// Usage in queue consumer
async function processPayment(payload: PaymentPayload, env: Env) {
  const idempotencyKey = `payment:${payload.orderId}`;
  
  const { result, cached } = await executeIdempotent(
    idempotencyKey,
    () => stripeClient.charges.create({
      amount: payload.amount,
      currency: payload.currency,
      source: payload.paymentMethod,
    }),
    env
  );
  
  if (cached) {
    console.log('Payment already processed:', payload.orderId);
  }
  
  return result;
}
```

## Delayed Jobs

Schedule jobs for future execution:

```typescript
// Using Queues with delay
await c.env.EXTERNAL_API_QUEUE.send(
  { type: 'send_reminder', payload: { userId } },
  { delaySeconds: 3600 } // 1 hour delay
);

// Using Durable Object Alarms for precise timing
export class ScheduledJobDO {
  constructor(private state: DurableObjectState) {}

  async scheduleJob(job: Job, executeAt: Date): Promise<void> {
    await this.state.storage.put(`job:${job.id}`, job);
    await this.state.storage.setAlarm(executeAt.getTime());
  }

  async alarm(): Promise<void> {
    const jobs = await this.state.storage.list({ prefix: 'job:' });
    
    for (const [key, job] of jobs) {
      try {
        await executeJob(job as Job);
        await this.state.storage.delete(key);
      } catch (error) {
        console.error('Scheduled job failed:', error);
        // Will retry on next alarm
      }
    }
  }
}
```

## Batch Processing

Process multiple items efficiently:

```typescript
interface BatchJob<T> {
  items: T[];
  batchId: string;
  total: number;
  offset: number;
}

// Split large jobs into batches
async function enqueueBatch<T>(
  items: T[],
  queue: Queue,
  batchSize = 100
): Promise<string> {
  const batchId = crypto.randomUUID();
  const batches: BatchJob<T>[] = [];
  
  for (let i = 0; i < items.length; i += batchSize) {
    batches.push({
      items: items.slice(i, i + batchSize),
      batchId,
      total: items.length,
      offset: i,
    });
  }
  
  // Enqueue all batches
  await Promise.all(batches.map(batch => queue.send(batch)));
  
  return batchId;
}

// Process batch
async function processBatch<T>(
  batch: BatchJob<T>,
  processor: (item: T) => Promise<void>
): Promise<void> {
  const results = await Promise.allSettled(
    batch.items.map(item => processor(item))
  );
  
  const failed = results.filter(r => r.status === 'rejected');
  
  console.log(JSON.stringify({
    event: 'batch_processed',
    batchId: batch.batchId,
    offset: batch.offset,
    total: batch.total,
    processed: results.length,
    failed: failed.length,
  }));
  
  if (failed.length > 0) {
    throw new Error(`${failed.length} items failed in batch`);
  }
}
```

## Progress Tracking

Track async job progress:

```typescript
interface Env {
  JOB_STATUS: KVNamespace;
}

interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: unknown;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

async function updateJobStatus(
  jobId: string,
  update: Partial<JobStatus>,
  env: Env
): Promise<void> {
  const existing = await env.JOB_STATUS.get(jobId, 'json') as JobStatus | null;
  const status: JobStatus = {
    ...existing,
    ...update,
    id: jobId,
    updatedAt: new Date().toISOString(),
  } as JobStatus;
  
  await env.JOB_STATUS.put(jobId, JSON.stringify(status), {
    expirationTtl: 86400, // 24 hours
  });
}

// API endpoint to check status
app.get('/jobs/:id/status', async (c) => {
  const status = await c.env.JOB_STATUS.get(c.req.param('id'), 'json');
  
  if (!status) {
    return c.json({ error: 'Job not found' }, 404);
  }
  
  return c.json(status);
});
```

## Error Handling Patterns

### Retry with Backoff in Consumer
```typescript
async function processWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry if it's a permanent failure
      if (isPermanentFailure(error)) {
        throw error;
      }
      
      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await sleep(delay);
    }
  }
  
  throw lastError;
}

function isPermanentFailure(error: unknown): boolean {
  if (error instanceof ApiError) {
    // 4xx errors (except 429) are permanent
    return error.status >= 400 && error.status < 500 && error.status !== 429;
  }
  return false;
}
```

### Dead Letter Queue Processing
```typescript
// Periodic job to review DLQ
app.get('/admin/dlq', async (c) => {
  const messages = await c.env.EXTERNAL_API_DLQ.list({ limit: 100 });
  return c.json(messages);
});

// Manual retry from DLQ
app.post('/admin/dlq/:id/retry', async (c) => {
  // Fetch from DLQ, re-enqueue to main queue
  // This would need custom logic based on your DLQ implementation
});
```

## Best Practices

1. **Always use idempotency keys** for external mutations
2. **Set reasonable timeouts** in queue consumers
3. **Log with correlation IDs** for tracing
4. **Monitor queue depth** and DLQ size
5. **Handle partial batch failures** gracefully
6. **Design for at-least-once delivery** (messages may be delivered multiple times)
7. **Keep messages small** - store large payloads in R2/KV
8. **Use DLQ** for investigation and manual retry
