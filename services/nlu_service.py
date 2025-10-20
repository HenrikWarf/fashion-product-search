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

        parsing_prompt = f"""You are an expert fashion stylist and AI assistant specializing in WOMEN'S FASHION. Analyze the following fashion search query and extract structured information.

IMPORTANT: This application is exclusively for women's fashion and clothing. All garments, styles, and recommendations must be for women.

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

    async def generate_prompt_variations(
        self, 
        parsed_attributes: Dict[str, Any], 
        original_query: str
    ) -> List[Dict[str, str]]:
        """
        Generate 3 distinct visual prompt variations from the same parsed attributes.
        Each variation focuses on a different interpretation aspect:
        - Variation 1: Different color palette interpretation
        - Variation 2: Different silhouette/fit interpretation
        - Variation 3: Different style/occasion interpretation

        Args:
            parsed_attributes: Parsed attributes from parse_fashion_query
            original_query: Original user query

        Returns:
            List of 3 dictionaries with 'prompt' and 'variation_type' keys
        """

        variation_prompt = f"""You are an expert fashion stylist specializing in WOMEN'S FASHION. Based on this fashion search query and its parsed attributes, create 3 DISTINCT visual concept variations.

CRITICAL: This application is EXCLUSIVELY for women's fashion. All concepts MUST be for women's clothing and styles. Never generate men's fashion.

Original Query: "{original_query}"

Parsed Attributes:
{parsed_attributes}

Generate 3 different interpretations of this request, each taking a different creative direction while staying true to the core request:

**VARIATION 1 - COLOR PALETTE FOCUS**: 
Create a version that explores an alternative color palette. If the original mentioned specific colors, try complementary or analogous colors. If no colors were specified, choose a bold, distinct color story.

**VARIATION 2 - SILHOUETTE/FIT FOCUS**: 
Create a version that explores a different silhouette or fit style. Try different lengths, proportions, or structural approaches (e.g., if original is fitted, try relaxed; if flowing, try structured).

**VARIATION 3 - STYLE/MOOD FOCUS**: 
Create a version that explores a different style interpretation or mood. Try different aesthetics (e.g., if original is classic, try modern; if casual, try elevated casual; if elegant, try edgy elegant).

IMPORTANT REQUIREMENTS:
- Each variation must maintain the core garment type(s) and occasion from the original request
- Each variation should feel meaningfully DIFFERENT from the others
- All variations should be realistic, purchasable designs (not avant-garde)
- Keep the same catalog photography style specifications (clean backgrounds, professional lighting)

Return your response in this exact JSON format:
{{
    "variations": [
        {{
            "variation_type": "Color Palette",
            "visual_prompt": "Detailed prompt for variation 1 with specific color focus...",
            "description": "Brief description of this variation's color approach"
        }},
        {{
            "variation_type": "Silhouette & Fit",
            "visual_prompt": "Detailed prompt for variation 2 with specific silhouette focus...",
            "description": "Brief description of this variation's silhouette approach"
        }},
        {{
            "variation_type": "Style & Mood",
            "visual_prompt": "Detailed prompt for variation 3 with specific style focus...",
            "description": "Brief description of this variation's style approach"
        }}
    ]
}}

Each visual_prompt should be detailed and ready to use for image generation."""

        try:
            model = self.gcp_client.get_gemini_model()
            response = model.generate_content(variation_prompt)

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
            variations = parsed_data.get("variations", [])

            if len(variations) == 3:
                return variations
            else:
                print(f"Warning: Expected 3 variations, got {len(variations)}. Using fallback.")
                return self._fallback_variations(parsed_attributes, original_query)

        except Exception as e:
            print(f"Error generating prompt variations with Gemini: {e}")
            return self._fallback_variations(parsed_attributes, original_query)

    def _fallback_variations(
        self, 
        parsed_attributes: Dict[str, Any], 
        original_query: str
    ) -> List[Dict[str, str]]:
        """Fallback variations if Gemini fails."""
        base_prompt = parsed_attributes.get("visual_generation_prompt", original_query)
        
        return [
            {
                "variation_type": "Color Palette",
                "visual_prompt": f"{base_prompt} with vibrant jewel tones",
                "description": "Bold jewel tone color palette"
            },
            {
                "variation_type": "Silhouette & Fit",
                "visual_prompt": f"{base_prompt} with a relaxed, flowing silhouette",
                "description": "Relaxed, flowing fit"
            },
            {
                "variation_type": "Style & Mood",
                "visual_prompt": f"{base_prompt} with modern minimalist aesthetic",
                "description": "Modern minimalist interpretation"
            }
        ]

    async def analyze_garment_regions(self, image_url: str) -> List[Dict[str, str]]:
        """
        Analyze a fashion concept image to identify distinct garment types/regions.
        Uses Gemini vision to detect individual garments and extract detailed descriptions.

        Args:
            image_url: URL/path to the concept image

        Returns:
            List of garment regions with categories and descriptions
            Example: [
                {
                    "category": "Tops",
                    "subcategory": "Blazer",
                    "description": "Navy structured blazer with notch lapels and gold buttons"
                },
                {
                    "category": "Bottoms",
                    "subcategory": "Trousers",
                    "description": "Grey tailored trousers with straight leg"
                }
            ]
        """
        import base64
        import io
        from PIL import Image
        import traceback
        import os

        print(f"\n{'='*80}")
        print("GARMENT REGION ANALYSIS")
        print(f"{'='*80}")
        print(f"Image URL: {image_url}")

        try:
            # Load image from local path
            if image_url.startswith('/images/'):
                filename = image_url.replace('/images/', '')
                filepath = os.path.join('generated_images', filename)
            else:
                filepath = image_url

            print(f"Resolved file path: {filepath}")
            print(f"File exists: {os.path.exists(filepath)}")

            if not os.path.exists(filepath):
                print(f"[ERROR] Image file not found at {filepath}")
                return []

            # Load image for Gemini vision
            from vertexai.generative_models import Image as GeminiImage
            image = GeminiImage.load_from_file(filepath)
            print(f"[✓] Image loaded successfully")

            # Create analysis prompt
            analysis_prompt = """Analyze this WOMEN'S fashion concept image and identify each distinct garment or fashion item shown.

CRITICAL: This is WOMEN'S FASHION ONLY. All garments must be women's clothing items.

For each garment you identify, extract:
1. **Category**: Main category from this list ONLY: Tops, Bottoms, Dresses, Shoes, Accessories, Outerwear
2. **Subcategory**: Specific women's garment type (e.g., Blazer, Trousers, Sneakers, Dress, Handbag)
3. **Description**: Detailed description including color, style, fit, fabric, patterns, and key distinguishing details

IMPORTANT GUIDELINES:
- Only include women's garments that are clearly visible and identifiable
- Each description should be detailed enough to search for similar women's products in a catalog
- Include: colors, fit/silhouette, style details, materials/fabrics, patterns, and notable features
- If it's a single-piece outfit (like a dress or jumpsuit), return just that one item
- If multiple items are shown (e.g., top + bottom + shoes), list each separately
- Be specific: "navy structured blazer" not just "blazer", "high-waisted grey trousers" not just "pants"

Return your analysis in this exact JSON format:
{
    "garments": [
        {
            "category": "Tops",
            "subcategory": "Blazer",
            "description": "Structured navy blazer with notch lapels, fitted silhouette, gold buttons, and professional tailoring"
        },
        {
            "category": "Bottoms",
            "subcategory": "Trousers",
            "description": "High-waisted grey wool trousers with straight leg, pleated front, and tailored fit"
        }
    ]
}

Return only the JSON, no additional text."""

            # Use Gemini vision model
            print(f"[2/3] Calling Gemini vision API...")
            model = self.gcp_client.get_gemini_model()
            response = model.generate_content([analysis_prompt, image])

            print(f"[✓] Gemini response received")

            # Extract JSON from response
            response_text = response.text.strip()
            print(f"Response text preview: {response_text[:200]}...")

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            import json
            parsed_data = json.loads(response_text.strip())
            garments = parsed_data.get("garments", [])

            print(f"[✓] Successfully identified {len(garments)} garment(s):")
            for i, garment in enumerate(garments, 1):
                print(f"  {i}. {garment['category']} - {garment['subcategory']}")
                print(f"     Description: {garment['description'][:80]}...")

            print(f"{'='*80}\n")
            return garments

        except Exception as e:
            print(f"[ERROR] Error analyzing garment regions: {e}")
            traceback.print_exc()
            print(f"{'='*80}\n")
            return []

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
            analysis_prompt = """You are an expert fashion stylist specializing in WOMEN'S FASHION. Analyze the uploaded image and extract structured information.

CRITICAL: This application is exclusively for WOMEN'S FASHION. If you detect men's fashion, convert/adapt it to equivalent women's fashion styles.

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
