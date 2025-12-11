# Security Headers

HTTP security headers that protect against common web vulnerabilities.

## Essential Security Headers

| Header | Purpose | Risk Mitigated |
|--------|---------|----------------|
| **Content-Security-Policy** | Control resource loading | XSS, injection |
| **Strict-Transport-Security** | Force HTTPS | MITM, downgrade |
| **X-Content-Type-Options** | Prevent MIME sniffing | Script injection |
| **X-Frame-Options** | Block framing | Clickjacking |
| **Referrer-Policy** | Control referrer info | Information leakage |
| **Permissions-Policy** | Restrict browser features | Feature abuse |

## Hono Security Headers

### Using secureHeaders Middleware
```typescript
import { Hono } from 'hono';
import { secureHeaders } from 'hono/secure-headers';

const app = new Hono();

// Apply default secure headers
app.use('*', secureHeaders());

// Custom configuration
app.use('*', secureHeaders({
  // Strict Transport Security
  strictTransportSecurity: 'max-age=31536000; includeSubDomains; preload',
  
  // Content Type Options
  xContentTypeOptions: 'nosniff',
  
  // Frame Options (or use CSP frame-ancestors)
  xFrameOptions: 'DENY',
  
  // XSS Protection (disabled - use CSP instead)
  xXssProtection: '0',
  
  // Referrer Policy
  referrerPolicy: 'strict-origin-when-cross-origin',
  
  // Permissions Policy
  permissionsPolicy: {
    camera: [],
    microphone: [],
    geolocation: [],
    payment: ['self'],
  },
}));
```

### Manual Header Setting
```typescript
app.use('*', async (c, next) => {
  // Set headers before response
  c.header('X-Content-Type-Options', 'nosniff');
  c.header('X-Frame-Options', 'DENY');
  c.header('X-XSS-Protection', '0');
  c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
  c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  
  await next();
});
```

## Content Security Policy (CSP)

CSP is the most powerful header for preventing XSS and injection attacks.

### Basic CSP
```typescript
app.use('*', async (c, next) => {
  c.header('Content-Security-Policy', [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; '));
  
  await next();
});
```

### CSP Directives Reference

| Directive | Controls | Example |
|-----------|----------|---------|
| `default-src` | Fallback for other directives | `'self'` |
| `script-src` | JavaScript sources | `'self' https://cdn.example.com` |
| `style-src` | CSS sources | `'self' 'unsafe-inline'` |
| `img-src` | Image sources | `'self' data: https:` |
| `font-src` | Font sources | `'self' https://fonts.gstatic.com` |
| `connect-src` | Fetch, XHR, WebSocket | `'self' https://api.example.com` |
| `frame-src` | iframe sources | `'none'` |
| `frame-ancestors` | Who can frame this page | `'self'` |
| `object-src` | Plugin sources | `'none'` |
| `base-uri` | Base URL for relative URLs | `'self'` |
| `form-action` | Form submission targets | `'self'` |

### CSP Source Values

| Value | Meaning |
|-------|---------|
| `'self'` | Same origin |
| `'none'` | Block all |
| `'unsafe-inline'` | Allow inline scripts/styles (avoid if possible) |
| `'unsafe-eval'` | Allow eval() (avoid) |
| `https:` | Any HTTPS source |
| `data:` | Data URIs |
| `'nonce-xxx'` | Script with matching nonce attribute |
| `'sha256-xxx'` | Script with matching hash |
| `'strict-dynamic'` | Trust scripts loaded by trusted scripts |

### Nonce-Based CSP
```typescript
import { createMiddleware } from 'hono/factory';

const cspNonce = createMiddleware(async (c, next) => {
  // Generate random nonce for each request
  const nonce = crypto.randomUUID().replace(/-/g, '');
  c.set('cspNonce', nonce);
  
  c.header('Content-Security-Policy', [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}'`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "connect-src 'self'",
    "frame-ancestors 'none'",
  ].join('; '));
  
  await next();
});

app.use('*', cspNonce);

// In HTML response
app.get('/', (c) => {
  const nonce = c.get('cspNonce');
  return c.html(`
    <!DOCTYPE html>
    <html>
    <head>
      <script nonce="${nonce}">
        console.log('This script is allowed');
      </script>
    </head>
    <body>
      <h1>Hello</h1>
    </body>
    </html>
  `);
});
```

### Report-Only Mode (Testing)
```typescript
// Use Report-Only header to test CSP without breaking the site
app.use('*', async (c, next) => {
  c.header('Content-Security-Policy-Report-Only', [
    "default-src 'self'",
    "script-src 'self'",
    "report-uri /csp-report",
  ].join('; '));
  
  await next();
});

// Endpoint to receive CSP violation reports
app.post('/csp-report', async (c) => {
  const report = await c.req.json();
  console.log('CSP Violation:', report);
  return c.text('OK');
});
```

## CORS Configuration

Cross-Origin Resource Sharing controls which origins can access your API.

### Hono CORS Middleware
```typescript
import { cors } from 'hono/cors';

// Development - permissive
app.use('/api/*', cors());

// Production - restrictive
app.use('/api/*', cors({
  origin: ['https://app.example.com', 'https://admin.example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  exposeHeaders: ['X-Request-ID', 'X-RateLimit-Remaining'],
  maxAge: 86400, // 24 hours
  credentials: true,
}));

// Dynamic origin validation
app.use('/api/*', cors({
  origin: (origin) => {
    // Allow subdomains
    if (origin?.endsWith('.example.com')) {
      return origin;
    }
    // Allow localhost in development
    if (process.env.NODE_ENV === 'development' && origin?.includes('localhost')) {
      return origin;
    }
    return null; // Reject
  },
}));
```

### CORS Headers Explained

| Header | Purpose |
|--------|---------|
| `Access-Control-Allow-Origin` | Allowed origin(s) |
| `Access-Control-Allow-Methods` | Allowed HTTP methods |
| `Access-Control-Allow-Headers` | Allowed request headers |
| `Access-Control-Expose-Headers` | Headers readable by client |
| `Access-Control-Max-Age` | Preflight cache duration |
| `Access-Control-Allow-Credentials` | Allow cookies/auth |

## Strict Transport Security (HSTS)

Forces browsers to use HTTPS for all future requests.

```typescript
app.use('*', async (c, next) => {
  // Only set on HTTPS connections
  if (c.req.url.startsWith('https://')) {
    c.header(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains; preload'
    );
  }
  await next();
});
```

### HSTS Options

| Directive | Purpose |
|-----------|---------|
| `max-age` | How long to remember (seconds) |
| `includeSubDomains` | Apply to all subdomains |
| `preload` | Allow browser preload list inclusion |

## Referrer Policy

Controls how much referrer information is sent.

```typescript
// Options from most to least restrictive
const referrerPolicies = [
  'no-referrer',                      // Never send referrer
  'no-referrer-when-downgrade',       // No referrer on HTTPS→HTTP
  'same-origin',                      // Only same origin
  'origin',                           // Only origin (no path)
  'strict-origin',                    // Origin only, no downgrade
  'origin-when-cross-origin',         // Full URL same-origin, origin cross-origin
  'strict-origin-when-cross-origin',  // Recommended default
  'unsafe-url',                       // Always full URL (avoid)
];

app.use('*', async (c, next) => {
  c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
  await next();
});
```

## Permissions Policy

Control browser features available to the page.

```typescript
app.use('*', async (c, next) => {
  c.header('Permissions-Policy', [
    'camera=()',                    // Disable camera
    'microphone=()',                // Disable microphone
    'geolocation=()',               // Disable geolocation
    'payment=(self)',               // Only allow payment on same origin
    'usb=()',                       // Disable USB
    'accelerometer=()',             // Disable accelerometer
    'gyroscope=()',                 // Disable gyroscope
  ].join(', '));
  
  await next();
});
```

## Complete Security Headers Middleware

```typescript
import { createMiddleware } from 'hono/factory';

interface SecurityOptions {
  isDevelopment?: boolean;
  allowedOrigins?: string[];
  reportUri?: string;
}

export const securityMiddleware = (options: SecurityOptions = {}) => 
  createMiddleware(async (c, next) => {
    const { isDevelopment = false, allowedOrigins = [], reportUri } = options;
    
    // Generate nonce for CSP
    const nonce = crypto.randomUUID().replace(/-/g, '');
    c.set('cspNonce', nonce);
    
    // Content Security Policy
    const cspDirectives = [
      "default-src 'self'",
      `script-src 'self' 'nonce-${nonce}'${isDevelopment ? " 'unsafe-eval'" : ''}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self'",
      "connect-src 'self'" + (isDevelopment ? ' ws: wss:' : ''),
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
      "upgrade-insecure-requests",
    ];
    
    if (reportUri) {
      cspDirectives.push(`report-uri ${reportUri}`);
    }
    
    c.header('Content-Security-Policy', cspDirectives.join('; '));
    
    // Other security headers
    c.header('X-Content-Type-Options', 'nosniff');
    c.header('X-Frame-Options', 'DENY');
    c.header('X-XSS-Protection', '0'); // Disabled, use CSP instead
    c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
    c.header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    
    // HSTS (only in production with HTTPS)
    if (!isDevelopment) {
      c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    }
    
    // Remove server identification
    c.header('X-Powered-By', ''); // Or don't set at all
    
    await next();
  });

// Usage
app.use('*', securityMiddleware({
  isDevelopment: process.env.NODE_ENV === 'development',
  reportUri: '/csp-report',
}));
```

## Testing Security Headers

### Online Tools
- **securityheaders.com** - Scan and grade your headers
- **observatory.mozilla.org** - Mozilla security scanner
- **csp-evaluator.withgoogle.com** - CSP analyzer

### Manual Testing
```bash
# Check headers with curl
curl -I https://your-api.com

# Check specific header
curl -s -I https://your-api.com | grep -i "content-security-policy"
```

## Best Practices

1. **Start strict, relax as needed** - Begin with restrictive CSP
2. **Use Report-Only first** - Test CSP without breaking the site
3. **Avoid unsafe-inline** - Use nonces or hashes instead
4. **Keep HSTS max-age high** - 1 year minimum for production
5. **Set frame-ancestors** - Prevent clickjacking
6. **Configure CORS carefully** - Never use `*` with credentials
7. **Test after deployment** - Headers can be overwritten by proxies
8. **Monitor CSP reports** - Catch issues and attacks
9. **Update regularly** - Security best practices evolve
10. **Document exceptions** - Explain why unsafe values are needed
