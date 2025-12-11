# Haptic Feedback

## expo-haptics

Provides haptic feedback using the device's vibration motor. Works in Expo Go.

### Installation

```bash
npx expo install expo-haptics
```

### Basic Haptics

```typescript
import * as Haptics from 'expo-haptics';

// Impact feedback - physical tap sensations
const lightTap = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
const mediumTap = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
const heavyTap = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);

// Additional impact styles (iOS 13+)
const softTap = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Soft);
const rigidTap = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Rigid);

// Notification feedback - semantic feedback
const success = () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
const warning = () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
const error = () => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

// Selection feedback - for UI selections
const selection = () => Haptics.selectionAsync();
```

### Impact Feedback Styles

| Style | Feeling | Use Case |
|-------|---------|----------|
| `Light` | Gentle tap | Toggle switches, small buttons |
| `Medium` | Standard tap | Regular button presses |
| `Heavy` | Strong tap | Important actions, confirmations |
| `Soft` | Cushioned tap | Soft UI elements |
| `Rigid` | Sharp tap | Precise interactions |

### Notification Feedback Types

| Type | Feeling | Use Case |
|------|---------|----------|
| `Success` | Double pulse | Task completed, payment success |
| `Warning` | Three pulses | Warnings, alerts |
| `Error` | Sharp buzz | Errors, failed actions |

### Selection Feedback

```typescript
// Use for:
// - Picker scrolling
// - Slider value changes
// - Segment control changes
// - List item selection

<Picker
  onValueChange={(value) => {
    Haptics.selectionAsync();
    setValue(value);
  }}
/>
```

---

## Common Patterns

### Button with Haptic Feedback

```typescript
import * as Haptics from 'expo-haptics';
import { TouchableOpacity, Text } from 'react-native';

interface HapticButtonProps {
  onPress: () => void;
  title: string;
  hapticStyle?: Haptics.ImpactFeedbackStyle;
}

function HapticButton({ 
  onPress, 
  title, 
  hapticStyle = Haptics.ImpactFeedbackStyle.Medium 
}: HapticButtonProps) {
  const handlePress = () => {
    Haptics.impactAsync(hapticStyle);
    onPress();
  };

  return (
    <TouchableOpacity onPress={handlePress}>
      <Text>{title}</Text>
    </TouchableOpacity>
  );
}
```

### Toggle Switch with Haptics

```typescript
import * as Haptics from 'expo-haptics';
import { Switch } from 'react-native';

function HapticSwitch({ value, onValueChange }: { 
  value: boolean; 
  onValueChange: (v: boolean) => void;
}) {
  const handleChange = (newValue: boolean) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onValueChange(newValue);
  };

  return <Switch value={value} onValueChange={handleChange} />;
}
```

### Slider with Selection Feedback

```typescript
import * as Haptics from 'expo-haptics';
import Slider from '@react-native-community/slider';
import { useRef } from 'react';

function HapticSlider({ 
  value, 
  onValueChange, 
  step = 1 
}: { 
  value: number; 
  onValueChange: (v: number) => void;
  step?: number;
}) {
  const lastValue = useRef(value);

  const handleChange = (newValue: number) => {
    // Trigger haptic when crossing step boundaries
    const crossed = Math.floor(newValue / step) !== Math.floor(lastValue.current / step);
    if (crossed) {
      Haptics.selectionAsync();
    }
    lastValue.current = newValue;
    onValueChange(newValue);
  };

  return (
    <Slider
      value={value}
      onValueChange={handleChange}
      step={step}
      minimumValue={0}
      maximumValue={100}
    />
  );
}
```

### Async Operation with Feedback

```typescript
import * as Haptics from 'expo-haptics';

async function submitPayment(amount: number) {
  try {
    // Processing...
    await processPayment(amount);
    
    // Success haptic
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    showSuccessMessage('Payment complete!');
    
  } catch (error) {
    // Error haptic
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    showErrorMessage('Payment failed');
  }
}
```

### Pull-to-Refresh Haptic

```typescript
import * as Haptics from 'expo-haptics';
import { RefreshControl, FlatList } from 'react-native';
import { useState } from 'react';

function HapticList({ data, renderItem }) {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    />
  );
}
```

### Long Press with Escalating Haptics

```typescript
import * as Haptics from 'expo-haptics';
import { Pressable } from 'react-native';

function LongPressButton({ onLongPress, children }) {
  const handlePressIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleLongPress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    onLongPress();
  };

  return (
    <Pressable
      onPressIn={handlePressIn}
      onLongPress={handleLongPress}
      delayLongPress={500}
    >
      {children}
    </Pressable>
  );
}
```

---

## Advanced: react-native-haptic-feedback

For more control over haptic patterns. Requires development build.

```bash
npm install react-native-haptic-feedback
npx expo prebuild --clean
```

```typescript
import ReactNativeHapticFeedback from 'react-native-haptic-feedback';

// More haptic types available
ReactNativeHapticFeedback.trigger('impactLight');
ReactNativeHapticFeedback.trigger('impactMedium');
ReactNativeHapticFeedback.trigger('impactHeavy');
ReactNativeHapticFeedback.trigger('notificationSuccess');
ReactNativeHapticFeedback.trigger('notificationWarning');
ReactNativeHapticFeedback.trigger('notificationError');
ReactNativeHapticFeedback.trigger('selection');

// Additional types
ReactNativeHapticFeedback.trigger('clockTick');      // Android
ReactNativeHapticFeedback.trigger('contextClick');   // Android
ReactNativeHapticFeedback.trigger('keyboardPress');  // Android
ReactNativeHapticFeedback.trigger('keyboardRelease'); // Android
ReactNativeHapticFeedback.trigger('keyboardTap');    // Android
ReactNativeHapticFeedback.trigger('longPress');      // Android
ReactNativeHapticFeedback.trigger('textHandleMove'); // Android
ReactNativeHapticFeedback.trigger('virtualKey');     // Android
ReactNativeHapticFeedback.trigger('virtualKeyRelease'); // Android

// Options
const options = {
  enableVibrateFallback: true,  // Fall back to vibration on older devices
  ignoreAndroidSystemSettings: false, // Respect system haptic settings
};

ReactNativeHapticFeedback.trigger('impactMedium', options);
```

---

## Platform Differences

| Feature | iOS | Android |
|---------|-----|---------|
| Taptic Engine | ✅ (iPhone 7+) | Uses Vibrator |
| Impact feedback | ✅ Native | ✅ Simulated |
| Notification feedback | ✅ Native | ✅ Simulated |
| Selection feedback | ✅ Native | ✅ Simulated |
| Soft/Rigid styles | ✅ iOS 13+ | ⚠️ May not differ |
| System haptic setting | ✅ Respected | ✅ Respected |

### iOS Limitations

Haptics are disabled when:
- Low Power Mode is enabled
- Camera is in use
- Dictation is active
- Device doesn't have Taptic Engine (iPhone 6s and earlier)

### Android Considerations

- Quality varies by device hardware
- Some styles may feel identical
- Falls back to basic vibration on older devices

---

## Best Practices

1. **Don't overuse**: Haptics should enhance, not annoy
2. **Match intensity to action**: Light for small actions, heavy for important ones
3. **Be consistent**: Same actions should have same haptic type
4. **Respect system settings**: Let users disable haptics
5. **Test on real devices**: Simulators don't provide haptic feedback

### When to Use Haptics

✅ Do use for:
- Button presses
- Toggle switches
- Slider value changes
- Success/error feedback
- Pull-to-refresh
- Important confirmations

❌ Don't use for:
- Every scroll event
- Continuous animations
- Background events
- Rapid repeated actions

---

## Haptic Feedback Hook

```typescript
import * as Haptics from 'expo-haptics';
import { useCallback } from 'react';

export function useHaptics() {
  const impact = useCallback((
    style: Haptics.ImpactFeedbackStyle = Haptics.ImpactFeedbackStyle.Medium
  ) => {
    Haptics.impactAsync(style);
  }, []);

  const notification = useCallback((
    type: Haptics.NotificationFeedbackType
  ) => {
    Haptics.notificationAsync(type);
  }, []);

  const selection = useCallback(() => {
    Haptics.selectionAsync();
  }, []);

  return {
    impact,
    notification,
    selection,
    // Convenience methods
    light: () => impact(Haptics.ImpactFeedbackStyle.Light),
    medium: () => impact(Haptics.ImpactFeedbackStyle.Medium),
    heavy: () => impact(Haptics.ImpactFeedbackStyle.Heavy),
    success: () => notification(Haptics.NotificationFeedbackType.Success),
    warning: () => notification(Haptics.NotificationFeedbackType.Warning),
    error: () => notification(Haptics.NotificationFeedbackType.Error),
  };
}

// Usage
function MyComponent() {
  const haptics = useHaptics();
  
  return (
    <Button onPress={() => {
      haptics.success();
      // ... action
    }} />
  );
}
```
