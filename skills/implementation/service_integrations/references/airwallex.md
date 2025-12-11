# Airwallex Integration

Integrate Airwallex payment processing, payouts, and multi-currency features into your application.

## Overview

Airwallex provides:
- **Payment acceptance**: Cards, wallets, local payment methods
- **Global payouts**: Pay vendors and suppliers worldwide
- **Multi-currency wallets**: Hold and manage funds in 60+ currencies
- **FX**: Competitive foreign exchange rates

## Authentication

### Obtain Access Token

Airwallex uses OAuth client credentials flow:

```typescript
// clients/airwallex.ts
interface AirwallexConfig {
  clientId: string;
  apiKey: string;
  environment: 'demo' | 'prod';
}

export class AirwallexClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor(private config: AirwallexConfig) {
    this.baseUrl = config.environment === 'prod'
      ? 'https://api.airwallex.com'
      : 'https://api-demo.airwallex.com';
  }

  private async ensureAccessToken(): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return this.accessToken;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/authentication/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-client-id': this.config.clientId,
        'x-api-key': this.config.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`Auth failed: ${response.status}`);
    }

    const data = await response.json();
    this.accessToken = data.token;
    this.tokenExpiry = Date.now() + (data.expires_in * 1000);
    
    return this.accessToken;
  }

  async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const token = await this.ensureAccessToken();

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new AirwallexError(
        error.code || 'API_ERROR',
        error.message || response.statusText,
        response.status
      );
    }

    return response.json();
  }
}

class AirwallexError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number
  ) {
    super(message);
    this.name = 'AirwallexError';
  }
}
```

## Payment Acceptance

### Create Payment Intent

```typescript
interface PaymentIntentRequest {
  amount: number;
  currency: string;
  merchant_order_id: string;
  request_id?: string; // Idempotency key
  descriptor?: string;
  customer_id?: string;
  metadata?: Record<string, string>;
  return_url?: string;
}

interface PaymentIntent {
  id: string;
  request_id: string;
  amount: number;
  currency: string;
  status: 'INITIAL' | 'REQUIRES_PAYMENT_METHOD' | 'REQUIRES_CAPTURE' | 'SUCCEEDED' | 'CANCELLED';
  client_secret: string;
  merchant_order_id: string;
  created_at: string;
}

export class AirwallexClient {
  // ... previous code ...

  async createPaymentIntent(data: PaymentIntentRequest): Promise<PaymentIntent> {
    return this.request<PaymentIntent>('POST', '/api/v1/pa/payment_intents/create', {
      ...data,
      request_id: data.request_id || crypto.randomUUID(),
    });
  }

  async getPaymentIntent(id: string): Promise<PaymentIntent> {
    return this.request<PaymentIntent>('GET', `/api/v1/pa/payment_intents/${id}`);
  }

  async confirmPaymentIntent(id: string, paymentMethod: object): Promise<PaymentIntent> {
    return this.request<PaymentIntent>('POST', `/api/v1/pa/payment_intents/${id}/confirm`, {
      payment_method: paymentMethod,
    });
  }

  async capturePaymentIntent(id: string, amount?: number): Promise<PaymentIntent> {
    return this.request<PaymentIntent>('POST', `/api/v1/pa/payment_intents/${id}/capture`, {
      capture_amount: amount,
    });
  }

  async cancelPaymentIntent(id: string, reason?: string): Promise<PaymentIntent> {
    return this.request<PaymentIntent>('POST', `/api/v1/pa/payment_intents/${id}/cancel`, {
      cancellation_reason: reason,
    });
  }
}
```

### Frontend Integration (React Native / Web)

```typescript
// Backend: Create intent and return client secret
app.post('/api/checkout', async (c) => {
  const { amount, currency, orderId } = await c.req.json();
  const airwallex = c.get('airwallex');

  const intent = await airwallex.createPaymentIntent({
    amount,
    currency,
    merchant_order_id: orderId,
    return_url: `${c.env.APP_URL}/checkout/complete`,
  });

  // Store intent ID with order
  await c.env.DB.prepare(`
    UPDATE orders SET payment_intent_id = ? WHERE id = ?
  `).bind(intent.id, orderId).run();

  return c.json({
    clientSecret: intent.client_secret,
    intentId: intent.id,
  });
});

// Frontend: Use Airwallex.js to complete payment
// See: https://www.airwallex.com/docs/developer-tools__sdks__airwallex.js
```

## Refunds

```typescript
interface RefundRequest {
  payment_intent_id: string;
  amount?: number; // Partial refund
  reason?: string;
  request_id?: string;
}

interface Refund {
  id: string;
  payment_intent_id: string;
  amount: number;
  currency: string;
  status: 'CREATED' | 'RECEIVED' | 'SUCCEEDED' | 'FAILED';
  reason?: string;
  created_at: string;
}

export class AirwallexClient {
  async createRefund(data: RefundRequest): Promise<Refund> {
    return this.request<Refund>('POST', '/api/v1/pa/refunds/create', {
      ...data,
      request_id: data.request_id || crypto.randomUUID(),
    });
  }

  async getRefund(id: string): Promise<Refund> {
    return this.request<Refund>('GET', `/api/v1/pa/refunds/${id}`);
  }
}
```

## Payouts (Transfers)

### Create Beneficiary

```typescript
interface BeneficiaryRequest {
  name: string;
  bank_details: {
    account_currency: string;
    account_name: string;
    account_number?: string;
    iban?: string;
    swift_code?: string;
    bank_country_code: string;
    bank_name?: string;
  };
  entity_type: 'COMPANY' | 'PERSONAL';
  address?: {
    city: string;
    country_code: string;
    postcode?: string;
    state?: string;
    street_address: string;
  };
}

interface Beneficiary {
  id: string;
  name: string;
  bank_details: object;
  status: 'CREATED' | 'VERIFIED' | 'REJECTED';
  created_at: string;
}

export class AirwallexClient {
  async createBeneficiary(data: BeneficiaryRequest): Promise<Beneficiary> {
    return this.request<Beneficiary>('POST', '/api/v1/beneficiaries/create', data);
  }

  async getBeneficiary(id: string): Promise<Beneficiary> {
    return this.request<Beneficiary>('GET', `/api/v1/beneficiaries/${id}`);
  }

  async listBeneficiaries(): Promise<{ items: Beneficiary[] }> {
    return this.request<{ items: Beneficiary[] }>('GET', '/api/v1/beneficiaries');
  }
}
```

### Create Transfer (Payout)

```typescript
interface TransferRequest {
  beneficiary_id: string;
  source_currency: string;
  source_amount?: number;
  payment_currency: string;
  payment_amount?: number;
  reason: string;
  reference?: string;
  request_id?: string;
}

interface Transfer {
  id: string;
  beneficiary_id: string;
  source_currency: string;
  source_amount: number;
  payment_currency: string;
  payment_amount: number;
  fee_currency: string;
  fee_amount: number;
  status: 'CREATED' | 'SUBMITTED' | 'PROCESSING' | 'SENT' | 'COMPLETED' | 'FAILED';
  created_at: string;
}

export class AirwallexClient {
  async createTransfer(data: TransferRequest): Promise<Transfer> {
    return this.request<Transfer>('POST', '/api/v1/transfers/create', {
      ...data,
      request_id: data.request_id || crypto.randomUUID(),
    });
  }

  async getTransfer(id: string): Promise<Transfer> {
    return this.request<Transfer>('GET', `/api/v1/transfers/${id}`);
  }
}
```

## FX (Foreign Exchange)

```typescript
interface FxQuote {
  quote_id: string;
  sell_currency: string;
  buy_currency: string;
  rate: number;
  sell_amount: number;
  buy_amount: number;
  valid_to: string;
}

interface ConversionRequest {
  sell_currency: string;
  buy_currency: string;
  sell_amount?: number;
  buy_amount?: number;
  reason: string;
  request_id?: string;
}

export class AirwallexClient {
  async getFxQuote(
    sellCurrency: string,
    buyCurrency: string,
    amount: number,
    direction: 'sell' | 'buy' = 'sell'
  ): Promise<FxQuote> {
    const params = new URLSearchParams({
      sell_currency: sellCurrency,
      buy_currency: buyCurrency,
      [direction === 'sell' ? 'sell_amount' : 'buy_amount']: amount.toString(),
    });

    return this.request<FxQuote>('GET', `/api/v1/fx/quotes?${params}`);
  }

  async createConversion(data: ConversionRequest): Promise<{ id: string }> {
    return this.request<{ id: string }>('POST', '/api/v1/fx/conversions/create', {
      ...data,
      request_id: data.request_id || crypto.randomUUID(),
    });
  }
}
```

## Balances

```typescript
interface Balance {
  available_amount: number;
  pending_amount: number;
  reserved_amount: number;
  total_amount: number;
  currency: string;
}

export class AirwallexClient {
  async getBalances(): Promise<{ items: Balance[] }> {
    return this.request<{ items: Balance[] }>('GET', '/api/v1/balances/current');
  }

  async getBalance(currency: string): Promise<Balance> {
    const { items } = await this.getBalances();
    const balance = items.find(b => b.currency === currency);
    if (!balance) throw new Error(`No balance for ${currency}`);
    return balance;
  }
}
```

## Webhook Events

### Event Types

| Event | Description |
|-------|-------------|
| `payment_intent.succeeded` | Payment completed successfully |
| `payment_intent.failed` | Payment failed |
| `payment_intent.cancelled` | Payment was cancelled |
| `payment_intent.requires_capture` | Auth successful, awaiting capture |
| `refund.succeeded` | Refund completed |
| `refund.failed` | Refund failed |
| `transfer.completed` | Payout completed |
| `transfer.failed` | Payout failed |

### Webhook Handler

```typescript
// webhooks/airwallex.ts
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Env }>();

app.post('/webhooks/airwallex', async (c) => {
  const body = await c.req.text();
  const signature = c.req.header('x-signature');
  const timestamp = c.req.header('x-timestamp');

  // Verify signature
  const isValid = await verifyAirwallexSignature(
    body,
    signature,
    timestamp,
    c.env.AIRWALLEX_WEBHOOK_SECRET
  );

  if (!isValid) {
    return c.json({ error: 'Invalid signature' }, 401);
  }

  const event = JSON.parse(body);
  
  // Idempotency check
  const processed = await c.env.KV.get(`webhook:${event.id}`);
  if (processed) {
    return c.json({ status: 'already_processed' }, 200);
  }

  // Route to handler
  switch (event.name) {
    case 'payment_intent.succeeded':
      await handlePaymentSucceeded(event.data, c.env);
      break;
    case 'payment_intent.failed':
      await handlePaymentFailed(event.data, c.env);
      break;
    case 'refund.succeeded':
      await handleRefundSucceeded(event.data, c.env);
      break;
    case 'transfer.completed':
      await handleTransferCompleted(event.data, c.env);
      break;
    default:
      console.log(`Unhandled event: ${event.name}`);
  }

  await c.env.KV.put(`webhook:${event.id}`, 'true', { expirationTtl: 604800 });
  
  return c.json({ status: 'processed' }, 200);
});

async function handlePaymentSucceeded(data: any, env: Env) {
  const { payment_intent_id, amount, currency } = data;
  
  // Update order
  await env.DB.prepare(`
    UPDATE orders 
    SET status = 'paid', 
        paid_amount = ?,
        paid_currency = ?,
        paid_at = datetime('now')
    WHERE payment_intent_id = ?
  `).bind(amount, currency, payment_intent_id).run();
  
  // Trigger fulfillment, send email, etc.
}

async function handlePaymentFailed(data: any, env: Env) {
  const { payment_intent_id, failure_reason } = data;
  
  await env.DB.prepare(`
    UPDATE orders 
    SET status = 'payment_failed',
        failure_reason = ?
    WHERE payment_intent_id = ?
  `).bind(failure_reason, payment_intent_id).run();
}

export default app;
```

### Signature Verification

```typescript
async function verifyAirwallexSignature(
  body: string,
  signature: string | null,
  timestamp: string | null,
  secret: string
): Promise<boolean> {
  if (!signature || !timestamp) return false;

  // Check timestamp (5 min tolerance)
  const timestampMs = parseInt(timestamp);
  if (Date.now() - timestampMs > 300000) return false;

  // Compute HMAC
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signatureBytes = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(timestamp + body)
  );

  const expected = Array.from(new Uint8Array(signatureBytes))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  return signature === expected;
}
```

## Complete Usage Example

```typescript
// services/payment-service.ts
export class PaymentService {
  constructor(
    private airwallex: AirwallexClient,
    private db: D1Database
  ) {}

  async createCheckout(orderId: string, amount: number, currency: string): Promise<string> {
    // Create Airwallex payment intent
    const intent = await this.airwallex.createPaymentIntent({
      amount,
      currency,
      merchant_order_id: orderId,
    });

    // Link to order
    await this.db.prepare(`
      UPDATE orders 
      SET payment_intent_id = ?, status = 'pending_payment'
      WHERE id = ?
    `).bind(intent.id, orderId).run();

    return intent.client_secret;
  }

  async processRefund(orderId: string, amount?: number): Promise<Refund> {
    const order = await this.db.prepare(
      'SELECT payment_intent_id, paid_amount FROM orders WHERE id = ?'
    ).bind(orderId).first<{ payment_intent_id: string; paid_amount: number }>();

    if (!order?.payment_intent_id) {
      throw new Error('Order has no payment');
    }

    const refund = await this.airwallex.createRefund({
      payment_intent_id: order.payment_intent_id,
      amount: amount || order.paid_amount,
      reason: 'Customer requested refund',
    });

    await this.db.prepare(`
      UPDATE orders SET refund_id = ?, refund_status = 'pending' WHERE id = ?
    `).bind(refund.id, orderId).run();

    return refund;
  }
}
```

## Best Practices

1. **Always use idempotency keys** (`request_id`) for create operations
2. **Store payment intent ID** with your order for reconciliation
3. **Handle webhooks** for async status updates (don't poll)
4. **Verify webhook signatures** before processing
5. **Use demo environment** for testing (api-demo.airwallex.com)
6. **Handle FX appropriately** - quote rates expire quickly
7. **Implement retry logic** for transient failures

## Demo vs Production

| Aspect | Demo | Production |
|--------|------|------------|
| Base URL | api-demo.airwallex.com | api.airwallex.com |
| Credentials | Demo client ID & API key | Production credentials |
| Cards | Test card numbers | Real cards |
| Funds | Simulated | Real money |
| Webhooks | Can be simulated | Real events |
