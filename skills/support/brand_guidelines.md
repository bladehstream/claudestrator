---
name: Brand Guidelines
id: brand_guidelines
version: 1.0
category: support
domain: [design, branding, presentation]
task_types: [design, implementation, styling]
keywords: [brand, branding, colors, fonts, typography, palette, style, guidelines, identity, visual]
complexity: [easy, normal]
pairs_with: [canvas_design, theme_factory, pptx]
source: https://github.com/anthropics/skills/tree/main/skills/brand-guidelines
---

# Brand Guidelines

## Role

Provide design resources for implementing consistent brand identity across various artifacts including presentations, documents, and web pages.

## Anthropic Brand Palette

### Primary Colors
```python
COLORS = {
    'dark': '#141413',      # Primary dark (backgrounds, text)
    'light': '#faf9f5',     # Primary light (backgrounds, text)
    'orange': '#e27b58',    # Accent option 1
    'blue': '#5b8ed0',      # Accent option 2
    'green': '#7ebd8f',     # Accent option 3
}
```

### Color Usage Guidelines
- **Dark (#141413)**: Primary text on light backgrounds, dark mode backgrounds
- **Light (#faf9f5)**: Primary backgrounds, text on dark
- **Accents**: Use for highlights, buttons, decorative elements

### Color Cycling
When applying colors to multiple elements, cycle through accents:
```python
ACCENT_CYCLE = ['orange', 'blue', 'green']

def get_accent_color(index):
    return COLORS[ACCENT_CYCLE[index % len(ACCENT_CYCLE)]]
```

## Typography

### Font Pairings
| Usage | Primary | Fallback |
|-------|---------|----------|
| Headings | Poppins | Arial |
| Body | Lora | Georgia |

### Size Hierarchy
- Headings (24pt+): Use Poppins
- Body text: Use Lora
- Captions/small text: Use Lora at reduced size

### Implementation
```python
def apply_font(text_element, size_pt):
    """Apply appropriate font based on size."""
    if size_pt >= 24:
        text_element.font.name = 'Poppins'
    else:
        text_element.font.name = 'Lora'
```

## Application Guidelines

### Presentations (PPTX)
```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# Convert hex to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )

# Apply brand colors
shape.fill.solid()
shape.fill.fore_color.rgb = hex_to_rgb('#e27b58')
```

### Web/CSS
```css
:root {
  --brand-dark: #141413;
  --brand-light: #faf9f5;
  --brand-orange: #e27b58;
  --brand-blue: #5b8ed0;
  --brand-green: #7ebd8f;

  --font-heading: 'Poppins', Arial, sans-serif;
  --font-body: 'Lora', Georgia, serif;
}

h1, h2, h3 {
  font-family: var(--font-heading);
  color: var(--brand-dark);
}

body {
  font-family: var(--font-body);
  background: var(--brand-light);
  color: var(--brand-dark);
}
```

### Documents
- Use Poppins for titles and section headers
- Use Lora for body paragraphs
- Apply accent colors sparingly for emphasis
- Maintain high contrast (dark on light or light on dark)

## Design Principles

1. **Consistency**: Apply the same colors and fonts throughout
2. **Contrast**: Ensure readability with proper color contrast
3. **Hierarchy**: Use size and weight to establish visual hierarchy
4. **Restraint**: Use accent colors sparingly for maximum impact
5. **Accessibility**: Meet WCAG contrast requirements

## Quick Reference

| Element | Color | Font | Size |
|---------|-------|------|------|
| Main Title | Dark | Poppins | 36-48pt |
| Subtitle | Dark (80% opacity) | Poppins | 24-30pt |
| Body | Dark | Lora | 14-18pt |
| Accent Text | Orange/Blue/Green | Poppins | Varies |
| Background | Light | - | - |

---

*Skill Version: 1.0*
*Source: Anthropic brand-guidelines skill*
