import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.gcp_client import get_gcp_client
from vertexai.generative_models import Image, GenerationConfig
import io


class LookGenerationService:
    """Service for generating styled outfit looks by combining multiple products using Gemini."""

    def __init__(self):
        self.gcp_client = get_gcp_client()
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_look_from_products(
        self,
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a styled outfit look combining 2-3 fashion products.

        Args:
            products: List of 2-3 product dictionaries with image_url and details

        Returns:
            Dictionary with look_image_url, description, and product references
        """

        print("\n" + "="*80)
        print("LOOK GENERATION STARTED")
        print("="*80)
        print(f"Number of products: {len(products)}")

        if len(products) < 2:
            raise ValueError("At least 2 products required to create a look")
        if len(products) > 3:
            raise ValueError("Maximum 3 products allowed for look creation")

        try:
            # Load product images
            print("\n[1] Loading product images...")
            product_images = []
            product_descriptions = []

            for i, product in enumerate(products):
                print(f"\n  Product {i+1}: {product.get('name', 'Unknown')}")
                print(f"    Image URL: {product.get('image_url', 'N/A')}")

                # Load image from URL
                image_url = product.get('image_url', '')
                if image_url:
                    try:
                        image_obj = self._load_image_from_url(image_url)
                        product_images.append(image_obj)
                        print(f"    [✓] Image loaded successfully")

                        # Build detailed product description
                        desc = self._build_product_description(product, i+1)
                        product_descriptions.append(desc)
                        print(f"    Description: {desc[:100]}...")
                    except Exception as e:
                        print(f"    [✗] Failed to load image: {e}")
                        raise ValueError(f"Could not load image for product: {product.get('name')}")

            print(f"\n[✓] Loaded {len(product_images)} product images")

            # Build the look generation prompt
            print("\n[2] Building look generation prompt...")
            prompt = self._build_look_prompt(product_descriptions)
            print(f"[✓] Prompt built ({len(prompt)} characters)")
            print(f"\nPrompt preview:\n{prompt[:300]}...\n")

            # Generate look with Gemini Flash 2.5 Image
            print("[3] Initializing Gemini 2.5 Flash Image model...")
            model = self.gcp_client.get_gemini_image_model()
            print("[✓] Model initialized")

            generation_config = GenerationConfig(
                temperature=0.6,  # Balanced creativity while maintaining catalog style
                max_output_tokens=8192,
            )

            # Prepare content with images and prompt
            print("\n[4] Preparing multimodal content (images + prompt)...")
            content_parts = []
            for img in product_images:
                content_parts.append(img)
            content_parts.append(prompt)
            print(f"[✓] Content prepared: {len(product_images)} images + 1 text prompt")

            # Send request to Gemini
            print("\n[5] Sending request to Gemini...")
            response = model.generate_content(
                content_parts,
                generation_config=generation_config
            )
            print("[✓] Response received from Gemini")

            # Extract generated look image
            print("\n[6] Extracting look image from response...")
            image_data = self._extract_image_from_response(response)

            if image_data:
                print(f"[✓] Image data extracted: {len(image_data)} bytes ({len(image_data)/1024:.2f} KB)")

                # Save look image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"look_{timestamp}.png"
                filepath = os.path.join(self.output_dir, filename)

                print(f"\n[7] Saving look image...")
                print(f"    Filepath: {filepath}")
                with open(filepath, "wb") as f:
                    f.write(image_data)
                print(f"[✓] Look image saved successfully")

                image_url = f"/images/{filename}"

                # Generate description
                description = self._generate_look_description(products)

                print(f"\n[8] Returning response")
                print(f"    Image URL: {image_url}")
                print(f"    Description: {description}")
                print("="*80)
                print("LOOK GENERATION COMPLETED SUCCESSFULLY")
                print("="*80 + "\n")

                return {
                    "look_image_url": image_url,
                    "description": description,
                    "products": products,
                    "local_path": filepath
                }
            else:
                print("[✗] No image data extracted from response")
                raise ValueError("Failed to generate look image from Gemini")

        except Exception as e:
            print(f"\n[✗] ERROR in look generation:")
            print(f"    Error type: {type(e).__name__}")
            print(f"    Error message: {str(e)}")
            import traceback
            print(f"    Traceback:")
            traceback.print_exc()
            print("="*80 + "\n")
            raise

    def _load_image_from_url(self, image_url: str) -> Image:
        """
        Load an image from a URL (supports both local /images/ paths and GCS URLs).

        Args:
            image_url: Image URL (can be /images/... or https://storage.googleapis.com/...)

        Returns:
            Vertex AI Image object
        """
        # Check if it's a local /images/ path
        if image_url.startswith('/images/'):
            filename = image_url.replace('/images/', '')
            filepath = os.path.join(self.output_dir, filename)

            if os.path.exists(filepath):
                return Image.load_from_file(filepath)
            else:
                raise FileNotFoundError(f"Local image not found: {filepath}")

        # Otherwise, treat as external URL (e.g., GCS URL)
        elif image_url.startswith('http://') or image_url.startswith('https://'):
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            # Create Image object from bytes
            return Image.from_bytes(image_bytes)
        else:
            raise ValueError(f"Unsupported image URL format: {image_url}")

    def _build_product_description(self, product: Dict[str, Any], index: int) -> str:
        """Build a detailed description string for a product."""
        parts = [f"Product {index}: {product.get('name', 'Unknown Product')}"]

        if product.get('category'):
            parts.append(f"Category: {product['category']}")
        if product.get('subcategory'):
            parts.append(f"({product['subcategory']})")
        if product.get('color'):
            parts.append(f"Color: {product['color']}")
        if product.get('secondary_color'):
            parts.append(f"with {product['secondary_color']} accents")
        if product.get('fabric'):
            parts.append(f"Fabric: {product['fabric']}")
        if product.get('pattern'):
            parts.append(f"Pattern: {product['pattern']}")
        if product.get('fit'):
            parts.append(f"Fit: {product['fit']}")
        if product.get('sleeve_length'):
            parts.append(f"Sleeve: {product['sleeve_length']}")
        if product.get('neck_style'):
            parts.append(f"Neckline: {product['neck_style']}")
        if product.get('style'):
            parts.append(f"Style: {product['style']}")

        return " | ".join(parts)

    def _build_look_prompt(self, product_descriptions: List[str]) -> str:
        """Build the prompt for Gemini to generate a styled outfit look."""

        products_text = "\n".join(product_descriptions)

        prompt = f"""Create a professional WOMEN'S fashion e-commerce outfit photograph showing these fashion items styled together as a cohesive look:

{products_text}

CRITICAL REQUIREMENTS:

1. **WOMEN'S FASHION ONLY**: This MUST be women's fashion. Female model wearing women's clothing. All styling must be for women.

2. **Show ALL Products Together**: The female model must be wearing ALL of the listed items simultaneously in a single photograph. Every product must be clearly visible and recognizable.

3. **Contemporary Catalog Photography Style**:
   - Modern women's fast-fashion aesthetic (H&M, Zara, COS style for women)
   - Clean, minimalist white or soft grey background
   - Professional studio lighting with soft, even illumination
   - Natural, confident female model pose
   - Front-facing composition showing full outfit
   - 9:16 portrait orientation (vertical/mobile-friendly)

4. **Product Accuracy**:
   - Match the exact colors described for each product
   - Match the exact fabrics and textures
   - Match the exact styles and details (sleeves, necklines, patterns, etc.)
   - Ensure each product looks realistic and wearable
   - Maintain commercial viability - this should look like real catalog items

5. **Styling & Composition**:
   - Style the items cohesively as a complete, harmonious women's outfit
   - Ensure products complement each other visually for women's fashion
   - Natural draping and fit appropriate to each women's garment
   - Show how the pieces work together in a real-world women's outfit
   - Professional fashion styling that makes the products look appealing for women

6. **What to AVOID**:
   - Do NOT create men's fashion or unisex styling
   - Do NOT use artistic or editorial fashion photography styles
   - Do NOT use dramatic lighting, creative shadows, or unusual angles
   - Do NOT use busy, decorated, or outdoor backgrounds
   - Do NOT create avant-garde or conceptual designs
   - Do NOT add products that weren't listed

The final image should look like a professional women's fashion product catalog styling shot showing customers how these items can be worn together as a complete women's outfit."""

        return prompt

    def _generate_look_description(self, products: List[Dict[str, Any]]) -> str:
        """Generate a natural language description of the styled look."""
        product_names = [p.get('name', 'item') for p in products]

        if len(products) == 2:
            desc = f"A styled look combining {product_names[0]} with {product_names[1]}"
        elif len(products) == 3:
            desc = f"A complete outfit featuring {product_names[0]}, {product_names[1]}, and {product_names[2]}"
        else:
            desc = f"A curated look combining {len(products)} pieces"

        # Add style notes if available
        styles = [p.get('style', '') for p in products if p.get('style')]
        if styles:
            desc += f" in a {styles[0]} style"

        return desc

    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """
        Extract image data from Gemini 2.5 Flash Image response.
        The model returns images in the response parts as inline_data.
        """
        try:
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            # Try to get text safely (some parts may only have images)
                            try:
                                text_content = part.text
                                if text_content:
                                    print(f"Gemini response text: {text_content[:100]}...")
                            except (ValueError, AttributeError):
                                pass

                            # Image parts contain inline_data with the generated image
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                    print("Successfully extracted image from inline_data")
                                    return part.inline_data.data

                            # Alternative: Check for _raw_part or _pb (protobuf) structure
                            if hasattr(part, '_raw_part'):
                                raw_part = part._raw_part
                                if hasattr(raw_part, 'inline_data') and raw_part.inline_data:
                                    print(f"Found image in _raw_part.inline_data")
                                    if hasattr(raw_part.inline_data, 'data') and raw_part.inline_data.data:
                                        data_bytes = raw_part.inline_data.data
                                        print(f"  Extracted {len(data_bytes)} bytes from _raw_part")
                                        return data_bytes

                            # Check if part has blob attribute
                            if hasattr(part, 'blob') and part.blob:
                                print("Found image in blob")
                                return part.blob

            print("No image found in Gemini response")
        except Exception as e:
            print(f"Error extracting image from response: {e}")
            import traceback
            traceback.print_exc()

        return None
