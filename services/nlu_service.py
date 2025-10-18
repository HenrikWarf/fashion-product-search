from typing import Dict, Any, List, Optional
from services.gcp_client import get_gcp_client


class NLUService:
    """Natural Language Understanding service using Gemini for query parsing."""

    def __init__(self):
        self.gcp_client = get_gcp_client()

    async def parse_fashion_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language fashion query into structured attributes.

        Args:
            query: Natural language fashion search query

        Returns:
            Dictionary containing extracted attributes and visual generation prompt
        """

        parsing_prompt = f"""You are an expert fashion stylist and AI assistant. Analyze the following fashion search query and extract structured information.

User Query: "{query}"

Please extract and structure the following information:

1. **Explicit Attributes**: Direct, quantifiable requirements
   - Occasion (e.g., wedding, office, casual)
   - Formality level (casual, business casual, formal, black tie)
   - Color preferences (specific colors or color families)
   - Price constraints
   - Size/fit considerations (petite, plus size, tall, etc.)
   - Season/weather considerations

2. **Subjective Style Terms**: Interpret subjective descriptions
   - Style descriptors (chic, elegant, edgy, bohemian, etc.)
   - Fit preferences (flattering, comfortable, structured, flowy)
   - Negative constraints (what to avoid)

3. **Inferred Needs**: Based on context
   - Appropriate garment types
   - Suitable fabrics and materials
   - Recommended silhouettes
   - Design details that would work well

4. **Visual Generation Prompt**: Create a detailed prompt for generating a concept image that:
   - Incorporates all extracted preferences
   - Considers what's typically available in fashion retail
   - Focuses on realistic, purchasable designs
   - Is biased toward common inventory attributes

Return your analysis in this JSON format:
{{
    "explicit_attributes": {{
        "occasion": "string or null",
        "formality": "string or null",
        "colors": ["color1", "color2"],
        "price_max": number or null,
        "price_min": number or null,
        "size_considerations": "string or null",
        "season": "string or null"
    }},
    "subjective_style": {{
        "style_terms": ["term1", "term2"],
        "fit_preferences": ["pref1", "pref2"],
        "avoid": ["constraint1", "constraint2"]
    }},
    "inferred_needs": {{
        "garment_types": ["type1", "type2"],
        "fabrics": ["fabric1", "fabric2"],
        "silhouettes": ["silhouette1", "silhouette2"],
        "details": ["detail1", "detail2"]
    }},
    "visual_generation_prompt": "Detailed prompt for image generation...",
    "search_keywords": ["keyword1", "keyword2", "keyword3"]
}}

Ensure the visual_generation_prompt is highly detailed and describes a specific, realistic fashion item that could exist in a retail catalog."""

        try:
            model = self.gcp_client.get_gemini_model()
            response = model.generate_content(parsing_prompt)

            # Extract JSON from response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            import json
            parsed_data = json.loads(response_text.strip())

            return parsed_data

        except Exception as e:
            print(f"Error parsing query with Gemini: {e}")
            # Fallback to basic parsing
            return self._basic_fallback_parsing(query)

    def _basic_fallback_parsing(self, query: str) -> Dict[str, Any]:
        """Fallback parsing if Gemini fails."""
        return {
            "explicit_attributes": {
                "occasion": None,
                "formality": None,
                "colors": [],
                "price_max": None,
                "price_min": None,
                "size_considerations": None,
                "season": None
            },
            "subjective_style": {
                "style_terms": [],
                "fit_preferences": [],
                "avoid": []
            },
            "inferred_needs": {
                "garment_types": ["dress"],
                "fabrics": [],
                "silhouettes": [],
                "details": []
            },
            "visual_generation_prompt": f"A beautiful, elegant fashion item based on: {query}",
            "search_keywords": query.split()
        }

    async def analyze_image_for_style(self, image_data: str, additional_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze an uploaded image using Gemini vision to extract style attributes.

        Args:
            image_data: Base64 encoded image data
            additional_description: Optional user-provided description to guide analysis

        Returns:
            Dictionary containing style analysis, attributes, and visual generation prompt
        """
        import base64
        import io
        from PIL import Image
        import traceback

        print(f"[DEBUG] Starting image analysis...")
        print(f"[DEBUG] Additional description: {additional_description}")
        print(f"[DEBUG] Image data length: {len(image_data) if image_data else 0}")

        try:
            # Parse base64 image data (remove data:image/... prefix if present)
            if ',' in image_data:
                print(f"[DEBUG] Found comma in image_data, splitting...")
                image_data = image_data.split(',')[1]

            print(f"[DEBUG] Image data length after parsing: {len(image_data)}")

            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            print(f"[DEBUG] Decoded image bytes length: {len(image_bytes)}")

            # Load image with PIL and convert to Vertex AI Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            print(f"[DEBUG] PIL Image loaded successfully: size={pil_image.size}, mode={pil_image.mode}")

            # Convert PIL Image to Vertex AI Part for Gemini
            from vertexai.generative_models import Part

            # Re-encode the image bytes for Vertex AI
            image_part = Part.from_data(
                data=image_bytes,
                mime_type=f"image/{pil_image.format.lower() if pil_image.format else 'png'}"
            )
            print(f"[DEBUG] Created Vertex AI image part")

            # Create analysis prompt
            analysis_prompt = """You are an expert fashion stylist analyzing an uploaded image. Analyze the fashion style shown in this image and extract structured information.

"""
            if additional_description:
                analysis_prompt += f"User's description: \"{additional_description}\"\n\n"

            analysis_prompt += """Please identify and extract:

1. **Style Characteristics**:
   - Overall style (e.g., casual, formal, bohemian, sporty, elegant)
   - Key colors and color palette
   - Garment types visible
   - Fit and silhouette
   - Fabric types or textures visible
   - Any notable patterns or details

2. **Occasion and Context**:
   - Suitable occasions for this style
   - Season appropriateness
   - Formality level

3. **Style Description**: A natural language description of the style (1-2 sentences)

4. **Visual Generation Prompt**: Create a detailed prompt to generate a similar fashion concept that:
   - Captures the essence of this style
   - Is realistic and purchasable
   - Incorporates similar colors, silhouettes, and details

Return your analysis in this JSON format:
{
    "explicit_attributes": {
        "occasion": "string or null",
        "formality": "string or null",
        "colors": ["color1", "color2"],
        "season": "string or null"
    },
    "subjective_style": {
        "style_terms": ["term1", "term2"],
        "fit_preferences": ["pref1", "pref2"]
    },
    "inferred_needs": {
        "garment_types": ["type1", "type2"],
        "fabrics": ["fabric1", "fabric2"],
        "silhouettes": ["silhouette1"],
        "details": ["detail1", "detail2"]
    },
    "style_description": "Natural language description of the style...",
    "visual_generation_prompt": "Detailed prompt for generating a similar concept...",
    "search_keywords": ["keyword1", "keyword2", "keyword3"]
}"""

            # Use Gemini vision model
            print(f"[DEBUG] Getting Gemini model...")
            model = self.gcp_client.get_gemini_model()

            print(f"[DEBUG] Calling Gemini vision API with image part...")
            response = model.generate_content([analysis_prompt, image_part])

            print(f"[DEBUG] Gemini response received")

            # Extract JSON from response
            response_text = response.text.strip()
            print(f"[DEBUG] Response text length: {len(response_text)}")
            print(f"[DEBUG] Response text preview: {response_text[:200]}...")

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            import json
            parsed_data = json.loads(response_text.strip())
            print(f"[DEBUG] Successfully parsed JSON response")
            print(f"[DEBUG] Parsed data keys: {list(parsed_data.keys())}")

            # Return in the format expected by the endpoint
            result = {
                "attributes": parsed_data,
                "visual_prompt": parsed_data.get("visual_generation_prompt", ""),
                "style_description": parsed_data.get("style_description", "Style based on uploaded image")
            }
            print(f"[DEBUG] Image analysis successful!")
            return result

        except Exception as e:
            print(f"[ERROR] Error analyzing image with Gemini vision: {e}")
            print(f"[ERROR] Full traceback:")
            traceback.print_exc()

            # Fallback response
            fallback_description = "Fashion style inspired by your uploaded image"
            if additional_description:
                fallback_description = f"Fashion style: {additional_description}"

            print(f"[DEBUG] Using fallback response")
            return {
                "attributes": self._basic_fallback_parsing(fallback_description),
                "visual_prompt": f"A fashionable outfit inspired by an uploaded style image. {additional_description or ''}",
                "style_description": fallback_description
            }
