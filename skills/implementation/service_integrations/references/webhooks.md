# Webhook Handling

Securely receive and process webhook events from external services.

## Webhook Security Fundamentals

### 1. Always Verify Signatures

Never trust webhook payloads without verification:

```typescript
// webhooks/verify.ts
interface VerifyOptions {
  signature: string | null;
  timestamp: string | null;
  body: string;
  secret: string;
  tolerance?: number; // seconds
}

export async function verifyWebhookSignature(options: VerifyOptions): Promise<boolean> {
  const { signature, timestamp, body, secret, tolerance = 300 } = options;

  if (!signature || !timestamp) {
    return false;
  }

  // Check timestamp to prevent replay attacks
  const timestampSeconds = parseInt(timestamp, 10);
  const now = Math.floor(Date.now() / 1000);
  
  if (Math.abs(now - timestampSeconds) > tolerance) {
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${body}`;
  const expectedSignature = await computeHmac(signedPayload, secret);

  // Constant-time comparison
  return timingSafeEqual(signature, expectedSignature);
}

async function computeHmac(message: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(message)
  );

  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
```

### 2. Idempotent Processing

Handle duplicate webhook deliveries safely:

```typescript
// webhooks/idempotency.ts
interface IdempotencyStore {
  check(eventId: string): Promise<boolean>;
  mark(eventId: string): Promise<void>;
}

// Using KV for idempotency
class KVIdempotencyStore implements IdempotencyStore {
  constructor(private kv: KVNamespace, private ttl: number = 86400 * 7) {}

  async check(eventId: string): Promise<boolean> {
    const exists = await this.kv.get(`webhook:processed:${eventId}`);
    return exists !== null;
  }

  async mark(eventId: string): Promise<void> {
    await this.kv.put(
      `webhook:processed:${eventId}`,
      JSON.stringify({ processedAt: new Date().toISOString() }),
      { expirationTtl: this.ttl }
    );
  }
}

// Using D1 for idempotency (with more metadata)
class D1IdempotencyStore implements IdempotencyStore {
  constructor(private db: D1Database) {}

  async check(eventId: string): Promise<boolean> {
    const result = await this.db.prepare(
      'SELECT id FROM processed_webhooks WHERE event_id = ?'
    ).bind(eventId).first();
    return result !== null;
  }

  async mark(eventId: string): Promise<void> {
    await this.db.prepare(`
      INSERT INTO processed_webhooks (event_id, processed_at)
      VALUES (?, datetime('now'))
    `).bind(eventId).run();
  }
}
```

## Webhook Handler Pattern

### Complete Handler Implementation

```typescript
// webhooks/handler.ts
import { Hono } from 'hono';
import { z } from 'zod';
import { verifyWebhookSignature } from './verify';
import { KVIdempotencyStore } from './idempotency';

const WebhookEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  data: z.unknown(),
  created_at: z.string(),
});

type WebhookEvent = z.infer<typeof WebhookEventSchema>;

type EventHandler = (event: WebhookEvent, env: Env) => Promise<void>;

const eventHandlers: Record<string, EventHandler> = {
  'payment_intent.succeeded': handlePaymentSucceeded,
  'payment_intent.failed': handlePaymentFailed,
  'customer.created': handleCustomerCreated,
  // Add more handlers
};

const app = new Hono<{ Bindings: Env }>();

app.post('/webhooks/payments', async (c) => {
  const logger = c.get('logger');
  const idempotency = new KVIdempotencyStore(c.env.KV);

  // Get raw body for signature verification
  const body = await c.req.text();
  const signature = c.req.header('x-signature');
  const timestamp = c.req.header('x-timestamp');

  // Verify signature
  const isValid = await verifyWebhookSignature({
    signature,
    timestamp,
    body,
    secret: c.env.WEBHOOK_SECRET,
  });

  if (!isValid) {
    logger.warn('Invalid webhook signature', {
      signature: signature?.slice(0, 10) + '...',
    });
    return c.json({ error: 'Invalid signature' }, 401);
  }

  // Parse and validate event
  let event: WebhookEvent;
  try {
    const parsed = JSON.parse(body);
    event = WebhookEventSchema.parse(parsed);
  } catch (error) {
    logger.error('Invalid webhook payload', { error: String(error) });
    return c.json({ error: 'Invalid payload' }, 400);
  }

  logger.info('Webhook received', { eventId: event.id, type: event.type });

  // Check idempotency
  if (await idempotency.check(event.id)) {
    logger.info('Webhook already processed', { eventId: event.id });
    return c.json({ status: 'already_processed' }, 200);
  }

  // Find handler
  const handler = eventHandlers[event.type];
  if (!handler) {
    logger.warn('No handler for event type', { type: event.type });
    // Still return 200 to acknowledge receipt
    return c.json({ status: 'ignored' }, 200);
  }

  // Process event
  try {
    await handler(event, c.env);
    await idempotency.mark(event.id);
    
    logger.info('Webhook processed', { eventId: event.id, type: event.type });
    return c.json({ status: 'processed' }, 200);
  } catch (error) {
    logger.error('Webhook processing failed', {
      eventId: event.id,
      type: event.type,
      error: String(error),
    });
    
    // Return 500 to trigger retry
    return c.json({ error: 'Processing failed' }, 500);
  }
});

// Event handlers
async function handlePaymentSucceeded(event: WebhookEvent, env: Env): Promise<void> {
  const data = event.data as { payment_intent_id: string; amount: number };
  
  // Update order status
  await env.DB.prepare(`
    UPDATE orders 
    SET payment_status = 'paid', paid_at = datetime('now')
    WHERE payment_intent_id = ?
  `).bind(data.payment_intent_id).run();
  
  // Send confirmation email
  // await sendOrderConfirmation(order);
}

async function handlePaymentFailed(event: WebhookEvent, env: Env): Promise<void> {
  const data = event.data as { payment_intent_id: string; failure_reason: string };
  
  await env.DB.prepare(`
    UPDATE orders 
    SET payment_status = 'failed', failure_reason = ?
    WHERE payment_intent_id = ?
  `).bind(data.failure_reason, data.payment_intent_id).run();
}

async function handleCustomerCreated(event: WebhookEvent, env: Env): Promise<void> {
  const data = event.data as { id: string; email: string };
  
  await env.DB.prepare(`
    INSERT INTO customers (external_id, email, created_at)
    VALUES (?, ?, datetime('now'))
    ON CONFLICT (external_id) DO NOTHING
  `).bind(data.id, data.email).run();
}

export default app;
```

## Provider-Specific Verification

### Stripe Signature Verification

```typescript
async function verifyStripeSignature(
  payload: string,
  signature: string,
  secret: string
): Promise<boolean> {
  // Stripe format: t=timestamp,v1=signature
  const elements = signature.split(',');
  const timestamp = elements.find(e => e.startsWith('t='))?.slice(2);
  const sig = elements.find(e => e.startsWith('v1='))?.slice(3);

  if (!timestamp || !sig) return false;

  // Check timestamp (5 min tolerance)
  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp);
  if (age > 300) return false;

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload}`;
  const expected = await computeHmac(signedPayload, secret);

  return timingSafeEqual(sig, expected);
}
```

### Airwallex Signature Verification

```typescript
async function verifyAirwallexSignature(
  payload: string,
  signature: string,
  timestamp: string,
  secret: string
): Promise<boolean> {
  // Check timestamp
  const timestampMs = parseInt(timestamp);
  if (Date.now() - timestampMs > 300000) return false; // 5 min

  // Airwallex: HMAC-SHA256(timestamp + payload)
  const signedPayload = timestamp + payload;
  const expected = await computeHmac(signedPayload, secret);

  return timingSafeEqual(signature, expected);
}
```

### SendGrid Signature Verification

```typescript
async function verifySendGridSignature(
  payload: string,
  signature: string,
  timestamp: string,
  verificationKey: string
): Promise<boolean> {
  // SendGrid uses ECDSA
  const timestampPayload = timestamp + payload;
  
  // Import public key
  const key = await crypto.subtle.importKey(
    'spki',
    base64ToArrayBuffer(verificationKey),
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['verify']
  );

  return crypto.subtle.verify(
    { name: 'ECDSA', hash: 'SHA-256' },
    key,
    base64ToArrayBuffer(signature),
    new TextEncoder().encode(timestampPayload)
  );
}
```

## Queue-Based Processing

For complex webhook processing, use a queue pattern:

```typescript
// webhooks/queue-handler.ts
app.post('/webhooks/payments', async (c) => {
  const body = await c.req.text();
  
  // Verify signature (same as before)
  const isValid = await verifyWebhookSignature({...});
  if (!isValid) return c.json({ error: 'Invalid signature' }, 401);

  const event = JSON.parse(body);

  // Quick acknowledgment - just queue the event
  await c.env.WEBHOOK_QUEUE.send({
    type: 'webhook',
    eventId: event.id,
    eventType: event.type,
    payload: body,
    receivedAt: new Date().toISOString(),
  });

  // Immediate response
  return c.json({ status: 'queued' }, 200);
});

// Queue consumer (separate worker or DO)
export default {
  async queue(batch: MessageBatch<WebhookMessage>, env: Env) {
    for (const message of batch.messages) {
      try {
        await processWebhookEvent(message.body, env);
        message.ack();
      } catch (error) {
        message.retry({ delaySeconds: 60 });
      }
    }
  },
};
```

## Webhook Testing

### Mock Webhook Sender

```typescript
// tests/webhook-sender.ts
export async function sendTestWebhook(
  url: string,
  event: object,
  secret: string
): Promise<Response> {
  const body = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const signature = await computeHmac(`${timestamp}.${body}`, secret);

  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-timestamp': timestamp,
      'x-signature': signature,
    },
    body,
  });
}

// Usage in tests
describe('Webhook Handler', () => {
  it('processes payment succeeded event', async () => {
    const response = await sendTestWebhook(
      'http://localhost:8787/webhooks/payments',
      {
        id: 'evt_123',
        type: 'payment_intent.succeeded',
        data: { payment_intent_id: 'pi_123', amount: 9999 },
        created_at: new Date().toISOString(),
      },
      'test_webhook_secret'
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: 'processed' });
  });
});
```

## Best Practices

### 1. Respond Quickly

```typescript
// Good: Quick response, async processing
app.post('/webhooks', async (c) => {
  const event = await parseAndVerify(c);
  
  // Queue for async processing
  c.executionCtx.waitUntil(processEvent(event, c.env));
  
  // Immediate response
  return c.json({ status: 'received' }, 200);
});
```

### 2. Log Everything

```typescript
app.post('/webhooks', async (c) => {
  const logger = c.get('logger');
  const body = await c.req.text();
  
  // Log receipt
  logger.info('Webhook received', {
    headers: Object.fromEntries(c.req.raw.headers),
    bodyPreview: body.slice(0, 200),
  });
  
  // ... processing ...
  
  // Log result
  logger.info('Webhook processed', { eventId, result });
});
```

### 3. Handle Retries Gracefully

```typescript
app.post('/webhooks', async (c) => {
  const event = await parseAndVerify(c);
  
  // Check if already processed
  const existingResult = await getProcessingResult(event.id);
  if (existingResult) {
    // Return same result as original processing
    return c.json(existingResult, 200);
  }
  
  // Process and store result
  const result = await processEvent(event);
  await storeProcessingResult(event.id, result);
  
  return c.json(result, 200);
});
```

### 4. Alert on Failures

```typescript
app.post('/webhooks', async (c) => {
  try {
    // ... processing ...
  } catch (error) {
    // Send alert for investigation
    c.executionCtx.waitUntil(
      sendAlert({
        type: 'webhook_failure',
        eventId: event.id,
        error: String(error),
      }, c.env)
    );
    
    throw error; // Return 500 to trigger retry
  }
});
```
