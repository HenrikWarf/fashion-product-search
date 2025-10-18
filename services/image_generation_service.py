import base64
import os
from typing import Optional, Dict, Any
from datetime import datetime
from services.gcp_client import get_gcp_client
from vertexai.generative_models import Part, Image as VertexImage
import vertexai.preview.vision_models as vision_models


class ImageGenerationService:
    """Service for generating and editing fashion concept images using Gemini."""

    def __init__(self):
        self.gcp_client = get_gcp_client()
        self.output_dir = "generated_images"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_concept_image(
        self,
        prompt: str,
        parsed_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate a fashion concept image based on the visual generation prompt.

        Args:
            prompt: Visual generation prompt from NLU service
            parsed_attributes: Structured attributes for additional context

        Returns:
            Dictionary with image_url and description
        """

        # Enhance the prompt with fashion photography best practices
        enhanced_prompt = self._enhance_image_prompt(prompt, parsed_attributes)

        print("\n" + "="*80)
        print("IMAGE GENERATION STARTED")
        print("="*80)
        print(f"Original prompt: {prompt[:100]}...")
        print(f"Enhanced prompt: {enhanced_prompt[:100]}...")

        try:
            print("\n[1] Initializing Gemini 2.5 Flash Image model...")
            model = self.gcp_client.get_gemini_image_model()
            print(f"[✓] Model initialized: {model._model_name if hasattr(model, '_model_name') else 'gemini-2.5-flash-image-preview'}")

            # Configure for image generation - Vertex AI version
            from vertexai.generative_models import GenerationConfig

            generation_config = GenerationConfig(
                temperature=0.6,  # Reduced from 0.7 for better catalog alignment
                max_output_tokens=8192,
            )

            print(f"\n[2] Generation config: temperature=0.6, max_output_tokens=8192")

            # Create prompt for Gemini 2.5 Flash Image generation with catalog-aligned specifications
            full_prompt = f"""Generate a high-quality fashion product photograph based on this description:

{enhanced_prompt}

Photography specifications (match e-commerce catalog style):
- Female model wearing the garment
- Front-facing view, full body or 3/4 length composition
- Clean minimalist background (white or soft grey)
- Professional studio lighting with soft, even illumination
- Contemporary fast-fashion photography style (H&M, Zara aesthetic)
- Scandinavian minimalist aesthetic
- Natural, relaxed model pose
- 9:16 portrait orientation (suitable for mobile and e-commerce)
- Realistic, wearable, commercially viable design
- Show garment clearly with accurate colors and details

Avoid:
- Artistic or editorial fashion photography styles
- Dramatic lighting or creative shadows
- Busy or decorative backgrounds
- Avant-garde or conceptual designs

Focus on creating a specific, detailed design that captures the essence of the request while remaining visually consistent with modern fast-fashion catalogs."""

            print(f"\n[3] Sending request to Gemini...")
            print(f"    Prompt length: {len(full_prompt)} characters")

            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            print(f"[✓] Response received from Gemini")
            print(f"    Response type: {type(response)}")

            # Debug response structure
            if hasattr(response, 'candidates'):
                print(f"    Number of candidates: {len(response.candidates)}")
                for i, candidate in enumerate(response.candidates):
                    print(f"    Candidate {i}:")
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        print(f"      Number of parts: {len(candidate.content.parts)}")
                        for j, part in enumerate(candidate.content.parts):
                            print(f"      Part {j}: {type(part).__name__}")
                            # Check what attributes the part has
                            print(f"        - Part attributes: {dir(part)}")
                            # Try to access text safely
                            try:
                                text_content = part.text
                                print(f"        - Has text: {len(text_content) if text_content else 0} chars")
                            except (ValueError, AttributeError) as e:
                                print(f"        - No text (expected for image parts)")
                            # Check for inline_data
                            if hasattr(part, 'inline_data'):
                                print(f"        - Has inline_data: {part.inline_data is not None}")
                                if part.inline_data:
                                    print(f"        - mime_type: {getattr(part.inline_data, 'mime_type', 'N/A')}")
                                    print(f"        - data size: {len(part.inline_data.data) if hasattr(part.inline_data, 'data') and part.inline_data.data else 0} bytes")
                            # Check for blob
                            if hasattr(part, 'blob'):
                                print(f"        - Has blob: {part.blob is not None}")

            # Extract image from response
            print(f"\n[4] Extracting image from response...")
            image_data = self._extract_image_from_response(response)

            if image_data:
                print(f"[✓] Image data extracted successfully")
                print(f"    Image size: {len(image_data)} bytes ({len(image_data)/1024:.2f} KB)")

                # Save image locally
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"concept_{timestamp}.png"
                filepath = os.path.join(self.output_dir, filename)

                print(f"\n[5] Saving image to disk...")
                print(f"    Filepath: {filepath}")

                with open(filepath, "wb") as f:
                    f.write(image_data)

                print(f"[✓] Image saved successfully")

                # In production, you'd upload to Cloud Storage and return that URL
                image_url = f"/images/{filename}"

                # Generate description
                description = self._generate_description(enhanced_prompt, parsed_attributes)

                print(f"\n[6] Returning response")
                print(f"    Image URL: {image_url}")
                print(f"    Description: {description[:100]}...")
                print("="*80)
                print("IMAGE GENERATION COMPLETED SUCCESSFULLY")
                print("="*80 + "\n")

                return {
                    "image_url": image_url,
                    "description": description,
                    "local_path": filepath
                }
            else:
                # Fallback if image generation fails
                print(f"[✗] No image data extracted - using fallback")
                print("="*80 + "\n")
                return self._fallback_image_response(prompt)

        except Exception as e:
            print(f"\n[✗] ERROR in image generation:")
            print(f"    Error type: {type(e).__name__}")
            print(f"    Error message: {str(e)}")
            import traceback
            print(f"    Traceback:")
            traceback.print_exc()
            print("="*80 + "\n")
            return self._fallback_image_response(prompt)

    async def refine_image(
        self,
        original_prompt: str,
        refinement_prompt: str,
        current_image_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Refine/edit an existing concept image based on user feedback.

        Args:
            original_prompt: Original query or description
            refinement_prompt: User's refinement instructions
            current_image_url: URL/path to current image (optional)

        Returns:
            Dictionary with refined image_url and description
        """

        print("\n" + "="*80)
        print("IMAGE REFINEMENT STARTED")
        print("="*80)
        print(f"Original: {original_prompt[:100]}...")
        print(f"Refinement: {refinement_prompt[:100]}...")

        try:
            print("\n[1] Initializing Gemini 2.5 Flash Image model...")
            model = self.gcp_client.get_gemini_image_model()
            print(f"[✓] Model initialized")

            # Create combined prompt for refinement with image editing instruction
            combined_prompt = f"""Edit the fashion product photograph shown in the image.

Requested Changes: {refinement_prompt}

Apply these modifications while maintaining catalog photography standards:
- Maintain the overall style and aesthetic
- Keep contemporary fast-fashion photography style (H&M, Zara aesthetic)
- Preserve clean minimalist background (white or soft grey)
- Maintain professional studio lighting with soft, even illumination
- Keep natural, relaxed model pose and front-facing composition
- Show the refined garment clearly with accurate colors and details
- Ensure 9:16 portrait orientation
- Keep elements that weren't mentioned in the changes
- Maintain realistic, commercially viable design

Make the specific changes requested while preserving the e-commerce catalog quality and all other aspects of the original design."""

            from vertexai.generative_models import GenerationConfig, Image, Part

            generation_config = GenerationConfig(
                temperature=0.6,  # Reduced from 0.7 for better catalog alignment
                max_output_tokens=8192,
            )

            # Load the current image if available
            content_parts = [combined_prompt]

            if current_image_url and current_image_url.startswith("/images/"):
                # Extract filename and load the image
                import os
                filename = current_image_url.replace("/images/", "")
                filepath = os.path.join(self.output_dir, filename)

                print(f"\n[2] Loading current image for editing...")
                print(f"    Image path: {filepath}")

                if os.path.exists(filepath):
                    print(f"[✓] Image file found")
                    # Load image for Gemini
                    image = Image.load_from_file(filepath)
                    content_parts.append(image)
                else:
                    print(f"[✗] Image file not found at {filepath}")
            else:
                print(f"\n[2] No previous image provided, generating new design...")

            # Generate refined image with Gemini 2.5 Flash Image
            print(f"\n[3] Sending refinement request to Gemini...")

            response = model.generate_content(
                content_parts,
                generation_config=generation_config
            )

            print(f"[✓] Response received from Gemini")

            print(f"\n[4] Extracting image from response...")
            image_data = self._extract_image_from_response(response)

            if image_data:
                print(f"[✓] Image data extracted: {len(image_data)} bytes")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"refined_{timestamp}.png"
                filepath = os.path.join(self.output_dir, filename)

                print(f"\n[5] Saving refined image...")
                with open(filepath, "wb") as f:
                    f.write(image_data)
                print(f"[✓] Saved to: {filepath}")

                image_url = f"/images/{filename}"
                description = f"Refined design incorporating: {refinement_prompt}"

                print("="*80)
                print("IMAGE REFINEMENT COMPLETED SUCCESSFULLY")
                print("="*80 + "\n")

                return {
                    "image_url": image_url,
                    "description": description,
                    "local_path": filepath
                }
            else:
                print(f"[✗] No image data extracted - using fallback")
                print("="*80 + "\n")
                return self._fallback_image_response(f"{original_prompt} with {refinement_prompt}")

        except Exception as e:
            print(f"\n[✗] ERROR in image refinement:")
            print(f"    Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            return self._fallback_image_response(f"{original_prompt} with {refinement_prompt}")

    def _enhance_image_prompt(
        self,
        prompt: str,
        parsed_attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance the prompt with catalog-aligned specificity for better matching."""

        if not parsed_attributes:
            return prompt

        enhancements = []

        # Add explicit attributes with more detail
        explicit = parsed_attributes.get("explicit_attributes", {})

        # Colors (primary and secondary)
        if explicit.get("colors"):
            colors_str = " and ".join(explicit['colors'])
            enhancements.append(f"Color: {colors_str}")

        # Pattern
        if explicit.get("pattern"):
            enhancements.append(f"Pattern: {explicit['pattern']}")

        # Season (affects fabric weight and style)
        if explicit.get("season"):
            enhancements.append(f"Season: {explicit['season']}")

        # Occasion (affects formality and styling)
        if explicit.get("occasion"):
            enhancements.append(f"Occasion: {explicit['occasion']}")

        # Add inferred needs with more structure
        inferred = parsed_attributes.get("inferred_needs", {})

        # Fabric/Material details
        if inferred.get("fabrics"):
            fabrics_str = ", ".join(inferred['fabrics'])
            enhancements.append(f"Fabric/Material: {fabrics_str}")

        # Silhouette/Fit
        if inferred.get("silhouettes"):
            silhouette_str = ", ".join(inferred['silhouettes'])
            enhancements.append(f"Fit/Silhouette: {silhouette_str}")

        # Garment type (helps with category matching)
        if inferred.get("garment_types"):
            garment_str = inferred['garment_types'][0] if len(inferred['garment_types']) > 0 else None
            if garment_str:
                enhancements.append(f"Garment Type: {garment_str}")

        # Style details (sleeve, neck, etc.) if available
        if explicit.get("sleeve_length"):
            enhancements.append(f"Sleeve Length: {explicit['sleeve_length']}")
        if explicit.get("neck_style"):
            enhancements.append(f"Neckline: {explicit['neck_style']}")
        if explicit.get("style"):
            enhancements.append(f"Style: {explicit['style']}")

        if enhancements:
            # Format as structured specifications for better alignment
            enhanced = f"{prompt}\n\nDetailed Product Specifications:\n- " + "\n- ".join(enhancements)
            return enhanced

        return prompt

    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """
        Extract image data from Gemini 2.5 Flash Image response.
        The model returns images in the response parts as inline_data.
        """
        try:
            # Iterate through response candidates and parts
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
                                # This part has no text, which is fine for image parts
                                pass

                            # Image parts contain inline_data with the generated image
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                    # Return the binary image data
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
                                    else:
                                        print(f"  _raw_part.inline_data has no data attribute or data is None")

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

    def _generate_description(
        self,
        prompt: str,
        parsed_attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a natural language description of the concept image."""

        if not parsed_attributes:
            return prompt

        parts = []

        explicit = parsed_attributes.get("explicit_attributes", {})
        if explicit.get("occasion"):
            parts.append(f"designed for {explicit['occasion']}")

        if explicit.get("colors"):
            colors = ", ".join(explicit["colors"])
            parts.append(f"in beautiful {colors} tones")

        inferred = parsed_attributes.get("inferred_needs", {})
        if inferred.get("silhouettes"):
            parts.append(f"featuring a {inferred['silhouettes'][0]} silhouette")

        if parts:
            return f"A fashion concept {', '.join(parts)}."

        return "A beautiful fashion concept tailored to your preferences."

    def _fallback_image_response(self, prompt: str) -> Dict[str, str]:
        """Fallback response when image generation is not available."""
        # Create an inline SVG placeholder that will always work
        svg_placeholder = '''data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='800' viewBox='0 0 600 800'%3E%3Crect width='600' height='800' fill='%23f5f5f5'/%3E%3Cg transform='translate(300,400)'%3E%3Ccircle cx='0' cy='-50' r='60' fill='%23d4af37' opacity='0.3'/%3E%3Cpath d='M -40,-80 L -40,-20 L -20,0 L -20,40 L 20,40 L 20,0 L 40,-20 L 40,-80 Z' fill='%23d4af37' opacity='0.5'/%3E%3Ctext x='0' y='100' text-anchor='middle' font-family='Arial,sans-serif' font-size='18' fill='%23666'%3EFashion Concept%3C/text%3E%3Ctext x='0' y='130' text-anchor='middle' font-family='Arial,sans-serif' font-size='14' fill='%23999'%3EImage generation in progress%3C/text%3E%3C/g%3E%3C/svg%3E'''

        return {
            "image_url": svg_placeholder,
            "description": f"Fashion concept based on: {prompt}. (Note: Image generation is currently in development - this is a placeholder)",
            "local_path": None
        }
