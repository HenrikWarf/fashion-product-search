# Schema Update Summary

The Athena application has been updated to work with your existing BigQuery `product_embeddings` table schema.

## Changes Made

### 1. BigQuery Schema Adaptation

**Your Table Structure:**
```sql
CREATE TABLE product_embeddings (
    product_id STRING,
    image_filename STRING,
    image_path STRING,
    gcs_uri STRING,
    embedding ARRAY<FLOAT64>,  -- 1408-dimensional
    created_at TIMESTAMP,
    metadata JSON
);
```

**Metadata JSON Structure:**
```json
{
  "productDisplayName": "Product Name",
  "brandName": "Brand",
  "price": {
    "mrp": 199.99
  },
  "baseColour": "Green",
  "articleType": {
    "typeName": "Dress"
  },
  "gender": "Women",
  "season": "Summer",
  "productDescriptors": {
    "description": {
      "value": "Product description text"
    }
  }
}
```

### 2. Updated Files

#### `services/product_search_service.py`
- **Updated embedding generation**: Now uses `MultiModalEmbeddingModel` with 1408 dimensions
- **Updated SQL queries**: Uses `JSON_VALUE()` to extract data from metadata column
- **Updated filtering**: Adapted WHERE clauses for JSON-based filtering
  - Price: `JSON_VALUE(metadata, '$.price.mrp')`
  - Color: `JSON_VALUE(metadata, '$.baseColour')`
  - Category: `JSON_VALUE(metadata, '$.articleType.typeName')`
  - Gender: `JSON_VALUE(metadata, '$.gender')`
  - Season: `JSON_VALUE(metadata, '$.season')`
- **Updated result parsing**: Extracts product details from JSON metadata

#### `main.py`
- Added `season` and `gender` fields to Product model
- These fields are now populated from the metadata JSON

#### `README.md`
- Updated BigQuery schema documentation
- Changed table name from `products` to `product_embeddings`
- Updated embedding dimensions from 768 to 1408
- Added metadata JSON structure documentation

#### `SETUP_GUIDE.md`
- Updated data preparation section to reflect existing table
- Added verification steps for metadata JSON structure
- Updated embedding dimension checks
- Changed all table references to `product_embeddings`

#### `.env.example`
- Updated default table name to `product_embeddings`

### 3. Key Technical Changes

#### Embedding Model
**Before:**
```python
from vertexai.language_models import TextEmbeddingModel
model = TextEmbeddingModel.from_pretrained("textembedding-gecko-multilingual@001")
# Returns 768-dimensional vectors
```

**After:**
```python
from vertexai.vision_models import MultiModalEmbeddingModel
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
embeddings = model.get_embeddings(contextual_text=text, dimension=1408)
# Returns 1408-dimensional vectors
```

#### Vector Search Query
**Before:**
```sql
SELECT product_id, name, price, color, category, brand, ...
FROM products
```

**After:**
```sql
SELECT
    product_id,
    gcs_uri,
    metadata,
    -- Calculate cosine similarity
    (SELECT SUM(a * b) / (SQRT(SUM(a * a)) * SQRT(SUM(b * b)))
     FROM UNNEST(embedding) AS a WITH OFFSET pos1
     JOIN UNNEST(q.embedding) AS b WITH OFFSET pos2
     ON pos1 = pos2) AS similarity_score
FROM product_embeddings
WHERE CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) <= 200
  AND LOWER(JSON_VALUE(metadata, '$.baseColour')) LIKE '%green%'
```

#### Result Parsing
**Before:**
```python
product = {
    "name": row.get("name"),
    "price": row.get("price"),
    "color": row.get("color"),
    ...
}
```

**After:**
```python
metadata = row.get("metadata", {})
if isinstance(metadata, str):
    metadata = json.loads(metadata)

product = {
    "name": metadata.get("productDisplayName", "Unknown Product"),
    "price": metadata.get("price", {}).get("mrp", 0),
    "color": metadata.get("baseColour", ""),
    "category": metadata.get("articleType", {}).get("typeName", ""),
    "brand": metadata.get("brandName", ""),
    "image_url": row.get("gcs_uri", ""),
    ...
}
```

### 4. What Works Now

✓ Vector similarity search with 1408-dimensional embeddings
✓ JSON-based metadata filtering (price, color, category, gender, season)
✓ Product result parsing from JSON metadata structure
✓ GCS URI image paths
✓ 40,000 product catalog support

### 5. Configuration

Update your `.env` file:
```env
BIGQUERY_DATASET=your_dataset_name
BIGQUERY_TABLE=product_embeddings
```

### 6. Testing the Changes

Verify the setup works:

```bash
# Test connection
python test_connection.py

# Check table access
bq query "SELECT COUNT(*) FROM your_dataset.product_embeddings"

# Verify metadata structure
bq query "
SELECT
  product_id,
  JSON_VALUE(metadata, '$.productDisplayName') as name,
  JSON_VALUE(metadata, '$.price.mrp') as price,
  ARRAY_LENGTH(embedding) as embedding_dim
FROM your_dataset.product_embeddings
LIMIT 5
"
```

### 7. Example Search Flow

1. **User Query**: "formal dress for summer wedding, under $200"

2. **NLU Parsing** → Extracts:
   - `price_max: 200`
   - `occasion: "wedding"`
   - `category: "dress"`

3. **Embedding Generation** → 1408-dimensional vector using MultiModalEmbeddingModel

4. **Vector Search** → SQL with JSON filtering:
   ```sql
   WHERE CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) <= 200
     AND LOWER(JSON_VALUE(metadata, '$.articleType.typeName')) LIKE '%dress%'
   ```

5. **Results** → Top matching products with similarity scores

## Compatibility Notes

- **Embedding Dimensions**: Must be 1408 (not 768)
- **Model**: Must use `multimodalembedding@001` for consistency
- **Metadata**: JSON structure must match expected format
- **Images**: GCS URIs in `gcs_uri` column

## Future Enhancements

Consider adding:
1. **Metadata validation** in data pipeline
2. **Caching** for frequently accessed metadata
3. **Materialized views** for common JSON extractions
4. **Full-text search** on product descriptions
5. **Image embedding search** using actual product images (not just text descriptions)
