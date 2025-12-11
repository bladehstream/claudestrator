#!/usr/bin/env python3
"""
UI Generator - Generate UI mockups and code using Google Gemini API.

Supports:
- Image generation (Nano Banana): Text-to-UI mockup images
- Code generation: Text-to-frontend code (React Native, React, HTML)
- Image-to-code: Convert wireframes/designs to code

Prerequisites:
    export GEMINI_API_KEY="your-api-key"
    pip install google-genai pillow --break-system-packages

Usage:
    # Generate mockup image
    python generate_ui.py --mode image --prompt "fintech dashboard" --output mockup.png
    
    # Generate code from description
    python generate_ui.py --mode code --prompt "payment form" --platform react-native --output PaymentForm.tsx
    
    # Convert image to code  
    python generate_ui.py --mode image-to-code --image wireframe.png --platform react-native --output Component.tsx
"""

import argparse
import base64
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies."""
    try:
        from google import genai
        from PIL import Image
        return True
    except ImportError:
        print("Installing required dependencies...")
        os.system("pip install google-genai pillow --break-system-packages -q")
        return True

def get_client():
    """Initialize Gemini client with API key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Get your API key at: https://aistudio.google.com/apikey")
        sys.exit(1)
    
    from google import genai
    return genai.Client(api_key=api_key)

def generate_ui_image(client, prompt: str, output_path: str, model: str = "flash"):
    """Generate UI mockup image using Nano Banana."""
    from PIL import Image
    import io
    
    model_id = "gemini-2.5-flash-image" if model == "flash" else "gemini-3-pro-image-preview"
    
    # Enhance prompt for UI generation
    enhanced_prompt = f"""Generate a high-quality UI mockup image:

{prompt}

Requirements:
- Clean, modern design
- Proper spacing and alignment
- Legible text labels
- Professional color palette
- Mobile or web appropriate sizing
"""
    
    print(f"Generating UI mockup with {model_id}...")
    
    response = client.models.generate_content(
        model=model_id,
        contents=[enhanced_prompt]
    )
    
    # Extract image from response
    for part in response.parts:
        if hasattr(part, 'inline_data') and part.inline_data is not None:
            image_data = base64.b64decode(part.inline_data.data)
            image = Image.open(io.BytesIO(image_data))
            image.save(output_path)
            print(f"✅ UI mockup saved to: {output_path}")
            return True
        elif hasattr(part, 'text') and part.text:
            print(f"Model response: {part.text}")
    
    print("❌ No image generated. The model may have returned text instead.")
    return False

def generate_ui_code(client, prompt: str, platform: str, output_path: str, model: str = "flash"):
    """Generate UI code from text description."""
    model_id = "gemini-2.5-flash" if model == "flash" else "gemini-2.5-pro"
    
    platform_instructions = {
        "react-native": """Generate React Native TypeScript code with:
- Functional component with proper TypeScript types
- NativeWind/Tailwind CSS classes for styling (className prop)
- Proper imports from react-native
- Responsive design considerations
- Include necessary state management with hooks""",
        
        "react": """Generate React TypeScript/JSX code with:
- Functional component with TypeScript types
- Tailwind CSS classes for styling
- Proper React hooks for state
- Accessible HTML semantics
- Responsive design with Tailwind breakpoints""",
        
        "html": """Generate clean HTML with embedded CSS:
- Semantic HTML5 elements
- Inline Tailwind CSS via CDN or embedded styles
- Mobile-first responsive design
- Accessible form elements if applicable
- Modern CSS features (flexbox, grid)"""
    }
    
    system_prompt = f"""You are a senior frontend developer. Generate production-ready UI code.

Platform: {platform}
{platform_instructions.get(platform, platform_instructions['react'])}

Requirements:
- Clean, maintainable code
- Proper component structure
- Include all necessary imports
- Add brief comments for complex logic
- Handle loading and error states where appropriate

Output ONLY the code, no explanations."""

    print(f"Generating {platform} code with {model_id}...")
    
    response = client.models.generate_content(
        model=model_id,
        contents=[
            {"role": "user", "parts": [{"text": system_prompt + "\n\nGenerate: " + prompt}]}
        ]
    )
    
    code = response.text
    
    # Clean up markdown code blocks if present
    if code.startswith("```"):
        lines = code.split("\n")
        # Remove first line (```language) and last line (```)
        code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    
    Path(output_path).write_text(code)
    print(f"✅ Code saved to: {output_path}")
    return True

def image_to_code(client, image_path: str, platform: str, output_path: str, model: str = "flash"):
    """Convert UI image/wireframe to code."""
    from PIL import Image
    import io
    
    model_id = "gemini-2.5-flash" if model == "flash" else "gemini-2.5-pro"
    
    # Load and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_types.get(ext, "image/png")
    
    platform_instructions = {
        "react-native": "React Native TypeScript with NativeWind/Tailwind classes",
        "react": "React TypeScript with Tailwind CSS",
        "html": "HTML5 with Tailwind CSS"
    }
    
    prompt = f"""Analyze this UI design image and generate production-ready {platform_instructions.get(platform, 'React')} code that recreates it.

Requirements:
- Match the layout, spacing, and visual hierarchy exactly
- Use appropriate colors (extract from image or use sensible defaults)
- Include all visible UI elements
- Make it responsive
- Use proper semantic elements
- Include necessary state management for interactive elements

Output ONLY the code, no explanations or markdown."""

    print(f"Converting image to {platform} code with {model_id}...")
    
    response = client.models.generate_content(
        model=model_id,
        contents=[
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_data}},
                    {"text": prompt}
                ]
            }
        ]
    )
    
    code = response.text
    
    # Clean up markdown code blocks if present
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    
    Path(output_path).write_text(code)
    print(f"✅ Code saved to: {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate UI mockups and code using Gemini API")
    parser.add_argument("--mode", choices=["image", "code", "image-to-code"], required=True,
                        help="Generation mode")
    parser.add_argument("--prompt", type=str, help="UI description prompt")
    parser.add_argument("--image", type=str, help="Input image path (for image-to-code mode)")
    parser.add_argument("--platform", choices=["react-native", "react", "html"], default="react-native",
                        help="Target platform for code generation")
    parser.add_argument("--model", choices=["flash", "pro"], default="flash",
                        help="Model tier (flash=faster/cheaper, pro=higher quality)")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode in ["image", "code"] and not args.prompt:
        parser.error(f"--prompt is required for {args.mode} mode")
    if args.mode == "image-to-code" and not args.image:
        parser.error("--image is required for image-to-code mode")
    
    check_dependencies()
    client = get_client()
    
    if args.mode == "image":
        generate_ui_image(client, args.prompt, args.output, args.model)
    elif args.mode == "code":
        generate_ui_code(client, args.prompt, args.platform, args.output, args.model)
    elif args.mode == "image-to-code":
        image_to_code(client, args.image, args.platform, args.output, args.model)

if __name__ == "__main__":
    main()
