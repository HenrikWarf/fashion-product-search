-- BigQuery Vector Index Setup for Athena Fashion Search
-- This script creates a vector index on the product_embeddings table for efficient similarity search

-- Replace these variables with your actual values:
-- - your_project_id
-- - your_dataset_name
-- - product_embeddings (or your table name)

-- Step 1: Create the vector index on the embedding column
CREATE OR REPLACE VECTOR INDEX product_embeddings_index
ON `your_project_id.your_dataset_name.product_embeddings`(embedding)
OPTIONS(
  distance_type = 'COSINE',
  index_type = 'IVF'
);

-- Step 2: Check index creation status
-- Run this query to monitor progress (coverage_percentage should reach 100)
SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage,
  last_refresh_time,
  disable_reason
FROM `your_project_id.your_dataset_name.INFORMATION_SCHEMA.VECTOR_INDEXES`
WHERE table_name = 'product_embeddings';

-- Expected output when ready:
-- index_status: ACTIVE
-- coverage_percentage: 100.0

-- Note: Index creation can take several minutes for 40,000 products
-- Wait for coverage_percentage to reach 100 before using VECTOR_SEARCH
