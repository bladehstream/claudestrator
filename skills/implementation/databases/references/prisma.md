# Prisma ORM Reference

Prisma is a next-generation TypeScript ORM providing type-safe database access, migrations, and schema management.

## Installation & Setup

```bash
# Install
npm install prisma @prisma/client
npm install -D prisma

# Initialize
npx prisma init

# Generate client after schema changes
npx prisma generate
```

## Schema Basics

### datasource & generator

```prisma
// prisma/schema.prisma
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["driverAdapters"]  // For edge runtimes
}

datasource db {
  provider = "postgresql"  // postgresql | mysql | sqlite | sqlserver | mongodb
  url      = env("DATABASE_URL")
}
```

### Model Definition

```prisma
model User {
  // Primary key
  id        String   @id @default(cuid())
  // or: id Int @id @default(autoincrement())
  // or: id String @id @default(uuid())
  
  // Fields with constraints
  email     String   @unique
  name      String?  // Optional (nullable)
  age       Int      @default(0)
  role      Role     @default(USER)
  
  // Relations
  posts     Post[]
  profile   Profile?
  
  // Timestamps
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  // Compound unique
  @@unique([email, name])
  
  // Indexes
  @@index([email])
  @@index([createdAt(sort: Desc)])
  
  // Table name override
  @@map("users")
}

enum Role {
  USER
  ADMIN
  MODERATOR
}
```

### Relations

```prisma
// One-to-One
model User {
  id      String   @id @default(cuid())
  profile Profile?
}

model Profile {
  id     String @id @default(cuid())
  bio    String
  user   User   @relation(fields: [userId], references: [id], onDelete: Cascade)
  userId String @unique
}

// One-to-Many
model User {
  id    String @id @default(cuid())
  posts Post[]
}

model Post {
  id       String @id @default(cuid())
  author   User   @relation(fields: [authorId], references: [id])
  authorId String
  
  @@index([authorId])
}

// Many-to-Many (implicit)
model Post {
  id         String     @id @default(cuid())
  categories Category[]
}

model Category {
  id    String @id @default(cuid())
  posts Post[]
}

// Many-to-Many (explicit - for extra fields)
model Post {
  id       String         @id @default(cuid())
  tags     PostTag[]
}

model Tag {
  id    String    @id @default(cuid())
  name  String    @unique
  posts PostTag[]
}

model PostTag {
  post      Post     @relation(fields: [postId], references: [id])
  postId    String
  tag       Tag      @relation(fields: [tagId], references: [id])
  tagId     String
  assignedAt DateTime @default(now())
  
  @@id([postId, tagId])
}
```

### Field Types

```prisma
model Example {
  // Scalars
  string    String
  int       Int
  bigInt    BigInt
  float     Float
  decimal   Decimal
  boolean   Boolean
  dateTime  DateTime
  json      Json
  bytes     Bytes
  
  // PostgreSQL-specific
  uuid      String   @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  text      String   @db.Text
  varchar   String   @db.VarChar(255)
  smallint  Int      @db.SmallInt
  real      Float    @db.Real
  jsonb     Json     @db.JsonB
  array     String[] @db.Text
}
```

## Client Usage

### Instantiation

```typescript
import { PrismaClient } from '@prisma/client';

// Singleton pattern (important for serverless)
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient({
  log: ['query', 'error', 'warn'],
});

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
```

### CRUD Operations

```typescript
// Create
const user = await prisma.user.create({
  data: {
    email: 'alice@example.com',
    name: 'Alice',
    posts: {
      create: [
        { title: 'First Post' },
        { title: 'Second Post' },
      ],
    },
  },
  include: { posts: true },
});

// Read
const user = await prisma.user.findUnique({
  where: { id: 'cuid' },
});

const user = await prisma.user.findUniqueOrThrow({
  where: { email: 'alice@example.com' },
});

const users = await prisma.user.findMany({
  where: {
    email: { contains: '@example.com' },
    posts: { some: { published: true } },
  },
  orderBy: { createdAt: 'desc' },
  take: 10,
  skip: 0,
});

// Update
const user = await prisma.user.update({
  where: { id: 'cuid' },
  data: { name: 'Alice Updated' },
});

// Upsert
const user = await prisma.user.upsert({
  where: { email: 'alice@example.com' },
  update: { name: 'Alice' },
  create: { email: 'alice@example.com', name: 'Alice' },
});

// Delete
await prisma.user.delete({ where: { id: 'cuid' } });

// Delete many
const { count } = await prisma.user.deleteMany({
  where: { createdAt: { lt: new Date('2024-01-01') } },
});
```

### Filtering

```typescript
const users = await prisma.user.findMany({
  where: {
    // Equality
    email: 'alice@example.com',
    
    // Comparison
    age: { gt: 18, lte: 65 },
    
    // String filters
    name: {
      contains: 'ali',
      startsWith: 'A',
      endsWith: 'e',
      mode: 'insensitive',
    },
    
    // In array
    role: { in: ['USER', 'ADMIN'] },
    
    // NOT
    NOT: { role: 'ADMIN' },
    
    // OR
    OR: [
      { email: { contains: '@gmail.com' } },
      { email: { contains: '@outlook.com' } },
    ],
    
    // Relation filters
    posts: {
      some: { published: true },  // At least one
      every: { published: true }, // All must match
      none: { published: false }, // None must match
    },
    
    // Null checks
    profile: { isNot: null },
  },
});
```

### Select & Include

```typescript
// Select specific fields
const user = await prisma.user.findUnique({
  where: { id },
  select: {
    id: true,
    email: true,
    posts: {
      select: { title: true },
      where: { published: true },
      take: 5,
    },
  },
});

// Include relations
const user = await prisma.user.findUnique({
  where: { id },
  include: {
    posts: {
      where: { published: true },
      orderBy: { createdAt: 'desc' },
      include: { tags: true },
    },
    profile: true,
  },
});
```

### Aggregations

```typescript
// Count
const count = await prisma.user.count({
  where: { role: 'USER' },
});

// Aggregate
const result = await prisma.post.aggregate({
  _count: { _all: true },
  _avg: { views: true },
  _max: { views: true },
  _min: { views: true },
  _sum: { views: true },
  where: { published: true },
});

// Group by
const groups = await prisma.user.groupBy({
  by: ['role'],
  _count: { _all: true },
  having: {
    _count: { _all: { gt: 10 } },
  },
});
```

### Transactions

```typescript
// Sequential operations (auto-rollback on error)
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { email: 'bob@example.com' } }),
  prisma.post.create({ data: { title: 'Hello', authorId: 'existing-id' } }),
]);

// Interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const user = await tx.user.findUnique({ where: { id } });
  if (!user) throw new Error('User not found');
  
  const balance = await tx.account.findUnique({ where: { userId: id } });
  if (balance.amount < 100) throw new Error('Insufficient funds');
  
  await tx.account.update({
    where: { userId: id },
    data: { amount: { decrement: 100 } },
  });
  
  return tx.transfer.create({ data: { amount: 100, fromId: id } });
}, {
  maxWait: 5000,      // Max wait for transaction slot
  timeout: 10000,     // Max transaction duration
  isolationLevel: 'Serializable',
});
```

### Raw Queries

```typescript
// Raw query
const users = await prisma.$queryRaw<User[]>`
  SELECT * FROM users WHERE email = ${email}
`;

// Raw execute
const count = await prisma.$executeRaw`
  UPDATE users SET name = ${name} WHERE id = ${id}
`;

// TypedSQL (v5.9+)
import { getUserById } from '@prisma/client/sql';

const user = await prisma.$queryRawTyped(getUserById(userId));
```

## Migrations

```bash
# Development: Create and apply migration
npx prisma migrate dev --name add_user_table

# Production: Apply pending migrations
npx prisma migrate deploy

# Reset database (dangerous!)
npx prisma migrate reset

# Check migration status
npx prisma migrate status

# Create migration without applying
npx prisma migrate dev --create-only
```

### Migration Workflow

```bash
# 1. Modify schema.prisma
# 2. Generate migration
npx prisma migrate dev --name descriptive_name

# 3. Review generated SQL in prisma/migrations/
# 4. Commit migration files to version control
# 5. Deploy to production
npx prisma migrate deploy
```

## Middleware

```typescript
prisma.$use(async (params, next) => {
  const before = Date.now();
  const result = await next(params);
  const after = Date.now();
  
  console.log(`${params.model}.${params.action} took ${after - before}ms`);
  
  return result;
});

// Soft delete middleware
prisma.$use(async (params, next) => {
  if (params.model === 'User') {
    if (params.action === 'delete') {
      params.action = 'update';
      params.args.data = { deletedAt: new Date() };
    }
    if (params.action === 'deleteMany') {
      params.action = 'updateMany';
      params.args.data = { deletedAt: new Date() };
    }
  }
  return next(params);
});
```

## Edge Runtime / Serverless

```typescript
// Using Prisma Accelerate (recommended)
import { PrismaClient } from '@prisma/client/edge';
import { withAccelerate } from '@prisma/extension-accelerate';

const prisma = new PrismaClient().$extends(withAccelerate());

// With caching
const users = await prisma.user.findMany({
  cacheStrategy: {
    ttl: 60,           // Cache for 60 seconds
    swr: 120,          // Stale-while-revalidate
  },
});
```

```prisma
// Enable edge preview
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["driverAdapters"]
}
```

## Best Practices

1. **Use singleton pattern** - Prevent connection exhaustion in serverless
2. **Always include relations selectively** - Avoid over-fetching
3. **Use indexes** - Add `@@index` for frequently queried columns
4. **Transaction for related operations** - Ensure data consistency
5. **Soft deletes via middleware** - Keep audit trail
6. **Type-safe raw queries** - Use `$queryRawTyped` when possible
7. **Connection pooling** - Use Prisma Accelerate or PgBouncer for serverless
8. **Review migrations** - Always check generated SQL before deploying
