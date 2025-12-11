# Connection Pooling Reference

Managing database connections efficiently for serverless, edge, and traditional deployments.

## Why Connection Pooling?

### The Problem

PostgreSQL creates a new process for each connection:
- ~10MB memory per connection
- Connection establishment overhead (~100-300ms)
- `max_connections` limit (typically 100-500)

### Serverless Challenge

```
Without pooling:
Request 1 → New connection → Query → Close
Request 2 → New connection → Query → Close  
Request 3 → New connection → Query → Close
(Each request pays connection cost)

With pooling:
Request 1 ─┐
Request 2 ─┼→ Pool → Reused connections → Database
Request 3 ─┘
(Connections reused, minimal overhead)
```

## PgBouncer

PgBouncer is the most widely used PostgreSQL connection pooler.

### Pool Modes

| Mode | Connection Lifetime | Use Case |
|------|-------------------|----------|
| **Session** | Entire client session | Admin tasks, long transactions |
| **Transaction** | Single transaction | Serverless, high concurrency |
| **Statement** | Single statement | Rare, limited compatibility |

### Configuration

```ini
# pgbouncer.ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
max_client_conn = 1000

# Timeouts
server_idle_timeout = 600
client_idle_timeout = 0
```

### Connection Strings

```bash
# Direct connection
postgresql://user:pass@host:5432/dbname

# Via PgBouncer
postgresql://user:pass@host:6432/dbname?pgbouncer=true
```

### Transaction Mode Limitations

In transaction mode, these features are unavailable:
- SET/RESET commands (session variables)
- LISTEN/NOTIFY
- Prepared statements (unless explicitly supported)
- Advisory locks held across transactions
- Cursors (WITH HOLD)

## Managed Pooling Services

### Supabase

```typescript
// Supavisor (built-in pooler)
// Session mode (port 5432) - direct connection
const sessionUrl = 'postgresql://user:pass@db.project.supabase.co:5432/postgres';

// Transaction mode (port 6543) - pooled
const pooledUrl = 'postgresql://user:pass@db.project.supabase.co:6543/postgres?pgbouncer=true';
```

### Neon

```typescript
// Pooled connection (default)
const pooledUrl = 'postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require';

// With connection pooling explicitly
// Neon handles this automatically
```

### PlanetScale (PostgreSQL)

```typescript
// Direct (port 5432)
const directUrl = 'postgresql://user:pass@host:5432/dbname';

// Via PgBouncer (port 6432)
const pooledUrl = 'postgresql://user:pass@host:6432/dbname';
```

## Prisma Connection Management

### Basic Pooling

```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
});
```

### Connection Pool Settings

```env
# In DATABASE_URL
DATABASE_URL="postgresql://user:pass@host:5432/db?connection_limit=5&pool_timeout=10"
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `connection_limit` | Max connections in pool | Based on CPUs |
| `pool_timeout` | Wait time for connection (seconds) | 10 |

### Serverless with PgBouncer

```env
# Use PgBouncer port and flags
DATABASE_URL="postgresql://user:pass@host:6432/db?pgbouncer=true&connection_limit=1"
```

### Prisma Accelerate (Recommended for Serverless)

```typescript
import { PrismaClient } from '@prisma/client/edge';
import { withAccelerate } from '@prisma/extension-accelerate';

const prisma = new PrismaClient().$extends(withAccelerate());

// With caching
const users = await prisma.user.findMany({
  cacheStrategy: {
    ttl: 60,        // Cache for 60 seconds
    swr: 120,       // Stale-while-revalidate for 120 seconds
  },
});
```

```env
# Use Accelerate connection string
DATABASE_URL="prisma://accelerate.prisma-data.net/?api_key=YOUR_API_KEY"
```

## Drizzle Connection Management

### PostgreSQL with postgres.js

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

// Connection pool handled by postgres.js
const client = postgres(process.env.DATABASE_URL!, {
  max: 10,              // Max connections
  idle_timeout: 20,     // Seconds before idle connection closed
  connect_timeout: 10,  // Connection timeout
});

export const db = drizzle(client);
```

### Node-postgres Pool

```typescript
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const db = drizzle(pool);
```

## Serverless Singleton Pattern

### Problem

```typescript
// ❌ Creates new client on every request
export async function handler() {
  const prisma = new PrismaClient();
  // ... query
  await prisma.$disconnect();
}
```

### Solution

```typescript
// lib/prisma.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// Usage
import { prisma } from '@/lib/prisma';

export async function handler() {
  return prisma.user.findMany();
}
```

## Edge Runtime Considerations

### Cloudflare Workers

```typescript
// Use Hyperdrive for connection pooling
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

export default {
  async fetch(request: Request, env: Env) {
    // Hyperdrive provides pooled connection
    const client = postgres(env.HYPERDRIVE.connectionString);
    const db = drizzle(client);
    
    const users = await db.select().from(users);
    return Response.json(users);
  }
};
```

### Vercel Edge

```typescript
// Use @vercel/postgres or Neon serverless driver
import { sql } from '@vercel/postgres';

export const config = { runtime: 'edge' };

export default async function handler() {
  const { rows } = await sql`SELECT * FROM users`;
  return Response.json(rows);
}
```

## Monitoring Connections

### PostgreSQL Queries

```sql
-- Current connections
SELECT count(*) FROM pg_stat_activity;

-- Connections by state
SELECT state, count(*) 
FROM pg_stat_activity 
GROUP BY state;

-- Connections by application
SELECT application_name, count(*) 
FROM pg_stat_activity 
GROUP BY application_name;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '5 minutes';
```

### PgBouncer Stats

```sql
-- Connect to pgbouncer admin
psql -p 6432 -U pgbouncer pgbouncer

-- Show pools
SHOW POOLS;

-- Show clients
SHOW CLIENTS;

-- Show servers
SHOW SERVERS;

-- Show stats
SHOW STATS;
```

## Best Practices

1. **Use transaction mode** - For serverless/high concurrency
2. **Singleton pattern** - Reuse client instance
3. **Set connection limits** - Match pool size to workload
4. **Monitor actively** - Track connection usage
5. **Use managed poolers** - Prisma Accelerate, Supavisor, Hyperdrive
6. **Timeout appropriately** - Set reasonable connection timeouts
7. **Close connections** - In long-running scripts, disconnect when done
8. **Test under load** - Verify pooling works at scale
