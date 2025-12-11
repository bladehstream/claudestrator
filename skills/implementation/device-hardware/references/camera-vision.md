# Camera & Vision

## expo-camera (Recommended for Most Use Cases)

Works in Expo Go. Provides camera preview, photo/video capture, and built-in barcode scanning.

### Installation

```bash
npx expo install expo-camera
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "expo-camera",
        {
          "cameraPermission": "Allow $(PRODUCT_NAME) to access camera for scanning documents",
          "microphonePermission": "Allow $(PRODUCT_NAME) to record audio",
          "recordAudioAndroid": true
        }
      ]
    ]
  }
}
```

### Basic Camera with Photo Capture

```typescript
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRef, useState } from 'react';
import { Button, View, Image } from 'react-native';

export function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<'front' | 'back'>('back');
  const [photo, setPhoto] = useState<string | null>(null);
  const cameraRef = useRef<CameraView>(null);

  if (!permission) return <View />;
  
  if (!permission.granted) {
    return (
      <View>
        <Button title="Grant Camera Permission" onPress={requestPermission} />
      </View>
    );
  }

  const takePhoto = async () => {
    if (cameraRef.current) {
      const result = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: false,
        exif: true,
      });
      setPhoto(result.uri);
    }
  };

  const toggleFacing = () => {
    setFacing(current => current === 'back' ? 'front' : 'back');
  };

  if (photo) {
    return (
      <View style={{ flex: 1 }}>
        <Image source={{ uri: photo }} style={{ flex: 1 }} />
        <Button title="Retake" onPress={() => setPhoto(null)} />
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing={facing}
        flash="auto"
      >
        <View style={{ flex: 1, justifyContent: 'flex-end', padding: 20 }}>
          <Button title="Take Photo" onPress={takePhoto} />
          <Button title="Flip Camera" onPress={toggleFacing} />
        </View>
      </CameraView>
    </View>
  );
}
```

### Video Recording

```typescript
const [isRecording, setIsRecording] = useState(false);

const startRecording = async () => {
  if (cameraRef.current) {
    setIsRecording(true);
    const video = await cameraRef.current.recordAsync({
      maxDuration: 60, // seconds
      maxFileSize: 100 * 1024 * 1024, // 100MB
      mute: false,
    });
    setIsRecording(false);
    console.log('Video URI:', video.uri);
  }
};

const stopRecording = () => {
  if (cameraRef.current && isRecording) {
    cameraRef.current.stopRecording();
  }
};
```

### Torch/Flashlight

```typescript
const [torch, setTorch] = useState(false);

<CameraView
  enableTorch={torch}
  // ...
/>

<Button title="Toggle Flash" onPress={() => setTorch(!torch)} />
```

---

## Barcode & QR Scanning with expo-camera

Built into expo-camera. Uses Google ML Kit on Android, DataScannerViewController on iOS 16+.

### Basic Barcode Scanner

```typescript
import { CameraView, useCameraPermissions, BarcodeScanningResult } from 'expo-camera';
import { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function BarcodeScanner() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [data, setData] = useState<string>('');

  const handleBarcodeScanned = (result: BarcodeScanningResult) => {
    if (!scanned) {
      setScanned(true);
      setData(result.data);
      console.log('Type:', result.type, 'Data:', result.data);
    }
  };

  if (!permission?.granted) {
    return <Button title="Grant Permission" onPress={requestPermission} />;
  }

  return (
    <View style={{ flex: 1 }}>
      <CameraView
        style={{ flex: 1 }}
        barcodeScannerSettings={{
          barcodeTypes: ['qr', 'ean13', 'ean8', 'code128', 'code39', 'pdf417'],
        }}
        onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
      />
      {scanned && (
        <View style={styles.overlay}>
          <Text>Scanned: {data}</Text>
          <Button title="Scan Again" onPress={() => setScanned(false)} />
        </View>
      )}
    </View>
  );
}
```

### Supported Barcode Types

| Type | Description |
|------|-------------|
| `qr` | QR Code |
| `aztec` | Aztec |
| `ean13` | EAN-13 (retail) |
| `ean8` | EAN-8 |
| `code39` | Code 39 |
| `code93` | Code 93 |
| `code128` | Code 128 |
| `codabar` | Codabar |
| `itf14` | ITF-14 |
| `upc_a` | UPC-A |
| `upc_e` | UPC-E |
| `pdf417` | PDF417 |
| `datamatrix` | Data Matrix |

### Scanning Region (Viewfinder)

```typescript
<CameraView
  barcodeScannerSettings={{
    barcodeTypes: ['qr'],
    // Limit scanning to center region (normalized 0-1)
    scanningArea: {
      x: 0.2,
      y: 0.3,
      width: 0.6,
      height: 0.4,
    },
  }}
/>
```

---

## react-native-vision-camera (Advanced Use Cases)

More powerful but requires development build. Use for frame processors, ML integration, or advanced camera controls.

### Installation

```bash
npm install react-native-vision-camera
npx expo prebuild --clean
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "react-native-vision-camera",
        {
          "cameraPermissionText": "$(PRODUCT_NAME) needs camera access",
          "enableMicrophonePermission": true,
          "microphonePermissionText": "$(PRODUCT_NAME) needs microphone access"
        }
      ]
    ]
  }
}
```

### Basic Usage

```typescript
import { Camera, useCameraDevice, useCameraPermission } from 'react-native-vision-camera';
import { useRef } from 'react';

export function VisionCameraScreen() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');
  const camera = useRef<Camera>(null);

  if (!hasPermission) {
    return <Button title="Grant Permission" onPress={requestPermission} />;
  }

  if (!device) {
    return <Text>No camera device</Text>;
  }

  const takePhoto = async () => {
    const photo = await camera.current?.takePhoto({
      qualityPrioritization: 'quality',
      flash: 'auto',
      enableShutterSound: true,
    });
    console.log(photo?.path);
  };

  return (
    <View style={{ flex: 1 }}>
      <Camera
        ref={camera}
        style={{ flex: 1 }}
        device={device}
        isActive={true}
        photo={true}
      />
      <Button title="Capture" onPress={takePhoto} />
    </View>
  );
}
```

### Frame Processors (for ML/OCR)

Frame processors run on every frame for real-time analysis:

```typescript
import { useFrameProcessor } from 'react-native-vision-camera';
import { useRunOnJS } from 'react-native-worklets-core';

// Install worklets package
// npm install react-native-worklets-core

const MyCamera = () => {
  const handleDetection = (text: string) => {
    console.log('Detected:', text);
  };

  const runOnJS = useRunOnJS(handleDetection);

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    // Process frame here (runs on separate thread)
    // Typically call ML Kit or other vision library
    // runOnJS(result);
  }, []);

  return (
    <Camera
      frameProcessor={frameProcessor}
      // ...
    />
  );
};
```

---

## expo-image-picker

For selecting photos/videos from gallery or taking new ones via system UI.

### Installation

```bash
npx expo install expo-image-picker
```

### Usage

```typescript
import * as ImagePicker from 'expo-image-picker';

// Pick from gallery
const pickImage = async () => {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsEditing: true,
    aspect: [4, 3],
    quality: 0.8,
  });

  if (!result.canceled) {
    console.log(result.assets[0].uri);
  }
};

// Take photo with system camera
const takePhoto = async () => {
  const { status } = await ImagePicker.requestCameraPermissionsAsync();
  if (status !== 'granted') return;

  const result = await ImagePicker.launchCameraAsync({
    allowsEditing: true,
    quality: 0.8,
  });

  if (!result.canceled) {
    console.log(result.assets[0].uri);
  }
};

// Pick multiple images
const pickMultiple = async () => {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsMultipleSelection: true,
    selectionLimit: 10,
  });

  if (!result.canceled) {
    result.assets.forEach(asset => console.log(asset.uri));
  }
};
```

---

## Platform Comparison

| Feature | expo-camera | vision-camera |
|---------|-------------|---------------|
| Expo Go | ✅ | ❌ |
| Photo capture | ✅ | ✅ |
| Video recording | ✅ | ✅ |
| Barcode scanning | ✅ Built-in | Via plugins |
| Frame processors | ❌ | ✅ |
| Manual focus/exposure | Limited | ✅ |
| Multiple cameras | ❌ | ✅ |
| 60fps video | ❌ | ✅ |
| RAW capture | ❌ | ✅ |

**Recommendation**: Start with `expo-camera`. Switch to `react-native-vision-camera` only if you need frame processors or advanced camera controls.
