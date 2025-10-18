"""
Category definitions and attribute templates for synthetic product generation.
H&M-inspired women's fashion catalog.
"""

# Category distribution (total: 200 products)
CATEGORY_DISTRIBUTION = {
    "Tops": 45,
    "Bottoms": 40,
    "Dresses": 40,
    "Outerwear": 30,
    "Activewear": 20,
    "Knitwear": 25
}

# Subcategories for each main category
SUBCATEGORIES = {
    "Tops": ["T-shirt", "Blouse", "Tank Top", "Crop Top", "Tunic", "Cami"],
    "Bottoms": ["Jeans", "Trousers", "Skirt", "Shorts", "Leggings", "Wide-Leg Pants"],
    "Dresses": ["Casual Dress", "Midi Dress", "Maxi Dress", "Mini Dress", "Shirt Dress", "Wrap Dress"],
    "Outerwear": ["Jacket", "Coat", "Blazer", "Vest", "Parka", "Trench Coat"],
    "Activewear": ["Sports Bra", "Training Top", "Leggings", "Hoodie", "Track Jacket", "Joggers"],
    "Knitwear": ["Sweater", "Cardigan", "Turtleneck", "Pullover", "Knit Top", "Jumper"]
}

# Color palette (H&M-inspired: modern, wearable, seasonal)
COLORS = {
    "neutrals": ["White", "Black", "Beige", "Grey", "Cream", "Taupe", "Ivory"],
    "earth_tones": ["Camel", "Brown", "Olive", "Khaki", "Terracotta", "Rust"],
    "pastels": ["Powder Pink", "Baby Blue", "Lavender", "Mint Green", "Peach"],
    "brights": ["Red", "Blue", "Green", "Yellow", "Pink", "Purple"],
    "darks": ["Navy", "Charcoal", "Burgundy", "Forest Green", "Plum"]
}

# All colors flattened for easy access
ALL_COLORS = [color for category in COLORS.values() for color in category]

# Fabric types
FABRICS = [
    "Cotton",
    "Cotton Blend",
    "Polyester",
    "Viscose",
    "Linen",
    "Denim",
    "Jersey",
    "Chiffon",
    "Silk Blend",
    "Wool Blend",
    "Knit",
    "Rib Knit",
    "French Terry",
    "Fleece",
    "Nylon",
    "Spandex Blend"
]

# Pattern types
PATTERNS = [
    "Solid",
    "Striped",
    "Floral",
    "Polka Dot",
    "Geometric",
    "Abstract",
    "Animal Print",
    "Plaid",
    "Check",
    "Textured"
]

# Fit types
FITS = [
    "Regular Fit",
    "Slim Fit",
    "Relaxed Fit",
    "Oversized",
    "Fitted",
    "Loose",
    "Bodycon",
    "A-Line"
]

# Sleeve lengths
SLEEVE_LENGTHS = [
    "Sleeveless",
    "Short Sleeve",
    "3/4 Sleeve",
    "Long Sleeve",
    "Cap Sleeve"
]

# Neck styles
NECK_STYLES = [
    "Round Neck",
    "V-Neck",
    "Turtleneck",
    "Crew Neck",
    "Scoop Neck",
    "Boat Neck",
    "High Neck",
    "Collar",
    "Off-Shoulder"
]

# Seasons
SEASONS = ["Spring", "Summer", "Fall", "Winter", "All Season"]

# Occasions
OCCASIONS = [
    "Casual",
    "Work",
    "Evening",
    "Party",
    "Sport",
    "Lounge",
    "Vacation"
]

# Styles
STYLES = [
    "Modern",
    "Classic",
    "Minimalist",
    "Bohemian",
    "Sporty",
    "Elegant",
    "Casual",
    "Trendy"
]

# Fictional brand names (H&M-style)
BRAND_NAMES = [
    "StyleCo",
    "ModernWear",
    "UrbanThread",
    "NorthLabel",
    "CoastLine",
    "MinimalChic",
    "EverydayStyle",
    "ThreadBare"
]

# Price ranges by category (in USD)
PRICE_RANGES = {
    "Tops": (19.99, 39.99),
    "Bottoms": (29.99, 59.99),
    "Dresses": (39.99, 79.99),
    "Outerwear": (59.99, 89.99),
    "Activewear": (24.99, 49.99),
    "Knitwear": (34.99, 54.99)
}

# Description templates
DESCRIPTION_TEMPLATES = {
    "Tops": "A {style} {subcategory} in {color} featuring {fabric} fabric with a {fit}. Perfect for {occasion} wear. {pattern} design with {neck_style} and {sleeve_length}.",
    "Bottoms": "Contemporary {subcategory} in {color} crafted from {fabric}. Features a {fit} with {pattern} styling. Ideal for {occasion} occasions.",
    "Dresses": "Elegant {subcategory} in {color} made from {fabric}. This {fit} dress features {pattern} detailing and {sleeve_length}. Perfect for {occasion}.",
    "Outerwear": "Essential {subcategory} in {color} made from durable {fabric}. {fit} silhouette with {pattern} design. Versatile piece for {season} layering.",
    "Activewear": "Performance-oriented {subcategory} in {color}. Made from breathable {fabric} with a {fit}. Designed for {occasion} activities with moisture-wicking properties.",
    "Knitwear": "Cozy {subcategory} in {color} knitted from soft {fabric}. Features a {fit} with {pattern} texture. Essential piece for {season} comfort."
}


def get_category_attributes(category: str) -> dict:
    """Get relevant attributes for a category."""
    return {
        "subcategories": SUBCATEGORIES.get(category, []),
        "price_range": PRICE_RANGES.get(category, (29.99, 59.99)),
        "description_template": DESCRIPTION_TEMPLATES.get(category, "")
    }
