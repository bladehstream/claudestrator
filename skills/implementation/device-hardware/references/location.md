# Location & GPS

## expo-location

Provides GPS location, geocoding, and geofencing. Works in Expo Go for foreground use.

### Installation

```bash
npx expo install expo-location
```

### Config Plugin (app.json)

```json
{
  "expo": {
    "plugins": [
      [
        "expo-location",
        {
          "locationAlwaysAndWhenInUsePermission": "Allow $(PRODUCT_NAME) to use your location",
          "locationAlwaysPermission": "Allow $(PRODUCT_NAME) to use your location in the background",
          "locationWhenInUsePermission": "Allow $(PRODUCT_NAME) to use your location",
          "isAndroidBackgroundLocationEnabled": true,
          "isAndroidForegroundServiceEnabled": true
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "NSLocationWhenInUseUsageDescription": "Allow $(PRODUCT_NAME) to use your location",
        "NSLocationAlwaysAndWhenInUseUsageDescription": "Allow $(PRODUCT_NAME) to use your location in the background",
        "UIBackgroundModes": ["location"]
      }
    },
    "android": {
      "permissions": [
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        "android.permission.FOREGROUND_SERVICE",
        "android.permission.FOREGROUND_SERVICE_LOCATION"
      ]
    }
  }
}
```

### Request Permissions

```typescript
import * as Location from 'expo-location';

const requestLocationPermission = async (): Promise<boolean> => {
  // Foreground permission
  const { status: foreground } = await Location.requestForegroundPermissionsAsync();
  if (foreground !== 'granted') {
    return false;
  }
  
  return true;
};

const requestBackgroundPermission = async (): Promise<boolean> => {
  // Must have foreground first
  const foreground = await requestLocationPermission();
  if (!foreground) return false;
  
  // Then request background
  const { status: background } = await Location.requestBackgroundPermissionsAsync();
  return background === 'granted';
};
```

### Get Current Location

```typescript
import * as Location from 'expo-location';

const getCurrentLocation = async () => {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') {
    throw new Error('Permission denied');
  }

  const location = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.High,
  });

  return {
    latitude: location.coords.latitude,
    longitude: location.coords.longitude,
    altitude: location.coords.altitude,
    accuracy: location.coords.accuracy,
    speed: location.coords.speed,
    heading: location.coords.heading,
    timestamp: location.timestamp,
  };
};
```

### Accuracy Levels

```typescript
import { Accuracy } from 'expo-location';

// From lowest to highest accuracy (and battery usage)
Accuracy.Lowest          // ~3000m accuracy
Accuracy.Low             // ~1000m accuracy
Accuracy.Balanced        // ~100m accuracy
Accuracy.High            // ~10m accuracy
Accuracy.Highest         // Best available (GPS)
Accuracy.BestForNavigation  // Highest + additional sensor data
```

### Watch Location (Continuous Updates)

```typescript
import * as Location from 'expo-location';
import { useState, useEffect } from 'react';

export function useLocation(options?: Location.LocationOptions) {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let subscription: Location.LocationSubscription;

    const startWatching = async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('Permission denied');
        return;
      }

      subscription = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.High,
          timeInterval: 1000,      // Update every 1 second
          distanceInterval: 10,    // Or when moved 10 meters
          ...options,
        },
        (loc) => {
          setLocation(loc);
        }
      );
    };

    startWatching();

    return () => {
      subscription?.remove();
    };
  }, []);

  return { location, error };
}

// Usage
function LocationDisplay() {
  const { location, error } = useLocation();

  if (error) return <Text>{error}</Text>;
  if (!location) return <Text>Getting location...</Text>;

  return (
    <View>
      <Text>Lat: {location.coords.latitude.toFixed(6)}</Text>
      <Text>Lng: {location.coords.longitude.toFixed(6)}</Text>
      <Text>Accuracy: {location.coords.accuracy?.toFixed(0)}m</Text>
    </View>
  );
}
```

### Geocoding (Address ↔ Coordinates)

```typescript
import * as Location from 'expo-location';

// Address to coordinates (Forward geocoding)
const geocodeAddress = async (address: string) => {
  const results = await Location.geocodeAsync(address);
  
  if (results.length > 0) {
    return {
      latitude: results[0].latitude,
      longitude: results[0].longitude,
    };
  }
  return null;
};

// Coordinates to address (Reverse geocoding)
const reverseGeocode = async (latitude: number, longitude: number) => {
  const results = await Location.reverseGeocodeAsync({ latitude, longitude });
  
  if (results.length > 0) {
    const { street, city, region, country, postalCode } = results[0];
    return {
      street,
      city,
      region,
      country,
      postalCode,
      formatted: `${street}, ${city}, ${region} ${postalCode}, ${country}`,
    };
  }
  return null;
};

// Example usage
const coords = await geocodeAddress('1600 Amphitheatre Parkway, Mountain View, CA');
// { latitude: 37.4220656, longitude: -122.0840897 }

const address = await reverseGeocode(37.4220656, -122.0840897);
// { street: '1600 Amphitheatre Pkwy', city: 'Mountain View', ... }
```

### Heading/Compass

```typescript
import * as Location from 'expo-location';
import { useState, useEffect } from 'react';

export function useHeading() {
  const [heading, setHeading] = useState<number | null>(null);

  useEffect(() => {
    let subscription: Location.LocationSubscription;

    const start = async () => {
      subscription = await Location.watchHeadingAsync((data) => {
        setHeading(data.trueHeading); // True north heading in degrees
        // data.magHeading for magnetic north
      });
    };

    start();
    return () => subscription?.remove();
  }, []);

  return heading;
}

// Compass component
function Compass() {
  const heading = useHeading();

  const getDirection = (deg: number) => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(deg / 45) % 8;
    return directions[index];
  };

  if (heading === null) return <Text>Loading...</Text>;

  return (
    <View>
      <Text style={{ fontSize: 48 }}>{getDirection(heading)}</Text>
      <Text>{heading.toFixed(0)}°</Text>
    </View>
  );
}
```

---

## Background Location

Requires development build and `expo-task-manager`.

```bash
npx expo install expo-task-manager
```

### Setup Background Task

```typescript
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

const LOCATION_TASK = 'background-location-task';

// Define task (must be outside component, at module level)
TaskManager.defineTask(LOCATION_TASK, ({ data, error }) => {
  if (error) {
    console.error(error);
    return;
  }
  
  if (data) {
    const { locations } = data as { locations: Location.LocationObject[] };
    
    // Process locations
    locations.forEach(location => {
      console.log('Background location:', location.coords);
      // Send to server, save locally, etc.
    });
  }
});

// Start background location
const startBackgroundLocation = async () => {
  // Request permissions
  const { status: foreground } = await Location.requestForegroundPermissionsAsync();
  if (foreground !== 'granted') return false;
  
  const { status: background } = await Location.requestBackgroundPermissionsAsync();
  if (background !== 'granted') return false;

  // Start tracking
  await Location.startLocationUpdatesAsync(LOCATION_TASK, {
    accuracy: Location.Accuracy.Balanced,
    timeInterval: 60000,        // Every 60 seconds
    distanceInterval: 100,      // Or every 100 meters
    foregroundService: {
      notificationTitle: 'Location Tracking',
      notificationBody: 'Tracking your location in the background',
      notificationColor: '#0000FF',
    },
    // iOS specific
    activityType: Location.ActivityType.AutomotiveNavigation,
    showsBackgroundLocationIndicator: true,
    pausesUpdatesAutomatically: false,
  });

  return true;
};

// Stop background location
const stopBackgroundLocation = async () => {
  const isRunning = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK);
  if (isRunning) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK);
  }
};
```

### Activity Types (iOS)

```typescript
Location.ActivityType.Other                  // General purpose
Location.ActivityType.AutomotiveNavigation   // Driving
Location.ActivityType.Fitness                // Walking/running
Location.ActivityType.OtherNavigation        // Boat, train, etc.
Location.ActivityType.Airborne               // Flying
```

---

## Geofencing

Monitor entry/exit from geographic regions.

```typescript
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

const GEOFENCE_TASK = 'geofence-task';

// Define geofence task
TaskManager.defineTask(GEOFENCE_TASK, ({ data, error }) => {
  if (error) {
    console.error(error);
    return;
  }

  if (data) {
    const { eventType, region } = data as {
      eventType: Location.GeofencingEventType;
      region: Location.LocationRegion;
    };

    if (eventType === Location.GeofencingEventType.Enter) {
      console.log(`Entered region: ${region.identifier}`);
      // Trigger notification, etc.
    } else if (eventType === Location.GeofencingEventType.Exit) {
      console.log(`Exited region: ${region.identifier}`);
    }
  }
});

// Start geofencing
const startGeofencing = async () => {
  const { status } = await Location.requestBackgroundPermissionsAsync();
  if (status !== 'granted') return;

  const regions: Location.LocationRegion[] = [
    {
      identifier: 'home',
      latitude: 37.4220656,
      longitude: -122.0840897,
      radius: 100, // meters
      notifyOnEnter: true,
      notifyOnExit: true,
    },
    {
      identifier: 'work',
      latitude: 37.7749,
      longitude: -122.4194,
      radius: 200,
      notifyOnEnter: true,
      notifyOnExit: true,
    },
  ];

  await Location.startGeofencingAsync(GEOFENCE_TASK, regions);
};

// Stop geofencing
const stopGeofencing = async () => {
  await Location.stopGeofencingAsync(GEOFENCE_TASK);
};
```

---

## Distance Calculation

```typescript
// Haversine formula for distance between two coordinates
const calculateDistance = (
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number => {
  const R = 6371e3; // Earth radius in meters
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // Distance in meters
};

// Usage
const distance = calculateDistance(
  37.4220656, -122.0840897, // Point A
  37.7749, -122.4194        // Point B
);
console.log(`Distance: ${(distance / 1000).toFixed(2)} km`);
```

---

## Platform Differences

| Feature | iOS | Android |
|---------|-----|---------|
| Foreground location | ✅ | ✅ |
| Background location | ✅ (dev build) | ✅ (dev build) |
| Geofencing | ✅ (dev build) | ✅ (dev build) |
| Geocoding | ✅ | ✅ |
| Heading | ✅ | ✅ |
| Max geofence regions | ~20 | ~100 |
| Background indicator | ✅ Blue bar | ✅ Notification |

### Android Specific

- Android 10+: Must request `ACCESS_BACKGROUND_LOCATION` separately
- Android 12+: Background permission requires user to go to settings
- Foreground service required for background updates

### iOS Specific

- Background location shows blue indicator bar
- System may throttle background updates to save battery
- `activityType` helps iOS optimize updates

---

## Commercial Alternative: react-native-background-geolocation

For production apps needing sophisticated background tracking:

```bash
npm install react-native-background-geolocation
```

Features:
- Battery-optimized motion detection
- Geofencing with unlimited regions
- HTTP/SQLite persistence
- Activity recognition
- Sophisticated filtering

Note: Requires license for production use.
