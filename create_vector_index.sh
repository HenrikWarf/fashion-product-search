#!/bin/bash

# Athena Fashion Search - Create Vector Index Script
# This script creates a vector index on your BigQuery product_embeddings table

set -e  # Exit on error

PROJECT_ID="ml-developer-project-fe07"
DATASET="products"
TABLE="product_embeddings"

echo "=========================================="
echo "  Creating Vector Index"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET"
echo "Table:   $TABLE"
echo ""

# Step 1: Create the vector index
echo "[1/3] Creating vector index..."
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" "
CREATE OR REPLACE VECTOR INDEX product_embeddings_index
ON \`${PROJECT_ID}.${DATASET}.${TABLE}\`(embedding)
OPTIONS(
  distance_type = 'COSINE',
  index_type = 'IVF'
)
"

if [ $? -eq 0 ]; then
    echo "✓ Vector index creation started successfully"
else
    echo "✗ Error creating vector index"
    exit 1
fi

echo ""
echo "[2/3] Checking index status..."
echo "This may take 5-15 minutes for 40,000 products..."
echo ""

# Step 2: Monitor index creation
while true; do
    # Query and show results in a readable format
    OUTPUT=$(bq query --use_legacy_sql=false --project_id="$PROJECT_ID" --format=prettyjson "
    SELECT
      index_status,
      ROUND(coverage_percentage, 2) as coverage_pct,
      last_refresh_time
    FROM \`${PROJECT_ID}.${DATASET}.INFORMATION_SCHEMA.VECTOR_INDEXES\`
    WHERE table_name = '${TABLE}'
    LIMIT 1
    " 2>&1)

    # Check if query succeeded
    if echo "$OUTPUT" | grep -q "index_status"; then
        # Extract values using Python for reliable JSON parsing
        STATUS=$(echo "$OUTPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['index_status'] if data else '')" 2>/dev/null || echo "")
        COVERAGE=$(echo "$OUTPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['coverage_pct'] if data else '')" 2>/dev/null || echo "")

        if [ -n "$STATUS" ]; then
            echo "[$(date '+%H:%M:%S')] Status: $STATUS | Coverage: ${COVERAGE}%"

            # Check if index is complete
            if [ "$STATUS" = "ACTIVE" ] && [ -n "$COVERAGE" ]; then
                # Use awk to compare coverage
                IS_COMPLETE=$(echo "$COVERAGE" | awk '{if ($1 >= 100.0) print "yes"; else print "no"}')
                if [ "$IS_COMPLETE" = "yes" ]; then
                    echo ""
                    echo "✓ Index is ready!"
                    break
                fi
            fi
        else
            echo "[$(date '+%H:%M:%S')] Index not found yet, waiting..."
        fi
    else
        echo "[$(date '+%H:%M:%S')] Checking index status..."
    fi

    sleep 30
done

echo ""
echo "[3/3] Verifying index..."
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" "
SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage,
  last_refresh_time
FROM \`${PROJECT_ID}.${DATASET}.INFORMATION_SCHEMA.VECTOR_INDEXES\`
WHERE table_name = '${TABLE}'
"

echo ""
echo "=========================================="
echo "  Vector Index Created Successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add this to your .env file:"
echo "   USE_VECTOR_INDEX=true"
echo ""
echo "2. Restart your application:"
echo "   python main.py"
echo ""
echo "Your searches will now be 20-50x faster!"
echo "=========================================="
