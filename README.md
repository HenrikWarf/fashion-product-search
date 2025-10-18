# Athena - AI-Powered Fashion Search

An intelligent fashion search application that uses Google's Gemini AI to understand natural language queries, generate visual fashion concepts, and match them with products from your catalog.

## Features

- **Natural Language Understanding**: Describe what you're looking for in plain English
- **Visual Concept Generation**: AI generates fashion concept images using Gemini Flash 2.5
- **Interactive Refinement**: Refine designs with text prompts
- **Smart Product Matching**: Vector similarity search using BigQuery and multimodal embeddings
- **Attribute-Based Filtering**: Intelligent filtering by price, color, style, occasion, etc.

## Architecture

### Frontend
- Pure HTML/CSS/JavaScript
- Clean, minimalist UI with Visual Workbench
- Three main views: Search, Workbench, Products

### Backend (Python/FastAPI)
- **NLU Service**: Gemini-powered query parsing and attribute extraction
- **Image Generation Service**: Concept image generation and refinement with Gemini Flash 2.5
- **Product Search Service**: BigQuery vector similarity search with multimodal embeddings

### GCP Services
- **Vertex AI**: Gemini models for NLU and image generation
- **BigQuery**: Product catalog storage with vector embeddings
- **Service Account**: Secure authentication

## Prerequisites

1. **Python 3.9+**
2. **GCP Project** with the following enabled:
   - Vertex AI API
   - BigQuery API
   - Cloud Storage API (optional, for production image hosting)
3. **GCP Service Account** with permissions:
   - `roles/aiplatform.user`
   - `roles/bigquery.dataViewer`
   - `roles/bigquery.jobUser`
4. **BigQuery Dataset** with product_embeddings table containing:
   - Product ID and GCS image URIs
   - 1408-dimensional embeddings (generated with `multimodalembedding@001`)
   - JSON metadata column with product details (productDisplayName, price, baseColour, brandName, articleType, etc.)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd fashion_product_search
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure GCP Service Account

1. Go to [GCP Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin > Service Accounts**
3. Create a new service account or use existing one
4. Grant required roles (listed in Prerequisites)
5. Create and download a JSON key
6. Save the key file in your project directory

### 3. Prepare BigQuery Table

Your BigQuery table should have this structure (product_embeddings schema):

```sql
CREATE TABLE `your_project.your_dataset.product_embeddings` (
    product_id STRING,
    image_filename STRING,
    image_path STRING,
    gcs_uri STRING,
    embedding ARRAY<FLOAT64>,  -- 1408-dimensional multimodal embeddings
    created_at TIMESTAMP,
    metadata JSON  -- Contains: productDisplayName, brandName, price, baseColour, articleType, etc.
);
```

**Important**:
- The `embedding` column should contain 1408-dimensional vectors generated using Google's `multimodalembedding@001` model
- The `metadata` JSON column contains all product details (name, price, color, category, brand, etc.)
- The `gcs_uri` column contains the full GCS path to the product image

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json

# BigQuery Configuration
BIGQUERY_DATASET=your_dataset_name
BIGQUERY_TABLE=product_embeddings

# Gemini Configuration (use defaults or customize)
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_IMAGE_MODEL=gemini-2.5-flash-preview-0205

# Server Configuration
PORT=8000
```

### 5. Run the Application

```bash
python main.py
```

The application will start on `http://localhost:8000`

## Usage

### 1. Search
Enter a natural language query like:
> "I need a formal dress for a summer wedding. Something pastel, under $200, and good for a petite person. I don't want anything too puffy or overwhelming."

### 2. View Generated Concept
The AI generates a visual concept image based on your description, biased toward available inventory.

### 3. Refine Design
Adjust the design with text prompts:
> "Make it sage green with flutter sleeves and a more structured fabric"

### 4. Find Matching Products
Click "Find Matching Products" to search your catalog using vector similarity.

## API Endpoints

### POST `/api/search`
Parse query and generate concept image.

**Request:**
```json
{
  "query": "formal dress for summer wedding, pastel, under $200"
}
```

**Response:**
```json
{
  "image_url": "/images/concept_20240116_123456.png",
  "description": "A fashion concept designed for summer wedding...",
  "parsed_attributes": { ... }
}
```

### POST `/api/refine`
Refine existing concept image.

**Request:**
```json
{
  "original_prompt": "formal dress for summer wedding",
  "refinement_prompt": "make it sage green with flutter sleeves",
  "current_image_url": "/images/concept_20240116_123456.png"
}
```

### POST `/api/match-products`
Find matching products from catalog.

**Request:**
```json
{
  "query": "original search query",
  "image_url": "/images/refined_20240116_123500.png",
  "description": "Refined design description"
}
```

**Response:**
```json
{
  "products": [
    {
      "id": "prod_123",
      "name": "Sage Flutter Dress",
      "price": 189.99,
      "similarity_score": 0.92,
      ...
    }
  ],
  "match_description": "Found 15 products that match your refined style..."
}
```

## Project Structure

```
fashion_product_search/
├── main.py                 # FastAPI application
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Environment template
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── static/                # Frontend files
│   ├── index.html         # Main HTML
│   ├── styles.css         # Styling
│   └── app.js             # Frontend JavaScript
├── services/              # Backend services
│   ├── __init__.py
│   ├── gcp_client.py      # GCP authentication and clients
│   ├── nlu_service.py     # Natural language understanding
│   ├── image_generation_service.py  # Image generation with Gemini
│   └── product_search_service.py    # BigQuery vector search
└── generated_images/      # Generated concept images (created automatically)
```

## Development Notes

### Image Generation

The current implementation includes placeholder logic for Gemini Flash 2.5 Image generation. As this model's API evolves, you may need to update the `_extract_image_from_response()` method in `image_generation_service.py`.

For now, the application uses a fallback placeholder image. To integrate actual image generation:

1. Check Vertex AI documentation for Gemini 2.5 Flash image generation API
2. Update the `generate_concept_image()` and `refine_image()` methods
3. Handle the response format for generated images

### Vector Search

The BigQuery vector search uses cosine similarity with the following specifications:
- Embeddings must be 1408-dimensional vectors
- Generated using `multimodalembedding@001` model from Vertex AI
- Stored as `ARRAY<FLOAT64>` in BigQuery
- Product metadata is stored in JSON format and queried using `JSON_VALUE()` for filtering

### Production Considerations

For production deployment:

1. **Image Storage**: Upload generated images to Cloud Storage instead of local filesystem
2. **Caching**: Implement caching for embeddings and search results
3. **Rate Limiting**: Add rate limiting to API endpoints
4. **Authentication**: Implement user authentication
5. **Monitoring**: Add logging and monitoring with Cloud Logging
6. **Scaling**: Deploy to Cloud Run or GKE for auto-scaling

## Troubleshooting

### "Service account key not found"
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` in `.env` points to your JSON key file
- Use absolute path or path relative to project root

### "Table not found" error
- Verify `BIGQUERY_DATASET` and `BIGQUERY_TABLE` in `.env`
- Ensure your service account has `bigquery.dataViewer` role
- Check table exists: `bq ls your_dataset`

### Image generation returns placeholder
- This is expected in the current implementation
- Gemini Flash 2.5 Image API integration is in progress
- Update `image_generation_service.py` when API is fully available

### No products returned
- Check that your products table has data
- Verify embeddings column is populated
- Review attribute filtering logic in `product_search_service.py`

## License

Proprietary

## Support

For issues or questions, please contact the development team.
