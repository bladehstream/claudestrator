# Secure Storage

## expo-secure-store

Encrypted key-value storage using iOS Keychain and Android Keystore. Works in Expo Go.

### Installation

```bash
npx expo install expo-secure-store
```

### Basic Usage

```typescript
import * as SecureStore from 'expo-secure-store';

// Store a value
const storeSecureValue = async (key: string, value: string) => {
  await SecureStore.setItemAsync(key, value);
};

// Retrieve a value
const getSecureValue = async (key: string): Promise<string | null> => {
  return await SecureStore.getItemAsync(key);
};

// Delete a value
const deleteSecureValue = async (key: string) => {
  await SecureStore.deleteItemAsync(key);
};

// Example usage
await storeSecureValue('auth_token', 'eyJhbGciOiJIUzI1NiIs...');
const token = await getSecureValue('auth_token');
await deleteSecureValue('auth_token');
```

### Store Objects (JSON)

```typescript
interface UserCredentials {
  username: string;
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

const storeCredentials = async (credentials: UserCredentials) => {
  await SecureStore.setItemAsync('credentials', JSON.stringify(credentials));
};

const getCredentials = async (): Promise<UserCredentials | null> => {
  const json = await SecureStore.getItemAsync('credentials');
  return json ? JSON.parse(json) : null;
};
```

### Security Options

```typescript
import * as SecureStore from 'expo-secure-store';

// iOS Keychain accessibility options
await SecureStore.setItemAsync('sensitive_data', 'value', {
  // When the data is accessible
  keychainAccessible: SecureStore.WHEN_UNLOCKED,
});

// Available options:
SecureStore.AFTER_FIRST_UNLOCK           // After first unlock, persists
SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY
SecureStore.ALWAYS                        // Always accessible (deprecated)
SecureStore.ALWAYS_THIS_DEVICE_ONLY      // (deprecated)
SecureStore.WHEN_PASSCODE_SET_THIS_DEVICE_ONLY  // Only with passcode
SecureStore.WHEN_UNLOCKED                 // Only when unlocked (default)
SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY
```

### Accessibility Options Explained

| Option | When Accessible | Migrates to New Device | Use Case |
|--------|-----------------|------------------------|----------|
| `WHEN_UNLOCKED` | Device unlocked | Yes | Default, most secure |
| `WHEN_UNLOCKED_THIS_DEVICE_ONLY` | Device unlocked | No | Device-specific secrets |
| `AFTER_FIRST_UNLOCK` | After first unlock | Yes | Background access needed |
| `AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY` | After first unlock | No | Background + device-bound |
| `WHEN_PASSCODE_SET_THIS_DEVICE_ONLY` | Passcode set | No | Highest security |

### Check Availability

```typescript
const isSecureStoreAvailable = async (): Promise<boolean> => {
  return await SecureStore.isAvailableAsync();
};

// Note: Returns false on web, Android emulators without Google APIs
```

---

## Common Patterns

### Authentication Token Manager

```typescript
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'auth_token';
const REFRESH_KEY = 'refresh_token';

class TokenManager {
  static async setTokens(accessToken: string, refreshToken: string) {
    await Promise.all([
      SecureStore.setItemAsync(TOKEN_KEY, accessToken),
      SecureStore.setItemAsync(REFRESH_KEY, refreshToken),
    ]);
  }

  static async getAccessToken(): Promise<string | null> {
    return SecureStore.getItemAsync(TOKEN_KEY);
  }

  static async getRefreshToken(): Promise<string | null> {
    return SecureStore.getItemAsync(REFRESH_KEY);
  }

  static async clearTokens() {
    await Promise.all([
      SecureStore.deleteItemAsync(TOKEN_KEY),
      SecureStore.deleteItemAsync(REFRESH_KEY),
    ]);
  }

  static async hasValidToken(): Promise<boolean> {
    const token = await this.getAccessToken();
    if (!token) return false;
    
    // Check expiration (assuming JWT)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }
}
```

### Biometric-Protected Storage

Combine with `expo-local-authentication` for biometric protection:

```typescript
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';

const getProtectedValue = async (key: string): Promise<string | null> => {
  // Require biometric authentication before accessing
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to access secure data',
    disableDeviceFallback: false,
  });

  if (!result.success) {
    throw new Error('Authentication failed');
  }

  return SecureStore.getItemAsync(key);
};

const storeProtectedValue = async (key: string, value: string) => {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to save secure data',
  });

  if (!result.success) {
    throw new Error('Authentication failed');
  }

  await SecureStore.setItemAsync(key, value, {
    keychainAccessible: SecureStore.WHEN_PASSCODE_SET_THIS_DEVICE_ONLY,
  });
};
```

### Encrypted User Preferences

```typescript
import * as SecureStore from 'expo-secure-store';

interface SecurePreferences {
  pinCode?: string;
  biometricEnabled?: boolean;
  lastLoginTimestamp?: number;
}

const PREFS_KEY = 'secure_preferences';

class SecurePreferencesManager {
  private static cache: SecurePreferences | null = null;

  static async get(): Promise<SecurePreferences> {
    if (this.cache) return this.cache;

    const json = await SecureStore.getItemAsync(PREFS_KEY);
    this.cache = json ? JSON.parse(json) : {};
    return this.cache!;
  }

  static async set(prefs: Partial<SecurePreferences>) {
    const current = await this.get();
    const updated = { ...current, ...prefs };
    await SecureStore.setItemAsync(PREFS_KEY, JSON.stringify(updated));
    this.cache = updated;
  }

  static async clear() {
    await SecureStore.deleteItemAsync(PREFS_KEY);
    this.cache = null;
  }
}
```

### PIN Code Storage

```typescript
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';

const PIN_KEY = 'user_pin_hash';

// Store PIN (hashed)
const setPin = async (pin: string) => {
  // Hash the PIN before storing
  const hash = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    pin
  );
  await SecureStore.setItemAsync(PIN_KEY, hash);
};

// Verify PIN
const verifyPin = async (pin: string): Promise<boolean> => {
  const storedHash = await SecureStore.getItemAsync(PIN_KEY);
  if (!storedHash) return false;

  const inputHash = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    pin
  );

  return storedHash === inputHash;
};

// Check if PIN is set
const hasPinSet = async (): Promise<boolean> => {
  const pin = await SecureStore.getItemAsync(PIN_KEY);
  return pin !== null;
};
```

---

## Storage Comparison

| Storage | Encrypted | Persists Uninstall | Use Case |
|---------|-----------|-------------------|----------|
| `expo-secure-store` | ✅ | iOS: Maybe*, Android: No | Tokens, credentials |
| `AsyncStorage` | ❌ | No | Non-sensitive preferences |
| `MMKV` | Optional | No | High-performance cache |

*iOS Keychain items persist if `kSecAttrAccessible` allows backup and same bundle ID is used.

---

## Platform Behavior

### iOS (Keychain)

- Data encrypted with device-specific key
- Can persist across app reinstalls (same bundle ID)
- Syncs to iCloud Keychain if configured
- Accessible based on `keychainAccessible` setting

### Android (EncryptedSharedPreferences)

- Uses Android Keystore for encryption
- Data deleted on app uninstall
- Not synced across devices
- Requires Android 6.0+ (API 23)

---

## Limitations

- **Key length**: Max 2048 bytes
- **Value length**: No hard limit, but keep reasonable (< 2KB recommended)
- **Sync operations**: All operations are async
- **Web support**: Not available (falls back gracefully)

---

## Security Best Practices

1. **Never store plaintext passwords** - Hash before storing
2. **Use appropriate accessibility** - Choose based on when data is needed
3. **Clear on logout** - Delete all sensitive data when user logs out
4. **Validate before use** - Check token expiration, data integrity
5. **Don't store unnecessary data** - Only store what's needed
6. **Consider biometric gating** - Add extra layer for sensitive operations

### What to Store in Secure Storage

✅ Do store:
- Authentication tokens (access, refresh)
- API keys (user-specific)
- Encryption keys
- PIN codes (hashed)
- Biometric flags

❌ Don't store:
- User preferences (use AsyncStorage)
- Cache data (use MMKV or file system)
- Large data (use encrypted file storage)
- Anything that needs to be searchable

---

## Migration from AsyncStorage

```typescript
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

const migrateToSecureStorage = async () => {
  const MIGRATION_KEY = 'secure_migration_complete';
  
  // Check if already migrated
  const migrated = await SecureStore.getItemAsync(MIGRATION_KEY);
  if (migrated) return;

  // Move sensitive keys
  const keysToMigrate = ['auth_token', 'refresh_token', 'user_pin'];
  
  for (const key of keysToMigrate) {
    const value = await AsyncStorage.getItem(key);
    if (value) {
      await SecureStore.setItemAsync(key, value);
      await AsyncStorage.removeItem(key);
    }
  }

  // Mark migration complete
  await SecureStore.setItemAsync(MIGRATION_KEY, 'true');
};
```
