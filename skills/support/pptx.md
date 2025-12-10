---
name: PowerPoint Handler
id: pptx
version: 1.0
category: support
domain: [documents, office, presentation]
task_types: [implementation, creation, editing]
keywords: [pptx, powerpoint, presentation, slides, office, template, html2pptx, ooxml]
complexity: [normal, complex]
pairs_with: [docx, pdf, xlsx, brand_guidelines]
source: https://github.com/anthropics/skills/tree/main/skills/pptx
---

# PowerPoint Handler

## Role

Presentation creation, editing, and analysis. Use when Claude needs to work with presentations (.pptx files) for creating new presentations, modifying content, working with layouts, adding comments or speaker notes.

## Overview

PPTX files are ZIP archives containing XML files and resources. This skill covers reading, creating, and modifying PowerPoint presentations.

## Workflows

### Reading and Analyzing

**Text extraction**:
```bash
python -m markitdown path-to-file.pptx
```

**Raw XML access**:
```bash
# Unpack presentation
python ooxml/scripts/unpack.py presentation.pptx output_dir/
```

**Key file structure**:
```
presentation.pptx (ZIP)
├── ppt/
│   ├── presentation.xml     # Main structure
│   ├── slides/
│   │   └── slide1.xml       # Individual slides
│   ├── slideMasters/        # Master templates
│   ├── slideLayouts/        # Layout definitions
│   ├── theme/               # Theme colors/fonts
│   ├── media/               # Images, videos
│   └── notesSlides/         # Speaker notes
└── docProps/                # Metadata
```

### Creating New Presentations

**HTML2PPTX Workflow** (recommended for new presentations):

1. Create HTML files for each slide (720pt x 405pt for 16:9)
2. Convert using html2pptx library
3. Validate with thumbnails

**Slide HTML Template**:
```html
<div style="width: 720pt; height: 405pt; position: relative;">
  <h1 style="position: absolute; top: 40pt; left: 40pt;">
    Slide Title
  </h1>
  <p style="position: absolute; top: 120pt; left: 40pt;">
    Content goes here
  </p>
</div>
```

**Generate thumbnails for validation**:
```bash
python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```

### Editing Existing Presentations

**Workflow**:
1. Unpack the file
2. Edit XML content
3. Validate changes
4. Repack

```bash
# Unpack
python ooxml/scripts/unpack.py presentation.pptx unpacked/

# Edit XML files in unpacked/ppt/slides/

# Validate
python ooxml/scripts/validate.py unpacked/ --original presentation.pptx

# Repack
python ooxml/scripts/pack.py unpacked/ output.pptx
```

### Template-Based Creation

**Process**:
1. Extract text and create thumbnails
2. Analyze template structure
3. Create presentation outline
4. Duplicate/reorder slides as needed
5. Replace text content

```bash
# Get slide inventory
python scripts/inventory.py template.pptx

# Rearrange slides
python scripts/rearrange.py template.pptx output.pptx --order "1,2,1,3,4"

# Replace text
python scripts/replace.py output.pptx replacements.json
```

**Replacements JSON format**:
```json
{
  "slides": [
    {
      "slide_number": 1,
      "replacements": [
        {"old": "Template Title", "new": "My Presentation"},
        {"old": "Subtitle text", "new": "Custom subtitle"}
      ]
    }
  ]
}
```

## Design Principles

### Content-Informed Design
- Design serves content, not the reverse
- Clear hierarchy in each slide
- Readable at presentation distance

### Typography
- **Web-safe fonts only**: Arial, Calibri, Times New Roman, etc.
- Clear size hierarchy
- Consistent alignment

### Color Palettes

**Professional Options**:
| Name | Primary | Secondary | Accent |
|------|---------|-----------|--------|
| Classic Blue | #1a365d | #2b6cb0 | #63b3ed |
| Forest | #1c4532 | #276749 | #68d391 |
| Coral | #742a2a | #c53030 | #fc8181 |
| Slate | #1a202c | #4a5568 | #a0aec0 |
| Purple | #44337a | #6b46c1 | #b794f4 |

### Layout Guidelines
- Consistent margins (40pt typical)
- Alignment guides
- Visual balance
- White space intentional

## Image Conversion

**PPTX to images**:
```bash
# Convert to PDF first
libreoffice --headless --convert-to pdf presentation.pptx

# Then to images
pdftoppm -jpeg presentation.pdf slide -r 150
```

## Dependencies

```bash
# Python packages
pip install markitdown defusedxml

# Node packages (for html2pptx)
npm install pptxgenjs playwright sharp

# System tools
apt install libreoffice poppler-utils
```

## Quick Reference

| Task | Tool/Method |
|------|-------------|
| Extract text | `python -m markitdown file.pptx` |
| Unpack/edit XML | unpack.py → edit → pack.py |
| Create from HTML | html2pptx workflow |
| Use template | inventory → rearrange → replace |
| Generate thumbnails | `python scripts/thumbnail.py` |
| Convert to images | LibreOffice → pdftoppm |

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Custom fonts | Fallback issues | Web-safe fonts |
| Cluttered slides | Hard to read | One idea per slide |
| Inconsistent styling | Unprofessional | Use template/theme |
| Direct XML edits without validation | Corrupt files | Always validate |
| Ignoring aspect ratio | Cropped content | Match template ratio |

---

*Skill Version: 1.0*
*Source: Anthropic pptx skill*
