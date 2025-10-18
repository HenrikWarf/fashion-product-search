#!/bin/bash

# Quick script to check vector index status

PROJECT_ID="ml-developer-project-fe07"
DATASET="products"
TABLE="product_embeddings"

echo "Checking vector index status..."
echo ""

bq query --use_legacy_sql=false --project_id="$PROJECT_ID" "
SELECT
  table_name,
  index_name,
  index_status,
  ROUND(coverage_percentage, 2) as coverage_pct,
  last_refresh_time,
  disable_reason
FROM \`${PROJECT_ID}.${DATASET}.INFORMATION_SCHEMA.VECTOR_INDEXES\`
WHERE table_name = '${TABLE}'
"
