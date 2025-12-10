---
name: Word Document Handler
id: docx
version: 1.0
category: support
domain: [documents, office, writing]
task_types: [implementation, editing, creation]
keywords: [docx, word, document, office, editing, tracked changes, comments, formatting, pandoc, ooxml]
complexity: [normal, complex]
pairs_with: [pdf, pptx, xlsx]
source: https://github.com/anthropics/skills/tree/main/skills/docx
---

# Word Document Handler

## Role

Work with Word documents (.docx files) for creating new documents, modifying or editing content, working with tracked changes, adding comments, and document analysis.

## Core Capabilities

- Creating new documents
- Modifying/editing content
- Working with tracked changes
- Adding comments
- Document analysis

## Workflows by Task

### Reading Documents

**For text extraction**:
```bash
pandoc input.docx -t markdown -o output.md
```

**For detailed analysis** (comments, formatting, metadata):
```bash
# Unpack the docx (it's a ZIP file)
unzip document.docx -d unpacked/
# Examine XML structure
cat unpacked/word/document.xml
cat unpacked/word/comments.xml
```

### Creating New Documents

Use the `docx` library (JavaScript/TypeScript) for programmatic creation:

```javascript
import { Document, Packer, Paragraph, TextRun } from 'docx';

const doc = new Document({
  sections: [{
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text: "Hello World",
            bold: true,
          }),
        ],
      }),
    ],
  }],
});

// Save the document
const buffer = await Packer.toBuffer(doc);
fs.writeFileSync("output.docx", buffer);
```

### Editing Existing Documents

Use the `python-docx` library for modifications:

```python
from docx import Document

doc = Document('input.docx')

# Access paragraphs
for para in doc.paragraphs:
    print(para.text)

# Modify content
doc.paragraphs[0].text = "New content"

# Save
doc.save('output.docx')
```

### Tracked Changes (Redlining)

**Important**: For legal, academic, business, or government documents, use the redlining workflow.

**Process**:
1. Plan changes in markdown first
2. Implement in OOXML format
3. Mark only actual changes (not unchanged text)
4. Preserve original formatting

**Batch approach**: Implement changes in batches of 3-10 related modifications for manageable debugging.

## Technical Foundation

### DOCX Structure
```
document.docx (ZIP archive)
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── word/
│   ├── document.xml      # Main content
│   ├── styles.xml        # Style definitions
│   ├── comments.xml      # Document comments
│   ├── numbering.xml     # List definitions
│   └── media/            # Embedded images
└── docProps/
    ├── core.xml          # Metadata
    └── app.xml           # Application info
```

### Key XML Elements
```xml
<!-- Paragraph -->
<w:p>
  <w:pPr><!-- paragraph properties --></w:pPr>
  <w:r>
    <w:rPr><!-- run properties --></w:rPr>
    <w:t>Text content</w:t>
  </w:r>
</w:p>

<!-- Tracked insertion -->
<w:ins w:author="Name" w:date="2024-01-01T00:00:00Z">
  <w:r><w:t>Inserted text</w:t></w:r>
</w:ins>

<!-- Tracked deletion -->
<w:del w:author="Name" w:date="2024-01-01T00:00:00Z">
  <w:r><w:delText>Deleted text</w:delText></w:r>
</w:del>
```

## Utility Commands

### Pack/Unpack
```bash
# Unpack for editing
unzip document.docx -d unpacked/

# Repack after editing
cd unpacked && zip -r ../output.docx . && cd ..
```

### Convert to Images (for visual analysis)
```bash
# Convert to PDF first, then to images
libreoffice --headless --convert-to pdf document.docx
pdftoppm -png document.pdf output
```

## Best Practices

### Minimal Edits
- Only modify what's necessary
- Preserve existing formatting
- Don't repeat unchanged text in tracked changes

### Validation
- Test output opens in Word
- Verify tracked changes display correctly
- Check formatting preserved

### Error Handling
- Validate XML after edits
- Keep backup of original
- Test with different Word versions

## Common Tasks

| Task | Tool | Approach |
|------|------|----------|
| Extract text | pandoc | `pandoc file.docx -t markdown` |
| Read structure | unzip + inspect | Examine XML files |
| Create new | docx (JS) | Programmatic generation |
| Edit existing | python-docx | Load, modify, save |
| Track changes | OOXML direct | Edit XML with tracked change markup |
| Add comments | OOXML direct | Add to comments.xml |

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Rewriting entire document | Loses track changes | Minimal, targeted edits |
| Ignoring formatting | Breaks layout | Preserve style properties |
| Large change batches | Hard to debug | 3-10 changes at a time |
| Not validating output | Corrupt files | Test before delivery |

---

*Skill Version: 1.0*
*Source: Anthropic docx skill*
