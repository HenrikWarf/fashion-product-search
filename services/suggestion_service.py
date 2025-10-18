import os
import json
from typing import List, Optional
from services.gcp_client import get_gcp_client
from vertexai.generative_models import Image, GenerationConfig


class SuggestionService:
    """Service for generating AI-powered style variation suggestions using Gemini with vision."""

    def __init__(self):
        self.gcp_client = get_gcp_client()

    async def generate_style_suggestions(
        self,
        image_url: str,
        description: str,
        original_query: str
    ) -> List[str]:
        """
        Analyze a fashion concept image and generate 4-6 style variation suggestions.

        Args:
            image_url: URL/path to the concept image
            description: Text description of the current concept
            original_query: User's original search query

        Returns:
            List of 4-6 short, actionable refinement suggestions
        """

        print("\n" + "="*80)
        print("GENERATING STYLE SUGGESTIONS")
        print("="*80)
        print(f"Image URL: {image_url}")
        print(f"Description: {description[:100]}...")
        print(f"Original Query: {original_query}")

        try:
            print("\n[1] Loading concept image...")

            # Load the image from local path
            if image_url.startswith("/images/"):
                filename = image_url.replace("/images/", "")
                filepath = os.path.join("generated_images", filename)

                if not os.path.exists(filepath):
                    print(f"[✗] Image file not found at {filepath}")
                    return self._fallback_suggestions()

                print(f"[✓] Image found: {filepath}")

                # Load image for Gemini vision
                image = Image.load_from_file(filepath)
            else:
                print(f"[✗] Unsupported image URL format: {image_url}")
                return self._fallback_suggestions()

            print("\n[2] Initializing Gemini model with vision...")
            model = self.gcp_client.get_gemini_model()  # Gemini 2.5 Flash supports vision
            print(f"[✓] Model initialized")

            # Create analysis prompt
            prompt = f"""Analyze this fashion concept image and generate 4-6 detailed style variation suggestions that maintain the core theme and aesthetic.

Current Design Context:
- Description: {description}
- Original Request: {original_query}

CRITICAL REQUIREMENTS:
1. **Preserve the Core Theme**: Each variation MUST maintain the fundamental style, mood, and aesthetic of the original concept
2. **Be Detailed and Descriptive**: Each suggestion should be 1-2 sentences with rich, specific details
3. **Offer Meaningful Variations**: Suggest genuinely different interpretations, not minor tweaks
4. **Appeal to Fashion Shoppers**: Write suggestions that would excite someone looking for alternatives

Generate suggestions covering different aspects:
- **Color Palette Variations**: Alternative color schemes that preserve the mood (e.g., "Luxe emerald green interpretation with the same flowing silhouette and bohemian details, featuring subtle gold embroidery along the neckline")
- **Silhouette & Length**: Different cuts while maintaining style (e.g., "Elegant tea-length version with A-line silhouette and delicate cap sleeves, preserving the romantic floral aesthetic")
- **Occasion Adaptation**: Dress up/down while keeping essence (e.g., "Elevated evening version in luxe satin with the original's relaxed fit, adding subtle beading for sophisticated occasions")
- **Seasonal Variations**: Adapt for different seasons (e.g., "Cozy autumn interpretation with the same silhouette in rich burgundy knit, maintaining the effortless bohemian vibe")
- **Detail & Embellishment**: Add distinctive features (e.g., "Enhanced version with intricate lace trim and flutter sleeves, keeping the original's whimsical garden party aesthetic")
- **Fabric & Texture**: Material variations that keep the style (e.g., "Lightweight linen version perfect for summer, maintaining the breezy relaxed fit and coastal aesthetic")

EXAMPLES OF GOOD SUGGESTIONS:
- Title: "Evening Elegance" | Description: "Sophisticated midi-length version in dusty rose with tiered ruffles and a fitted bodice, preserving the feminine romantic garden aesthetic"
- Title: "Jewel Tones" | Description: "Bold jewel-toned interpretation featuring the same relaxed silhouette in deep sapphire with golden embroidered details for evening elegance"
- Title: "Minimalist Chic" | Description: "Minimalist cream version with clean lines and subtle pleating, maintaining the effortless chic vibe in a more understated palette"

Return your suggestions in this exact JSON format with both title and description:
{{
    "suggestions": [
        {{
            "title": "Evening Elegance",
            "description": "Sophisticated midi-length version in dusty rose with tiered ruffles and a fitted bodice, preserving the feminine romantic garden aesthetic"
        }},
        {{
            "title": "Jewel Tones",
            "description": "Bold jewel-toned interpretation featuring the same relaxed silhouette in deep sapphire with golden embroidered details for evening elegance"
        }},
        {{
            "title": "Minimalist Chic",
            "description": "Minimalist cream version with clean lines and subtle pleating, maintaining the effortless chic vibe in a more understated palette"
        }},
        {{
            "title": "Autumn Warmth",
            "description": "Cozy autumn interpretation in rich burgundy knit with the original's flowing shape, adding cable-knit texture for warmth"
        }}
    ]
}}

Return only the JSON, no additional text."""

            generation_config = GenerationConfig(
                temperature=0.7,  # Higher for creative suggestions
                max_output_tokens=4096,  # Increased significantly for longer detailed suggestions
            )

            print("\n[3] Sending request to Gemini...")
            response = model.generate_content(
                [image, prompt],
                generation_config=generation_config
            )

            print(f"[✓] Response received from Gemini")

            # Extract and parse JSON response
            response_text = response.text.strip()
            print(f"[4] Parsing response...")
            print(f"Response text length: {len(response_text)} characters")
            print(f"Response text preview: {response_text[:200]}...")

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Check if response was truncated
            if not response_text.endswith("}"):
                print(f"[!] Warning: Response appears truncated (doesn't end with '}}'), attempting to repair...")
                print(f"Last 100 chars: ...{response_text[-100:]}")

                # Try to repair truncated JSON
                response_text = self._repair_truncated_json(response_text)
                print(f"[!] Repaired JSON, new length: {len(response_text)}")

            try:
                parsed_data = json.loads(response_text)
                suggestions = parsed_data.get("suggestions", [])
            except json.JSONDecodeError as json_err:
                print(f"[✗] JSON parsing failed: {json_err}")
                print(f"[!] Trying to extract partial suggestions from malformed JSON...")

                # Try to extract any complete suggestions from the partial JSON
                suggestions = self._extract_partial_suggestions(response_text)
                if suggestions:
                    print(f"[✓] Extracted {len(suggestions)} partial suggestions")
                    return suggestions

                print(f"[!] Using fallback suggestions")
                return self._fallback_suggestions()

            print(f"[✓] Parsed {len(suggestions)} suggestions")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {i}. {suggestion}")

            print("="*80)
            print("SUGGESTION GENERATION COMPLETED")
            print("="*80 + "\n")

            return suggestions[:6]  # Return max 6 suggestions

        except Exception as e:
            print(f"\n[✗] ERROR generating suggestions:")
            print(f"    Error type: {type(e).__name__}")
            print(f"    Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")

            return self._fallback_suggestions()

    def _repair_truncated_json(self, text: str) -> str:
        """Attempt to repair truncated JSON by closing open structures."""
        # Count open braces and brackets
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')

        # Find the last complete suggestion if any
        last_complete_obj = text.rfind('"}')
        if last_complete_obj != -1:
            # Truncate to last complete object
            text = text[:last_complete_obj + 2]

        # Close any open structures
        if open_brackets > 0:
            text += ']' * open_brackets
        if open_braces > 0:
            text += '}' * open_braces

        return text

    def _extract_partial_suggestions(self, text: str) -> List[dict]:
        """Extract any complete suggestions from partially malformed JSON."""
        import re
        suggestions = []

        # Try to find complete suggestion objects using regex
        pattern = r'\{\s*"title"\s*:\s*"([^"]+)"\s*,\s*"description"\s*:\s*"([^"]+)"\s*\}'
        matches = re.findall(pattern, text, re.DOTALL)

        for title, description in matches:
            suggestions.append({
                "title": title.strip(),
                "description": description.strip()
            })

        return suggestions

    def _fallback_suggestions(self) -> List[dict]:
        """Fallback suggestions when AI generation fails."""
        return [
            {"title": "Color Variation", "description": "Try a different color palette while maintaining the overall aesthetic"},
            {"title": "Length Adjustment", "description": "Adjust the length for a different silhouette"},
            {"title": "Detail Enhancement", "description": "Add decorative elements or embellishments"},
            {"title": "Silhouette Change", "description": "Modify the overall shape and fit"}
        ]
