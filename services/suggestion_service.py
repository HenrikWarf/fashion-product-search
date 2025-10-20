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
            prompt = f"""Analyze this WOMEN'S fashion concept image and generate 6-8 actionable edit suggestions that the user can apply to refine this design.

CRITICAL: This is WOMEN'S FASHION ONLY. All suggestions must be appropriate for women's clothing and styles.

Current Design Context:
- Description: {description}
- Original Request: {original_query}

Generate a MIX of suggestions:

**GENERIC EDITS (3-4 suggestions)** - Common modifications that work for most fashion items:
- Color changes: "make it burgundy", "change to navy blue", "try it in cream"
- Length adjustments: "make it longer", "change to midi length", "shorten to mini"
- Pattern modifications: "add stripes", "remove the pattern", "add floral print"
- Fit changes: "make it more fitted", "add a relaxed fit", "make it oversized"

**IMAGE-SPECIFIC EDITS (3-4 suggestions)** - Based on what you actually see in the image:
- Specific details to modify: "add puff sleeves", "change to V-neck", "add a belt"
- Elements to add/remove: "remove the ruffles", "add lace trim", "simplify the neckline"
- Style tweaks: "make it more casual", "add formal details", "give it bohemian touches"

IMPORTANT:
- Each suggestion must be SHORT and ACTIONABLE (2-6 words)
- Write as if the user is speaking: "make it...", "add...", "change to...", "remove..."
- Focus on ONE clear edit per suggestion
- Be specific and concrete, not vague

GOOD examples: "make it burgundy", "add long sleeves", "change to maxi length", "remove the belt", "add floral pattern"
BAD examples: "Consider a different color palette", "This would look great with different sleeves", "Try changing the style"

Return ONLY this JSON format:
{{
    "suggestions": [
        "make it burgundy",
        "add puff sleeves",
        "change to midi length",
        "remove the pattern",
        "make it more fitted",
        "add a belt"
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
                print(f"[!] Using fallback suggestions")
                return self._fallback_suggestions()

            print(f"[✓] Parsed {len(suggestions)} suggestions")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {i}. {suggestion}")

            print("="*80)
            print("SUGGESTION GENERATION COMPLETED")
            print("="*80 + "\n")

            return suggestions[:8]  # Return max 8 suggestions

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

    def _fallback_suggestions(self) -> List[str]:
        """Fallback suggestions when AI generation fails."""
        return [
            "change the color",
            "adjust the length",
            "add pattern details",
            "modify the sleeves",
            "make it more fitted",
            "add embellishments"
        ]
