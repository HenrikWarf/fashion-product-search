# Athena Setup Guide

This guide walks you through setting up the Athena fashion search application step-by-step.

## Table of Contents
1. [GCP Project Setup](#gcp-project-setup)
2. [BigQuery Data Preparation](#bigquery-data-preparation)
3. [Service Account Configuration](#service-account-configuration)
4. [Local Environment Setup](#local-environment-setup)
5. [Running the Application](#running-the-application)
6. [Testing](#testing)

## GCP Project Setup

### Step 1: Create or Select GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID (e.g., `my-fashion-search-123`)

### Step 2: Enable Required APIs

Run these commands in Cloud Shell or local terminal (with gcloud installed):

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
```

Or enable through the console:
1. Navigate to **APIs & Services > Library**
2. Search and enable:
   - Vertex AI API
   - BigQuery API
   - Cloud Storage API

## BigQuery Data Preparation

### Step 1: Create Dataset

```bash
# Create dataset
bq mk --dataset \
  --location=US \
  ${PROJECT_ID}:fashion_products
```

### Step 2: Prepare Your Product Data

Since you already have the `product_embeddings` table with 40,000 products, verify it has the correct structure:

**Expected Schema:**
- `product_id`: STRING - Unique identifier (e.g., "10000")
- `image_filename`: STRING - Original filename (e.g., "10000.jpg")
- `image_path`: STRING - Path in GCS (e.g., "images/10000.jpg")
- `gcs_uri`: STRING - Full GCS URI (e.g., "gs://bucket_name/images/10000.jpg")
- `embedding`: ARRAY<FLOAT64> - 1408-dimensional vector
- `created_at`: TIMESTAMP - When the embedding was generated
- `metadata`: JSON - Product metadata containing:
  - `productDisplayName`: Product name
  - `brandName`: Brand name
  - `price.mrp`: Price value
  - `baseColour`: Color
  - `articleType.typeName`: Category/type
  - `gender`: Target gender
  - `season`: Season
  - `productDescriptors.description.value`: Product description

**Verify your table:**
```bash
# Check table schema
bq show --schema --format=prettyjson ${PROJECT_ID}:fashion_products.product_embeddings

# Check sample data
bq query --use_legacy_sql=false "
SELECT
  product_id,
  gcs_uri,
  JSON_VALUE(metadata, '$.productDisplayName') as name,
  JSON_VALUE(metadata, '$.price.mrp') as price,
  ARRAY_LENGTH(embedding) as embedding_dim
FROM fashion_products.product_embeddings
LIMIT 5
"
```

### Step 3: Verify Embeddings

Since your table already has embeddings generated with the multimodal embedding model, verify they are correct:

```bash
# Check embedding dimensions (should be 1408)
bq query --use_legacy_sql=false "
SELECT
  product_id,
  ARRAY_LENGTH(embedding) as embedding_dimension,
  JSON_VALUE(metadata, '$.productDisplayName') as product_name
FROM fashion_products.product_embeddings
WHERE embedding IS NOT NULL
LIMIT 10
"
```

**Expected output:**
- All embeddings should have dimension = 1408
- This matches the `multimodalembedding@001` model output

**Note:** If you need to generate NEW embeddings in the future, use this approach:

```python
# generate_embeddings.py (for reference)
from vertexai.vision_models import MultiModalEmbeddingModel
import vertexai

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Use multimodal embedding model
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

# For text
embeddings = model.get_embeddings(
    contextual_text="Product description here",
    dimension=1408
)
text_embedding = embeddings.text_embedding  # 1408-dimensional vector

# For images
embeddings = model.get_embeddings(
    image=image_object,
    dimension=1408
)
image_embedding = embeddings.image_embedding  # 1408-dimensional vector
```

### Step 4: Your Table is Ready!

Since you already have the `product_embeddings` table populated with 40,000 products, you're ready to proceed. The table schema is:

```sql
-- Your existing table structure
CREATE TABLE `your-project.fashion_products.product_embeddings` (
    product_id STRING,
    image_filename STRING,
    image_path STRING,
    gcs_uri STRING,
    embedding ARRAY<FLOAT64>,  -- 1408-dimensional vectors
    created_at TIMESTAMP,
    metadata JSON  -- All product metadata
);
```

**Verify record count:**
```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) as total_products
FROM fashion_products.product_embeddings
WHERE embedding IS NOT NULL
"
```

Expected: ~40,000 products

## Service Account Configuration

### Step 1: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create athena-fashion-search \
  --display-name="Athena Fashion Search Service Account" \
  --description="Service account for Athena fashion search application"

# Set service account email
export SA_EMAIL="athena-fashion-search@${PROJECT_ID}.iam.gserviceaccount.com"
```

### Step 2: Grant Permissions

```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

# Grant BigQuery Data Viewer role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataViewer"

# Grant BigQuery Job User role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.jobUser"
```

### Step 3: Create and Download Key

```bash
# Create key
gcloud iam service-accounts keys create athena-sa-key.json \
  --iam-account=${SA_EMAIL}

# Move to project directory
mv athena-sa-key.json ~/Documents/fashion_product_search/
```

**Important**: Keep this key file secure and never commit it to version control!

## Local Environment Setup

### Step 1: Install Python Dependencies

```bash
cd ~/Documents/fashion_product_search

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Update with your values:
```env
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./athena-sa-key.json

BIGQUERY_DATASET=fashion_products
BIGQUERY_TABLE=product_embeddings

GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_IMAGE_MODEL=gemini-2.5-flash-preview-0205

PORT=8000
```

### Step 3: Verify GCP Connection

Test your configuration with this Python script:

```python
# test_connection.py
from services.gcp_client import get_gcp_client
from config import get_settings

try:
    settings = get_settings()
    print(f"Project ID: {settings.gcp_project_id}")

    client = get_gcp_client()
    print("✓ GCP Client initialized")

    # Test BigQuery
    bq_client = client.bigquery
    query = f"SELECT COUNT(*) as count FROM `{settings.bigquery_dataset}.{settings.bigquery_table}`"
    result = bq_client.query(query).result()
    for row in result:
        print(f"✓ BigQuery connected - {row.count} products found")

    # Test Gemini
    model = client.get_gemini_model()
    print("✓ Gemini model loaded")

    print("\n✓ All connections successful!")

except Exception as e:
    print(f"✗ Error: {e}")
```

Run the test:
```bash
python test_connection.py
```

## Running the Application

### Start the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
python main.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## Testing

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "Athena Fashion Search API"}
```

### Test 2: Search API

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "formal dress for summer wedding, pastel colors, under $200"}'
```

### Test 3: Full User Journey

1. Open `http://localhost:8000` in browser
2. Enter query: "I need a formal dress for a summer wedding. Something pastel, under $200, and good for a petite person."
3. Click search and wait for concept image
4. Try refining: "make it sage green with flutter sleeves"
5. Click "Find Matching Products"
6. Verify products are displayed with similarity scores

## Common Issues

### Issue: "Service account key not found"
**Solution**: Verify the path to your JSON key file in `.env` is correct

### Issue: "Permission denied on BigQuery"
**Solution**: Run the grant permissions commands again from Service Account Configuration

### Issue: "Table not found"
**Solution**:
```bash
# Check if table exists
bq ls fashion_products

# Check if you can query it
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM fashion_products.product_embeddings"
```

### Issue: "No products returned from search"
**Solution**:
- Verify your product_embeddings table has data: `bq query "SELECT COUNT(*) FROM fashion_products.product_embeddings"`
- Check embeddings are populated: `bq query "SELECT COUNT(*) FROM fashion_products.product_embeddings WHERE embedding IS NOT NULL"`
- Ensure embedding dimensions are 1408 (not 768)
- Verify metadata JSON structure matches expected format
- Check the vector search query in `product_search_service.py`

### Issue: Port 8000 already in use
**Solution**:
```bash
# Change port in .env
PORT=8001

# Or kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

## Next Steps

Once your application is running:

1. **Add More Products**: Expand your catalog with more diverse items
2. **Fine-tune Prompts**: Adjust prompts in `nlu_service.py` for better understanding
3. **Customize UI**: Modify `static/styles.css` to match your brand
4. **Add Features**: Implement voice input, user accounts, favorites, etc.
5. **Deploy to Production**: Follow deployment guide for Cloud Run

## Support

For additional help:
- Check the main README.md
- Review GCP documentation: https://cloud.google.com/vertex-ai/docs
- Review BigQuery documentation: https://cloud.google.com/bigquery/docs
