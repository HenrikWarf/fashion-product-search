"""
Script to generate style concept images for the Athena fashion search app.
Uses Gemini Flash 2.5 Image to create visual representations of each style concept.
"""

import os
from datetime import datetime
from services.gcp_client import get_gcp_client
from vertexai.generative_models import GenerationConfig

# Style concepts matching those in static/app.js
STYLE_CONCEPTS = [
    {
        'id': 'minimalist',
        'title': 'Modern Minimalist',
        'filename': 'concept_minimalist.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing a modern minimalist style outfit.

STYLE CHARACTERISTICS:
- Clean, simple lines and contemporary silhouettes
- Neutral color palette: beige, grey, white, cream tones
- High-quality, structured fabrics (cotton, linen, fine knits)
- Minimal accessories and details
- Effortless, sophisticated elegance

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Natural, soft lighting
- Front-facing pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary fast-fashion catalog aesthetic (H&M, COS, Zara style)

OUTFIT ELEMENTS:
- Could include: tailored trousers, simple knit top, structured blazer, or minimal dress
- Focus on perfect fit and quality fabrics
- Neutral tones that work together harmoniously

AVOID:
- Busy patterns or prints
- Bright colors
- Excessive accessories
- Editorial or artistic photography styles'''
    },
    {
        'id': 'bohemian',
        'title': 'Bohemian Chic',
        'filename': 'concept_bohemian.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing a bohemian chic style outfit.

STYLE CHARACTERISTICS:
- Free-spirited, relaxed aesthetic
- Earthy color palette: olive green, terracotta, rust, warm browns, cream
- Flowing, natural fabrics (cotton, linen, soft rayon)
- Relaxed, comfortable fits
- Natural, effortless vibe

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Natural, soft lighting
- Front-facing pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary fast-fashion catalog aesthetic (H&M, Zara, Mango style)

OUTFIT ELEMENTS:
- Could include: flowing maxi dress, tunic, wide-leg pants, or layered separates
- Natural textures and draping
- Earthy, warm tones

AVOID:
- Outdoor or natural backgrounds (use studio setting)
- Excessive accessories or jewelry
- Editorial or artistic photography styles
- Overly costume-like or theatrical looks'''
    },
    {
        'id': 'elegant',
        'title': 'Elegant Evening',
        'filename': 'concept_elegant.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing an elegant evening style outfit.

STYLE CHARACTERISTICS:
- Sophisticated, refined aesthetic
- Rich color palette: deep jewel tones (emerald, sapphire, burgundy, navy)
- Luxurious fabrics: silk, satin, velvet, fine jersey
- Tailored, flattering fits
- Polished, dressy appearance

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Professional studio lighting with soft, even illumination
- Front-facing pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary fast-fashion catalog aesthetic (Zara, & Other Stories style)

OUTFIT ELEMENTS:
- Could include: elegant dress, tailored jumpsuit, or dressy separates
- Refined details like subtle draping or structured necklines
- Deep, rich colors that feel sophisticated

AVOID:
- Dramatic or editorial lighting
- Excessive sparkle or embellishments
- Formal gown styling (keep it wearable evening wear)
- Busy backgrounds'''
    },
    {
        'id': 'sporty',
        'title': 'Sporty Active',
        'filename': 'concept_sporty.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing a sporty active style outfit.

STYLE CHARACTERISTICS:
- Athletic, energetic aesthetic
- Bold color palette: bright blues, teals, coral, white, black
- Performance fabrics: technical knits, breathable materials
- Fitted, functional silhouettes
- Modern activewear style

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Natural, bright lighting
- Confident, active pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary activewear catalog aesthetic (Lululemon, Athleta, Nike style)

OUTFIT ELEMENTS:
- Could include: leggings, sports top, athletic jacket, or coordinated athleisure set
- Clean, modern lines
- Bold colors or color-blocking
- Functional yet stylish

AVOID:
- Gym or outdoor backgrounds (use studio setting)
- Excessive sportswear branding
- Action or movement blur
- Editorial or artistic photography styles'''
    },
    {
        'id': 'classic',
        'title': 'Classic Work',
        'filename': 'concept_classic.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing a classic workwear style outfit.

STYLE CHARACTERISTICS:
- Professional, polished aesthetic
- Neutral business palette: charcoal, navy, black, white, camel
- Structured, quality fabrics: wool blend, cotton poplin, fine knits
- Tailored, professional fits
- Timeless, office-appropriate style

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Professional studio lighting
- Confident, professional pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary workwear catalog aesthetic (Reiss, Massimo Dutti style)

OUTFIT ELEMENTS:
- Could include: tailored trousers, blazer, professional dress, or polished separates
- Classic silhouettes with modern touches
- Neutral, business-appropriate colors
- Professional and wearable

AVOID:
- Office or corporate backgrounds (use studio setting)
- Overly formal or conservative styling
- Dated business wear looks
- Busy patterns'''
    },
    {
        'id': 'casual',
        'title': 'Casual Weekend',
        'filename': 'concept_casual.png',
        'prompt': '''Create a professional fashion catalog photograph showcasing a casual weekend style outfit.

STYLE CHARACTERISTICS:
- Relaxed, comfortable aesthetic
- Warm, approachable palette: soft pinks, warm grays, denim blue, coral, cream
- Comfortable fabrics: cotton, denim, soft knits, jersey
- Easy, relaxed fits
- Everyday wearable style

COMPOSITION:
- Single model in a clean, minimalist white/light grey studio setting
- Natural, friendly lighting
- Relaxed, approachable pose showing full outfit
- 9:16 portrait orientation (vertical/mobile-friendly)
- Contemporary casual catalog aesthetic (Gap, J.Crew, Everlane style)

OUTFIT ELEMENTS:
- Could include: jeans, casual top, sweater, or comfortable dress
- Easy, wearable pieces for everyday life
- Warm, inviting colors
- Comfortable yet put-together

AVOID:
- Outdoor or lifestyle backgrounds (use studio setting)
- Overly loungewear or pajama-like styling
- Sloppy or unkempt appearance
- Editorial or artistic photography styles'''
    }
]


def generate_concept_image(concept: dict, output_dir: str = "static/concept_images") -> str:
    """
    Generate a concept image using Gemini Flash 2.5 Image.

    Args:
        concept: Dictionary with id, title, filename, and prompt
        output_dir: Directory to save generated images

    Returns:
        Path to saved image file
    """
    print(f"\n{'='*80}")
    print(f"GENERATING: {concept['title']}")
    print(f"{'='*80}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize GCP client and get Gemini Image model
    gcp_client = get_gcp_client()
    model = gcp_client.get_gemini_image_model()

    # Generation config
    generation_config = GenerationConfig(
        temperature=0.4,  # Lower temperature for more consistent style
        max_output_tokens=8192,
    )

    print(f"\n[1] Sending prompt to Gemini Flash 2.5 Image...")
    print(f"    Prompt length: {len(concept['prompt'])} characters")

    # Generate image
    response = model.generate_content(
        concept['prompt'],
        generation_config=generation_config
    )

    print(f"[2] Response received from Gemini")

    # Extract image data from response
    image_data = None
    if hasattr(response, 'candidates') and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    # Check for inline_data with image
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data') and part.inline_data.data:
                            image_data = part.inline_data.data
                            print(f"[3] Image data extracted: {len(image_data)} bytes ({len(image_data)/1024:.2f} KB)")
                            break

                    # Check for _raw_part structure
                    if hasattr(part, '_raw_part'):
                        raw_part = part._raw_part
                        if hasattr(raw_part, 'inline_data') and raw_part.inline_data:
                            if hasattr(raw_part.inline_data, 'data') and raw_part.inline_data.data:
                                image_data = raw_part.inline_data.data
                                print(f"[3] Image data extracted from _raw_part: {len(image_data)} bytes ({len(image_data)/1024:.2f} KB)")
                                break

                if image_data:
                    break

    if not image_data:
        raise ValueError(f"Failed to extract image data for {concept['title']}")

    # Save image
    filepath = os.path.join(output_dir, concept['filename'])
    print(f"\n[4] Saving image to: {filepath}")

    with open(filepath, 'wb') as f:
        f.write(image_data)

    print(f"[✓] Successfully generated {concept['title']}")
    print(f"    Saved to: {filepath}")
    print(f"{'='*80}\n")

    return filepath


def main():
    """Generate all concept images."""
    print("\n" + "="*80)
    print("STYLE CONCEPT IMAGE GENERATION")
    print("="*80)
    print(f"Total concepts to generate: {len(STYLE_CONCEPTS)}")
    print("="*80 + "\n")

    output_dir = "static/concept_images"
    generated_files = []

    for i, concept in enumerate(STYLE_CONCEPTS, 1):
        print(f"\nProgress: {i}/{len(STYLE_CONCEPTS)}")
        try:
            filepath = generate_concept_image(concept, output_dir)
            generated_files.append(filepath)
        except Exception as e:
            print(f"\n[✗] ERROR generating {concept['title']}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"Successfully generated: {len(generated_files)}/{len(STYLE_CONCEPTS)} images")
    print(f"\nGenerated files:")
    for filepath in generated_files:
        print(f"  - {filepath}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
