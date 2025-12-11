# Common Database Patterns Reference

Reusable patterns for soft deletes, timestamps, audit trails, and more.

## Soft Deletes

### Schema Pattern

```typescript
// Prisma
model User {
  id        String    @id @default(cuid())
  email     String    @unique
  name      String?
  deletedAt DateTime?
  
  @@index([deletedAt])
}

// Drizzle
export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  deletedAt: timestamp('deleted_at'),
}, (table) => [
  index('users_deleted_at_idx').on(table.deletedAt),
]);
```

### Prisma Middleware

```typescript
prisma.$use(async (params, next) => {
  // Intercept delete operations
  if (params.action === 'delete') {
    params.action = 'update';
    params.args.data = { deletedAt: new Date() };
  }
  
  if (params.action === 'deleteMany') {
    params.action = 'updateMany';
    if (params.args.data) {
      params.args.data.deletedAt = new Date();
    } else {
      params.args.data = { deletedAt: new Date() };
    }
  }
  
  // Filter out soft-deleted records
  if (params.action === 'findUnique' || params.action === 'findFirst') {
    params.action = 'findFirst';
    params.args.where = { ...params.args.where, deletedAt: null };
  }
  
  if (params.action === 'findMany') {
    if (!params.args) params.args = {};
    if (!params.args.where) params.args.where = {};
    params.args.where.deletedAt = null;
  }
  
  return next(params);
});

// Include deleted records when needed
const allUsers = await prisma.user.findMany({
  where: { deletedAt: { not: null } },
});

// Permanently delete
await prisma.user.delete({ where: { id } });
```

### Drizzle Helper Functions

```typescript
// Soft delete
export async function softDelete(id: string) {
  return db.update(users)
    .set({ deletedAt: new Date() })
    .where(eq(users.id, id));
}

// Find non-deleted
export async function findActiveUsers() {
  return db.select()
    .from(users)
    .where(isNull(users.deletedAt));
}

// Restore
export async function restore(id: string) {
  return db.update(users)
    .set({ deletedAt: null })
    .where(eq(users.id, id));
}

// Permanent delete
export async function hardDelete(id: string) {
  return db.delete(users).where(eq(users.id, id));
}
```

## Timestamps

### Automatic Timestamps

```typescript
// Prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

// Drizzle helper
export const timestamps = {
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at')
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
};

export const posts = pgTable('posts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  ...timestamps,
});
```

### Full Timestamp Set

```typescript
// For audit-heavy applications
export const fullTimestamps = {
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull().$onUpdate(() => new Date()),
  deletedAt: timestamp('deleted_at'),
  createdBy: text('created_by'),
  updatedBy: text('updated_by'),
  deletedBy: text('deleted_by'),
};
```

## Audit Trail

### Separate Audit Table

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id TEXT NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_data JSONB,
  new_data JSONB,
  changed_by TEXT,
  changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at);
```

### TypeScript Audit Service

```typescript
interface AuditEntry {
  tableName: string;
  recordId: string;
  action: 'INSERT' | 'UPDATE' | 'DELETE';
  oldData?: Record<string, unknown>;
  newData?: Record<string, unknown>;
  changedBy?: string;
}

async function createAuditEntry(entry: AuditEntry) {
  return db.insert(auditLog).values({
    tableName: entry.tableName,
    recordId: entry.recordId,
    action: entry.action,
    oldData: entry.oldData,
    newData: entry.newData,
    changedBy: entry.changedBy,
    changedAt: new Date(),
  });
}

// Usage in service layer
async function updateUser(id: string, data: Partial<User>, userId: string) {
  const oldUser = await db.query.users.findFirst({
    where: eq(users.id, id),
  });
  
  const [updatedUser] = await db.update(users)
    .set(data)
    .where(eq(users.id, id))
    .returning();
  
  await createAuditEntry({
    tableName: 'users',
    recordId: id,
    action: 'UPDATE',
    oldData: oldUser,
    newData: updatedUser,
    changedBy: userId,
  });
  
  return updatedUser;
}
```

### PostgreSQL Trigger-Based Audit

```sql
-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, record_id, action, new_data, changed_at)
    VALUES (TG_TABLE_NAME, NEW.id::text, 'INSERT', row_to_json(NEW), NOW());
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_at)
    VALUES (TG_TABLE_NAME, NEW.id::text, 'UPDATE', row_to_json(OLD), row_to_json(NEW), NOW());
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_data, changed_at)
    VALUES (TG_TABLE_NAME, OLD.id::text, 'DELETE', row_to_json(OLD), NOW());
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER users_audit
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

## Multi-Tenancy

### Column-Based (Shared Schema)

```typescript
// Drizzle
export const tenants = pgTable('tenants', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
});

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  tenantId: text('tenant_id').notNull().references(() => tenants.id),
  email: text('email').notNull(),
  
  // Unique per tenant
  @@unique([tenantId, email])
}, (table) => [
  index('users_tenant_idx').on(table.tenantId),
]);

// Always filter by tenant
function getUsersForTenant(tenantId: string) {
  return db.select()
    .from(users)
    .where(eq(users.tenantId, tenantId));
}
```

### Row-Level Security (PostgreSQL)

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation ON users
  USING (tenant_id = current_setting('app.current_tenant')::text);

-- Set tenant for session
SET app.current_tenant = 'tenant-123';

-- Now all queries automatically filter by tenant
SELECT * FROM users;  -- Only returns tenant-123 users
```

## Slug Generation

```typescript
// Unique slug with fallback
export async function generateSlug(title: string, table: string): Promise<string> {
  const baseSlug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  
  let slug = baseSlug;
  let counter = 1;
  
  while (true) {
    const existing = await db.select({ id: posts.id })
      .from(posts)
      .where(eq(posts.slug, slug))
      .limit(1);
    
    if (existing.length === 0) break;
    
    slug = `${baseSlug}-${counter}`;
    counter++;
  }
  
  return slug;
}

// Usage
const slug = await generateSlug('My Blog Post');
// Returns: 'my-blog-post' or 'my-blog-post-1' if exists
```

## Pagination Patterns

### Offset Pagination

```typescript
async function getUsers(page: number, pageSize: number) {
  const offset = (page - 1) * pageSize;
  
  const [users, countResult] = await Promise.all([
    db.select()
      .from(users)
      .orderBy(desc(users.createdAt))
      .limit(pageSize)
      .offset(offset),
    db.select({ count: sql<number>`count(*)` })
      .from(users),
  ]);
  
  const total = countResult[0].count;
  
  return {
    data: users,
    pagination: {
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize),
    },
  };
}
```

### Cursor Pagination

```typescript
async function getUsers(cursor?: string, limit = 20) {
  const query = db.select()
    .from(users)
    .orderBy(desc(users.createdAt), desc(users.id))
    .limit(limit + 1);  // Fetch one extra to check hasMore
  
  if (cursor) {
    const [cursorDate, cursorId] = decodeCursor(cursor);
    query.where(
      or(
        lt(users.createdAt, cursorDate),
        and(
          eq(users.createdAt, cursorDate),
          lt(users.id, cursorId),
        ),
      ),
    );
  }
  
  const results = await query;
  const hasMore = results.length > limit;
  const data = hasMore ? results.slice(0, -1) : results;
  
  const nextCursor = hasMore 
    ? encodeCursor(data[data.length - 1].createdAt, data[data.length - 1].id)
    : null;
  
  return {
    data,
    nextCursor,
    hasMore,
  };
}

function encodeCursor(date: Date, id: string): string {
  return Buffer.from(`${date.toISOString()}:${id}`).toString('base64');
}

function decodeCursor(cursor: string): [Date, string] {
  const decoded = Buffer.from(cursor, 'base64').toString();
  const [date, id] = decoded.split(':');
  return [new Date(date), id];
}
```

## Optimistic Locking

```typescript
// Add version column
export const documents = pgTable('documents', {
  id: text('id').primaryKey(),
  content: text('content').notNull(),
  version: integer('version').default(1).notNull(),
  ...timestamps,
});

// Update with version check
async function updateDocument(
  id: string, 
  content: string, 
  expectedVersion: number
) {
  const result = await db.update(documents)
    .set({ 
      content, 
      version: sql`${documents.version} + 1`,
    })
    .where(
      and(
        eq(documents.id, id),
        eq(documents.version, expectedVersion),
      ),
    )
    .returning();
  
  if (result.length === 0) {
    throw new Error('Document was modified by another user');
  }
  
  return result[0];
}
```

## Tree Structures (Adjacency List)

```typescript
// Schema
export const categories = pgTable('categories', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  parentId: text('parent_id').references(() => categories.id),
}, (table) => [
  index('categories_parent_idx').on(table.parentId),
]);

// Get children
async function getChildren(parentId: string | null) {
  return db.select()
    .from(categories)
    .where(parentId ? eq(categories.parentId, parentId) : isNull(categories.parentId));
}

// Get full tree (recursive CTE)
async function getTree() {
  return db.execute(sql`
    WITH RECURSIVE category_tree AS (
      SELECT id, name, parent_id, 0 as depth, ARRAY[id] as path
      FROM categories
      WHERE parent_id IS NULL
      
      UNION ALL
      
      SELECT c.id, c.name, c.parent_id, ct.depth + 1, ct.path || c.id
      FROM categories c
      JOIN category_tree ct ON c.parent_id = ct.id
    )
    SELECT * FROM category_tree ORDER BY path
  `);
}
```

## Best Practices Summary

1. **Soft deletes** - Use for recoverable data, with index on `deletedAt`
2. **Timestamps** - Always include `createdAt`/`updatedAt`
3. **Audit trails** - Separate table for compliance-heavy apps
4. **Multi-tenancy** - Index tenant column, consider RLS
5. **Pagination** - Cursor for large datasets, offset for known small sets
6. **Optimistic locking** - Version field for concurrent updates
7. **Slugs** - Generate from title with uniqueness check
