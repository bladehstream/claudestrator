# Authentication

## Biometrics with expo-local-authentication

### Installation

```bash
npx expo install expo-local-authentication
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "expo-local-authentication",
        {
          "faceIDPermission": "Allow $(PRODUCT_NAME) to use Face ID for secure authentication"
        }
      ]
    ]
  }
}
```

### Check Availability

```typescript
import * as LocalAuthentication from 'expo-local-authentication';

// Check if device has biometric hardware
const hasHardware = await LocalAuthentication.hasHardwareAsync();

// Check if biometrics are enrolled
const isEnrolled = await LocalAuthentication.isEnrolledAsync();

// Get supported authentication types
const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();
// Returns: [1] = Fingerprint, [2] = FaceID, [3] = Iris

// Map to human-readable
const typeNames = {
  [LocalAuthentication.AuthenticationType.FINGERPRINT]: 'Fingerprint',
  [LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION]: 'Face ID',
  [LocalAuthentication.AuthenticationType.IRIS]: 'Iris',
};
```

### Authenticate

```typescript
const authenticate = async (): Promise<boolean> => {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to continue',
    cancelLabel: 'Cancel',
    disableDeviceFallback: false, // Allow PIN/pattern fallback
    fallbackLabel: 'Use passcode', // iOS only
  });

  if (result.success) {
    return true;
  }
  
  // Handle failure
  if (result.error === 'user_cancel') {
    // User cancelled
  } else if (result.error === 'user_fallback') {
    // User chose passcode fallback
  } else if (result.error === 'lockout') {
    // Too many failed attempts
  }
  
  return false;
};
```

### Security Levels (Android)

```typescript
// Check security level on Android
const securityLevel = await LocalAuthentication.getEnrolledLevelAsync();

// SecurityLevel.NONE = 0 (no security)
// SecurityLevel.SECRET = 1 (PIN/pattern/password)
// SecurityLevel.BIOMETRIC = 2 (fingerprint/face)
```

### Platform Notes

| Feature | iOS | Android |
|---------|-----|---------|
| Touch ID/Fingerprint | ✅ Expo Go | ✅ Expo Go |
| Face ID | ✅ Dev build only | ✅ Expo Go |
| PIN fallback | ✅ | ✅ |
| Custom fallback label | ✅ | ❌ |
| Lockout detection | ✅ | ✅ |

---

## FIDO2/Passkeys with react-native-passkey

Provides WebAuthn/FIDO2 support for phishing-resistant authentication including platform authenticators (device biometrics) and roaming authenticators (YubiKey, Google Titan).

### Installation

```bash
npm install react-native-passkey
npx expo prebuild --clean
```

### Prerequisites

**iOS (apple-app-site-association)**:
Host at `https://yourdomain.com/.well-known/apple-app-site-association`:
```json
{
  "webcredentials": {
    "apps": ["TEAMID.com.yourcompany.yourapp"]
  }
}
```

**Android (assetlinks.json)**:
Host at `https://yourdomain.com/.well-known/assetlinks.json`:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.yourcompany.yourapp",
    "sha256_cert_fingerprints": ["SHA256:..."]
  }
}]
```

**Config Plugin (app.json)**:
```json
{
  "expo": {
    "plugins": [
      ["react-native-passkey", {
        "associatedDomains": ["webcredentials:yourdomain.com"]
      }]
    ],
    "ios": {
      "associatedDomains": ["webcredentials:yourdomain.com"]
    }
  }
}
```

### Registration (Create Passkey)

```typescript
import { Passkey } from 'react-native-passkey';

const register = async (userId: string, username: string) => {
  // Get challenge from your server
  const { challenge, rpId, rpName } = await fetchRegistrationOptions();

  try {
    const result = await Passkey.create({
      challenge: base64ToArrayBuffer(challenge),
      rp: {
        id: rpId,        // e.g., "yourdomain.com"
        name: rpName,    // e.g., "Your App"
      },
      user: {
        id: stringToArrayBuffer(userId),
        name: username,
        displayName: username,
      },
      pubKeyCredParams: [
        { type: 'public-key', alg: -7 },   // ES256
        { type: 'public-key', alg: -257 }, // RS256
      ],
      authenticatorSelection: {
        authenticatorAttachment: 'platform', // or 'cross-platform' for security keys
        userVerification: 'required',
        residentKey: 'required',
      },
      timeout: 60000,
    });

    // Send result.response to server for verification
    await verifyRegistration(result);
  } catch (error) {
    handlePasskeyError(error);
  }
};
```

### Authentication (Get Passkey)

```typescript
const authenticate = async () => {
  const { challenge, rpId, allowCredentials } = await fetchAuthOptions();

  try {
    const result = await Passkey.get({
      challenge: base64ToArrayBuffer(challenge),
      rpId,
      allowCredentials: allowCredentials?.map(cred => ({
        type: 'public-key',
        id: base64ToArrayBuffer(cred.id),
      })),
      userVerification: 'required',
      timeout: 60000,
    });

    // Send result.response to server for verification
    const { token } = await verifyAuthentication(result);
    return token;
  } catch (error) {
    handlePasskeyError(error);
  }
};
```

### Security Key (YubiKey) Specific

```typescript
// iOS: Force security key instead of platform authenticator
import { Passkey } from 'react-native-passkey';

// Registration with security key
const result = await Passkey.createSecurityKey({
  // Same options as create()
  challenge: base64ToArrayBuffer(challenge),
  rp: { id: rpId, name: rpName },
  user: { id: userId, name: username, displayName: username },
  pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
  authenticatorSelection: {
    authenticatorAttachment: 'cross-platform',
    userVerification: 'required',
  },
});

// Authentication with security key
const authResult = await Passkey.getSecurityKey({
  challenge: base64ToArrayBuffer(challenge),
  rpId,
  userVerification: 'required',
});
```

**Android limitation**: Cannot force security key programmatically. User selects via system UI.

### Error Handling

```typescript
const handlePasskeyError = (error: unknown) => {
  if (error instanceof Error) {
    switch (error.name) {
      case 'NotAllowedError':
        // User cancelled or denied
        break;
      case 'SecurityError':
        // RP ID mismatch or domain not associated
        break;
      case 'InvalidStateError':
        // Credential already exists (registration)
        break;
      case 'NotSupportedError':
        // Platform doesn't support passkeys
        break;
      case 'AbortError':
        // Operation timed out
        break;
    }
  }
};
```

### Platform Support

| Feature | iOS | Android |
|---------|-----|---------|
| Platform passkeys | iOS 15+ | API 28+ |
| Security keys (NFC) | iOS 13.3+ | API 28+ |
| Security keys (USB-C) | ✅ | ✅ |
| Force security key | ✅ `createSecurityKey()` | ❌ System UI only |
| largeBlob extension | iOS 17+ | Android 14+ |
| PRF extension | iOS 18+ | Not yet |

### Supported Security Keys

- YubiKey 5 series (NFC, USB-C, USB-A)
- Google Titan
- Feitian
- Nitrokey
- SoloKeys
- Any FIDO2-certified hardware authenticator

---

## Combined Authentication Flow

```typescript
import * as LocalAuthentication from 'expo-local-authentication';
import { Passkey } from 'react-native-passkey';

type AuthMethod = 'biometric' | 'passkey' | 'security-key' | 'pin';

const getAvailableMethods = async (): Promise<AuthMethod[]> => {
  const methods: AuthMethod[] = [];
  
  // Check biometrics
  const hasBiometric = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  if (hasBiometric && isEnrolled) {
    methods.push('biometric');
  }
  
  // Check passkey support
  const passkeysSupported = await Passkey.isSupported();
  if (passkeysSupported) {
    methods.push('passkey');
    methods.push('security-key');
  }
  
  // PIN always available as fallback
  methods.push('pin');
  
  return methods;
};

const authenticateWithMethod = async (method: AuthMethod): Promise<boolean> => {
  switch (method) {
    case 'biometric':
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate',
        disableDeviceFallback: true,
      });
      return result.success;
      
    case 'passkey':
      return await authenticateWithPasskey();
      
    case 'security-key':
      return await authenticateWithSecurityKey();
      
    case 'pin':
      return await authenticateWithPIN();
  }
};
```
