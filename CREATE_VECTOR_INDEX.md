# Creating a Vector Index for Efficient Product Search

## Why You Need This

With 40,000 products, calculating cosine similarity for every product on each search is slow. A vector index uses Approximate Nearest Neighbor (ANN) search for much faster results.

## Steps to Create the Index

### 1. Update the SQL Script

Edit `setup_vector_index.sql` and replace:
- `your_project_id` with your GCP project ID
- `your_dataset_name` with your BigQuery dataset name
- Verify table name is `product_embeddings`

### 2. Run the Index Creation Command

Using `bq` command-line tool:

```bash
# Set your project
export PROJECT_ID="your-project-id"
export DATASET="your_dataset_name"

# Create the vector index
bq query --use_legacy_sql=false "
CREATE OR REPLACE VECTOR INDEX product_embeddings_index
ON \`${PROJECT_ID}.${DATASET}.product_embeddings\`(embedding)
OPTIONS(
  distance_type = 'COSINE',
  index_type = 'IVF'
)
"
```

Or using the BigQuery Console:
1. Go to https://console.cloud.google.com/bigquery
2. Click **Compose New Query**
3. Paste the SQL from `setup_vector_index.sql` (with your values filled in)
4. Click **Run**

### 3. Monitor Index Creation

Check the status:

```bash
bq query --use_legacy_sql=false "
SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage,
  last_refresh_time
FROM \`${PROJECT_ID}.${DATASET}.INFORMATION_SCHEMA.VECTOR_INDEXES\`
WHERE table_name = 'product_embeddings'
"
```

**Wait for:**
- `index_status`: ACTIVE
- `coverage_percentage`: 100.0

This typically takes 5-15 minutes for 40,000 products.

### 4. Update Your Application Configuration

Once the index is ready (coverage_percentage = 100), update your `.env` file:

```env
# Add this line to enable vector search
USE_VECTOR_INDEX=true
```

Then restart your application.

## How It Works

### Before (Slow - Full Scan):
```sql
-- Calculates similarity for ALL 40,000 products
SELECT *, cosine_similarity(embedding, query_embedding)
FROM products
ORDER BY similarity DESC
LIMIT 20
```
**Time:** ~5-10 seconds

### After (Fast - Index Lookup):
```sql
-- Uses ANN index to find top candidates quickly
SELECT * FROM VECTOR_SEARCH(
  TABLE products,
  'embedding',
  (SELECT query_embedding),
  top_k => 20,
  distance_type => 'COSINE'
)
```
**Time:** ~100-500ms

## Performance Expectations

| Products | Without Index | With Index |
|----------|--------------|------------|
| 10,000   | 2-3s         | 100-200ms  |
| 40,000   | 5-10s        | 200-400ms  |
| 100,000  | 15-30s       | 300-600ms  |

## Options and Tuning

### Index Options

```sql
OPTIONS(
  distance_type = 'COSINE',        -- or 'EUCLIDEAN', 'DOT_PRODUCT'
  index_type = 'IVF',              -- Inverted File index (recommended)
  ivf_options = '{
    "num_lists": 1000              -- More lists = better accuracy, slower build
  }'
)
```

### Query Options

```sql
VECTOR_SEARCH(...,
  options => '{
    "fraction_lists_to_search": 0.01  -- Search 1% of lists (lower = faster, less accurate)
  }'
)
```

**Tuning `fraction_lists_to_search`:**
- `0.001` (0.1%): Fastest, ~80-90% recall
- `0.01` (1%): Balanced, ~90-95% recall  ← **Recommended**
- `0.05` (5%): High accuracy, ~95-99% recall
- `0.1` (10%): Best accuracy, ~99%+ recall

## Troubleshooting

### Index Not Creating

**Error:** "Dataset not found"
- Check your project ID and dataset name
- Ensure you have `bigquery.tables.update` permission

**Error:** "Column 'embedding' not found"
- Verify the embedding column exists
- Check it's an `ARRAY<FLOAT64>` type

### Index Stuck at Low Coverage

- Wait longer (can take 15+ minutes)
- Check for errors: `SELECT disable_reason FROM INFORMATION_SCHEMA.VECTOR_INDEXES`

### Poor Search Results

- Increase `fraction_lists_to_search` to 0.05 or 0.1
- Verify embeddings are normalized (unit vectors)
- Check that query embeddings use the same model (multimodalembedding@001)

## Costs

Vector index costs:
- **Storage:** ~$0.02 per GB per month
- **Query:** Standard BigQuery on-demand pricing
- **Index Creation:** One-time, included in query costs

For 40,000 products with 1408-dim embeddings:
- Index size: ~220 MB
- Monthly cost: ~$0.005 (negligible)

## Next Steps

After creating the index:

1. ✓ Create the vector index (above)
2. ✓ Wait for 100% coverage
3. ✓ Set `USE_VECTOR_INDEX=true` in `.env`
4. ✓ Restart the application
5. ✓ Test search performance

The application will automatically use `VECTOR_SEARCH` when the flag is enabled!
