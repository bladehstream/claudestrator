---
name: Canvas Designer
id: canvas_design
version: 1.0
category: design
domain: [art, design, creative, print]
task_types: [design, creative, implementation]
keywords: [canvas, design, poster, art, visual, pdf, png, static, composition, typography, color, layout]
complexity: [normal, complex]
pairs_with: [algorithmic_art, brand_guidelines, theme_factory]
source: https://github.com/anthropics/skills/tree/main/skills/canvas-design
---

# Canvas Designer

## Role

Create beautiful visual art in .png and .pdf documents using design philosophy. Use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.

## Core Process

### Two-Step Workflow
1. **Philosophy Development**: Establish a design philosophy (aesthetic movement expressed via form, color, composition)
2. **Visual Manifestation**: Execute the philosophy in PDF or PNG format

## Design Philosophy

### Creating a Philosophy Manifesto

Write 4-6 paragraphs that:
- Name an aesthetic movement (e.g., "Brutalist Joy", "Chromatic Silence")
- Articulate aesthetic direction through spatial, chromatic, and compositional language
- Guide all visual decisions
- Leave room for creative interpretation

### Philosophy Examples

**Brutalist Joy**: Raw concrete forms meet unexpected bursts of color. Heavy geometric shapes anchor compositions while playful elements dance at edges. Typography is bold, unapologetic.

**Chromatic Silence**: Vast fields of carefully chosen color create meditative spaces. Elements are minimal, precisely placed. The absence speaks louder than presence.

**Geometric Harvest**: Organic forms constructed from sharp angles. Warm earth tones meet golden accents. Patterns suggest growth, abundance, structure.

## Design Principles

### Visual Communication
- Text appears as rare, powerful gesture
- Only essential typography
- Let visuals carry the message
- Every element serves purpose

### Craftsmanship Standard
- Work should appear "meticulously crafted"
- Suggest countless hours of expert labor
- Achieve "museum or magazine quality"
- "Pristine, masterpiece" execution

### Composition Rules
- No redundancy across design aspects
- Each element mentioned once with depth
- "Nothing falls off the page and nothing overlaps"
- Professional margins throughout

## Canvas Execution

### Technical Requirements
- Single-page, highly visual compositions
- Systematic patterns and perfect shapes
- Limited, intentional color palettes
- Minimal, positioned typography (text as design element)

### Layout Guidelines
```
+----------------------------------+
|          [margin]                |
|   +------------------------+     |
|   |                        |     |
|   |    Visual Content      |     |
|   |                        |     |
|   |    [systematic         |     |
|   |     patterns]          |     |
|   |                        |     |
|   +------------------------+     |
|   |  Typography (if any)   |     |
|          [margin]                |
+----------------------------------+
```

### Color Palette Approach
```python
# Limited, intentional palettes
palette = {
    'primary': '#...',      # Dominant color
    'secondary': '#...',    # Supporting color
    'accent': '#...',       # Highlight/contrast
    'background': '#...',   # Canvas base
}

# Each color serves specific purpose
# Never more than 4-5 colors
```

### Typography as Design
```css
/* Typography is a design element, not just text */
.title {
  /* Position intentionally */
  position: absolute;
  /* Size for visual impact */
  font-size: [large];
  /* Treat as shape in composition */
}
```

## Quality Standards

### The Test
"Would this hang in a museum?"
"Would this appear in a design magazine?"

### Refinement Process
1. Complete initial composition
2. Review against philosophy
3. Refine composition (not add more)
4. Remove anything non-essential
5. Perfect alignment and spacing
6. Final quality check

### What Makes Quality
- Flawless execution
- Clear visual hierarchy
- Balanced negative space
- Harmonious color relationships
- Intentional every detail

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Cluttered composition | Overwhelming, unprofessional | Embrace negative space |
| Random color choices | Discordant, amateur | Intentional palette |
| Centered everything | Boring, predictable | Dynamic positioning |
| Too much text | Dilutes visual impact | Text as rare gesture |
| Adding more graphics | Busy, confused | Refine, don't add |
| Copying existing work | Copyright issues, unoriginal | Develop unique philosophy |

## Output Formats

### PNG Generation
- High resolution (300dpi for print, 72dpi for screen)
- Appropriate dimensions for use case
- Optimized file size

### PDF Generation
- Vector where possible
- Proper bleed for print
- Embedded fonts
- Color space appropriate to use (RGB/CMYK)

## Workflow Summary

1. **Understand request**: What is the purpose? Who is the audience?
2. **Develop philosophy**: Write your aesthetic manifesto
3. **Plan composition**: Sketch layout based on philosophy
4. **Select palette**: Choose intentional, limited colors
5. **Execute design**: Build with systematic precision
6. **Refine**: Remove, don't add
7. **Deliver**: Export in appropriate format

---

*Skill Version: 1.0*
*Source: Anthropic canvas-design skill*
