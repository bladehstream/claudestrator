---
name: Slack GIF Creator
id: slack_gif_creator
version: 1.0
category: implementation
domain: [creative, animation, slack]
task_types: [implementation, creative, asset]
keywords: [gif, slack, animation, emoji, animated, pillow, imageio, custom, reaction]
complexity: [normal]
pairs_with: [algorithmic_art, svg_asset_generator]
source: https://github.com/anthropics/skills/tree/main/skills/slack-gif-creator
---

# Slack GIF Creator

## Role

Create animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack."

## Slack Requirements

### Dimensions
| Type | Size | Notes |
|------|------|-------|
| Emoji GIFs | 128x128 | Recommended for custom emoji |
| Message GIFs | 480x480 | For inline messages |

### Parameters
| Parameter | Range | Notes |
|-----------|-------|-------|
| FPS | 10-30 | Lower = smaller file |
| Colors | 48-128 | Fewer = smaller file |
| Duration | <3 sec | For emoji GIFs |

## Core Workflow

```python
from PIL import Image, ImageDraw
import imageio
import numpy as np

class GIFBuilder:
    def __init__(self, width=128, height=128, fps=15, loop=0):
        self.width = width
        self.height = height
        self.fps = fps
        self.loop = loop  # 0 = infinite loop
        self.frames = []

    def add_frame(self, image):
        """Add a PIL Image frame."""
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        self.frames.append(image)

    def add_frames(self, images):
        """Add multiple frames."""
        for img in images:
            self.add_frame(img)

    def save(self, path, optimize=True, colors=128):
        """Save the GIF."""
        if not self.frames:
            raise ValueError("No frames to save")

        duration = 1000 // self.fps  # ms per frame

        self.frames[0].save(
            path,
            save_all=True,
            append_images=self.frames[1:],
            duration=duration,
            loop=self.loop,
            optimize=optimize,
            colors=colors,
        )

    def preview_frames(self):
        """Return frame count and duration info."""
        return {
            "frames": len(self.frames),
            "duration_sec": len(self.frames) / self.fps,
            "size": f"{self.width}x{self.height}",
        }
```

## Drawing Graphics

### Working with User-Uploaded Images

```python
from PIL import Image

# Load and resize user image
user_img = Image.open("uploaded.png")
user_img = user_img.convert("RGBA")
user_img = user_img.resize((100, 100), Image.Resampling.LANCZOS)

# Create frame with user image
frame = Image.new("RGBA", (128, 128), (255, 255, 255, 255))
# Center the image
x = (128 - 100) // 2
y = (128 - 100) // 2
frame.paste(user_img, (x, y), user_img)
```

### Drawing from Scratch

```python
from PIL import Image, ImageDraw

# Create blank frame
frame = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
draw = ImageDraw.Draw(frame)

# Basic shapes
draw.rectangle([10, 10, 50, 50], fill="red", outline="black")
draw.ellipse([60, 10, 100, 50], fill="blue")
draw.line([10, 70, 100, 70], fill="green", width=3)
draw.polygon([(64, 80), (40, 120), (88, 120)], fill="yellow")

# Text (use default font or load custom)
draw.text((10, 10), "Hi!", fill="black")
```

## Animation Concepts

### Shake/Vibrate
```python
def shake_animation(base_image, intensity=3, frames=10):
    """Create shake effect."""
    result = []
    for i in range(frames):
        frame = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        offset_x = int(np.sin(i * 0.8) * intensity)
        offset_y = int(np.cos(i * 1.2) * intensity)
        frame.paste(base_image, (offset_x, offset_y))
        result.append(frame)
    return result
```

### Pulse/Heartbeat
```python
def pulse_animation(base_image, min_scale=0.9, max_scale=1.1, frames=20):
    """Create pulse effect."""
    result = []
    for i in range(frames):
        t = i / frames
        scale = min_scale + (max_scale - min_scale) * (0.5 + 0.5 * np.sin(t * 2 * np.pi))

        new_size = (int(base_image.width * scale), int(base_image.height * scale))
        scaled = base_image.resize(new_size, Image.Resampling.LANCZOS)

        frame = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        x = (base_image.width - new_size[0]) // 2
        y = (base_image.height - new_size[1]) // 2
        frame.paste(scaled, (x, y))
        result.append(frame)
    return result
```

### Bounce
```python
def bounce_animation(base_image, height=20, frames=15):
    """Create bounce effect."""
    result = []
    for i in range(frames):
        t = i / frames
        # Eased bounce using sine
        y_offset = int(abs(np.sin(t * np.pi)) * height)

        frame = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        frame.paste(base_image, (0, -y_offset))
        result.append(frame)
    return result
```

### Spin/Rotate
```python
def spin_animation(base_image, frames=20):
    """Create spin effect."""
    result = []
    for i in range(frames):
        angle = (i / frames) * 360
        rotated = base_image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        result.append(rotated)
    return result
```

### Fade In/Out
```python
def fade_animation(base_image, frames=15, fade_in=True):
    """Create fade effect."""
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        if not fade_in:
            t = 1 - t

        frame = base_image.copy()
        alpha = frame.split()[3]
        alpha = alpha.point(lambda x: int(x * t))
        frame.putalpha(alpha)
        result.append(frame)
    return result
```

## Easing Functions

```python
import math

def ease_in_out_quad(t):
    """Smooth acceleration and deceleration."""
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2

def ease_out_bounce(t):
    """Bouncy end."""
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

def ease_in_elastic(t):
    """Elastic snap."""
    if t == 0 or t == 1:
        return t
    return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * math.pi / 3))
```

## Optimization Strategies

### Reduce File Size

```python
# Fewer colors
gif.save(path, colors=64)  # Instead of 256

# Lower FPS
builder = GIFBuilder(fps=10)  # Instead of 30

# Smaller dimensions
builder = GIFBuilder(width=64, height=64)  # For very small emoji

# Optimize palette
gif.save(path, optimize=True)
```

### Validate Before Delivery

```python
import os

def validate_gif(path, max_kb=128):
    """Check GIF meets Slack requirements."""
    size_kb = os.path.getsize(path) / 1024

    with Image.open(path) as img:
        width, height = img.size
        n_frames = img.n_frames

    issues = []
    if size_kb > max_kb:
        issues.append(f"File size {size_kb:.1f}KB > {max_kb}KB limit")
    if width > 128 or height > 128:
        issues.append(f"Size {width}x{height} > 128x128 for emoji")

    return {"valid": len(issues) == 0, "issues": issues, "size_kb": size_kb}
```

## Dependencies

```bash
pip install pillow imageio numpy
```

---

*Skill Version: 1.0*
*Source: Anthropic slack-gif-creator skill*
