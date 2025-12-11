# GraphQL API Design

## Schema Design Fundamentals

### Type Definitions

```graphql
# Object types
type User {
  id: ID!
  email: String!
  name: String
  role: UserRole!
  posts: [Post!]!
  createdAt: DateTime!
}

# Enums
enum UserRole {
  USER
  ADMIN
  MODERATOR
}

# Input types (for mutations)
input CreateUserInput {
  email: String!
  name: String
  role: UserRole = USER
}

input UpdateUserInput {
  name: String
  role: UserRole
}

# Custom scalars
scalar DateTime
scalar JSON
```

### Naming Conventions

- **Types**: PascalCase (`User`, `BlogPost`)
- **Fields**: camelCase (`firstName`, `createdAt`)
- **Enums**: SCREAMING_SNAKE_CASE (`USER_ROLE`, `ORDER_STATUS`)
- **Input types**: PascalCase with `Input` suffix (`CreateUserInput`)
- **Mutations**: verb + noun (`createUser`, `updatePost`, `deleteComment`)

### Queries

```graphql
type Query {
  # Single resource
  user(id: ID!): User
  
  # Collection with pagination and filtering
  users(
    first: Int
    after: String
    filter: UserFilter
    orderBy: UserOrderBy
  ): UserConnection!
  
  # Search
  searchUsers(query: String!, limit: Int = 10): [User!]!
}

input UserFilter {
  role: UserRole
  createdAfter: DateTime
  createdBefore: DateTime
}

input UserOrderBy {
  field: UserOrderField!
  direction: OrderDirection!
}

enum UserOrderField {
  CREATED_AT
  NAME
  EMAIL
}

enum OrderDirection {
  ASC
  DESC
}
```

### Mutations

```graphql
type Mutation {
  # Create - returns created resource
  createUser(input: CreateUserInput!): CreateUserPayload!
  
  # Update - returns updated resource
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  
  # Delete - returns success/deleted id
  deleteUser(id: ID!): DeleteUserPayload!
}

# Payload types for mutations
type CreateUserPayload {
  user: User
  errors: [Error!]
}

type UpdateUserPayload {
  user: User
  errors: [Error!]
}

type DeleteUserPayload {
  deletedId: ID
  success: Boolean!
  errors: [Error!]
}

type Error {
  field: String
  message: String!
  code: String!
}
```

### Relay-Style Pagination (Connections)

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Usage
type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
  ): UserConnection!
}
```

## Resolver Implementation

### Basic Resolver Structure

```typescript
const resolvers = {
  Query: {
    user: async (_, { id }, context) => {
      return context.dataSources.users.findById(id);
    },
    
    users: async (_, { first, after, filter }, context) => {
      return context.dataSources.users.findMany({
        limit: first,
        cursor: after,
        filter,
      });
    },
  },
  
  Mutation: {
    createUser: async (_, { input }, context) => {
      try {
        const user = await context.dataSources.users.create(input);
        return { user, errors: null };
      } catch (error) {
        return {
          user: null,
          errors: [{ message: error.message, code: 'CREATE_FAILED' }],
        };
      }
    },
  },
  
  // Field resolvers
  User: {
    posts: async (user, _, context) => {
      return context.dataSources.posts.findByUserId(user.id);
    },
  },
};
```

### Context Setup

```typescript
interface Context {
  user: AuthenticatedUser | null;
  dataSources: {
    users: UserDataSource;
    posts: PostDataSource;
  };
}

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }) => ({
    user: await authenticateRequest(req),
    dataSources: {
      users: new UserDataSource(),
      posts: new PostDataSource(),
    },
  }),
});
```

## N+1 Problem & DataLoader

### The Problem

```graphql
# This query
query {
  users(first: 10) {
    edges {
      node {
        id
        posts { id title }  # N additional queries!
      }
    }
  }
}
```

### Solution: DataLoader

```typescript
import DataLoader from 'dataloader';

// Create loader that batches requests
const postsByUserIdLoader = new DataLoader(async (userIds: string[]) => {
  const posts = await db.posts.findMany({
    where: { userId: { in: userIds } },
  });
  
  // Return in same order as input
  const postsByUser = new Map();
  posts.forEach(post => {
    if (!postsByUser.has(post.userId)) {
      postsByUser.set(post.userId, []);
    }
    postsByUser.get(post.userId).push(post);
  });
  
  return userIds.map(id => postsByUser.get(id) || []);
});

// Use in resolver
const resolvers = {
  User: {
    posts: (user, _, context) => {
      return context.loaders.postsByUserId.load(user.id);
    },
  },
};
```

## Error Handling

### GraphQL Error Format

```json
{
  "data": null,
  "errors": [
    {
      "message": "User not found",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["user"],
      "extensions": {
        "code": "NOT_FOUND",
        "argumentName": "id"
      }
    }
  ]
}
```

### Custom Error Classes

```typescript
import { GraphQLError } from 'graphql';

export class NotFoundError extends GraphQLError {
  constructor(resource: string, id: string) {
    super(`${resource} with id ${id} not found`, {
      extensions: {
        code: 'NOT_FOUND',
        resource,
        id,
      },
    });
  }
}

export class ValidationError extends GraphQLError {
  constructor(message: string, field?: string) {
    super(message, {
      extensions: {
        code: 'VALIDATION_ERROR',
        field,
      },
    });
  }
}

export class UnauthorizedError extends GraphQLError {
  constructor() {
    super('Not authenticated', {
      extensions: { code: 'UNAUTHENTICATED' },
    });
  }
}
```

### Error Handling in Resolvers

```typescript
const resolvers = {
  Query: {
    user: async (_, { id }, context) => {
      if (!context.user) {
        throw new UnauthorizedError();
      }
      
      const user = await context.dataSources.users.findById(id);
      
      if (!user) {
        throw new NotFoundError('User', id);
      }
      
      return user;
    },
  },
};
```

## Authorization

### Field-Level Authorization

```typescript
const resolvers = {
  User: {
    email: (user, _, context) => {
      // Only show email to self or admin
      if (context.user?.id === user.id || context.user?.role === 'ADMIN') {
        return user.email;
      }
      return null;
    },
    
    privateData: (user, _, context) => {
      if (context.user?.id !== user.id) {
        throw new ForbiddenError('Cannot access private data');
      }
      return user.privateData;
    },
  },
};
```

### Directive-Based Authorization

```graphql
directive @auth(requires: Role = USER) on FIELD_DEFINITION

type Query {
  publicData: String
  userData: String @auth
  adminData: String @auth(requires: ADMIN)
}
```

```typescript
// Directive implementation
const authDirective = (schema, directiveName) => {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, directiveName)?.[0];
      
      if (authDirective) {
        const { requires } = authDirective;
        const { resolve = defaultFieldResolver } = fieldConfig;
        
        fieldConfig.resolve = async (source, args, context, info) => {
          if (!context.user) {
            throw new UnauthorizedError();
          }
          if (requires && context.user.role !== requires) {
            throw new ForbiddenError('Insufficient permissions');
          }
          return resolve(source, args, context, info);
        };
      }
      return fieldConfig;
    },
  });
};
```

## Subscriptions

```graphql
type Subscription {
  postCreated: Post!
  userUpdated(userId: ID!): User!
  messageReceived(channelId: ID!): Message!
}
```

```typescript
import { PubSub } from 'graphql-subscriptions';

const pubsub = new PubSub();

const resolvers = {
  Mutation: {
    createPost: async (_, { input }, context) => {
      const post = await context.dataSources.posts.create(input);
      pubsub.publish('POST_CREATED', { postCreated: post });
      return { post };
    },
  },
  
  Subscription: {
    postCreated: {
      subscribe: () => pubsub.asyncIterator(['POST_CREATED']),
    },
    
    userUpdated: {
      subscribe: (_, { userId }) => {
        return pubsub.asyncIterator([`USER_UPDATED_${userId}`]);
      },
    },
  },
};
```

## Query Complexity & Depth Limiting

### Prevent Expensive Queries

```typescript
import depthLimit from 'graphql-depth-limit';
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    depthLimit(10),  // Max query depth
    createComplexityLimitRule(1000, {
      scalarCost: 1,
      objectCost: 10,
      listFactor: 10,
    }),
  ],
});
```

### Cost Directives

```graphql
directive @cost(value: Int!, multipliers: [String!]) on FIELD_DEFINITION

type Query {
  users(first: Int!): [User!]! @cost(value: 10, multipliers: ["first"])
  expensiveOperation: Result! @cost(value: 100)
}
```

## Best Practices Summary

1. **Use input types** for all mutation arguments
2. **Return payload types** from mutations with errors field
3. **Use connections** for paginated lists (Relay spec)
4. **Implement DataLoader** to solve N+1 problems
5. **Add query depth/complexity limits** to prevent abuse
6. **Use enums** for fixed value sets
7. **Make fields nullable** unless guaranteed to exist
8. **Use custom scalars** for DateTime, JSON, etc.
9. **Document with descriptions** - they appear in GraphQL Playground
10. **Version via schema evolution** - deprecate fields, don't remove
