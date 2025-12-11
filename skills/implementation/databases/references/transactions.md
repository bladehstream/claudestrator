# Database Transactions Reference

Transaction patterns, isolation levels, and concurrency handling for TypeScript applications.

## ACID Properties

| Property | Description | Example |
|----------|-------------|---------|
| **Atomicity** | All or nothing | Transfer funds: both debit and credit succeed or both fail |
| **Consistency** | Valid state to valid state | Constraints maintained after transaction |
| **Isolation** | Concurrent transactions don't interfere | Parallel reads see consistent data |
| **Durability** | Committed data survives crashes | After commit, data is persisted |

## Isolation Levels

### PostgreSQL Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Use Case |
|-------|------------|---------------------|--------------|----------|
| Read Uncommitted* | ✗ | ✓ | ✓ | N/A (same as Read Committed) |
| **Read Committed** (default) | ✗ | ✓ | ✓ | Most applications |
| Repeatable Read | ✗ | ✗ | ✗** | Reports, consistent reads |
| Serializable | ✗ | ✗ | ✗ | Financial, strict consistency |

*PostgreSQL Read Uncommitted = Read Committed  
**PostgreSQL Repeatable Read prevents phantoms via snapshot isolation

### Anomalies Explained

**Dirty Read**: Reading uncommitted changes from another transaction
```sql
-- Transaction 1          -- Transaction 2
UPDATE accounts SET balance = 0;
                          SELECT balance FROM accounts; -- Sees 0
ROLLBACK;
                          -- Transaction 2 read data that never existed
```

**Non-Repeatable Read**: Same query returns different results in same transaction
```sql
-- Transaction 1          -- Transaction 2
SELECT balance FROM accounts; -- Returns 100
                          UPDATE accounts SET balance = 50;
                          COMMIT;
SELECT balance FROM accounts; -- Returns 50 (different!)
```

**Phantom Read**: New rows appear in repeated query
```sql
-- Transaction 1          -- Transaction 2
SELECT COUNT(*) FROM orders; -- Returns 10
                          INSERT INTO orders VALUES (...);
                          COMMIT;
SELECT COUNT(*) FROM orders; -- Returns 11 (phantom row)
```

### Setting Isolation Level

```sql
-- Per transaction
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- or
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Session default
SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

## Prisma Transactions

### Batch Transactions

```typescript
// Multiple operations, auto-rollback on error
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { email: 'alice@example.com' } }),
  prisma.post.create({ data: { title: 'Hello', authorId: 'existing-id' } }),
]);
```

### Interactive Transactions

```typescript
// Full control with rollback
const result = await prisma.$transaction(async (tx) => {
  // 1. Check balance
  const account = await tx.account.findUnique({
    where: { id: fromAccountId },
  });
  
  if (!account || account.balance < amount) {
    throw new Error('Insufficient funds');
  }
  
  // 2. Deduct from source
  await tx.account.update({
    where: { id: fromAccountId },
    data: { balance: { decrement: amount } },
  });
  
  // 3. Add to destination
  await tx.account.update({
    where: { id: toAccountId },
    data: { balance: { increment: amount } },
  });
  
  // 4. Create transfer record
  return tx.transfer.create({
    data: { fromId: fromAccountId, toId: toAccountId, amount },
  });
});
```

### Transaction Options

```typescript
await prisma.$transaction(
  async (tx) => {
    // ... operations
  },
  {
    maxWait: 5000,  // Max time to wait for transaction slot (ms)
    timeout: 10000, // Max transaction duration (ms)
    isolationLevel: 'Serializable', // ReadCommitted | RepeatableRead | Serializable
  }
);
```

## Drizzle Transactions

### Basic Transaction

```typescript
await db.transaction(async (tx) => {
  const [user] = await tx.insert(users)
    .values({ email: 'alice@example.com' })
    .returning();
  
  await tx.insert(posts)
    .values({ title: 'Hello', authorId: user.id });
});
```

### Manual Rollback

```typescript
await db.transaction(async (tx) => {
  await tx.insert(users).values({ email: 'bob@example.com' });
  
  // Explicit rollback
  tx.rollback();
  
  // This code won't execute
  await tx.insert(posts).values({ title: 'Never created' });
});
```

### Nested Transactions (Savepoints)

```typescript
await db.transaction(async (tx1) => {
  await tx1.insert(users).values({ email: 'outer@example.com' });
  
  try {
    await tx1.transaction(async (tx2) => {
      await tx2.insert(posts).values({ title: 'Nested' });
      throw new Error('Rollback inner only');
    });
  } catch (e) {
    // Inner rolled back, outer continues
  }
  
  // This still executes
  await tx1.insert(logs).values({ message: 'Outer committed' });
});
```

### Isolation Level in Drizzle

```typescript
// PostgreSQL
import { sql } from 'drizzle-orm';

await db.transaction(async (tx) => {
  await tx.execute(sql`SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`);
  // ... operations
});
```

## Optimistic vs Pessimistic Locking

### Optimistic Locking (Version Field)

```typescript
// Schema
const posts = pgTable('posts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  version: integer('version').default(1).notNull(),
});

// Update with version check
async function updatePost(id: string, title: string, expectedVersion: number) {
  const result = await db.update(posts)
    .set({ 
      title, 
      version: sql`${posts.version} + 1` 
    })
    .where(
      and(
        eq(posts.id, id),
        eq(posts.version, expectedVersion)
      )
    )
    .returning();
  
  if (result.length === 0) {
    throw new Error('Concurrent modification detected');
  }
  
  return result[0];
}
```

### Pessimistic Locking (SELECT FOR UPDATE)

```typescript
// Prisma
const account = await prisma.$queryRaw<Account[]>`
  SELECT * FROM accounts WHERE id = ${id} FOR UPDATE
`;

// Drizzle
import { sql } from 'drizzle-orm';

await db.transaction(async (tx) => {
  const [account] = await tx.execute(sql`
    SELECT * FROM accounts WHERE id = ${id} FOR UPDATE
  `);
  
  // Account is locked until transaction commits
  await tx.update(accounts)
    .set({ balance: account.balance - 100 })
    .where(eq(accounts.id, id));
});
```

### Lock Types

```sql
-- Exclusive lock (blocks all)
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;

-- Share lock (blocks updates, allows reads)
SELECT * FROM accounts WHERE id = 1 FOR SHARE;

-- Skip locked rows
SELECT * FROM jobs WHERE status = 'pending' 
FOR UPDATE SKIP LOCKED 
LIMIT 1;

-- No wait (fail immediately if locked)
SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;
```

## Common Patterns

### Transfer Funds

```typescript
async function transferFunds(
  fromId: string, 
  toId: string, 
  amount: number
) {
  return prisma.$transaction(async (tx) => {
    // Lock accounts in consistent order to prevent deadlocks
    const [from, to] = fromId < toId 
      ? [fromId, toId] 
      : [toId, fromId];
    
    const accounts = await tx.$queryRaw<Account[]>`
      SELECT * FROM accounts 
      WHERE id IN (${from}, ${to}) 
      FOR UPDATE
    `;
    
    const fromAccount = accounts.find(a => a.id === fromId);
    const toAccount = accounts.find(a => a.id === toId);
    
    if (!fromAccount || !toAccount) {
      throw new Error('Account not found');
    }
    
    if (fromAccount.balance < amount) {
      throw new Error('Insufficient funds');
    }
    
    await tx.account.update({
      where: { id: fromId },
      data: { balance: { decrement: amount } },
    });
    
    await tx.account.update({
      where: { id: toId },
      data: { balance: { increment: amount } },
    });
    
    return { success: true };
  }, {
    isolationLevel: 'Serializable',
  });
}
```

### Idempotent Operations

```typescript
async function processPayment(paymentId: string, amount: number) {
  return prisma.$transaction(async (tx) => {
    // Check if already processed
    const existing = await tx.payment.findUnique({
      where: { id: paymentId },
    });
    
    if (existing) {
      return existing; // Already processed, return existing
    }
    
    // Process new payment
    const payment = await tx.payment.create({
      data: { id: paymentId, amount, status: 'completed' },
    });
    
    await tx.account.update({
      where: { id: 'merchant' },
      data: { balance: { increment: amount } },
    });
    
    return payment;
  });
}
```

### Retry on Serialization Failure

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Check if serialization/deadlock error
      const isRetryable = 
        error.code === '40001' || // Serialization failure
        error.code === '40P01';   // Deadlock
      
      if (!isRetryable || attempt === maxRetries) {
        throw error;
      }
      
      // Exponential backoff
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 100));
    }
  }
  
  throw lastError;
}

// Usage
const result = await withRetry(() => 
  transferFunds('acc1', 'acc2', 100)
);
```

## Best Practices

1. **Keep transactions short** - Long transactions block other operations
2. **Consistent lock ordering** - Prevent deadlocks by locking in same order
3. **Use appropriate isolation** - Don't over-serialize
4. **Handle failures** - Retry serialization failures with backoff
5. **Avoid user interaction** - Never wait for user input in transaction
6. **Prefer optimistic** - Use version fields when conflicts are rare
7. **Test concurrency** - Verify behavior under parallel load
8. **Monitor locks** - Watch for long-running transactions
