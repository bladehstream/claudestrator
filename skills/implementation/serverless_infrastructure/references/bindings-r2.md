# Cloudflare R2 Object Storage Bindings

S3-compatible object storage with zero egress fees. Ideal for files, images, backups, and large data objects.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Max object size** | 5 TB |
| **Max bucket size** | Unlimited |
| **Storage classes** | Standard, Infrequent Access |
| **Compatibility** | S3 API compatible |
| **Egress costs** | None (zero egress fees) |
| **Replication** | Automatic global replication |

## Configuration

### wrangler.toml
```toml
[[r2_buckets]]
binding = "STORAGE"
bucket_name = "my-bucket"

# Optional: Jurisdictional restriction
[[r2_buckets]]
binding = "STORAGE_EU"
bucket_name = "my-eu-bucket"
jurisdiction = "eu"
```

### Create Bucket
```bash
# Create bucket
npx wrangler r2 bucket create my-bucket

# List buckets
npx wrangler r2 bucket list

# Create with location hint
npx wrangler r2 bucket create my-bucket --location=WEUR
```

## Basic Operations

### TypeScript Types
```typescript
interface Env {
  STORAGE: R2Bucket;
}

// R2Object properties
interface R2ObjectMetadata {
  key: string;
  size: number;
  etag: string;
  httpEtag: string;
  uploaded: Date;
  httpMetadata?: R2HTTPMetadata;
  customMetadata?: Record<string, string>;
}
```

### Read Operations
```typescript
// Get object (returns R2ObjectBody or null)
const object = await c.env.STORAGE.get('path/to/file.pdf');

if (object) {
  // Access body as different types
  const arrayBuffer = await object.arrayBuffer();
  const text = await object.text();
  const json = await object.json();
  const blob = await object.blob();
  const stream = object.body; // ReadableStream
  
  // Access metadata
  console.log(object.key, object.size, object.etag);
  console.log(object.httpMetadata?.contentType);
  console.log(object.customMetadata?.userId);
}

// Head (metadata only, no body)
const head = await c.env.STORAGE.head('path/to/file.pdf');
```

### Write Operations
```typescript
// Put from various sources
await c.env.STORAGE.put('file.txt', 'Hello World');
await c.env.STORAGE.put('data.json', JSON.stringify(data));
await c.env.STORAGE.put('image.png', arrayBuffer);
await c.env.STORAGE.put('upload.pdf', readableStream);

// Put with metadata
await c.env.STORAGE.put('document.pdf', pdfData, {
  httpMetadata: {
    contentType: 'application/pdf',
    contentDisposition: 'attachment; filename="document.pdf"',
    cacheControl: 'public, max-age=86400',
  },
  customMetadata: {
    userId: '123',
    uploadedAt: new Date().toISOString(),
    originalName: 'my-document.pdf',
  },
});

// Conditional put (only if not exists)
await c.env.STORAGE.put('file.txt', 'content', {
  onlyIf: { etagDoesNotMatch: '*' },
});
```

### Delete Operations
```typescript
// Delete single object
await c.env.STORAGE.delete('path/to/file.pdf');

// Delete multiple objects
await c.env.STORAGE.delete(['file1.pdf', 'file2.pdf', 'file3.pdf']);
```

### List Operations
```typescript
// List objects
const listed = await c.env.STORAGE.list();

for (const object of listed.objects) {
  console.log(object.key, object.size);
}

// List with prefix (folder-like)
const listed = await c.env.STORAGE.list({ prefix: 'uploads/' });

// List with delimiter (get "folders")
const listed = await c.env.STORAGE.list({
  prefix: 'uploads/',
  delimiter: '/',
});

// listed.objects = files directly in uploads/
// listed.delimitedPrefixes = ["uploads/2024/", "uploads/images/"]

// Paginate through results
let cursor: string | undefined;
const allObjects: R2Object[] = [];

do {
  const listed = await c.env.STORAGE.list({ cursor, limit: 1000 });
  allObjects.push(...listed.objects);
  cursor = listed.truncated ? listed.cursor : undefined;
} while (cursor);
```

## Common Patterns

### File Upload Handler
```typescript
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Env }>();

app.post('/upload', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('file') as File | null;
  
  if (!file) {
    return c.json({ error: 'No file provided' }, 400);
  }
  
  // Validate file
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    return c.json({ error: 'File too large' }, 400);
  }
  
  const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
  if (!allowedTypes.includes(file.type)) {
    return c.json({ error: 'Invalid file type' }, 400);
  }
  
  // Generate unique key
  const ext = file.name.split('.').pop();
  const key = `uploads/${crypto.randomUUID()}.${ext}`;
  
  // Upload to R2
  await c.env.STORAGE.put(key, file.stream(), {
    httpMetadata: {
      contentType: file.type,
    },
    customMetadata: {
      originalName: file.name,
      uploadedAt: new Date().toISOString(),
    },
  });
  
  return c.json({ key, size: file.size });
});
```

### File Download Handler
```typescript
app.get('/files/:key{.+}', async (c) => {
  const key = c.req.param('key');
  const object = await c.env.STORAGE.get(key);
  
  if (!object) {
    return c.json({ error: 'Not found' }, 404);
  }
  
  const headers = new Headers();
  headers.set('Content-Type', object.httpMetadata?.contentType || 'application/octet-stream');
  headers.set('Content-Length', String(object.size));
  headers.set('ETag', object.httpEtag);
  
  if (object.httpMetadata?.contentDisposition) {
    headers.set('Content-Disposition', object.httpMetadata.contentDisposition);
  }
  
  return new Response(object.body, { headers });
});
```

### Presigned URLs (Using S3 API)
```typescript
import { AwsClient } from 'aws4fetch';

interface Env {
  STORAGE: R2Bucket;
  R2_ACCESS_KEY: string;
  R2_SECRET_KEY: string;
  R2_ACCOUNT_ID: string;
  R2_BUCKET_NAME: string;
}

async function getPresignedUrl(
  env: Env,
  key: string,
  expiresIn: number = 3600
): Promise<string> {
  const client = new AwsClient({
    accessKeyId: env.R2_ACCESS_KEY,
    secretAccessKey: env.R2_SECRET_KEY,
  });
  
  const url = new URL(
    `https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${env.R2_BUCKET_NAME}/${key}`
  );
  
  // Add presign parameters
  url.searchParams.set('X-Amz-Expires', String(expiresIn));
  
  const signed = await client.sign(
    new Request(url, { method: 'GET' }),
    { aws: { signQuery: true } }
  );
  
  return signed.url;
}

// Usage
app.get('/download/:key{.+}', async (c) => {
  const key = c.req.param('key');
  
  // Verify user has access to this file...
  
  const presignedUrl = await getPresignedUrl(c.env, key, 300); // 5 minutes
  return c.redirect(presignedUrl);
});
```

### Image Processing Pipeline
```typescript
app.post('/images', async (c) => {
  const formData = await c.req.formData();
  const file = formData.get('image') as File | null;
  
  if (!file || !file.type.startsWith('image/')) {
    return c.json({ error: 'Invalid image' }, 400);
  }
  
  const id = crypto.randomUUID();
  const buffer = await file.arrayBuffer();
  
  // Store original
  await c.env.STORAGE.put(`images/${id}/original`, buffer, {
    httpMetadata: { contentType: file.type },
  });
  
  // Queue resize jobs (using Cloudflare Queue)
  await c.env.IMAGE_QUEUE.send({
    id,
    sizes: [
      { name: 'thumb', width: 150, height: 150 },
      { name: 'medium', width: 800, height: 600 },
      { name: 'large', width: 1920, height: 1080 },
    ],
  });
  
  return c.json({
    id,
    original: `images/${id}/original`,
    status: 'processing',
  });
});
```

### Multipart Upload (Large Files)
```typescript
// For files > 5GB, use multipart upload
async function multipartUpload(
  bucket: R2Bucket,
  key: string,
  stream: ReadableStream,
  contentType: string
): Promise<R2Object> {
  // Create multipart upload
  const multipart = await bucket.createMultipartUpload(key, {
    httpMetadata: { contentType },
  });
  
  const parts: R2UploadedPart[] = [];
  const reader = stream.getReader();
  const partSize = 10 * 1024 * 1024; // 10MB parts
  let partNumber = 1;
  let buffer = new Uint8Array(0);
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (value) {
        // Append to buffer
        const newBuffer = new Uint8Array(buffer.length + value.length);
        newBuffer.set(buffer);
        newBuffer.set(value, buffer.length);
        buffer = newBuffer;
      }
      
      // Upload part when buffer is large enough or done
      while (buffer.length >= partSize || (done && buffer.length > 0)) {
        const chunk = buffer.slice(0, partSize);
        buffer = buffer.slice(partSize);
        
        const part = await multipart.uploadPart(partNumber, chunk);
        parts.push(part);
        partNumber++;
      }
      
      if (done) break;
    }
    
    // Complete multipart upload
    return await multipart.complete(parts);
  } catch (error) {
    // Abort on error
    await multipart.abort();
    throw error;
  }
}
```

### Storage Service Class
```typescript
export class StorageService {
  constructor(private bucket: R2Bucket) {}

  async upload(
    key: string,
    data: ReadableStream | ArrayBuffer | string,
    options?: {
      contentType?: string;
      metadata?: Record<string, string>;
    }
  ): Promise<{ key: string; size: number; etag: string }> {
    const result = await this.bucket.put(key, data, {
      httpMetadata: options?.contentType
        ? { contentType: options.contentType }
        : undefined,
      customMetadata: options?.metadata,
    });
    
    return {
      key: result.key,
      size: result.size,
      etag: result.etag,
    };
  }

  async download(key: string): Promise<{
    body: ReadableStream;
    metadata: R2ObjectMetadata;
  } | null> {
    const object = await this.bucket.get(key);
    if (!object) return null;
    
    return {
      body: object.body,
      metadata: {
        key: object.key,
        size: object.size,
        etag: object.etag,
        httpEtag: object.httpEtag,
        uploaded: object.uploaded,
        httpMetadata: object.httpMetadata,
        customMetadata: object.customMetadata,
      },
    };
  }

  async exists(key: string): Promise<boolean> {
    const head = await this.bucket.head(key);
    return head !== null;
  }

  async delete(key: string | string[]): Promise<void> {
    await this.bucket.delete(key);
  }

  async listByPrefix(
    prefix: string,
    options?: { limit?: number }
  ): Promise<{ key: string; size: number; uploaded: Date }[]> {
    const listed = await this.bucket.list({
      prefix,
      limit: options?.limit || 1000,
    });
    
    return listed.objects.map((obj) => ({
      key: obj.key,
      size: obj.size,
      uploaded: obj.uploaded,
    }));
  }

  async getSignedUploadUrl(key: string, expiresIn: number = 3600): Promise<string> {
    // Implement with aws4fetch for presigned PUT URL
    throw new Error('Implement with aws4fetch');
  }
}
```

## Conditional Operations

```typescript
// Only get if modified since
const object = await c.env.STORAGE.get('file.txt', {
  onlyIf: {
    uploadedAfter: new Date('2024-01-01'),
  },
});

// Only put if ETag matches (optimistic locking)
try {
  await c.env.STORAGE.put('config.json', newConfig, {
    onlyIf: { etagMatches: currentEtag },
  });
} catch (error) {
  // Conflict - someone else modified the file
}

// Only put if not exists
await c.env.STORAGE.put('unique-key', data, {
  onlyIf: { etagDoesNotMatch: '*' },
});
```

## Public Access

### Public Bucket via Custom Domain
```toml
# wrangler.toml - serve bucket via Workers
[[r2_buckets]]
binding = "STORAGE"
bucket_name = "public-assets"
```

```typescript
// Simple static file server
app.get('/assets/*', async (c) => {
  const key = c.req.path.replace('/assets/', '');
  const object = await c.env.STORAGE.get(key);
  
  if (!object) {
    return c.notFound();
  }
  
  return new Response(object.body, {
    headers: {
      'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
      'Cache-Control': 'public, max-age=31536000, immutable',
      'ETag': object.httpEtag,
    },
  });
});
```

## Error Handling

```typescript
async function safeUpload(
  bucket: R2Bucket,
  key: string,
  data: ArrayBuffer
): Promise<{ success: boolean; error?: string }> {
  try {
    await bucket.put(key, data);
    return { success: true };
  } catch (error) {
    if (error instanceof Error) {
      console.error('R2 upload failed:', error.message);
      return { success: false, error: error.message };
    }
    return { success: false, error: 'Unknown error' };
  }
}
```

## Testing

### Local Development
```bash
# R2 works locally with persist
npx wrangler dev --persist-to=.wrangler/state

# Or use remote R2
npx wrangler dev --remote
```

### Upload Test File
```bash
# Via wrangler
npx wrangler r2 object put my-bucket/test.txt --file=./test.txt

# Via curl (to local dev server)
curl -X POST http://localhost:8787/upload \
  -F "file=@./test.pdf"
```

## Best Practices

1. **Use meaningful key paths** - Organize like folders: `users/{id}/avatar.png`
2. **Set Content-Type on upload** - Browsers need this for proper handling
3. **Use custom metadata** - Store original filename, user ID, timestamps
4. **Implement presigned URLs** - For direct client uploads/downloads
5. **Handle large files with multipart** - Required for files > 5GB
6. **Use conditional operations** - Prevent race conditions
7. **Clean up orphaned files** - Implement garbage collection for unused files
8. **Set appropriate cache headers** - Leverage Cloudflare's CDN
