# Mobile Authentication (React Native / Expo)

## Overview

Mobile apps require special authentication handling due to:
- No httpOnly cookies (no browser)
- Secure hardware storage available (Keychain/Keystore)
- Biometric authentication capabilities
- Background token refresh requirements
- App switching and state persistence

## Secure Token Storage

### expo-secure-store

```bash
npx expo install expo-secure-store
```

```typescript
import * as SecureStore from 'expo-secure-store';

// Storage keys
const KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  USER_DATA: 'auth_user_data',
};

// Store token
async function storeToken(key: string, value: string): Promise<void> {
  await SecureStore.setItemAsync(key, value, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
  });
}

// Retrieve token
async function getToken(key: string): Promise<string | null> {
  return SecureStore.getItemAsync(key);
}

// Delete token
async function deleteToken(key: string): Promise<void> {
  await SecureStore.deleteItemAsync(key);
}

// Store with biometric protection
async function storeWithBiometrics(
  key: string,
  value: string
): Promise<void> {
  await SecureStore.setItemAsync(key, value, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    requireAuthentication: true,  // Requires biometrics to access
  });
}

// Clear all auth data on logout
async function clearAuthData(): Promise<void> {
  await Promise.all([
    deleteToken(KEYS.ACCESS_TOKEN),
    deleteToken(KEYS.REFRESH_TOKEN),
    deleteToken(KEYS.USER_DATA),
  ]);
}
```

### Auth Storage Service

```typescript
interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;  // Unix timestamp
}

interface User {
  id: string;
  email: string;
  name?: string;
}

class AuthStorage {
  async saveTokens(tokens: AuthTokens): Promise<void> {
    await storeToken(KEYS.ACCESS_TOKEN, tokens.accessToken);
    await storeToken(KEYS.REFRESH_TOKEN, tokens.refreshToken);
  }

  async getAccessToken(): Promise<string | null> {
    return getToken(KEYS.ACCESS_TOKEN);
  }

  async getRefreshToken(): Promise<string | null> {
    return getToken(KEYS.REFRESH_TOKEN);
  }

  async saveUser(user: User): Promise<void> {
    await storeToken(KEYS.USER_DATA, JSON.stringify(user));
  }

  async getUser(): Promise<User | null> {
    const data = await getToken(KEYS.USER_DATA);
    return data ? JSON.parse(data) : null;
  }

  async clear(): Promise<void> {
    await clearAuthData();
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getAccessToken();
    return !!token;
  }
}

export const authStorage = new AuthStorage();
```

## Biometric Authentication

### Setup

```bash
npx expo install expo-local-authentication
```

```json
// app.json
{
  "expo": {
    "plugins": [
      [
        "expo-local-authentication",
        {
          "faceIDPermission": "Allow $(PRODUCT_NAME) to use Face ID for authentication."
        }
      ]
    ]
  }
}
```

### Implementation

```typescript
import * as LocalAuthentication from 'expo-local-authentication';

interface BiometricCapability {
  isSupported: boolean;
  isEnrolled: boolean;
  biometryType: 'fingerprint' | 'facial' | 'iris' | null;
}

// Check biometric capability
async function checkBiometricCapability(): Promise<BiometricCapability> {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();

  let biometryType: 'fingerprint' | 'facial' | 'iris' | null = null;
  if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
    biometryType = 'facial';
  } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
    biometryType = 'fingerprint';
  } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.IRIS)) {
    biometryType = 'iris';
  }

  return {
    isSupported: hasHardware,
    isEnrolled,
    biometryType,
  };
}

// Authenticate with biometrics
async function authenticateWithBiometrics(
  promptMessage = 'Authenticate to continue'
): Promise<{ success: boolean; error?: string }> {
  const capability = await checkBiometricCapability();

  if (!capability.isSupported) {
    return { success: false, error: 'Biometrics not supported' };
  }

  if (!capability.isEnrolled) {
    return { success: false, error: 'No biometrics enrolled' };
  }

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage,
    cancelLabel: 'Cancel',
    disableDeviceFallback: false,  // Allow PIN/password fallback
    fallbackLabel: 'Use passcode',
  });

  if (result.success) {
    return { success: true };
  }

  return {
    success: false,
    error: result.error || 'Authentication failed',
  };
}
```

### Biometric-Protected Login Flow

```typescript
// Enable biometric login after successful password login
async function enableBiometricLogin(
  email: string,
  refreshToken: string
): Promise<boolean> {
  const { success } = await authenticateWithBiometrics(
    'Enable biometric login'
  );

  if (!success) return false;

  // Store credentials with biometric protection
  await SecureStore.setItemAsync(
    'biometric_credentials',
    JSON.stringify({ email, refreshToken }),
    { requireAuthentication: true }
  );

  return true;
}

// Login with biometrics
async function loginWithBiometrics(): Promise<AuthTokens | null> {
  const { success } = await authenticateWithBiometrics('Login');

  if (!success) return null;

  // Retrieve stored credentials
  const credentialsJson = await SecureStore.getItemAsync('biometric_credentials');
  if (!credentialsJson) return null;

  const { refreshToken } = JSON.parse(credentialsJson);

  // Exchange refresh token for new tokens
  const tokens = await refreshTokens(refreshToken);
  await authStorage.saveTokens(tokens);

  return tokens;
}

// Check if biometric login is available
async function isBiometricLoginEnabled(): Promise<boolean> {
  const capability = await checkBiometricCapability();
  if (!capability.isSupported || !capability.isEnrolled) return false;

  const credentials = await SecureStore.getItemAsync('biometric_credentials');
  return !!credentials;
}
```

## API Client with Token Management

```typescript
import { authStorage } from './authStorage';

interface ApiClientConfig {
  baseUrl: string;
  onTokenRefresh?: (tokens: AuthTokens) => void;
  onAuthError?: () => void;
}

class ApiClient {
  private baseUrl: string;
  private isRefreshing = false;
  private refreshPromise: Promise<AuthTokens | null> | null = null;
  private onTokenRefresh?: (tokens: AuthTokens) => void;
  private onAuthError?: () => void;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.onTokenRefresh = config.onTokenRefresh;
    this.onAuthError = config.onAuthError;
  }

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const accessToken = await authStorage.getAccessToken();

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options.headers,
      },
    });

    // Handle 401 - try to refresh token
    if (response.status === 401) {
      const newTokens = await this.refreshTokensIfNeeded();
      if (newTokens) {
        // Retry with new token
        return this.fetch(endpoint, options);
      } else {
        this.onAuthError?.();
        throw new Error('Authentication failed');
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  private async refreshTokensIfNeeded(): Promise<AuthTokens | null> {
    // Prevent multiple simultaneous refresh attempts
    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.doRefreshTokens();

    try {
      return await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async doRefreshTokens(): Promise<AuthTokens | null> {
    const refreshToken = await authStorage.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) return null;

      const tokens: AuthTokens = await response.json();
      await authStorage.saveTokens(tokens);
      this.onTokenRefresh?.(tokens);

      return tokens;
    } catch {
      return null;
    }
  }

  // Convenience methods
  async get<T>(endpoint: string): Promise<T> {
    return this.fetch(endpoint);
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.fetch(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient({
  baseUrl: 'https://api.example.com',
  onAuthError: () => {
    // Navigate to login
  },
});
```

## Auth Context and Hook

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { authStorage } from './authStorage';
import { apiClient } from './apiClient';

interface AuthState {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: User | null;
  biometricEnabled: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  loginWithBiometrics: () => Promise<boolean>;
  logout: () => Promise<void>;
  enableBiometricLogin: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    isLoading: true,
    isAuthenticated: false,
    user: null,
    biometricEnabled: false,
  });

  // Check auth state on mount
  useEffect(() => {
    checkAuthState();
  }, []);

  async function checkAuthState() {
    const [user, biometricEnabled] = await Promise.all([
      authStorage.getUser(),
      isBiometricLoginEnabled(),
    ]);

    setState({
      isLoading: false,
      isAuthenticated: !!user,
      user,
      biometricEnabled,
    });
  }

  async function login(email: string, password: string) {
    const response = await apiClient.post<{
      tokens: AuthTokens;
      user: User;
    }>('/auth/login', { email, password });

    await authStorage.saveTokens(response.tokens);
    await authStorage.saveUser(response.user);

    setState(prev => ({
      ...prev,
      isAuthenticated: true,
      user: response.user,
    }));
  }

  async function loginWithBiometricsHandler(): Promise<boolean> {
    const tokens = await loginWithBiometrics();
    if (!tokens) return false;

    const user = await apiClient.get<User>('/auth/me');
    await authStorage.saveUser(user);

    setState(prev => ({
      ...prev,
      isAuthenticated: true,
      user,
    }));

    return true;
  }

  async function logout() {
    try {
      await apiClient.post('/auth/logout', {});
    } catch {
      // Ignore errors during logout
    }

    await authStorage.clear();

    setState({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      biometricEnabled: false,
    });
  }

  async function enableBiometricLoginHandler(): Promise<boolean> {
    const refreshToken = await authStorage.getRefreshToken();
    const user = state.user;

    if (!refreshToken || !user) return false;

    const success = await enableBiometricLogin(user.email, refreshToken);
    if (success) {
      setState(prev => ({ ...prev, biometricEnabled: true }));
    }

    return success;
  }

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        loginWithBiometrics: loginWithBiometricsHandler,
        logout,
        enableBiometricLogin: enableBiometricLoginHandler,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## Login Screen Example

```typescript
import { useState } from 'react';
import { View, TextInput, Button, Text, TouchableOpacity } from 'react-native';
import { useAuth } from './AuthContext';
import { Ionicons } from '@expo/vector-icons';

export function LoginScreen() {
  const { login, loginWithBiometrics, biometricEnabled, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function handleLogin() {
    try {
      setError('');
      await login(email, password);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleBiometricLogin() {
    try {
      setError('');
      const success = await loginWithBiometrics();
      if (!success) {
        setError('Biometric authentication failed');
      }
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <View style={{ padding: 20 }}>
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      
      {error && <Text style={{ color: 'red' }}>{error}</Text>}
      
      <Button title="Login" onPress={handleLogin} disabled={isLoading} />
      
      {biometricEnabled && (
        <TouchableOpacity onPress={handleBiometricLogin}>
          <Ionicons name="finger-print" size={48} />
          <Text>Login with biometrics</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
```

## Security Best Practices

1. **Use SecureStore** for all sensitive data
2. **Never log tokens** or sensitive data
3. **Clear auth data** on logout
4. **Handle app background** - re-verify on resume
5. **Implement token refresh** proactively
6. **Use biometrics** as second factor, not replacement
7. **Validate server certificate** (certificate pinning for high security)
8. **Detect rooted/jailbroken** devices for sensitive apps
