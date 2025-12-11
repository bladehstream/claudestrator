# Permissions Matrix

Complete reference for iOS and Android permissions required by hardware features.

## Quick Reference

| Feature | iOS Permission | Android Permission | Runtime Request |
|---------|---------------|-------------------|-----------------|
| Camera | Camera | CAMERA | Yes |
| Microphone | Microphone | RECORD_AUDIO | Yes |
| Location (foreground) | When In Use | ACCESS_FINE_LOCATION | Yes |
| Location (background) | Always | ACCESS_BACKGROUND_LOCATION | Yes |
| Contacts | Contacts | READ_CONTACTS | Yes |
| Calendar | Calendars | READ_CALENDAR, WRITE_CALENDAR | Yes |
| Photos | Photo Library | READ_MEDIA_IMAGES | Yes |
| Bluetooth | Bluetooth | BLUETOOTH_SCAN, BLUETOOTH_CONNECT | Yes (Android 12+) |
| NFC | NFC Tag Reading | NFC | No (manifest only) |
| Biometrics | Face ID | USE_BIOMETRIC | No (auto-prompted) |
| Motion sensors | Motion & Fitness | - | iOS only |
| Haptics | - | VIBRATE | No |

---

## iOS Permissions (Info.plist)

### Camera & Media

```xml
<!-- Camera -->
<key>NSCameraUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to take photos and scan documents</string>

<!-- Microphone -->
<key>NSMicrophoneUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to record audio</string>

<!-- Photo Library (read) -->
<key>NSPhotoLibraryUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your photos</string>

<!-- Photo Library (write) -->
<key>NSPhotoLibraryAddUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to save photos</string>
```

### Location

```xml
<!-- Foreground only -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your location</string>

<!-- Background location -->
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your location in the background</string>

<!-- Legacy (iOS 10 and earlier) -->
<key>NSLocationAlwaysUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to always access your location</string>

<!-- Background modes for location -->
<key>UIBackgroundModes</key>
<array>
  <string>location</string>
</array>
```

### Biometrics

```xml
<!-- Face ID -->
<key>NSFaceIDUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to use Face ID for authentication</string>
```

### Motion & Sensors

```xml
<!-- Motion sensors (required iOS 13+) -->
<key>NSMotionUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access motion data</string>
```

### Bluetooth

```xml
<!-- Bluetooth -->
<key>NSBluetoothAlwaysUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to connect to Bluetooth devices</string>

<!-- Legacy (iOS 12 and earlier) -->
<key>NSBluetoothPeripheralUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to connect to Bluetooth devices</string>

<!-- Background Bluetooth -->
<key>UIBackgroundModes</key>
<array>
  <string>bluetooth-central</string>
  <string>bluetooth-peripheral</string>
</array>
```

### NFC

```xml
<!-- NFC Tag Reading -->
<key>NFCReaderUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to read NFC tags</string>

<!-- ISO7816 AIDs (for smart cards) -->
<key>com.apple.developer.nfc.readersession.iso7816.select-identifiers</key>
<array>
  <string>A0000002471001</string>
</array>

<!-- FeliCa system codes (Japan transit) -->
<key>com.apple.developer.nfc.readersession.felica.systemcodes</key>
<array>
  <string>88B4</string>
</array>
```

### Contacts & Calendar

```xml
<!-- Contacts -->
<key>NSContactsUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your contacts</string>

<!-- Calendar -->
<key>NSCalendarsUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your calendar</string>

<!-- Reminders -->
<key>NSRemindersUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to access your reminders</string>
```

### Speech Recognition

```xml
<!-- Speech Recognition -->
<key>NSSpeechRecognitionUsageDescription</key>
<string>Allow $(PRODUCT_NAME) to use speech recognition</string>
```

---

## Android Permissions (AndroidManifest.xml)

### Camera & Media

```xml
<!-- Camera -->
<uses-permission android:name="android.permission.CAMERA" />

<!-- Microphone -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />

<!-- Storage (Android 12 and below) -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="32" />

<!-- Media (Android 13+) -->
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
<uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
<uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
```

### Location

```xml
<!-- Coarse location (city-level) -->
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<!-- Fine location (GPS) -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

<!-- Background location (Android 10+) -->
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />

<!-- Foreground service for background location -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
```

### Bluetooth

```xml
<!-- Bluetooth (Android 11 and below) -->
<uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />

<!-- Bluetooth (Android 12+) -->
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />

<!-- Note: Remove neverForLocation flag if you use BLE for location beacons -->
```

### NFC

```xml
<!-- NFC -->
<uses-permission android:name="android.permission.NFC" />

<!-- Require NFC hardware -->
<uses-feature android:name="android.hardware.nfc" android:required="true" />

<!-- Or make optional -->
<uses-feature android:name="android.hardware.nfc" android:required="false" />
```

### Sensors

```xml
<!-- Body sensors (heart rate, etc.) -->
<uses-permission android:name="android.permission.BODY_SENSORS" />

<!-- High sampling rate sensors (Android 12+, >200Hz) -->
<uses-permission android:name="android.permission.HIGH_SAMPLING_RATE_SENSORS" />

<!-- Activity recognition (step counter) -->
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />
```

### Other

```xml
<!-- Vibration/Haptics -->
<uses-permission android:name="android.permission.VIBRATE" />

<!-- System brightness -->
<uses-permission android:name="android.permission.WRITE_SETTINGS" />

<!-- Contacts -->
<uses-permission android:name="android.permission.READ_CONTACTS" />
<uses-permission android:name="android.permission.WRITE_CONTACTS" />

<!-- Calendar -->
<uses-permission android:name="android.permission.READ_CALENDAR" />
<uses-permission android:name="android.permission.WRITE_CALENDAR" />

<!-- Phone state (for call detection) -->
<uses-permission android:name="android.permission.READ_PHONE_STATE" />

<!-- Internet -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

---

## Expo Config Plugin Format

### app.json Example

```json
{
  "expo": {
    "plugins": [
      [
        "expo-camera",
        {
          "cameraPermission": "Allow $(PRODUCT_NAME) to access camera",
          "microphonePermission": "Allow $(PRODUCT_NAME) to record audio",
          "recordAudioAndroid": true
        }
      ],
      [
        "expo-location",
        {
          "locationAlwaysAndWhenInUsePermission": "Allow $(PRODUCT_NAME) to use location",
          "isAndroidBackgroundLocationEnabled": true,
          "isAndroidForegroundServiceEnabled": true
        }
      ],
      [
        "expo-local-authentication",
        {
          "faceIDPermission": "Allow $(PRODUCT_NAME) to use Face ID"
        }
      ],
      "expo-sensors",
      [
        "react-native-ble-plx",
        {
          "isBackgroundEnabled": true,
          "modes": ["peripheral", "central"],
          "bluetoothAlwaysPermission": "Allow $(PRODUCT_NAME) to use Bluetooth"
        }
      ],
      [
        "react-native-nfc-manager",
        {
          "nfcPermission": "Allow $(PRODUCT_NAME) to read NFC tags",
          "selectIdentifiers": ["A0000002471001"]
        }
      ],
      [
        "@jamsch/expo-speech-recognition",
        {
          "microphonePermission": "Allow $(PRODUCT_NAME) to use microphone",
          "speechRecognitionPermission": "Allow $(PRODUCT_NAME) to recognize speech"
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "UIBackgroundModes": ["location", "bluetooth-central"]
      }
    },
    "android": {
      "permissions": [
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        "android.permission.BLUETOOTH_SCAN",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.NFC",
        "android.permission.VIBRATE",
        "android.permission.HIGH_SAMPLING_RATE_SENSORS"
      ]
    }
  }
}
```

---

## Runtime Permission Requests

### Expo Pattern

```typescript
import * as Camera from 'expo-camera';
import * as Location from 'expo-location';
import * as Contacts from 'expo-contacts';

// Camera
const { status } = await Camera.requestCameraPermissionsAsync();

// Location (foreground)
const { status } = await Location.requestForegroundPermissionsAsync();

// Location (background)
const { status } = await Location.requestBackgroundPermissionsAsync();

// Contacts
const { status } = await Contacts.requestPermissionsAsync();
```

### React Native Pattern (Android)

```typescript
import { PermissionsAndroid, Platform } from 'react-native';

const requestPermissions = async () => {
  if (Platform.OS !== 'android') return true;

  const permissions = [
    PermissionsAndroid.PERMISSIONS.CAMERA,
    PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
    PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
    PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
  ];

  const results = await PermissionsAndroid.requestMultiple(permissions);
  
  return Object.values(results).every(
    result => result === PermissionsAndroid.RESULTS.GRANTED
  );
};
```

---

## Permission Denied Handling

```typescript
import { Linking, Alert } from 'react-native';

const handlePermissionDenied = (permission: string) => {
  Alert.alert(
    'Permission Required',
    `${permission} permission is required for this feature. Please enable it in Settings.`,
    [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Open Settings', onPress: () => Linking.openSettings() },
    ]
  );
};
```

---

## Android Version-Specific Permissions

| Android Version | API | Permission Changes |
|-----------------|-----|-------------------|
| Android 13 | 33 | Granular media permissions (READ_MEDIA_*) |
| Android 12 | 31 | New Bluetooth permissions (BLUETOOTH_SCAN, CONNECT) |
| Android 11 | 30 | Scoped storage enforcement |
| Android 10 | 29 | ACCESS_BACKGROUND_LOCATION separate |
| Android 6 | 23 | Runtime permissions introduced |

---

## iOS Version-Specific Requirements

| iOS Version | Requirement |
|-------------|-------------|
| iOS 18.1+ | NFC payment capabilities in select countries |
| iOS 17+ | Privacy manifest required for certain APIs |
| iOS 16+ | DataScannerViewController for barcode scanning |
| iOS 15+ | Passkeys/WebAuthn support |
| iOS 14+ | Approximate location option |
| iOS 13+ | Background processing, motion permission required |
