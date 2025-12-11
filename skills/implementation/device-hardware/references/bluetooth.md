# Bluetooth Low Energy (BLE)

## react-native-ble-plx

The most popular BLE library for React Native. Requires development build.

### Installation

```bash
npm install react-native-ble-plx
npx expo prebuild --clean
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "react-native-ble-plx",
        {
          "isBackgroundEnabled": true,
          "modes": ["peripheral", "central"],
          "bluetoothAlwaysPermission": "Allow $(PRODUCT_NAME) to connect to Bluetooth devices"
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "NSBluetoothAlwaysUsageDescription": "Allow $(PRODUCT_NAME) to connect to Bluetooth devices",
        "NSBluetoothPeripheralUsageDescription": "Allow $(PRODUCT_NAME) to connect to Bluetooth devices",
        "UIBackgroundModes": ["bluetooth-central", "bluetooth-peripheral"]
      }
    },
    "android": {
      "permissions": [
        "android.permission.BLUETOOTH",
        "android.permission.BLUETOOTH_ADMIN",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.BLUETOOTH_SCAN",
        "android.permission.ACCESS_FINE_LOCATION"
      ]
    }
  }
}
```

### Initialize BLE Manager

```typescript
import { BleManager, Device, State } from 'react-native-ble-plx';
import { useEffect, useRef, useState } from 'react';
import { Platform, PermissionsAndroid } from 'react-native';

export function useBLE() {
  const managerRef = useRef<BleManager | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const manager = new BleManager();
    managerRef.current = manager;

    const subscription = manager.onStateChange((state) => {
      if (state === State.PoweredOn) {
        setIsReady(true);
      }
    }, true);

    return () => {
      subscription.remove();
      manager.destroy();
    };
  }, []);

  return { manager: managerRef.current, isReady };
}
```

### Request Permissions (Android)

```typescript
const requestBLEPermissions = async (): Promise<boolean> => {
  if (Platform.OS === 'android') {
    const apiLevel = Platform.Version;
    
    if (apiLevel >= 31) {
      // Android 12+
      const results = await PermissionsAndroid.requestMultiple([
        PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
        PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      ]);
      
      return Object.values(results).every(
        result => result === PermissionsAndroid.RESULTS.GRANTED
      );
    } else {
      // Android 11 and below
      const result = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
      );
      return result === PermissionsAndroid.RESULTS.GRANTED;
    }
  }
  
  return true; // iOS handles permissions automatically
};
```

### Scan for Devices

```typescript
const [devices, setDevices] = useState<Device[]>([]);
const [isScanning, setIsScanning] = useState(false);

const startScan = () => {
  if (!manager || isScanning) return;
  
  setDevices([]);
  setIsScanning(true);

  manager.startDeviceScan(
    null, // Service UUIDs to filter (null = all)
    { allowDuplicates: false },
    (error, device) => {
      if (error) {
        console.error('Scan error:', error);
        setIsScanning(false);
        return;
      }

      if (device && device.name) {
        setDevices(prev => {
          const exists = prev.some(d => d.id === device.id);
          return exists ? prev : [...prev, device];
        });
      }
    }
  );

  // Stop after 10 seconds
  setTimeout(() => {
    manager.stopDeviceScan();
    setIsScanning(false);
  }, 10000);
};

const stopScan = () => {
  manager?.stopDeviceScan();
  setIsScanning(false);
};
```

### Scan with Service Filter

```typescript
// Only find devices advertising specific services
const SERVICE_UUID = '180D'; // Heart Rate Service

manager.startDeviceScan(
  [SERVICE_UUID],
  { allowDuplicates: false },
  (error, device) => {
    // Only devices with Heart Rate service
  }
);
```

### Connect to Device

```typescript
const [connectedDevice, setConnectedDevice] = useState<Device | null>(null);

const connectToDevice = async (device: Device): Promise<Device | null> => {
  try {
    // Connect
    const connected = await device.connect({
      timeout: 10000, // 10 second timeout
      autoConnect: false,
    });
    
    // Discover services and characteristics
    const discovered = await connected.discoverAllServicesAndCharacteristics();
    
    setConnectedDevice(discovered);
    
    // Monitor connection state
    discovered.onDisconnected((error, disconnectedDevice) => {
      console.log('Disconnected:', disconnectedDevice?.id);
      setConnectedDevice(null);
    });
    
    return discovered;
  } catch (error) {
    console.error('Connection failed:', error);
    return null;
  }
};

const disconnect = async () => {
  if (connectedDevice) {
    await connectedDevice.cancelConnection();
    setConnectedDevice(null);
  }
};
```

### Read Characteristic

```typescript
const readCharacteristic = async (
  device: Device,
  serviceUUID: string,
  characteristicUUID: string
): Promise<string | null> => {
  try {
    const characteristic = await device.readCharacteristicForService(
      serviceUUID,
      characteristicUUID
    );
    
    // Value is base64 encoded
    if (characteristic.value) {
      const decoded = Buffer.from(characteristic.value, 'base64');
      return decoded.toString();
    }
    
    return null;
  } catch (error) {
    console.error('Read failed:', error);
    return null;
  }
};
```

### Write Characteristic

```typescript
const writeCharacteristic = async (
  device: Device,
  serviceUUID: string,
  characteristicUUID: string,
  value: string
): Promise<boolean> => {
  try {
    // Encode value as base64
    const base64Value = Buffer.from(value).toString('base64');
    
    await device.writeCharacteristicWithResponseForService(
      serviceUUID,
      characteristicUUID,
      base64Value
    );
    
    return true;
  } catch (error) {
    console.error('Write failed:', error);
    return false;
  }
};

// Write without response (faster, no confirmation)
const writeWithoutResponse = async (
  device: Device,
  serviceUUID: string,
  characteristicUUID: string,
  value: string
): Promise<boolean> => {
  try {
    const base64Value = Buffer.from(value).toString('base64');
    
    await device.writeCharacteristicWithoutResponseForService(
      serviceUUID,
      characteristicUUID,
      base64Value
    );
    
    return true;
  } catch (error) {
    return false;
  }
};
```

### Monitor Characteristic (Notifications)

```typescript
const subscribeToCharacteristic = (
  device: Device,
  serviceUUID: string,
  characteristicUUID: string,
  onData: (value: string) => void
) => {
  const subscription = device.monitorCharacteristicForService(
    serviceUUID,
    characteristicUUID,
    (error, characteristic) => {
      if (error) {
        console.error('Monitor error:', error);
        return;
      }
      
      if (characteristic?.value) {
        const decoded = Buffer.from(characteristic.value, 'base64').toString();
        onData(decoded);
      }
    }
  );
  
  // Return subscription for cleanup
  return subscription;
};

// Usage
useEffect(() => {
  if (!connectedDevice) return;
  
  const subscription = subscribeToCharacteristic(
    connectedDevice,
    '180D', // Heart Rate Service
    '2A37', // Heart Rate Measurement
    (value) => {
      console.log('Heart rate:', value);
    }
  );
  
  return () => subscription.remove();
}, [connectedDevice]);
```

### Get Services and Characteristics

```typescript
const exploreDevice = async (device: Device) => {
  const services = await device.services();
  
  for (const service of services) {
    console.log('Service:', service.uuid);
    
    const characteristics = await service.characteristics();
    for (const char of characteristics) {
      console.log('  Characteristic:', char.uuid);
      console.log('    Readable:', char.isReadable);
      console.log('    Writable:', char.isWritableWithResponse);
      console.log('    Notifiable:', char.isNotifiable);
    }
  }
};
```

---

## Common BLE Services

| UUID | Service | Description |
|------|---------|-------------|
| `180D` | Heart Rate | Heart rate monitors |
| `180F` | Battery | Battery level |
| `1800` | Generic Access | Device name, appearance |
| `1801` | Generic Attribute | Service changed |
| `180A` | Device Information | Manufacturer, model, serial |
| `1805` | Current Time | Time sync |
| `1816` | Cycling Speed | Bike sensors |
| `1818` | Cycling Power | Power meters |

---

## BLE Peripheral Mode (Act as BLE Server)

Make device advertise as a BLE peripheral:

```typescript
// Note: Requires additional setup
const startAdvertising = async () => {
  // react-native-ble-plx supports peripheral mode
  // but implementation is platform-specific
  
  // For full peripheral support, consider:
  // - react-native-ble-peripheral (Android)
  // - iOS requires native code for full peripheral
};
```

---

## Alternative: react-native-ble-manager

Another popular BLE library with device bonding support.

```bash
npm install react-native-ble-manager
```

Key differences:
- Better bonding/pairing support
- Different API style (callbacks vs promises)
- Similar capabilities overall

---

## Platform Notes

| Feature | iOS | Android |
|---------|-----|---------|
| BLE Central | ✅ | ✅ |
| BLE Peripheral | ✅ | ✅ |
| Background scanning | ✅ (with UIBackgroundModes) | ✅ |
| Location permission for BLE | ❌ Not required | ✅ Required (Android 12+) |
| Bluetooth Classic | ❌ | ❌ (not in RN libs) |
| Max connections | ~7 | ~7 |

---

## Complete BLE Example

```typescript
import { BleManager, Device } from 'react-native-ble-plx';
import { useState, useEffect, useRef } from 'react';
import { View, Text, FlatList, TouchableOpacity, Button } from 'react-native';

export function BLEScanner() {
  const managerRef = useRef<BleManager | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [connected, setConnected] = useState<Device | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    managerRef.current = new BleManager();
    return () => {
      managerRef.current?.destroy();
    };
  }, []);

  const scan = () => {
    const manager = managerRef.current;
    if (!manager) return;

    setDevices([]);
    setIsScanning(true);

    manager.startDeviceScan(null, null, (error, device) => {
      if (error) {
        setIsScanning(false);
        return;
      }
      if (device?.name) {
        setDevices(prev => {
          if (prev.find(d => d.id === device.id)) return prev;
          return [...prev, device];
        });
      }
    });

    setTimeout(() => {
      manager.stopDeviceScan();
      setIsScanning(false);
    }, 10000);
  };

  const connect = async (device: Device) => {
    const manager = managerRef.current;
    if (!manager) return;

    manager.stopDeviceScan();
    setIsScanning(false);

    try {
      const d = await device.connect();
      await d.discoverAllServicesAndCharacteristics();
      setConnected(d);
    } catch (e) {
      console.error(e);
    }
  };

  const disconnect = async () => {
    await connected?.cancelConnection();
    setConnected(null);
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      {connected ? (
        <View>
          <Text>Connected to: {connected.name}</Text>
          <Button title="Disconnect" onPress={disconnect} />
        </View>
      ) : (
        <>
          <Button 
            title={isScanning ? 'Scanning...' : 'Scan'} 
            onPress={scan} 
            disabled={isScanning}
          />
          <FlatList
            data={devices}
            keyExtractor={item => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity 
                onPress={() => connect(item)}
                style={{ padding: 15, borderBottomWidth: 1 }}
              >
                <Text>{item.name}</Text>
                <Text style={{ color: 'gray' }}>{item.id}</Text>
              </TouchableOpacity>
            )}
          />
        </>
      )}
    </View>
  );
}
```
