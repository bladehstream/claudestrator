# Role-Based Access Control (RBAC)

## Overview

RBAC restricts system access based on user roles. Users are assigned roles, and roles are granted permissions. This simplifies permission management compared to assigning permissions directly to users.

## Authorization Models

| Model | Description | Use When |
|-------|-------------|----------|
| **RBAC** | Users → Roles → Permissions | Simple hierarchical access |
| **ABAC** | Attribute-based (user, resource, context) | Complex conditional access |
| **ReBAC** | Relationship-based (user relations to resource) | Social/collaborative apps |

## Basic RBAC Implementation

### Type Definitions

```typescript
// Define roles as const for type safety
const ROLES = ['admin', 'manager', 'user', 'guest'] as const;
type Role = typeof ROLES[number];

// Define permissions
const PERMISSIONS = [
  'create',
  'read',
  'update',
  'delete',
  'manage',
] as const;
type Permission = typeof PERMISSIONS[number];

// Define resources
const RESOURCES = [
  'users',
  'posts',
  'comments',
  'settings',
  'analytics',
] as const;
type Resource = typeof RESOURCES[number];

// Permission map type
type PermissionMap = {
  [R in Role]: {
    [Res in Resource]?: Permission[];
  };
};
```

### Permission Matrix

```typescript
const permissions: PermissionMap = {
  admin: {
    users: ['create', 'read', 'update', 'delete', 'manage'],
    posts: ['create', 'read', 'update', 'delete', 'manage'],
    comments: ['create', 'read', 'update', 'delete', 'manage'],
    settings: ['read', 'update', 'manage'],
    analytics: ['read'],
  },
  manager: {
    users: ['read'],
    posts: ['create', 'read', 'update', 'delete'],
    comments: ['create', 'read', 'update', 'delete'],
    settings: ['read'],
    analytics: ['read'],
  },
  user: {
    posts: ['create', 'read', 'update'],  // Own posts only
    comments: ['create', 'read', 'update', 'delete'],  // Own comments only
  },
  guest: {
    posts: ['read'],
    comments: ['read'],
  },
};

// Check permission
function hasPermission(
  role: Role,
  resource: Resource,
  permission: Permission
): boolean {
  return permissions[role]?.[resource]?.includes(permission) ?? false;
}

// Check multiple permissions (any)
function hasAnyPermission(
  role: Role,
  resource: Resource,
  requiredPermissions: Permission[]
): boolean {
  return requiredPermissions.some((p) => hasPermission(role, resource, p));
}

// Check multiple permissions (all)
function hasAllPermissions(
  role: Role,
  resource: Resource,
  requiredPermissions: Permission[]
): boolean {
  return requiredPermissions.every((p) => hasPermission(role, resource, p));
}
```

## Hierarchical RBAC

```typescript
// Role hierarchy: admin > manager > user > guest
const roleHierarchy: Record<Role, Role[]> = {
  admin: ['admin', 'manager', 'user', 'guest'],
  manager: ['manager', 'user', 'guest'],
  user: ['user', 'guest'],
  guest: ['guest'],
};

// Check if role has access to target role level
function hasRoleLevel(userRole: Role, requiredRole: Role): boolean {
  return roleHierarchy[userRole]?.includes(requiredRole) ?? false;
}

// Get all permissions for role (including inherited)
function getAllPermissions(role: Role): Map<Resource, Set<Permission>> {
  const result = new Map<Resource, Set<Permission>>();
  
  for (const inheritedRole of roleHierarchy[role] || []) {
    for (const [resource, perms] of Object.entries(permissions[inheritedRole] || {})) {
      if (!result.has(resource as Resource)) {
        result.set(resource as Resource, new Set());
      }
      perms?.forEach((p) => result.get(resource as Resource)!.add(p));
    }
  }
  
  return result;
}
```

## Hono Middleware Implementation

```typescript
import { Hono, Context, Next } from 'hono';
import { HTTPException } from 'hono/http-exception';

interface User {
  id: string;
  email: string;
  role: Role;
}

// Middleware to require specific role
function requireRole(...allowedRoles: Role[]) {
  return async (c: Context, next: Next) => {
    const user = c.get('user') as User | undefined;

    if (!user) {
      throw new HTTPException(401, { message: 'Unauthorized' });
    }

    // Check if user has any of the allowed roles
    const hasRole = allowedRoles.some((role) => 
      hasRoleLevel(user.role, role)
    );

    if (!hasRole) {
      throw new HTTPException(403, { message: 'Forbidden' });
    }

    await next();
  };
}

// Middleware to require specific permission
function requirePermission(resource: Resource, permission: Permission) {
  return async (c: Context, next: Next) => {
    const user = c.get('user') as User | undefined;

    if (!user) {
      throw new HTTPException(401, { message: 'Unauthorized' });
    }

    if (!hasPermission(user.role, resource, permission)) {
      throw new HTTPException(403, { 
        message: `Missing permission: ${permission} on ${resource}` 
      });
    }

    await next();
  };
}

// Usage
const app = new Hono();

// Admin only route
app.get('/admin/users', requireRole('admin'), async (c) => {
  const users = await db.users.findMany();
  return c.json(users);
});

// Manager or admin route
app.get('/reports', requireRole('manager', 'admin'), async (c) => {
  const reports = await db.reports.findMany();
  return c.json(reports);
});

// Permission-based route
app.post('/posts', requirePermission('posts', 'create'), async (c) => {
  const data = await c.req.json();
  const post = await db.posts.create({ data });
  return c.json(post);
});

app.delete(
  '/posts/:id',
  requirePermission('posts', 'delete'),
  async (c) => {
    const id = c.req.param('id');
    await db.posts.delete({ where: { id } });
    return c.json({ deleted: true });
  }
);
```

## Resource Ownership Check

```typescript
// For user-owned resources, check ownership
interface OwnedResource {
  userId: string;
}

async function canAccessResource(
  user: User,
  resource: Resource,
  permission: Permission,
  resourceData?: OwnedResource
): Promise<boolean> {
  // Admin can access all
  if (user.role === 'admin') {
    return hasPermission(user.role, resource, permission);
  }

  // Check base permission
  if (!hasPermission(user.role, resource, permission)) {
    return false;
  }

  // For non-admin, check ownership if resource has owner
  if (resourceData && resourceData.userId !== user.id) {
    // Only admin can access others' resources
    return false;
  }

  return true;
}

// Middleware with ownership check
function requireOwnership(
  resource: Resource,
  permission: Permission,
  getResource: (c: Context) => Promise<OwnedResource | null>
) {
  return async (c: Context, next: Next) => {
    const user = c.get('user') as User;
    const resourceData = await getResource(c);

    if (!resourceData) {
      throw new HTTPException(404, { message: 'Resource not found' });
    }

    const canAccess = await canAccessResource(
      user,
      resource,
      permission,
      resourceData
    );

    if (!canAccess) {
      throw new HTTPException(403, { message: 'Forbidden' });
    }

    c.set('resource', resourceData);
    await next();
  };
}

// Usage
app.put(
  '/posts/:id',
  requireOwnership('posts', 'update', async (c) => {
    const id = c.req.param('id');
    return db.posts.findUnique({ where: { id } });
  }),
  async (c) => {
    const post = c.get('resource');
    const data = await c.req.json();
    const updated = await db.posts.update({
      where: { id: post.id },
      data,
    });
    return c.json(updated);
  }
);
```

## Database Schema

```sql
-- Roles table (for dynamic roles)
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Permissions table
CREATE TABLE permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "posts:create"
  resource VARCHAR(50) NOT NULL,
  action VARCHAR(50) NOT NULL,
  description TEXT
);

-- Role permissions (many-to-many)
CREATE TABLE role_permissions (
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- User roles (many-to-many for multiple roles)
CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMP DEFAULT NOW(),
  assigned_by UUID REFERENCES users(id),
  PRIMARY KEY (user_id, role_id)
);

-- Indexes
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
```

## Dynamic RBAC with Database

```typescript
// Load permissions from database
async function loadPermissions(db: Database): Promise<PermissionMap> {
  const roles = await db.roles.findMany({
    include: {
      rolePermissions: {
        include: { permission: true },
      },
    },
  });

  const permissionMap: Record<string, Record<string, string[]>> = {};

  for (const role of roles) {
    permissionMap[role.name] = {};
    
    for (const rp of role.rolePermissions) {
      const { resource, action } = rp.permission;
      if (!permissionMap[role.name][resource]) {
        permissionMap[role.name][resource] = [];
      }
      permissionMap[role.name][resource].push(action);
    }
  }

  return permissionMap as PermissionMap;
}

// Cache permissions
let cachedPermissions: PermissionMap | null = null;
let cacheExpiry = 0;

async function getPermissions(db: Database): Promise<PermissionMap> {
  const now = Date.now();
  
  if (!cachedPermissions || now > cacheExpiry) {
    cachedPermissions = await loadPermissions(db);
    cacheExpiry = now + 5 * 60 * 1000;  // Cache for 5 minutes
  }
  
  return cachedPermissions;
}

// Invalidate cache on role/permission changes
function invalidatePermissionCache(): void {
  cachedPermissions = null;
  cacheExpiry = 0;
}
```

## React Native Permission Hook

```typescript
import { useAuth } from './AuthContext';

export function usePermission() {
  const { user } = useAuth();

  const can = (resource: Resource, permission: Permission): boolean => {
    if (!user) return false;
    return hasPermission(user.role, resource, permission);
  };

  const canAny = (resource: Resource, permissions: Permission[]): boolean => {
    if (!user) return false;
    return hasAnyPermission(user.role, resource, permissions);
  };

  const isRole = (...roles: Role[]): boolean => {
    if (!user) return false;
    return roles.some((role) => hasRoleLevel(user.role, role));
  };

  return { can, canAny, isRole };
}

// Usage in component
function PostActions({ post }) {
  const { can, isRole } = usePermission();

  return (
    <View>
      {can('posts', 'update') && (
        <Button title="Edit" onPress={() => editPost(post.id)} />
      )}
      {can('posts', 'delete') && (
        <Button title="Delete" onPress={() => deletePost(post.id)} />
      )}
      {isRole('admin', 'manager') && (
        <Button title="Feature" onPress={() => featurePost(post.id)} />
      )}
    </View>
  );
}
```

## Best Practices

1. **Principle of least privilege**: Start with minimal permissions
2. **Role granularity**: Balance between too few and too many roles
3. **Audit logging**: Log all permission checks and changes
4. **Cache permissions**: Avoid database lookups on every request
5. **Separate concerns**: Keep authorization logic separate from business logic
6. **Test thoroughly**: Unit test permission logic
7. **Document roles**: Maintain clear documentation of role responsibilities
