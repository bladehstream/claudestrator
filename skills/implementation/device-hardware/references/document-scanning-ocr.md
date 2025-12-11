# Document Scanning & OCR

## Document Scanning with react-native-document-scanner-plugin

Provides edge detection, perspective correction, and automatic cropping for documents, receipts, IDs.

### Installation

```bash
npm install react-native-document-scanner-plugin
npx expo prebuild --clean
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "react-native-document-scanner-plugin",
        {
          "cameraPermission": "Allow $(PRODUCT_NAME) to scan documents"
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "NSCameraUsageDescription": "Allow $(PRODUCT_NAME) to scan documents"
      }
    }
  }
}
```

### Basic Document Scanner

```typescript
import DocumentScanner from 'react-native-document-scanner-plugin';
import { useState } from 'react';
import { Button, Image, View } from 'react-native';

export function DocumentScannerScreen() {
  const [scannedImage, setScannedImage] = useState<string | null>(null);

  const scanDocument = async () => {
    try {
      const result = await DocumentScanner.scanDocument({
        letUserAdjustCrop: true,     // Allow manual corner adjustment
        maxNumDocuments: 1,           // Single document mode
        responseType: 'imageFilePath', // or 'base64'
      });

      if (result.scannedImages && result.scannedImages.length > 0) {
        setScannedImage(result.scannedImages[0]);
      }
    } catch (error) {
      console.error('Scan failed:', error);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {scannedImage ? (
        <>
          <Image source={{ uri: scannedImage }} style={{ flex: 1 }} resizeMode="contain" />
          <Button title="Scan Another" onPress={() => setScannedImage(null)} />
        </>
      ) : (
        <Button title="Scan Document" onPress={scanDocument} />
      )}
    </View>
  );
}
```

### Multi-Page Scanning

```typescript
const scanMultiplePages = async () => {
  const result = await DocumentScanner.scanDocument({
    letUserAdjustCrop: true,
    maxNumDocuments: 10, // Allow up to 10 pages
    responseType: 'imageFilePath',
  });

  if (result.scannedImages) {
    // Array of image paths
    result.scannedImages.forEach((imagePath, index) => {
      console.log(`Page ${index + 1}:`, imagePath);
    });
  }
};
```

### Scanner Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `letUserAdjustCrop` | boolean | true | Allow manual corner adjustment |
| `maxNumDocuments` | number | unlimited | Max pages to scan |
| `responseType` | string | 'imageFilePath' | 'imageFilePath' or 'base64' |

---

## OCR Options

### Option 1: Google Cloud Vision API (Recommended for Expo Go)

Works without native dependencies. Requires Google Cloud API key.

```typescript
const extractTextWithGoogleVision = async (imageUri: string): Promise<string> => {
  // Convert image to base64
  const response = await fetch(imageUri);
  const blob = await response.blob();
  const base64 = await blobToBase64(blob);

  const apiKey = 'YOUR_GOOGLE_CLOUD_API_KEY';
  const apiUrl = `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`;

  const requestBody = {
    requests: [{
      image: { content: base64 },
      features: [{ type: 'TEXT_DETECTION', maxResults: 1 }],
    }],
  };

  const result = await fetch(apiUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

  const data = await result.json();
  return data.responses[0]?.fullTextAnnotation?.text || '';
};

// Helper function
const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = (reader.result as string).split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};
```

### Option 2: ML Kit via Vision Camera Frame Processors (On-Device)

Requires development build. Runs entirely on-device.

```bash
npm install react-native-vision-camera
npm install react-native-mlkit-ocr
npx expo prebuild --clean
```

```typescript
import { Camera, useFrameProcessor } from 'react-native-vision-camera';
import { scanOCR } from 'react-native-mlkit-ocr';

const OCRCamera = () => {
  const [text, setText] = useState('');

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    const result = scanOCR(frame);
    if (result.text) {
      runOnJS(setText)(result.text);
    }
  }, []);

  return (
    <View style={{ flex: 1 }}>
      <Camera
        style={{ flex: 1 }}
        device={device}
        isActive={true}
        frameProcessor={frameProcessor}
      />
      <Text>{text}</Text>
    </View>
  );
};
```

### Option 3: Tesseract.js in WebView (Offline, No Native)

Works in Expo Go. Slower but fully offline.

```typescript
import { WebView } from 'react-native-webview';
import { useRef, useState } from 'react';
import * as FileSystem from 'expo-file-system';

export function TesseractOCR({ imageUri }: { imageUri: string }) {
  const webViewRef = useRef<WebView>(null);
  const [extractedText, setExtractedText] = useState('');

  const runOCR = async () => {
    const base64 = await FileSystem.readAsStringAsync(imageUri, {
      encoding: FileSystem.EncodingType.Base64,
    });
    
    webViewRef.current?.injectJavaScript(`
      (async () => {
        const { createWorker } = Tesseract;
        const worker = await createWorker('eng');
        const { data: { text } } = await worker.recognize('data:image/jpeg;base64,${base64}');
        await worker.terminate();
        window.ReactNativeWebView.postMessage(JSON.stringify({ text }));
      })();
    `);
  };

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js"></script>
    </head>
    <body></body>
    </html>
  `;

  return (
    <View style={{ flex: 1 }}>
      <WebView
        ref={webViewRef}
        source={{ html }}
        onMessage={(event) => {
          const { text } = JSON.parse(event.nativeEvent.data);
          setExtractedText(text);
        }}
        style={{ height: 0 }}
      />
      <Button title="Extract Text" onPress={runOCR} />
      <Text>{extractedText}</Text>
    </View>
  );
}
```

---

## OCR Comparison

| Solution | Expo Go | Offline | Speed | Accuracy | Cost |
|----------|---------|---------|-------|----------|------|
| Google Vision API | ✅ | ❌ | Fast | Excellent | Per-request |
| ML Kit (vision-camera) | ❌ | ✅ | Fast | Excellent | Free |
| Tesseract.js WebView | ✅ | ✅ | Slow | Good | Free |
| Commercial (Scanbot) | ❌ | ✅ | Fast | Excellent | License |

**Recommendation**:
- Prototyping in Expo Go → Google Vision API
- Production with dev build → ML Kit
- Must be offline + Expo Go → Tesseract.js (accept slower speed)

---

## Complete Document Scanning Flow

```typescript
import DocumentScanner from 'react-native-document-scanner-plugin';

interface ScannedDocument {
  imagePath: string;
  extractedText: string;
}

export const scanAndExtractText = async (): Promise<ScannedDocument | null> => {
  // Step 1: Scan document
  const scanResult = await DocumentScanner.scanDocument({
    letUserAdjustCrop: true,
    maxNumDocuments: 1,
    responseType: 'imageFilePath',
  });

  if (!scanResult.scannedImages?.length) {
    return null;
  }

  const imagePath = scanResult.scannedImages[0];

  // Step 2: Extract text via OCR
  const extractedText = await extractTextWithGoogleVision(imagePath);

  return {
    imagePath,
    extractedText,
  };
};
```

---

## MRZ/Passport Scanning

For Machine Readable Zone (MRZ) on passports and ID cards:

### Using regex on OCR output

```typescript
const extractMRZ = (ocrText: string) => {
  // MRZ lines are typically 44 chars (TD1), 36 chars (TD2), or 30 chars (TD3)
  const lines = ocrText.split('\n').filter(line => 
    /^[A-Z0-9<]{30,44}$/.test(line.replace(/\s/g, ''))
  );
  
  if (lines.length >= 2) {
    return {
      line1: lines[0],
      line2: lines[1],
      line3: lines[2] || null,
    };
  }
  return null;
};

// Parse MRZ data
const parseMRZ = (mrz: { line1: string; line2: string }) => {
  // TD3 format (passports): 44 chars per line
  const documentType = mrz.line1.substring(0, 2);
  const country = mrz.line1.substring(2, 5);
  const surname = mrz.line1.substring(5).split('<<')[0].replace(/</g, ' ').trim();
  const givenNames = mrz.line1.substring(5).split('<<')[1]?.replace(/</g, ' ').trim();
  
  const passportNumber = mrz.line2.substring(0, 9).replace(/</g, '');
  const nationality = mrz.line2.substring(10, 13);
  const dateOfBirth = mrz.line2.substring(13, 19); // YYMMDD
  const sex = mrz.line2.substring(20, 21);
  const expiryDate = mrz.line2.substring(21, 27); // YYMMDD

  return {
    documentType,
    country,
    surname,
    givenNames,
    passportNumber,
    nationality,
    dateOfBirth,
    sex,
    expiryDate,
  };
};
```

### Commercial MRZ Solutions

For production ID verification, consider:
- **Dynamsoft** - Comprehensive SDK with high accuracy
- **Regula** - Document verification specialist
- **Jumio/Onfido** - Full identity verification platforms
