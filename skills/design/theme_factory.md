---
name: Theme Factory
id: theme_factory
version: 1.0
category: design
domain: [design, styling, presentation]
task_types: [design, styling, implementation]
keywords: [theme, color, palette, fonts, styling, design system, colors, branding, scheme]
complexity: [easy, normal]
pairs_with: [canvas_design, brand_guidelines, frontend_design, pptx]
source: https://github.com/anthropics/skills/tree/main/skills/theme-factory
---

# Theme Factory

## Role

Provide a curated toolkit with pre-set professional themes for styling various artifacts like presentations, documents, and web pages. Help users apply consistent, visually appealing themes.

## Workflow

1. Display theme showcase for visual reference
2. Request user selection
3. Apply chosen theme's colors and fonts throughout artifact
4. For unmet needs, generate custom themes based on user input

## Available Themes

### 1. Ocean Depths
| Element | Value |
|---------|-------|
| Primary | #0a4d68 |
| Secondary | #088395 |
| Accent | #05bfdb |
| Background | #00ffca |
| Text | #0a4d68 |
| Heading Font | Montserrat |
| Body Font | Open Sans |
| Context | Professional, calm, corporate |

### 2. Sunset Boulevard
| Element | Value |
|---------|-------|
| Primary | #ff6b35 |
| Secondary | #f7c59f |
| Accent | #efefef |
| Background | #2a2d34 |
| Text | #efefef |
| Heading Font | Playfair Display |
| Body Font | Raleway |
| Context | Creative, warm, energetic |

### 3. Forest Canopy
| Element | Value |
|---------|-------|
| Primary | #2d6a4f |
| Secondary | #40916c |
| Accent | #95d5b2 |
| Background | #d8f3dc |
| Text | #1b4332 |
| Heading Font | Merriweather |
| Body Font | Source Sans Pro |
| Context | Natural, organic, sustainable |

### 4. Modern Minimalist
| Element | Value |
|---------|-------|
| Primary | #000000 |
| Secondary | #333333 |
| Accent | #ff4444 |
| Background | #ffffff |
| Text | #000000 |
| Heading Font | Helvetica Neue |
| Body Font | Helvetica Neue |
| Context | Clean, modern, professional |

### 5. Golden Hour
| Element | Value |
|---------|-------|
| Primary | #daa520 |
| Secondary | #b8860b |
| Accent | #ffd700 |
| Background | #fffaf0 |
| Text | #4a3f35 |
| Heading Font | Cormorant Garamond |
| Body Font | Lato |
| Context | Luxury, warm, premium |

### 6. Arctic Frost
| Element | Value |
|---------|-------|
| Primary | #4a90a4 |
| Secondary | #a8dadc |
| Accent | #e63946 |
| Background | #f1faee |
| Text | #1d3557 |
| Heading Font | Roboto Slab |
| Body Font | Roboto |
| Context | Clean, fresh, modern |

### 7. Desert Rose
| Element | Value |
|---------|-------|
| Primary | #b5838d |
| Secondary | #e5989b |
| Accent | #ffcdb2 |
| Background | #fff1e6 |
| Text | #6d6875 |
| Heading Font | Josefin Sans |
| Body Font | Nunito |
| Context | Soft, feminine, elegant |

### 8. Tech Innovation
| Element | Value |
|---------|-------|
| Primary | #7209b7 |
| Secondary | #3a0ca3 |
| Accent | #4cc9f0 |
| Background | #0f0e17 |
| Text | #fffffe |
| Heading Font | Space Grotesk |
| Body Font | Inter |
| Context | Tech, futuristic, innovative |

### 9. Botanical Garden
| Element | Value |
|---------|-------|
| Primary | #606c38 |
| Secondary | #283618 |
| Accent | #fefae0 |
| Background | #dda15e |
| Text | #283618 |
| Heading Font | Libre Baskerville |
| Body Font | Karla |
| Context | Organic, artisanal, earthy |

### 10. Midnight Galaxy
| Element | Value |
|---------|-------|
| Primary | #7400b8 |
| Secondary | #6930c3 |
| Accent | #e0aaff |
| Background | #10002b |
| Text | #e0aaff |
| Heading Font | Orbitron |
| Body Font | Exo 2 |
| Context | Cosmic, dramatic, mysterious |

## Application Guidelines

### Maintaining Visual Identity
- Apply theme consistently across all elements
- Use primary color for main headings and key elements
- Use secondary for supporting elements
- Reserve accent for emphasis and CTAs
- Ensure text contrasts with background

### Contrast Requirements
```
WCAG AA Requirements:
- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio
- UI components: 3:1 contrast ratio
```

### CSS Implementation
```css
:root {
  /* Theme: [Theme Name] */
  --color-primary: [primary];
  --color-secondary: [secondary];
  --color-accent: [accent];
  --color-background: [background];
  --color-text: [text];

  --font-heading: '[heading font]', sans-serif;
  --font-body: '[body font]', sans-serif;
}

h1, h2, h3 {
  font-family: var(--font-heading);
  color: var(--color-primary);
}

body {
  font-family: var(--font-body);
  background: var(--color-background);
  color: var(--color-text);
}

.accent {
  color: var(--color-accent);
}

.button-primary {
  background: var(--color-primary);
  color: var(--color-background);
}
```

## Custom Theme Generation

When existing themes don't fit, generate custom themes based on:

1. **User's industry/context**: Tech, healthcare, finance, creative, etc.
2. **Mood/tone**: Professional, playful, serious, innovative
3. **Brand colors**: If user provides existing brand colors
4. **Accessibility needs**: High contrast requirements

### Custom Theme Template
```yaml
name: [Theme Name]
colors:
  primary: [hex]
  secondary: [hex]
  accent: [hex]
  background: [hex]
  text: [hex]
fonts:
  heading: [Font Name]
  body: [Font Name]
context: [Brief description of ideal use cases]
```

---

*Skill Version: 1.0*
*Source: Anthropic theme-factory skill*
