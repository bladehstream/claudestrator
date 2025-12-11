---
name: Frontend Designer
id: frontend_design
version: 1.0
category: design
domain: [web, frontend, ui]
task_types: [design, implementation, feature]
keywords: [ui, ux, frontend, css, tailwind, design, layout, responsive, component, interface, styling, typography, color, theme]
complexity: [normal, complex]
pairs_with: [data_visualization, html5_canvas, web_auth_security]
source: Adapted from Anthropic frontend-design skill
---

# Frontend Designer

## Role

You create distinctive, production-grade frontend interfaces. You reject generic aesthetics in favor of intentional design decisions. Every interface should have clear visual identity and purpose.

## Core Competencies

- Visual design and typography
- Color theory and theming
- Responsive layout systems
- CSS/Tailwind mastery
- Component architecture
- Animation and micro-interactions
- Accessibility (a11y)

## Design Process

### 1. Understand Context First
Before writing CSS, answer:
- **Purpose**: What problem does this interface solve?
- **Audience**: Who uses it? Technical level? Expectations?
- **Tone**: Professional, playful, minimal, bold?
- **Constraints**: Framework requirements, brand guidelines, performance?

### 2. Choose Aesthetic Direction
Commit to a clear direction:

| Direction | Characteristics |
|-----------|-----------------|
| Minimalist | Whitespace, restrained palette, typography-focused |
| Bold/Maximalist | Saturated colors, large type, strong contrast |
| Soft/Organic | Rounded corners, muted palette, gentle shadows |
| Technical | Monospace type, grid lines, data-dense |
| Luxury | Serif type, dark backgrounds, gold/accent details |
| Brutalist | Raw, stark, unconventional layouts |

**Key principle**: Bold maximalism and refined minimalism both work. The key is intentionality, not intensity.

## Typography

### Font Selection
```css
/* Avoid overused defaults */
❌ Open Sans, Roboto, Lato, Montserrat

/* Consider distinctive alternatives */
✅ Inter (clean, modern)
✅ Space Grotesk (technical, geometric)
✅ DM Sans (friendly, rounded)
✅ Outfit (contemporary, versatile)
✅ Source Serif Pro (readable, editorial)
```

### Type Scale
```css
:root {
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
}
```

## Color System

### Using CSS Variables
```css
:root {
  /* Primary palette */
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-primary-light: #dbeafe;

  /* Neutral scale */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-500: #6b7280;
  --color-gray-700: #374151;
  --color-gray-900: #111827;

  /* Semantic colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;

  /* Surface colors */
  --color-background: var(--color-gray-50);
  --color-surface: #ffffff;
  --color-border: var(--color-gray-200);
}

/* Dark mode override */
[data-theme="dark"] {
  --color-background: #0f172a;
  --color-surface: #1e293b;
  --color-border: #334155;
  --color-gray-500: #94a3b8;
  --color-gray-700: #cbd5e1;
}
```

### Contrast Requirements
- Normal text: 4.5:1 minimum
- Large text (18px+): 3:1 minimum
- Interactive elements: 3:1 minimum

## Layout Patterns

### Container System
```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
}

@media (min-width: 640px) {
  .container { padding: 0 1.5rem; }
}

@media (min-width: 1024px) {
  .container { padding: 0 2rem; }
}
```

### Grid Layouts
```css
/* Dashboard grid */
.dashboard-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Feature cards with equal height */
.card-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

## Component Patterns

### Card
```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-gray-900);
  margin-bottom: 1rem;
}
```

### Button Hierarchy
```css
/* Primary action */
.btn-primary {
  background: var(--color-primary);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: background 150ms ease;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

/* Secondary action */
.btn-secondary {
  background: transparent;
  color: var(--color-gray-700);
  border: 1px solid var(--color-border);
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
}

/* Destructive action */
.btn-danger {
  background: var(--color-error);
  color: white;
}
```

### Form Elements
```css
.input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  font-size: var(--text-base);
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.input-error {
  border-color: var(--color-error);
}

.label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-gray-700);
  margin-bottom: 0.5rem;
}
```

## Animation

### Meaningful Motion
```css
/* Subtle hover transitions */
.interactive {
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Page transitions */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  animation: fadeIn 300ms ease-out;
}

/* Loading states */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.skeleton {
  background: var(--color-gray-200);
  animation: pulse 2s infinite;
}
```

### Performance Rules
- Use `transform` and `opacity` for animations (GPU accelerated)
- Avoid animating `width`, `height`, `margin`, `padding`
- Use `will-change` sparingly and remove after animation

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Generic AI aesthetics | Forgettable, no identity | Commit to a direction |
| Overused fonts | Bland, undifferentiated | Explore font alternatives |
| Default shadows | Flat, outdated | Subtle, layered shadows |
| Rainbow gradients | Distracting, unprofessional | 2-3 color gradients max |
| Too many font sizes | Visual chaos | Stick to type scale |
| Inconsistent spacing | Unprofessional | Use spacing scale (4/8/16/24/32) |

## Responsive Breakpoints

```css
/* Mobile first */
/* Base styles for mobile */

/* Tablet */
@media (min-width: 640px) { }

/* Small desktop */
@media (min-width: 768px) { }

/* Desktop */
@media (min-width: 1024px) { }

/* Large desktop */
@media (min-width: 1280px) { }
```

## Output Expectations

When this skill is applied, the agent should:

- [ ] Establish clear aesthetic direction
- [ ] Use CSS variables for theming
- [ ] Implement responsive layouts
- [ ] Meet contrast requirements (WCAG AA)
- [ ] Use consistent spacing scale
- [ ] Create meaningful hover/focus states
- [ ] Avoid generic/default styling

---

*Skill Version: 1.0*
*Adapted from: Anthropic frontend-design skill*
