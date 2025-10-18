# Synthetic Fashion Catalog Generator

Generate a synthetic women's fashion catalog with 200 products using:
- **Imagen 4** for high-quality product photography
- **Gemini** for diverse product specifications
- **Multimodal Embeddings** for vector search
- **BigQuery** with flattened schema for easy querying

## Overview

This tool creates a complete synthetic product catalog with H&M-style aesthetic:
- 200 unique women's fashion products
- Professional e-commerce photography
- Realistic metadata (prices, descriptions, attributes)
- Fully searchable with vector embeddings
- Stored in flat BigQuery schema (no JSON parsing needed)

## Category Distribution

- **Tops** (45): T-shirts, Blouses, Sweaters, Cardigans, Tank tops
- **Bottoms** (40): Jeans, Trousers, Skirts, Shorts, Leggings
- **Dresses** (40): Casual, Formal, Midi, Maxi, Mini
- **Outerwear** (30): Jackets, Coats, Blazers, Vests
- **Activewear** (20): Sports bras, Leggings, Hoodies, Track jackets
- **Knitwear** (25): Jumpers, Cardigans, Turtlenecks, Pullovers

## Prerequisites

1. GCP Project with Vertex AI enabled
2. Service account with permissions:
   - BigQuery Admin
   - Storage Admin
   - Vertex AI User
3. Authenticated with `gcloud auth application-default login`

## Installation

```bash
cd synthetic_catalog
pip install -r requirements.txt
```

## Usage

### Step 1: Create BigQuery Table

```bash
bq query --use_legacy_sql=false --project_id="ml-developer-project-fe07" < create_table.sql
```

This creates the `synthetic_products` table with flattened schema.

### Step 2: Generate Product Specifications

```bash
cd ..
python synthetic_catalog/product_specs_generator.py \
  --count 200 \
  --output synthetic_catalog/output/product_specifications.json
```

This uses Gemini to generate 200 diverse product specs with realistic attributes.

**Output**: `synthetic_catalog/output/product_specifications.json`

### Step 3: Generate Full Catalog

```bash
python synthetic_catalog/catalog_creator.py \
  --specs synthetic_catalog/output/product_specifications.json \
  --gcs-bucket assortment_automation \
  --gcs-prefix synthetic_catalog/images \
  --bq-dataset products \
  --bq-table synthetic_products
```

This will:
1. Generate product images with Imagen 4
2. Upload to Cloud Storage
3. Create embeddings
4. Insert into BigQuery

**Time**: ~6-10 hours for 200 products (with rate limiting)
**Cost**: ~$20-25

### Step 4: Create Vector Index

```bash
./create_vector_index_synthetic.sh
```

Or manually:

```bash
bq query --use_legacy_sql=false --project_id="ml-developer-project-fe07" "
CREATE OR REPLACE VECTOR INDEX synthetic_products_index
ON \`ml-developer-project-fe07.products.synthetic_products\`(embedding)
OPTIONS(
  distance_type = 'COSINE',
  index_type = 'IVF'
)
"
```

Wait for index to complete (check status):

```bash
bq query --use_legacy_sql=false --project_id="ml-developer-project-fe07" "
SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage
FROM \`ml-developer-project-fe07.products.INFORMATION_SCHEMA.VECTOR_INDEXES\`
WHERE table_name = 'synthetic_products'
"
```

### Step 5: Update Application

Update `config.py` to use the new table:

```python
BIGQUERY_TABLE = "synthetic_products"
```

Then restart the application.

## Resume Failed Runs

If the generation fails or is interrupted, resume from a specific index:

```bash
python synthetic_catalog/catalog_creator.py \
  --specs synthetic_catalog/output/product_specifications.json \
  --resume-from 50
```

Check the log file for the last successful index:

```bash
tail synthetic_catalog/output/generation_log.jsonl
```

## File Structure

```
synthetic_catalog/
├── category_definitions.py        # Category templates and attributes
├── product_specs_generator.py     # Generate specs with Gemini
├── image_generator.py             # Generate images with Imagen 4
├── catalog_creator.py             # Main orchestrator
├── create_table.sql               # BigQuery table schema
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── output/
    ├── product_specifications.json  # Generated specs
    ├── generation_log.jsonl         # Progress log
    ├── summary_report.txt           # Final report
    └── images/                      # Local copy of images
```

## Schema

The `synthetic_products` table has a flat structure (no JSON):

| Column | Type | Description |
|--------|------|-------------|
| product_id | STRING | Unique ID (SYN-XXXXXXXX) |
| image_filename | STRING | Filename in GCS |
| gcs_uri | STRING | Full GCS path |
| embedding | ARRAY<FLOAT64> | 1408-dim vector |
| product_name | STRING | Display name |
| brand_name | STRING | Fictional brand |
| category | STRING | Main category |
| subcategory | STRING | Specific type |
| base_color | STRING | Primary color |
| secondary_color | STRING | Optional |
| pattern | STRING | Solid, Striped, etc. |
| fabric | STRING | Cotton, Denim, etc. |
| fit | STRING | Regular, Slim, etc. |
| sleeve_length | STRING | Long, Short, etc. |
| neck_style | STRING | V-Neck, Round, etc. |
| season | STRING | Spring/Summer/Fall/Winter |
| occasion | STRING | Casual, Formal, etc. |
| style | STRING | Modern, Classic, etc. |
| gender | STRING | Always "Women" |
| price_original | FLOAT64 | Original price |
| price_discounted | FLOAT64 | Sale price (optional) |
| description | STRING | Marketing text |
| created_at | TIMESTAMP | Creation time |

## Querying Examples

```sql
-- Find red dresses under $50
SELECT product_name, base_color, price_original
FROM `ml-developer-project-fe07.products.synthetic_products`
WHERE category = 'Dresses'
  AND base_color = 'Red'
  AND price_original < 50
ORDER BY price_original;

-- Count by category
SELECT category, COUNT(*) as count
FROM `ml-developer-project-fe07.products.synthetic_products`
GROUP BY category
ORDER BY count DESC;

-- Find casual summer tops
SELECT product_name, base_color, price_original
FROM `ml-developer-project-fe07.products.synthetic_products`
WHERE category = 'Tops'
  AND season = 'Summer'
  AND occasion = 'Casual'
LIMIT 10;
```

## Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| Gemini (specs) | 200 requests | ~$0.02 |
| Imagen 4 (images) | 200 images | ~$20.00 |
| Embeddings | 200 embeddings | ~$0.20 |
| BigQuery Storage | ~100MB | ~$0.002/mo |
| GCS Storage | ~50MB | ~$0.001/mo |
| **Total** | One-time | **~$20-25** |

## Troubleshooting

### Imagen 4 Quota Errors
- Add `time.sleep(2)` between requests
- Use `--resume-from` to restart
- Request quota increase in GCP Console

### BigQuery Insert Errors
- Check table schema matches
- Verify all required fields are present
- Check for null values in required columns

### Embedding Generation Fails
- Ensure multimodalembedding@001 is available
- Check GCS URIs are accessible
- Verify service account permissions

## Next Steps

After generation:

1. ✅ Verify data in BigQuery
2. ✅ Create vector index
3. ✅ Update application config
4. ✅ Test searches
5. ✅ Compare with original catalog

## License

This generates synthetic data for demonstration purposes only.
