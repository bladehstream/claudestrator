---
name: Algorithmic Art Creator
id: algorithmic_art
version: 1.0
category: implementation
domain: [art, web, creative]
task_types: [implementation, feature, creative]
keywords: [algorithmic, art, generative, p5js, canvas, creative, visual, random, seeded, interactive, particle, flow, pattern]
complexity: [normal, complex]
pairs_with: [html5_canvas, canvas_design, theme_factory]
source: https://github.com/anthropics/skills/tree/main/skills/algorithmic-art
---

# Algorithmic Art Creator

## Role

Create original algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid copyright violations.

## Algorithmic Philosophies

The algorithm flows from the philosophy. Never select from a set of preset patterns. Instead, develop a unique philosophy for each piece that guides all visual decisions.

### Philosophy Structure

A philosophy is a 4-6 paragraph manifesto that:
- Names an aesthetic movement (e.g., "Organic Turbulence", "Quantum Harmonics")
- Articulates direction through spatial, chromatic, and compositional language
- Guides form, color, and composition choices
- Leaves room for creative interpretation

### Example Philosophies

**Organic Turbulence**: Embraces natural flow and chaos. Elements curve and swirl like wind through leaves. Colors shift gradually through organic palettes. Movement is never linear.

**Quantum Harmonics**: Discrete particles exist in probability clouds. Sharp geometric forms vibrate at edges. Dualistic color schemes create tension. Small variations compound into complex patterns.

**Recursive Whispers**: Self-similar forms nest infinitely. Each level echoes the parent but transformed. Muted palettes where each iteration fades. Space between repetitions carries meaning.

## Essential Principles

1. **Philosophy First**: Develop the aesthetic philosophy before any code
2. **Seeded Randomness**: All randomness must be reproducible via seed
3. **Parametric Expression**: Key variables exposed for exploration
4. **Interactive Controls**: Users can modify parameters and save favorites

## Technical Requirements

### Seeded Randomness
```javascript
// Always use seeded random
let seed;

function setup() {
  seed = floor(random(1000000));
  randomSeed(seed);
  noiseSeed(seed);
}

function regenerate(newSeed) {
  seed = newSeed;
  randomSeed(seed);
  noiseSeed(seed);
  // Regenerate artwork
}
```

### Parameter Structure
```javascript
const params = {
  // Core parameters
  complexity: 0.5,      // 0-1 range
  density: 0.7,         // 0-1 range
  speed: 1.0,           // Multiplier

  // Palette
  hueBase: 200,         // Starting hue
  saturation: 70,       // Base saturation

  // Composition
  centerWeight: 0.5,    // How centered vs. distributed
  scale: 1.0,           // Overall size multiplier
};
```

### Core Algorithm Pattern
```javascript
function generateArt() {
  // 1. Initialize based on philosophy
  initializeFromPhilosophy();

  // 2. Create base structure
  createPrimaryForms();

  // 3. Add complexity layers
  addSecondaryElements();

  // 4. Apply finishing effects
  applyAtmosphericEffects();
}
```

## Interactive Artifact Structure

### Required UI Elements
- Seed input/display with navigation (prev/next/random)
- Parameter sliders for key variables
- Save/export functionality
- Reset to defaults button

### Template Structure
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/p5@1.9.0/lib/p5.min.js"></script>
  <style>
    body {
      margin: 0;
      background: #141413;
      font-family: system-ui;
      color: #faf9f5;
    }
    .controls {
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(20, 20, 19, 0.9);
      padding: 20px;
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <div class="controls">
    <!-- Parameter controls here -->
  </div>
  <script>
    // p5.js sketch here
  </script>
</body>
</html>
```

## Craftsmanship Requirements

- **No visual artifacts**: Clean edges, no aliasing issues
- **Smooth motion**: Consistent frame rate, smooth interpolation
- **Color harmony**: Intentional palette, not random colors
- **Balanced composition**: Visual weight distributed thoughtfully
- **Responsive canvas**: Adapts to window size

## The Creative Process

1. **Understand the request**: What emotion or concept should the art evoke?
2. **Develop philosophy**: Write 4-6 paragraphs describing the aesthetic approach
3. **Design algorithm**: Plan the technical approach based on philosophy
4. **Implement core**: Build the primary visual generation
5. **Add interactivity**: Parameter controls and seed navigation
6. **Refine and polish**: Iterate on visual quality

## Quality Standards

- Every piece must have a unique visual identity
- Parameters should meaningfully affect output
- Seed navigation should reveal variety in the algorithm
- UI should be unobtrusive but accessible
- Code should be clean and well-organized

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| Preset patterns | Generic, uninspired | Develop unique philosophy |
| Unseeded random | Non-reproducible | Always use seeded random |
| Hard-coded values | Inflexible | Use parameters |
| Copy existing artists | Copyright issues | Create original work |
| Overly complex UI | Distracting | Minimal, effective controls |

---

*Skill Version: 1.0*
*Source: Anthropic algorithmic-art skill*
