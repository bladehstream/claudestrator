---
name: ui-generator
id: ui_generator
version: "1.0"
category: support
description: AI-powered UI asset and code generation using Google Gemini API (Nano Banana for images, Gemini for code). Use when the user wants to generate UI mockups, component designs, wireframes, or production-ready frontend code (React Native, HTML/CSS, React) from text descriptions or reference images. Supports FinTech, mobile apps, web dashboards, and general UI/UX design workflows.
domain:
  - ui
  - frontend
  - react-native
  - react
  - html
  - design
task_types:
  - implementation
  - design
keywords:
  - ui generation
  - mockup
  - wireframe
  - gemini
  - nano banana
  - image generation
  - code generation
  - react native
  - tailwind
  - nativewind
  - component
  - design system
  - fintech ui
  - dashboard
  - mobile ui
  - web ui
complexity: normal
pairs_with:
  - frontend_design
  - brand_guidelines
source: ui-generator.skill (local)
---

# UI Generator Skill

Generate UI mockups and production-ready frontend code using Google's Gemini API.

## Capabilities

1. **Image Generation** (Nano Banana): Generate UI mockup images from text descriptions
2. **Image-to-Code**: Convert wireframes/screenshots to frontend code
3. **Text-to-Code**: Generate React Native, HTML/CSS, or React components from descriptions
4. **Style Transfer**: Apply design systems to generated components

## Prerequisites

Requires `GEMINI_API_KEY` environment variable. If not set, instruct user to:
1. Visit https://aistudio.google.com/apikey
2. Create API key (enable billing for Nano Banana Pro)
3. Set: `export GEMINI_API_KEY="your-key"`

## Quick Start

### Generate UI Mockup Image
```bash
python3 ui-generator/scripts/generate_ui.py --mode image --prompt "mobile fintech dashboard with balance card, transactions list, dark theme with blue accents" --output mockup.png
```

### Generate Code from Description
```bash
python3 ui-generator/scripts/generate_ui.py --mode code --prompt "payment form with card input, amount field, submit button" --platform react-native --output PaymentForm.tsx
```

### Convert Image to Code
```bash
python3 ui-generator/scripts/generate_ui.py --mode image-to-code --image wireframe.png --platform react-native --output Component.tsx
```

## Script Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `--mode` | image, code, image-to-code | Generation type |
| `--platform` | react-native, react, html | Output format |
| `--model` | flash, pro | Gemini model (flash=free tier) |
| `--prompt` | string | UI description |
| `--image` | path | Input image for conversion |
| `--output` | path | Output file path |

## Prompting Guide

See `ui-generator/references/prompting-guide.md` for detailed templates. Key principles:

**Be Specific:**
```
Bad:  "login screen"
Good: "mobile login screen for banking app with email/password fields, biometric login button, forgot password link, dark theme (#1a1a2e background, #4361ee accent)"
```

**Include Context:**
- Platform (mobile/web/tablet)
- Component type (screen/component/layout)
- Design system (colors, fonts, spacing)
- Interaction states (hover, loading, error)

## Model Selection

| Model | Use Case | Cost |
|-------|----------|------|
| `gemini-2.5-flash-image` (Nano Banana) | Fast mockups | Free tier: 350/month |
| `gemini-3-pro-image-preview` (Nano Banana Pro) | Production quality, better text | $0.134/image |
| `gemini-2.5-flash` | Fast code gen | Free tier available |
| `gemini-2.5-pro` | Complex components | Pay-per-token |

## Limitations

- Rate limits apply (check Google AI Studio for current quotas)
- Generated code requires review for production use
- Complex flows should be split into individual components
- Nano Banana Pro requires billing-enabled project

## Reference Documents

Consult these before generating code:

- `ui-generator/references/prompting-guide.md` - Prompt templates for Nano Banana
- `ui-generator/references/code-standards.md` - WCAG accessibility, color systems, component patterns

**Code Standards Include:**
- WCAG AA color contrast ratios (verified hex values)
- React Native component structure with TypeScript
- NativeWind/Tailwind patterns
- Accessibility attributes (accessibilityRole, accessibilityLabel)
- FinTech component patterns (BalanceCard, TransactionItem, FormInput)
