# NFC (Near Field Communication)

## react-native-nfc-manager

The standard library for NFC in React Native. Requires development build.

### Installation

```bash
npm install react-native-nfc-manager
npx expo prebuild --clean
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "react-native-nfc-manager",
        {
          "nfcPermission": "Allow $(PRODUCT_NAME) to read NFC tags",
          "selectIdentifiers": ["A0000002471001"],
          "systemCodes": ["88B4"]
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "NFCReaderUsageDescription": "Allow $(PRODUCT_NAME) to read NFC tags",
        "com.apple.developer.nfc.readersession.iso7816.select-identifiers": ["A0000002471001"],
        "com.apple.developer.nfc.readersession.felica.systemcodes": ["88B4"]
      }
    },
    "android": {
      "permissions": ["android.permission.NFC"]
    }
  }
}
```

### Initialize NFC Manager

```typescript
import NfcManager, { NfcTech, Ndef } from 'react-native-nfc-manager';
import { useEffect, useState } from 'react';

export function useNFC() {
  const [isSupported, setIsSupported] = useState(false);
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    const init = async () => {
      const supported = await NfcManager.isSupported();
      setIsSupported(supported);
      
      if (supported) {
        await NfcManager.start();
        const enabled = await NfcManager.isEnabled();
        setIsEnabled(enabled);
      }
    };
    
    init();
    
    return () => {
      NfcManager.cancelTechnologyRequest().catch(() => {});
    };
  }, []);

  return { isSupported, isEnabled };
}
```

### Read NDEF Tag

```typescript
const readNdefTag = async (): Promise<string | null> => {
  try {
    // Request NFC technology
    await NfcManager.requestTechnology(NfcTech.Ndef);
    
    // Get tag info
    const tag = await NfcManager.getTag();
    
    if (tag?.ndefMessage) {
      // Parse NDEF records
      const records = tag.ndefMessage.map(record => {
        if (record.tnf === Ndef.TNF_WELL_KNOWN) {
          if (Ndef.isType(record, Ndef.RTD_TEXT)) {
            return Ndef.text.decodePayload(record.payload as number[]);
          }
          if (Ndef.isType(record, Ndef.RTD_URI)) {
            return Ndef.uri.decodePayload(record.payload as number[]);
          }
        }
        return null;
      }).filter(Boolean);
      
      return records.join('\n');
    }
    
    return null;
  } catch (error) {
    console.error('NFC read error:', error);
    return null;
  } finally {
    NfcManager.cancelTechnologyRequest().catch(() => {});
  }
};
```

### Write NDEF Tag

```typescript
const writeNdefTag = async (text: string): Promise<boolean> => {
  try {
    await NfcManager.requestTechnology(NfcTech.Ndef);
    
    // Create NDEF message
    const bytes = Ndef.encodeMessage([
      Ndef.textRecord(text),
    ]);
    
    // Write to tag
    await NfcManager.ndefHandler.writeNdefMessage(bytes);
    
    return true;
  } catch (error) {
    console.error('NFC write error:', error);
    return false;
  } finally {
    NfcManager.cancelTechnologyRequest().catch(() => {});
  }
};

// Write URL
const writeUrlTag = async (url: string): Promise<boolean> => {
  try {
    await NfcManager.requestTechnology(NfcTech.Ndef);
    
    const bytes = Ndef.encodeMessage([
      Ndef.uriRecord(url),
    ]);
    
    await NfcManager.ndefHandler.writeNdefMessage(bytes);
    return true;
  } catch (error) {
    return false;
  } finally {
    NfcManager.cancelTechnologyRequest().catch(() => {});
  }
};
```

### Background Tag Reading (iOS)

iOS can detect NFC tags while app is backgrounded (iPhone XS and later).

```typescript
// Check if background reading is supported
const canBackground = await NfcManager.isBackgroundTagDetectionSupported();

// Register for background tag events
NfcManager.setEventListener('stateChange', (state) => {
  console.log('NFC state:', state); // 'on' | 'off' | 'turning_on' | 'turning_off'
});

// Handle tag detected in background
NfcManager.setEventListener('tagDiscovered', (tag) => {
  console.log('Background tag:', tag);
});
```

### Read MIFARE/ISO14443

```typescript
const readMifare = async () => {
  try {
    // For MIFARE Classic
    await NfcManager.requestTechnology(NfcTech.MifareClassic);
    
    // Authenticate sector (key A)
    const keyA = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]; // Default key
    await NfcManager.mifareClassicHandlerAndroid.mifareClassicAuthenticateA(0, keyA);
    
    // Read block 1
    const data = await NfcManager.mifareClassicHandlerAndroid.mifareClassicReadBlock(1);
    console.log('Block data:', data);
    
  } finally {
    NfcManager.cancelTechnologyRequest().catch(() => {});
  }
};
```

### ISO7816 Smart Cards

```typescript
const readSmartCard = async () => {
  try {
    await NfcManager.requestTechnology(NfcTech.IsoDep);
    
    // Select application by AID
    const selectCommand = [
      0x00, 0xA4, 0x04, 0x00, // SELECT command
      0x07, // Length of AID
      0xA0, 0x00, 0x00, 0x02, 0x47, 0x10, 0x01, // AID
    ];
    
    const response = await NfcManager.isoDepHandler.transceive(selectCommand);
    console.log('Response:', response);
    
  } finally {
    NfcManager.cancelTechnologyRequest().catch(() => {});
  }
};
```

---

## NFC Technologies Reference

| Technology | iOS | Android | Use Case |
|------------|-----|---------|----------|
| `Ndef` | ✅ | ✅ | Standard NFC tags |
| `NfcA` (ISO14443-3A) | ✅ | ✅ | MIFARE, NFC Forum Type 2 |
| `NfcB` (ISO14443-3B) | ✅ | ✅ | Calypso cards |
| `NfcF` (FeliCa) | ✅ | ✅ | Japan transit cards |
| `NfcV` (ISO15693) | ✅ | ✅ | Vicinity cards |
| `IsoDep` (ISO14443-4) | ⚠️ | ✅ | Smart cards, ~20s timeout on iOS |
| `MifareClassic` | ❌ | ✅ | Legacy access cards |
| `MifareUltralight` | ✅ | ✅ | NFC Forum Type 2 |

---

## Platform Limitations

### iOS Limitations

- **No Host Card Emulation (HCE)**: iOS cannot act as an NFC card
- **Foreground only**: NFC sessions require app to be in foreground
- **~20 second timeout**: ISO-DEP connections time out after ~20 seconds
- **Requires Apple Developer Program**: $99/year for NFC entitlements
- **Background reading**: Only iPhone XS and later, limited to NDEF tags

### Android Capabilities

- **Full HCE support**: Can emulate NFC cards
- **Background detection**: Can detect tags when app is backgrounded
- **No timeout issues**: Extended ISO-DEP sessions supported
- **MIFARE Classic**: Full support (not available on all devices)

---

## Host Card Emulation (Android Only)

Use `react-native-hce` to make Android device act as an NFC card.

```bash
npm install react-native-hce
```

```typescript
import HCESession from 'react-native-hce';

const startHCE = async () => {
  const session = await HCESession.start({
    content: {
      type: 'text',
      content: 'Hello from HCE',
    },
    writable: false,
  });
  
  // Listen for NFC reader
  session.on('read', () => {
    console.log('Card was read');
  });
  
  // Stop when done
  // await session.terminate();
};
```

---

## Common NFC Patterns

### NFC Tag Scanner Component

```typescript
import NfcManager, { NfcTech, Ndef } from 'react-native-nfc-manager';
import { useState, useEffect } from 'react';
import { View, Text, Button, ActivityIndicator } from 'react-native';

type ScanState = 'idle' | 'scanning' | 'success' | 'error';

export function NFCScanner() {
  const [state, setState] = useState<ScanState>('idle');
  const [data, setData] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    NfcManager.start();
    return () => {
      NfcManager.cancelTechnologyRequest().catch(() => {});
    };
  }, []);

  const scan = async () => {
    setState('scanning');
    setData('');
    setError('');

    try {
      await NfcManager.requestTechnology(NfcTech.Ndef);
      const tag = await NfcManager.getTag();
      
      if (tag?.ndefMessage) {
        const text = tag.ndefMessage
          .map(record => {
            if (Ndef.isType(record, Ndef.RTD_TEXT)) {
              return Ndef.text.decodePayload(record.payload as number[]);
            }
            if (Ndef.isType(record, Ndef.RTD_URI)) {
              return Ndef.uri.decodePayload(record.payload as number[]);
            }
            return null;
          })
          .filter(Boolean)
          .join('\n');
        
        setData(text || `Tag ID: ${tag.id}`);
        setState('success');
      } else {
        setData(`Tag ID: ${tag?.id || 'Unknown'}`);
        setState('success');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setState('error');
    } finally {
      NfcManager.cancelTechnologyRequest().catch(() => {});
    }
  };

  const cancel = () => {
    NfcManager.cancelTechnologyRequest().catch(() => {});
    setState('idle');
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
      {state === 'scanning' && (
        <>
          <ActivityIndicator size="large" />
          <Text style={{ textAlign: 'center', marginTop: 20 }}>
            Hold your device near an NFC tag
          </Text>
          <Button title="Cancel" onPress={cancel} />
        </>
      )}
      
      {state === 'success' && (
        <>
          <Text style={{ fontSize: 18, marginBottom: 20 }}>Tag Data:</Text>
          <Text selectable>{data}</Text>
          <Button title="Scan Another" onPress={scan} />
        </>
      )}
      
      {state === 'error' && (
        <>
          <Text style={{ color: 'red' }}>{error}</Text>
          <Button title="Try Again" onPress={scan} />
        </>
      )}
      
      {state === 'idle' && (
        <Button title="Scan NFC Tag" onPress={scan} />
      )}
    </View>
  );
}
```

---

## FinTech NFC Use Cases

| Use Case | Feasible | Notes |
|----------|----------|-------|
| Read loyalty cards | ✅ | NDEF tags |
| Read employee badges | ⚠️ | MIFARE - Android only for Classic |
| Read transit cards | ⚠️ | Often encrypted, limited data |
| Payment card reading | ❌ | Blocked/regulated, use Airwallex |
| Payment card emulation | ❌ iOS / ⚠️ Android | Apple Wallet only / Android HCE requires certs |
| FIDO2 security keys | ✅ | Via `react-native-passkey` |
