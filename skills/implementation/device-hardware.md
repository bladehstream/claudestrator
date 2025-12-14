---
name: device-hardware
id: device_hardware
version: 1.0
category: implementation
description: Comprehensive guide for React Native/Expo hardware integration including biometrics (Face ID, Touch ID, fingerprint), FIDO2/Passkeys (YubiKey, security keys), camera (photos, video, barcode/QR scanning), document scanning with OCR, NFC tag reading/writing, Bluetooth Low Energy (BLE), sensors (accelerometer, gyroscope, magnetometer, barometer), haptic feedback, audio recording, speech recognition, GPS/location tracking, and secure storage. Use when building mobile apps that need device hardware access, authentication features, scanning capabilities, or sensor data.
domain:
  - react-native
  - expo
  - mobile
  - hardware
  - fintech
task_types:
  - implementation
  - feature
keywords:
  - biometrics
  - face id
  - touch id
  - fingerprint
  - fido2
  - passkeys
  - yubikey
  - security key
  - camera
  - barcode
  - qr code
  - document scanning
  - ocr
  - nfc
  - bluetooth
  - ble
  - sensors
  - accelerometer
  - gyroscope
  - haptics
  - audio
  - speech recognition
  - gps
  - location
  - secure storage
  - expo-local-authentication
  - expo-camera
  - expo-sensors
  - expo-haptics
  - expo-location
  - react-native-ble-plx
  - react-native-nfc-manager
complexity: [normal]
pairs_with:
  - software_security
  - frontend_design
source: device-hardware.skill (local)
---

# Device Hardware Integration for React Native/Expo

This skill provides patterns for integrating device hardware in React Native/Expo apps.

## Quick Reference: Library Selection

### Authentication
| Need | Library | Expo Go | Dev Build |
|------|---------|---------|-----------|
| Biometrics (Touch ID, Face ID, fingerprint) | `expo-local-authentication` | Partial | Yes |
| FIDO2/Passkeys/Security Keys | `react-native-passkey` | No | Yes |
| Secure credential storage | `expo-secure-store` | Yes | Yes |

### Camera & Scanning
| Need | Library | Expo Go | Dev Build |
|------|---------|---------|-----------|
| Basic camera/photos | `expo-camera` | Yes | Yes |
| QR/Barcode scanning | `expo-camera` | Yes | Yes |
| Document scanning | `react-native-document-scanner-plugin` | No | Yes |
| Advanced frame processing | `react-native-vision-camera` | No | Yes |

### Connectivity
| Need | Library | Expo Go | Dev Build |
|------|---------|---------|-----------|
| NFC tags | `react-native-nfc-manager` | No | Yes |
| Bluetooth Low Energy | `react-native-ble-plx` | No | Yes |
| GPS/Location | `expo-location` | Yes | Yes |
| Background location | `expo-location` + `expo-task-manager` | No | Yes |

### Sensors & Feedback
| Need | Library | Expo Go | Dev Build |
|------|---------|---------|-----------|
| Motion sensors | `expo-sensors` | Yes | Yes |
| Haptic feedback | `expo-haptics` | Yes | Yes |
| Audio recording | `expo-audio` | Yes | Yes |
| Speech recognition | `@jamsch/expo-speech-recognition` | No | Yes |

## Workflow: Adding Hardware Features

### Step 1: Determine Build Requirements

```
Need NFC, BLE, FIDO2, Document Scanning, or Speech Recognition?
  -> YES: Use Development Build (npx expo prebuild)
  -> NO: Can use Expo Go for prototyping

Need Face ID on iOS?
  -> YES: Use Development Build
  -> NO: Touch ID works in Expo Go
```

### Step 2: Install and Configure

```bash
# Install library
npx expo install <library-name>

# Add config plugin to app.json (if required)
{
  "expo": {
    "plugins": ["<library-name>"]
  }
}

# Rebuild native code
npx expo prebuild --clean
npx expo run:ios  # or run:android
```

### Step 3: Handle Permissions

Always check and request permissions before accessing hardware:

```typescript
// Pattern: Permission handling
const [permission, requestPermission] = useXxxPermissions();

useEffect(() => {
  if (!permission?.granted) {
    requestPermission();
  }
}, []);

// Handle denial gracefully
if (!permission?.granted) {
  return <PermissionDeniedView onRetry={requestPermission} />;
}
```

## Platform Differences Summary

| Feature | iOS | Android | Notes |
|---------|-----|---------|-------|
| Face ID | Yes (Dev build only) | Yes | iOS requires `NSFaceIDUsageDescription` |
| NFC Write | Yes (iPhone 7+) | Yes | |
| NFC Card Emulation (HCE) | No (Never) | Yes | Apple blocks this |
| Background Location | Yes | Yes | Both need special permissions |
| Light Sensor | No | Yes | Android only |
| Security Key choice | Yes (Can force) | System UI | Android doesn't let app force security key |

## Reference Files

Detailed implementation guides organized by feature:

- **[references/authentication.md](device-hardware/references/authentication.md)**: Biometrics, PIN, FIDO2/Passkeys, YubiKey integration
- **[references/camera-vision.md](device-hardware/references/camera-vision.md)**: Camera, photo/video capture, barcode/QR scanning
- **[references/document-scanning-ocr.md](device-hardware/references/document-scanning-ocr.md)**: Document scanner, OCR text extraction
- **[references/nfc.md](device-hardware/references/nfc.md)**: NFC tag reading/writing, NDEF, platform limitations
- **[references/bluetooth.md](device-hardware/references/bluetooth.md)**: BLE scanning, connecting, read/write characteristics
- **[references/sensors.md](device-hardware/references/sensors.md)**: Accelerometer, gyroscope, magnetometer, barometer, pedometer
- **[references/audio-speech.md](device-hardware/references/audio-speech.md)**: Audio recording, playback, speech recognition, TTS
- **[references/haptics.md](device-hardware/references/haptics.md)**: Haptic feedback patterns
- **[references/location.md](device-hardware/references/location.md)**: GPS, background tracking, geofencing
- **[references/secure-storage.md](device-hardware/references/secure-storage.md)**: Keychain/Keystore, encrypted storage
- **[references/permissions.md](device-hardware/references/permissions.md)**: Complete permission matrix for iOS and Android

## Common Patterns

### Error Handling for Hardware

```typescript
const useHardwareFeature = () => {
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkAvailability = async () => {
      try {
        const available = await SomeHardware.isAvailableAsync();
        setIsAvailable(available);
        if (!available) {
          setError('This feature is not available on your device');
        }
      } catch (e) {
        setError('Failed to check hardware availability');
        setIsAvailable(false);
      }
    };
    checkAvailability();
  }, []);

  return { isAvailable, error };
};
```

### Cleanup Pattern for Subscriptions

```typescript
useEffect(() => {
  let subscription: Subscription | null = null;

  const startListening = async () => {
    subscription = SomeSensor.addListener((data) => {
      // Handle data
    });
  };

  startListening();

  return () => {
    subscription?.remove();
  };
}, []);
```

### Platform-Specific Implementation

```typescript
import { Platform } from 'react-native';

const handleFeature = async () => {
  if (Platform.OS === 'ios') {
    // iOS-specific implementation
  } else if (Platform.OS === 'android') {
    // Android-specific implementation
  }
};
```

## FinTech-Specific Considerations

For payment and financial apps:

1. **Authentication**: Combine biometrics with PIN fallback for accessibility
2. **FIDO2**: Use `react-native-passkey` for phishing-resistant auth
3. **Secure Storage**: Always use `expo-secure-store` for tokens/credentials
4. **NFC**: Can read loyalty cards and badges; payment card reading requires PCI-DSS compliance
5. **Document Scanning**: Useful for ID verification, receipt capture

## Troubleshooting

### "Module not found" after install
-> Run `npx expo prebuild --clean` and rebuild

### Permission denied on iOS
-> Check Info.plist has required usage descriptions

### NFC not detecting on iOS
-> Ensure app is in foreground; iOS NFC only works in foreground

### Biometrics not working in Expo Go
-> Face ID requires development build; use `npx expo run:ios`

### BLE scan returns no devices
-> Check location permission (required on Android for BLE scanning)
