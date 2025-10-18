"""
Product Specifications Generator using Gemini.
Generates diverse, realistic fashion product specifications.
"""

import json
import sys
import os
import random
from typing import List, Dict, Any
import argparse

# Add parent directory to path to import from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gcp_client import get_gcp_client
from synthetic_catalog.category_definitions import (
    CATEGORY_DISTRIBUTION,
    SUBCATEGORIES,
    ALL_COLORS,
    FABRICS,
    PATTERNS,
    FITS,
    SLEEVE_LENGTHS,
    NECK_STYLES,
    SEASONS,
    OCCASIONS,
    STYLES,
    BRAND_NAMES,
    PRICE_RANGES,
    DESCRIPTION_TEMPLATES,
    get_category_attributes
)


class ProductSpecsGenerator:
    """Generate product specifications using Gemini."""

    def __init__(self):
        self.gcp_client = get_gcp_client()

    def generate_specifications(self, total_count: int = 200) -> List[Dict[str, Any]]:
        """
        Generate product specifications for all categories.

        Args:
            total_count: Total number of products to generate (default: 200)

        Returns:
            List of product specification dictionaries
        """
        print(f"\n{'='*80}")
        print(f"GENERATING {total_count} PRODUCT SPECIFICATIONS")
        print(f"{'='*80}\n")

        all_specs = []

        for category, count in CATEGORY_DISTRIBUTION.items():
            print(f"[{category}] Generating {count} products...")
            specs = self._generate_category_specs(category, count)
            all_specs.extend(specs)
            print(f"  ✓ Generated {len(specs)} {category} products\n")

        print(f"{'='*80}")
        print(f"TOTAL: Generated {len(all_specs)} product specifications")
        print(f"{'='*80}\n")

        return all_specs

    def _generate_category_specs(self, category: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate specifications for a specific category using Gemini.

        Args:
            category: Product category
            count: Number of products to generate

        Returns:
            List of product specifications
        """
        category_attrs = get_category_attributes(category)
        subcategories = category_attrs["subcategories"]
        price_min, price_max = category_attrs["price_range"]

        # Build Gemini prompt
        prompt = self._build_gemini_prompt(
            category=category,
            subcategories=subcategories,
            count=count,
            price_range=(price_min, price_max)
        )

        try:
            model = self.gcp_client.get_gemini_model()
            response = model.generate_content(prompt)

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            specs = json.loads(response_text.strip())

            # Validate and clean specs
            validated_specs = [self._validate_spec(spec, category) for spec in specs]
            validated_specs = [s for s in validated_specs if s is not None]

            return validated_specs

        except Exception as e:
            print(f"  ✗ Error generating specs with Gemini: {e}")
            print(f"  → Falling back to template-based generation")
            return self._generate_fallback_specs(category, count)

    def _build_gemini_prompt(
        self,
        category: str,
        subcategories: List[str],
        count: int,
        price_range: tuple
    ) -> str:
        """Build prompt for Gemini to generate product specifications."""

        return f"""Generate {count} unique women's fashion product specifications for the category: {category}

Requirements:
- Modern, H&M-inspired aesthetic: minimalist, contemporary, wearable, trendy
- Diverse color palette: neutrals (white, black, beige, grey), earth tones (camel, olive, rust), pastels (pink, lavender, mint), and seasonal colors
- Mix of styles: casual, formal, trendy, classic, bohemian
- Realistic price range: ${price_range[0]} - ${price_range[1]}
- Subcategories to include: {', '.join(subcategories)}

For each product, generate:
- product_name: Descriptive name (e.g., "Ribbed Cotton Turtleneck", "High-Waist Wide-Leg Jeans")
- brand_name: Pick from [{', '.join(BRAND_NAMES)}]
- category: "{category}"
- subcategory: Pick from [{', '.join(subcategories)}]
- base_color: Primary color (e.g., "Beige", "Navy", "Black")
- secondary_color: Optional secondary color or null
- pattern: "Solid", "Striped", "Floral", "Geometric", etc.
- fabric: "Cotton", "Linen", "Denim", "Knit", "Viscose", etc.
- fit: "Regular Fit", "Slim Fit", "Oversized", "Relaxed Fit", etc.
- sleeve_length: "Long Sleeve", "Short Sleeve", "Sleeveless", etc. (if applicable)
- neck_style: "Round Neck", "V-Neck", "Turtleneck", "Collar", etc. (if applicable)
- season: "Spring", "Summer", "Fall", "Winter", or "All Season"
- occasion: "Casual", "Work", "Evening", "Party", "Sport", etc.
- style: "Modern", "Classic", "Minimalist", "Bohemian", etc.
- gender: "Women"
- price_original: Float value in range ${price_range[0]} - ${price_range[1]}
- price_discounted: Optional (20-30% discount) or null
- description: 2-3 sentence marketing description

Return ONLY a JSON array with exactly {count} products. No additional text.

Example format:
[
  {{
    "product_name": "Ribbed Knit Turtleneck",
    "brand_name": "ModernWear",
    "category": "Knitwear",
    "subcategory": "Turtleneck",
    "base_color": "Beige",
    "secondary_color": null,
    "pattern": "Solid",
    "fabric": "Cotton Blend",
    "fit": "Regular Fit",
    "sleeve_length": "Long Sleeve",
    "neck_style": "Turtleneck",
    "season": "Fall",
    "occasion": "Casual",
    "style": "Minimalist",
    "gender": "Women",
    "price_original": 39.99,
    "price_discounted": null,
    "description": "A cozy ribbed knit turtleneck in warm beige. Made from soft cotton blend fabric with a regular fit. Perfect for layering during the cooler months."
  }}
]"""

    def _validate_spec(self, spec: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Validate and ensure spec has all required fields."""
        required_fields = [
            "product_name", "brand_name", "category", "base_color",
            "season", "gender", "price_original"
        ]

        # Check required fields
        for field in required_fields:
            if field not in spec or not spec[field]:
                print(f"  ⚠ Missing required field '{field}', skipping product")
                return None

        # Ensure category matches
        spec["category"] = category

        # Ensure gender is "Women"
        spec["gender"] = "Women"

        # Fill in optional fields with defaults
        spec.setdefault("subcategory", category)
        spec.setdefault("secondary_color", None)
        spec.setdefault("pattern", "Solid")
        spec.setdefault("fabric", "Cotton")
        spec.setdefault("fit", "Regular Fit")
        spec.setdefault("sleeve_length", None)
        spec.setdefault("neck_style", None)
        spec.setdefault("occasion", "Casual")
        spec.setdefault("style", "Modern")
        spec.setdefault("price_discounted", None)
        spec.setdefault("description", f"A beautiful {spec['product_name'].lower()}.")

        return spec

    def _generate_fallback_specs(self, category: str, count: int) -> List[Dict[str, Any]]:
        """Generate specs using templates if Gemini fails."""
        specs = []
        category_attrs = get_category_attributes(category)
        subcategories = category_attrs["subcategories"]
        price_min, price_max = category_attrs["price_range"]
        template = category_attrs["description_template"]

        for i in range(count):
            subcategory = random.choice(subcategories)
            base_color = random.choice(ALL_COLORS)
            fabric = random.choice(FABRICS)
            pattern = random.choice(PATTERNS)
            fit = random.choice(FITS)
            season = random.choice(SEASONS)
            occasion = random.choice(OCCASIONS)
            style_choice = random.choice(STYLES)
            brand = random.choice(BRAND_NAMES)

            sleeve = random.choice(SLEEVE_LENGTHS) if category in ["Tops", "Dresses", "Knitwear", "Outerwear"] else None
            neck = random.choice(NECK_STYLES) if category in ["Tops", "Dresses", "Knitwear"] else None

            price = round(random.uniform(price_min, price_max), 2)
            discounted = round(price * 0.75, 2) if random.random() < 0.3 else None

            # Build product name
            product_name = f"{fit.split()[0]} {fabric} {subcategory}"
            if pattern != "Solid":
                product_name = f"{pattern} {product_name}"

            # Build description
            description = template.format(
                style=style_choice.lower(),
                subcategory=subcategory.lower(),
                color=base_color.lower(),
                fabric=fabric.lower(),
                fit=fit.lower(),
                occasion=occasion.lower(),
                pattern=pattern.lower(),
                neck_style=neck.lower() if neck else "classic neckline",
                sleeve_length=sleeve.lower() if sleeve else "versatile sleeves",
                season=season
            )

            spec = {
                "product_name": product_name,
                "brand_name": brand,
                "category": category,
                "subcategory": subcategory,
                "base_color": base_color,
                "secondary_color": None,
                "pattern": pattern,
                "fabric": fabric,
                "fit": fit,
                "sleeve_length": sleeve,
                "neck_style": neck,
                "season": season,
                "occasion": occasion,
                "style": style_choice,
                "gender": "Women",
                "price_original": price,
                "price_discounted": discounted,
                "description": description
            }

            specs.append(spec)

        return specs


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic product specifications")
    parser.add_argument("--count", type=int, default=200, help="Total number of products to generate")
    parser.add_argument("--output", type=str, default="output/product_specifications.json", help="Output JSON file")

    args = parser.parse_args()

    # Generate specifications
    generator = ProductSpecsGenerator()
    specs = generator.generate_specifications(args.count)

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(specs, f, indent=2)

    print(f"✓ Saved {len(specs)} product specifications to: {output_path}")


if __name__ == "__main__":
    main()
