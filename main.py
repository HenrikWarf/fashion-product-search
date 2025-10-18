from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from config import get_settings
from services.nlu_service import NLUService
from services.image_generation_service import ImageGenerationService
from services.product_search_service import ProductSearchService
from services.suggestion_service import SuggestionService
from services.look_generation_service import LookGenerationService

# Initialize FastAPI app
app = FastAPI(
    title="Athena Fashion Search API",
    description="AI-powered fashion search with visual concept generation",
    version="1.0.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
nlu_service = NLUService()
image_service = ImageGenerationService()
product_service = ProductSearchService()
suggestion_service = SuggestionService()
look_service = LookGenerationService()

# Request/Response Models
class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    image_url: str
    description: str
    parsed_attributes: Dict[str, Any]


class SearchByImageRequest(BaseModel):
    image_data: str  # Base64 encoded image
    additional_description: Optional[str] = None


class SearchByImageResponse(BaseModel):
    image_url: str
    description: str
    analyzed_style: str


class RefineRequest(BaseModel):
    original_prompt: str
    refinement_prompt: str
    current_image_url: Optional[str] = None


class RefineResponse(BaseModel):
    image_url: str
    description: str


class MatchProductsRequest(BaseModel):
    query: str
    image_url: str
    description: str


class Product(BaseModel):
    id: Optional[str]
    name: str
    description: Optional[str]
    price: Optional[float]
    price_original: Optional[float] = None
    price_discounted: Optional[float] = None
    image_url: Optional[str]
    color: Optional[str]
    secondary_color: Optional[str] = None
    category: Optional[str]
    subcategory: Optional[str] = None
    brand: Optional[str]
    pattern: Optional[str] = None
    fabric: Optional[str] = None
    fit: Optional[str] = None
    sleeve_length: Optional[str] = None
    neck_style: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    style: Optional[str] = None
    gender: Optional[str] = None
    similarity_score: float


class MatchProductsResponse(BaseModel):
    products: List[Product]
    match_description: str


class SuggestionRequest(BaseModel):
    image_url: str
    description: str
    query: str


class StyleSuggestion(BaseModel):
    title: str
    description: str


class SuggestionResponse(BaseModel):
    suggestions: List[StyleSuggestion]


class CreateLookRequest(BaseModel):
    products: List[Product]


class CreateLookResponse(BaseModel):
    look_image_url: str
    description: str
    products: List[Product]


# API Endpoints
@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Main search endpoint: Parse query and generate concept image.

    Flow:
    1. Parse natural language query with Gemini NLU
    2. Generate visual concept image using Gemini Flash 2.5 Image
    3. Return image and description
    """
    try:
        # Parse the fashion query
        parsed_attributes = await nlu_service.parse_fashion_query(request.query)

        # Generate concept image
        visual_prompt = parsed_attributes.get("visual_generation_prompt", request.query)
        image_result = await image_service.generate_concept_image(
            visual_prompt,
            parsed_attributes
        )

        return SearchResponse(
            image_url=image_result["image_url"],
            description=image_result["description"],
            parsed_attributes=parsed_attributes
        )

    except Exception as e:
        print(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/search-by-image", response_model=SearchByImageResponse)
async def search_by_image(request: SearchByImageRequest):
    """
    Search by uploaded image: Analyze image and generate concept.

    Flow:
    1. Analyze uploaded image with Gemini vision to extract style attributes
    2. Generate fashion concept image based on analyzed style
    3. Return concept image, description, and analyzed style
    """
    import traceback

    print("\n" + "="*80)
    print("[ENDPOINT] /api/search-by-image called")
    print(f"[ENDPOINT] Image data length: {len(request.image_data) if request.image_data else 0}")
    print(f"[ENDPOINT] Additional description: {request.additional_description}")
    print("="*80 + "\n")

    try:
        # Analyze the uploaded image to extract style attributes
        print("[ENDPOINT] Calling analyze_image_for_style...")
        style_analysis = await nlu_service.analyze_image_for_style(
            request.image_data,
            request.additional_description
        )
        print(f"[ENDPOINT] Style analysis received: {list(style_analysis.keys())}")

        # Generate concept image based on analyzed style
        print("[ENDPOINT] Generating concept image...")
        image_result = await image_service.generate_concept_image(
            style_analysis["visual_prompt"],
            style_analysis["attributes"]
        )
        print(f"[ENDPOINT] Image generated: {image_result.get('image_url', 'N/A')}")

        result = SearchByImageResponse(
            image_url=image_result["image_url"],
            description=image_result["description"],
            analyzed_style=style_analysis["style_description"]
        )
        print("[ENDPOINT] Returning successful response\n")
        return result

    except Exception as e:
        print(f"[ENDPOINT ERROR] Error in search-by-image endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


@app.post("/api/refine", response_model=RefineResponse)
async def refine(request: RefineRequest):
    """
    Refine concept image based on user feedback.

    Flow:
    1. Take refinement instructions
    2. Generate new/edited image with Gemini Flash 2.5 Image
    3. Return refined image
    """
    try:
        refined_result = await image_service.refine_image(
            request.original_prompt,
            request.refinement_prompt,
            request.current_image_url
        )

        return RefineResponse(
            image_url=refined_result["image_url"],
            description=refined_result["description"]
        )

    except Exception as e:
        print(f"Error in refine endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")


@app.post("/api/match-products", response_model=MatchProductsResponse)
async def match_products(request: MatchProductsRequest):
    """
    Find matching products from catalog using vector search.

    Flow:
    1. Re-parse the query for attributes
    2. Use image description to generate embedding
    3. Search BigQuery with vector similarity
    4. Return ranked products
    """
    try:
        # Re-parse query for filtering attributes
        parsed_attributes = await nlu_service.parse_fashion_query(request.query)

        # Search products using the generated concept image
        products = await product_service.search_products_by_image(
            request.image_url,
            parsed_attributes,
            limit=10
        )

        # Generate match description
        match_description = product_service.generate_match_description(
            products,
            parsed_attributes
        )

        return MatchProductsResponse(
            products=[Product(**p) for p in products],
            match_description=match_description
        )

    except Exception as e:
        print(f"Error in match-products endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Product matching failed: {str(e)}")


@app.post("/api/suggest-refinements", response_model=SuggestionResponse)
async def suggest_refinements(request: SuggestionRequest):
    """
    Generate AI-powered style variation suggestions for current concept.

    Flow:
    1. Load concept image
    2. Analyze with Gemini vision
    3. Generate 4-6 contextual suggestions
    4. Return suggestions as short, actionable phrases
    """
    try:
        suggestions = await suggestion_service.generate_style_suggestions(
            request.image_url,
            request.description,
            request.query
        )

        return SuggestionResponse(suggestions=suggestions)

    except Exception as e:
        print(f"Error in suggest-refinements endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")


@app.post("/api/create-look", response_model=CreateLookResponse)
async def create_look(request: CreateLookRequest):
    """
    Generate a styled outfit look combining 2-3 selected products.

    Flow:
    1. Receive selected products (2-3 items)
    2. Load product images from URLs
    3. Use Gemini Flash 2.5 Image to generate styled outfit
    4. Return generated look image with product references
    """
    try:
        # Convert Pydantic models to dictionaries for the service
        products_data = [product.dict() for product in request.products]

        # Validate product count
        if len(products_data) < 2:
            raise HTTPException(status_code=400, detail="At least 2 products required to create a look")
        if len(products_data) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 products allowed for look creation")

        # Generate look
        look_result = await look_service.generate_look_from_products(products_data)

        return CreateLookResponse(
            look_image_url=look_result["look_image_url"],
            description=look_result["description"],
            products=request.products
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create-look endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Look generation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Athena Fashion Search API"}


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="generated_images"), name="images")


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )
