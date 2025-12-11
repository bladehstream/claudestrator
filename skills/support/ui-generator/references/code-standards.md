# Code Generation Standards

Guidelines for generating production-ready, accessible UI code.

## React Native / Expo Standards

### Component Structure

```typescript
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface ComponentNameProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  title,
  onPress,
  disabled = false,
}) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      style={[styles.container, disabled && styles.disabled]}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled }}
    >
      <Text style={styles.title}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    minHeight: 44, // iOS minimum touch target
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  disabled: {
    opacity: 0.5,
  },
  title: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
```

### NativeWind (Tailwind) Pattern

```typescript
import { View, Text, Pressable } from 'react-native';

export const Button = ({ title, onPress, disabled }) => (
  <Pressable
    onPress={onPress}
    disabled={disabled}
    className={`min-h-[44px] px-4 py-3 rounded-lg bg-blue-500 
      items-center justify-center ${disabled ? 'opacity-50' : ''}`}
    accessibilityRole="button"
  >
    <Text className="text-[17px] font-semibold text-white">{title}</Text>
  </Pressable>
);
```

### Accessibility Requirements

Always include:
- `accessibilityRole` — button, link, header, image, etc.
- `accessibilityLabel` — Descriptive text for screen readers
- `accessibilityState` — { disabled, selected, checked, expanded }
- `accessibilityHint` — Optional action description

```typescript
<TouchableOpacity
  accessibilityRole="button"
  accessibilityLabel="Send payment of $150 to John"
  accessibilityHint="Double tap to confirm and send payment"
  accessibilityState={{ disabled: isLoading }}
>
```

### Safe Area Handling

```typescript
import { SafeAreaView } from 'react-native-safe-area-context';

export const Screen = ({ children }) => (
  <SafeAreaView style={{ flex: 1 }} edges={['top', 'bottom']}>
    {children}
  </SafeAreaView>
);
```

## Color System

### Dark Theme (WCAG AA Compliant)

```typescript
export const colors = {
  // Backgrounds
  background: '#0F172A',      // Primary background
  surface: '#1E293B',         // Cards, elevated surfaces
  surfaceAlt: '#334155',      // Secondary surfaces
  
  // Text (all pass 4.5:1 on background)
  textPrimary: '#F8FAFC',     // 14.5:1 ratio
  textSecondary: '#94A3B8',   // 5.4:1 ratio
  textTertiary: '#64748B',    // 4.6:1 ratio
  
  // Interactive
  primary: '#3B82F6',         // Blue accent
  primaryHover: '#2563EB',
  secondary: '#8B5CF6',       // Purple
  
  // Semantic
  success: '#22C55E',         // Green
  warning: '#F59E0B',         // Amber
  error: '#EF4444',           // Red
  info: '#0EA5E9',            // Sky blue
  
  // Borders
  border: '#334155',
  borderFocus: '#3B82F6',
};
```

### Light Theme (WCAG AA Compliant)

```typescript
export const colorsLight = {
  background: '#FFFFFF',
  surface: '#F8FAFC',
  surfaceAlt: '#F1F5F9',
  
  textPrimary: '#0F172A',     // 15.3:1 ratio
  textSecondary: '#475569',   // 7.1:1 ratio
  textTertiary: '#64748B',    // 4.6:1 ratio
  
  primary: '#2563EB',
  success: '#16A34A',
  warning: '#D97706',
  error: '#DC2626',
  
  border: '#E2E8F0',
  borderFocus: '#2563EB',
};
```

## Typography Scale

### iOS (SF Pro Based)

```typescript
export const typography = {
  largeTitle: { fontSize: 34, fontWeight: '700', lineHeight: 41 },
  title1: { fontSize: 28, fontWeight: '700', lineHeight: 34 },
  title2: { fontSize: 22, fontWeight: '700', lineHeight: 28 },
  title3: { fontSize: 20, fontWeight: '600', lineHeight: 25 },
  headline: { fontSize: 17, fontWeight: '600', lineHeight: 22 },
  body: { fontSize: 17, fontWeight: '400', lineHeight: 22 },
  callout: { fontSize: 16, fontWeight: '400', lineHeight: 21 },
  subhead: { fontSize: 15, fontWeight: '400', lineHeight: 20 },
  footnote: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
  caption1: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
  caption2: { fontSize: 11, fontWeight: '400', lineHeight: 13 },
};
```

## Spacing System

```typescript
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  '4xl': 40,
  '5xl': 48,
};

export const radius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  '2xl': 24,
  full: 9999,
};
```

## FinTech Component Patterns

### Balance Display

```typescript
export const BalanceCard = ({ balance, currency = 'USD', masked = false }) => (
  <View className="bg-slate-800 p-5 rounded-2xl">
    <Text className="text-slate-400 text-sm mb-1">Available Balance</Text>
    <View className="flex-row items-baseline">
      <Text className="text-white text-3xl font-bold">
        {masked ? '••••••' : formatCurrency(balance, currency)}
      </Text>
      <Text className="text-slate-400 text-sm ml-2">{currency}</Text>
    </View>
  </View>
);
```

### Transaction Item

```typescript
export const TransactionItem = ({ merchant, amount, date, category, icon }) => (
  <View 
    className="flex-row items-center py-3 border-b border-slate-700"
    accessibilityLabel={`${merchant}, ${formatCurrency(amount)}, ${date}`}
  >
    <View className="w-10 h-10 rounded-full bg-slate-700 items-center justify-center mr-3">
      <Icon name={icon} size={20} color="#94A3B8" />
    </View>
    <View className="flex-1">
      <Text className="text-white font-medium">{merchant}</Text>
      <Text className="text-slate-400 text-sm">{category}</Text>
    </View>
    <View className="items-end">
      <Text className={amount < 0 ? 'text-red-400 font-medium' : 'text-green-400 font-medium'}>
        {formatCurrency(amount)}
      </Text>
      <Text className="text-slate-500 text-xs">{date}</Text>
    </View>
  </View>
);
```

### Form Input

```typescript
export const FormInput = ({ 
  label, 
  value, 
  onChangeText, 
  error,
  secureTextEntry,
  ...props 
}) => (
  <View className="mb-4">
    <Text className="text-slate-300 text-sm mb-2">{label}</Text>
    <TextInput
      value={value}
      onChangeText={onChangeText}
      secureTextEntry={secureTextEntry}
      className={`bg-slate-800 border ${error ? 'border-red-500' : 'border-slate-600'} 
        rounded-lg px-4 py-3 text-white text-base min-h-[48px]`}
      placeholderTextColor="#64748B"
      accessibilityLabel={label}
      accessibilityState={{ error: !!error }}
      {...props}
    />
    {error && (
      <Text className="text-red-400 text-sm mt-1" accessibilityLiveRegion="polite">
        {error}
      </Text>
    )}
  </View>
);
```

## HTML/CSS Standards

### Tailwind Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            background: '#0F172A',
            surface: '#1E293B',
          }
        }
      }
    }
  </script>
</head>
<body class="bg-background min-h-screen text-white">
  <!-- Content -->
</body>
</html>
```

### Accessibility in HTML

```html
<!-- Buttons -->
<button 
  type="button"
  class="min-h-[44px] px-4 py-3"
  aria-label="Descriptive action"
  aria-disabled="false"
>
  Action
</button>

<!-- Form inputs -->
<label for="email" class="block text-sm mb-2">Email address</label>
<input 
  type="email" 
  id="email"
  name="email"
  aria-describedby="email-error"
  aria-invalid="false"
  class="w-full px-4 py-3 rounded-lg"
/>
<p id="email-error" role="alert" class="text-red-400 text-sm mt-1 hidden">
  Error message
</p>

<!-- Images -->
<img src="icon.svg" alt="Descriptive alt text" role="img" />

<!-- Headings (proper hierarchy) -->
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
```

## Code Quality Checklist

Before outputting generated code, verify:

- [ ] All colors meet WCAG 4.5:1 contrast for text
- [ ] Touch targets are minimum 44pt/48dp
- [ ] Accessibility labels on all interactive elements
- [ ] Proper TypeScript types/interfaces
- [ ] Error states handled
- [ ] Loading states included
- [ ] Safe areas respected (mobile)
- [ ] Keyboard dismissal handled (forms)
- [ ] No hardcoded strings (i18n ready)
