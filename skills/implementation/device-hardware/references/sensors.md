# Sensors

## expo-sensors

Provides access to device motion sensors. Works in Expo Go.

### Installation

```bash
npx expo install expo-sensors
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": ["expo-sensors"],
    "ios": {
      "infoPlist": {
        "NSMotionUsageDescription": "Allow $(PRODUCT_NAME) to access motion sensors"
      }
    },
    "android": {
      "permissions": ["android.permission.HIGH_SAMPLING_RATE_SENSORS"]
    }
  }
}
```

---

## Accelerometer

Measures device acceleration in m/s² including gravity.

```typescript
import { Accelerometer, AccelerometerMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function useAccelerometer(updateInterval = 100) {
  const [data, setData] = useState<AccelerometerMeasurement>({ x: 0, y: 0, z: 0 });
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    Accelerometer.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    Accelerometer.setUpdateInterval(updateInterval);
    const subscription = Accelerometer.addListener(setData);
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { data, isAvailable };
}

// Usage
function ShakeDetector() {
  const { data } = useAccelerometer(50);
  const [shakeCount, setShakeCount] = useState(0);
  const lastShake = useRef(0);

  useEffect(() => {
    const acceleration = Math.sqrt(data.x ** 2 + data.y ** 2 + data.z ** 2);
    const now = Date.now();
    
    // Detect shake (acceleration > 15 m/s², debounce 500ms)
    if (acceleration > 15 && now - lastShake.current > 500) {
      lastShake.current = now;
      setShakeCount(c => c + 1);
    }
  }, [data]);

  return <Text>Shakes detected: {shakeCount}</Text>;
}
```

---

## Gyroscope

Measures rotation rate in rad/s.

```typescript
import { Gyroscope, GyroscopeMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function useGyroscope(updateInterval = 100) {
  const [data, setData] = useState<GyroscopeMeasurement>({ x: 0, y: 0, z: 0 });
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    Gyroscope.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    Gyroscope.setUpdateInterval(updateInterval);
    const subscription = Gyroscope.addListener(setData);
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { data, isAvailable };
}

// Rotation detection
function RotationMonitor() {
  const { data } = useGyroscope(50);
  
  const rotationSpeed = Math.sqrt(data.x ** 2 + data.y ** 2 + data.z ** 2);
  const isRotating = rotationSpeed > 0.5;
  
  return (
    <View>
      <Text>Rotation: {rotationSpeed.toFixed(2)} rad/s</Text>
      <Text>{isRotating ? 'Device is rotating' : 'Device is still'}</Text>
    </View>
  );
}
```

---

## Magnetometer

Measures magnetic field in microteslas (μT). Useful for compass.

```typescript
import { Magnetometer, MagnetometerMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function useMagnetometer(updateInterval = 100) {
  const [data, setData] = useState<MagnetometerMeasurement>({ x: 0, y: 0, z: 0 });
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    Magnetometer.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    Magnetometer.setUpdateInterval(updateInterval);
    const subscription = Magnetometer.addListener(setData);
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { data, isAvailable };
}

// Compass heading
function Compass() {
  const { data, isAvailable } = useMagnetometer(100);
  
  // Calculate heading (simplified, assumes device is flat)
  const heading = Math.atan2(data.y, data.x) * (180 / Math.PI);
  const normalizedHeading = (heading + 360) % 360;
  
  const getDirection = (deg: number) => {
    if (deg >= 337.5 || deg < 22.5) return 'N';
    if (deg >= 22.5 && deg < 67.5) return 'NE';
    if (deg >= 67.5 && deg < 112.5) return 'E';
    if (deg >= 112.5 && deg < 157.5) return 'SE';
    if (deg >= 157.5 && deg < 202.5) return 'S';
    if (deg >= 202.5 && deg < 247.5) return 'SW';
    if (deg >= 247.5 && deg < 292.5) return 'W';
    return 'NW';
  };

  if (!isAvailable) return <Text>Magnetometer not available</Text>;

  return (
    <View>
      <Text style={{ fontSize: 48 }}>{getDirection(normalizedHeading)}</Text>
      <Text>{normalizedHeading.toFixed(0)}°</Text>
    </View>
  );
}
```

---

## Barometer

Measures atmospheric pressure in hPa (hectopascals).

```typescript
import { Barometer, BarometerMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function useBarometer(updateInterval = 1000) {
  const [data, setData] = useState<BarometerMeasurement>({ pressure: 0, relativeAltitude: 0 });
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    Barometer.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    Barometer.setUpdateInterval(updateInterval);
    const subscription = Barometer.addListener(setData);
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { data, isAvailable };
}

// Altitude estimation
function AltitudeDisplay() {
  const { data, isAvailable } = useBarometer(1000);
  
  // Estimate altitude from pressure (simplified formula)
  // Standard pressure at sea level: 1013.25 hPa
  const altitude = 44330 * (1 - Math.pow(data.pressure / 1013.25, 0.1903));

  if (!isAvailable) return <Text>Barometer not available</Text>;

  return (
    <View>
      <Text>Pressure: {data.pressure.toFixed(1)} hPa</Text>
      <Text>Est. Altitude: {altitude.toFixed(0)} m</Text>
      <Text>Relative Alt: {data.relativeAltitude?.toFixed(1) || 'N/A'} m</Text>
    </View>
  );
}
```

---

## Pedometer

Counts steps. iOS tracks steps in background.

```typescript
import { Pedometer, PedometerResult } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function usePedometer() {
  const [steps, setSteps] = useState(0);
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    Pedometer.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    // Watch for live step updates
    const subscription = Pedometer.watchStepCount((result) => {
      setSteps(result.steps);
    });
    
    return () => subscription.remove();
  }, [isAvailable]);

  return { steps, isAvailable };
}

// Get historical steps
async function getStepsForToday(): Promise<number> {
  const isAvailable = await Pedometer.isAvailableAsync();
  if (!isAvailable) return 0;

  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  const result = await Pedometer.getStepCountAsync(startOfDay, now);
  return result.steps;
}

// Steps component
function StepCounter() {
  const { steps, isAvailable } = usePedometer();
  const [todaySteps, setTodaySteps] = useState(0);

  useEffect(() => {
    getStepsForToday().then(setTodaySteps);
  }, []);

  if (!isAvailable) return <Text>Pedometer not available</Text>;

  return (
    <View>
      <Text>Steps since app opened: {steps}</Text>
      <Text>Steps today: {todaySteps}</Text>
    </View>
  );
}
```

---

## DeviceMotion

Combined sensor data with sensor fusion (more accurate orientation).

```typescript
import { DeviceMotion, DeviceMotionMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';

export function useDeviceMotion(updateInterval = 100) {
  const [data, setData] = useState<DeviceMotionMeasurement | null>(null);
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    DeviceMotion.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    DeviceMotion.setUpdateInterval(updateInterval);
    const subscription = DeviceMotion.addListener(setData);
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { data, isAvailable };
}

function OrientationDisplay() {
  const { data, isAvailable } = useDeviceMotion(50);

  if (!isAvailable || !data) return <Text>DeviceMotion not available</Text>;

  const { rotation } = data;
  
  // Rotation in radians
  const pitch = rotation?.beta ?? 0;  // Front/back tilt
  const roll = rotation?.gamma ?? 0;  // Left/right tilt
  const yaw = rotation?.alpha ?? 0;   // Compass direction

  return (
    <View>
      <Text>Pitch: {(pitch * 180 / Math.PI).toFixed(1)}°</Text>
      <Text>Roll: {(roll * 180 / Math.PI).toFixed(1)}°</Text>
      <Text>Yaw: {(yaw * 180 / Math.PI).toFixed(1)}°</Text>
    </View>
  );
}
```

DeviceMotion provides:
- `acceleration` - Linear acceleration (gravity removed)
- `accelerationIncludingGravity` - Total acceleration
- `rotation` - Device orientation (alpha, beta, gamma)
- `rotationRate` - Angular velocity
- `orientation` - Screen orientation (0, 90, 180, 270)

---

## Light Sensor (Android Only)

```typescript
import { LightSensor, LightSensorMeasurement } from 'expo-sensors';
import { useState, useEffect } from 'react';
import { Platform } from 'react-native';

export function useLightSensor(updateInterval = 500) {
  const [illuminance, setIlluminance] = useState(0);
  const [isAvailable, setIsAvailable] = useState(false);

  useEffect(() => {
    if (Platform.OS !== 'android') {
      setIsAvailable(false);
      return;
    }
    LightSensor.isAvailableAsync().then(setIsAvailable);
  }, []);

  useEffect(() => {
    if (!isAvailable) return;

    LightSensor.setUpdateInterval(updateInterval);
    const subscription = LightSensor.addListener((data) => {
      setIlluminance(data.illuminance);
    });
    
    return () => subscription.remove();
  }, [isAvailable, updateInterval]);

  return { illuminance, isAvailable };
}

// Ambient light detection
function LightMeter() {
  const { illuminance, isAvailable } = useLightSensor(500);
  
  const getLightLevel = (lux: number) => {
    if (lux < 10) return 'Very Dark';
    if (lux < 50) return 'Dark';
    if (lux < 200) return 'Dim';
    if (lux < 500) return 'Normal';
    if (lux < 1000) return 'Bright';
    return 'Very Bright';
  };

  if (!isAvailable) return <Text>Light sensor not available (iOS doesn't support)</Text>;

  return (
    <View>
      <Text>{illuminance.toFixed(0)} lux</Text>
      <Text>{getLightLevel(illuminance)}</Text>
    </View>
  );
}
```

---

## Sensor Update Intervals

```typescript
// Set update interval in milliseconds
Accelerometer.setUpdateInterval(16);  // ~60fps
Gyroscope.setUpdateInterval(16);
Magnetometer.setUpdateInterval(100);
Barometer.setUpdateInterval(1000);
DeviceMotion.setUpdateInterval(16);
LightSensor.setUpdateInterval(500);
```

**Performance note**: High-frequency updates (< 100ms) increase battery drain. Use the slowest interval that meets your needs.

**Android 12+ note**: For intervals faster than 200ms, the `HIGH_SAMPLING_RATE_SENSORS` permission is required.

---

## Platform Comparison

| Sensor | iOS | Android |
|--------|-----|---------|
| Accelerometer | ✅ | ✅ |
| Gyroscope | ✅ | ✅ |
| Magnetometer | ✅ | ✅ |
| Barometer | ✅ (iPhone 6+) | ✅ (device dependent) |
| Pedometer | ✅ | ✅ |
| DeviceMotion | ✅ | ✅ |
| Light Sensor | ❌ | ✅ |

---

## Combined Sensor Hook

```typescript
import { Accelerometer, Gyroscope, Magnetometer } from 'expo-sensors';
import { useState, useEffect, useRef } from 'react';

interface SensorData {
  acceleration: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  magnetic: { x: number; y: number; z: number };
}

export function useSensors(updateInterval = 100): SensorData {
  const [data, setData] = useState<SensorData>({
    acceleration: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0, z: 0 },
    magnetic: { x: 0, y: 0, z: 0 },
  });

  useEffect(() => {
    Accelerometer.setUpdateInterval(updateInterval);
    Gyroscope.setUpdateInterval(updateInterval);
    Magnetometer.setUpdateInterval(updateInterval);

    const sub1 = Accelerometer.addListener((d) => 
      setData(prev => ({ ...prev, acceleration: d }))
    );
    const sub2 = Gyroscope.addListener((d) => 
      setData(prev => ({ ...prev, rotation: d }))
    );
    const sub3 = Magnetometer.addListener((d) => 
      setData(prev => ({ ...prev, magnetic: d }))
    );

    return () => {
      sub1.remove();
      sub2.remove();
      sub3.remove();
    };
  }, [updateInterval]);

  return data;
}
```
