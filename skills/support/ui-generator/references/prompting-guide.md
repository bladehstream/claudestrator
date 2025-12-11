# UI Generation Prompting Guide

Effective prompts for Nano Banana and Gemini UI generation.

## Prompt Structure

### For Mockup Images (Nano Banana)

```
Design a [platform] [component-type] for [app-type] with:
- [Element 1]: [specific details]
- [Element 2]: [specific details]
- [Element 3]: [specific details]

Style: [theme] theme with [primary-color] primary, [accent-color] accents
Layout: [layout-description]
```

### For Code Generation (Gemini)

```
Create a [platform] [component-name] component that:
- [Functionality 1]
- [Functionality 2]
- [Functionality 3]

Props/State:
- [prop/state 1]: [type] - [purpose]
- [prop/state 2]: [type] - [purpose]

Styling: [framework] with [specific-styles]
```

## Template Examples

### FinTech Dashboard

**Image Prompt:**
```
Design a mobile fintech app dashboard screen showing:
- Header with user greeting and notification bell icon
- Balance card with large amount display, masked account number
- Quick action row: Send, Request, Pay Bills, More buttons
- Recent transactions list with merchant icons, amounts, dates
- Bottom navigation: Home, Cards, Scan, Activity, Profile

Style: Dark theme (#0F172A background), blue primary (#3B82F6), 
white text, subtle card shadows
Layout: Single column, cards with 16px padding and 12px border-radius
```

**Code Prompt:**
```
Create a React Native FinTech dashboard screen with:
- Animated balance card showing formatted currency
- Horizontal scroll quick actions with icons
- FlatList of transactions with pull-to-refresh
- Bottom tab navigator integration

State: balance (number), transactions (array), isRefreshing (boolean)
Styling: NativeWind with dark theme colors
Include TypeScript types and proper error handling
```

### Payment Form

**Image Prompt:**
```
Design a mobile payment form screen with:
- Card number input with card brand icon detection
- Row of expiry (MM/YY) and CVV inputs
- Amount input with currency dropdown
- Recipient field with contact picker icon
- Primary "Send Payment" button
- Secondary "Cancel" link

Style: Light theme, clean white cards, blue (#2563EB) primary button
Layout: Vertical stack, 24px section spacing, rounded inputs
```

**Code Prompt:**
```
Create a PaymentForm React Native component with:
- Credit card input with Luhn validation and formatting
- Expiry date input with MM/YY auto-formatting
- CVV input with 3-4 digit validation
- Amount input with currency formatting
- Form validation and error display
- Loading state on submit

Props: onSubmit (function), initialAmount (number), currencies (array)
Styling: NativeWind, form inputs with focus states
Include proper TypeScript interfaces
```

### Login Screen

**Image Prompt:**
```
Design a mobile banking login screen with:
- App logo at top (placeholder circle)
- Welcome text and subtitle
- Email input with icon
- Password input with show/hide toggle
- "Forgot Password?" link aligned right
- Primary "Sign In" button full width
- Biometric login button (Face ID / Fingerprint)
- "New user? Sign up" link at bottom

Style: Gradient background (#1E3A5F to #0F172A), white inputs,
blue accent buttons, subtle shadows
```

### Data Table / List

**Code Prompt:**
```
Create a TransactionList React Native component with:
- Section headers by date (Today, Yesterday, This Week, etc.)
- Transaction rows with merchant icon, name, category, amount
- Color-coded amounts (green positive, red negative)
- Swipe actions for delete/edit
- Empty state with illustration placeholder
- Skeleton loading state

Props: transactions (array), onDelete (function), isLoading (boolean)
Use FlatList with section support, NativeWind styling
```

## Key Principles

### Be Specific About Layout
- Specify exact spacing: "16px padding", "24px gap"
- Describe hierarchy: "large 32px balance, small 14px label"
- Define alignment: "center-aligned", "left-aligned with right amount"

### Include Visual Details
- Colors: Use hex codes "#3B82F6" not "blue"
- Shadows: "subtle shadow" or "elevation-2"
- Corners: "8px border-radius" or "fully rounded"
- Icons: Specify icon style (outlined, filled, size)

### Specify States
- Loading: skeleton, spinner, shimmer
- Error: red borders, error messages
- Empty: illustration, call-to-action
- Success: checkmarks, green accents

### Platform-Specific Notes

**React Native:**
- Use NativeWind className syntax
- Consider safe areas (StatusBar, bottom)
- Specify ScrollView vs FlatList usage

**React Web:**
- Include responsive breakpoints
- Specify hover states
- Consider accessibility (aria labels)

**HTML:**
- Include Tailwind CDN or style tag
- Use semantic elements
- Mobile-first responsive
