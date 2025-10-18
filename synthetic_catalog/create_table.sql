-- Create flattened synthetic products table
-- Run with: bq query --use_legacy_sql=false < create_table.sql

CREATE TABLE IF NOT EXISTS `ml-developer-project-fe07.products.synthetic_products` (
  -- Identity
  product_id STRING NOT NULL,

  -- Image References
  image_filename STRING NOT NULL,
  gcs_uri STRING NOT NULL,

  -- Embedding (for vector search)
  embedding ARRAY<FLOAT64>,

  -- Core Product Info
  product_name STRING NOT NULL,
  brand_name STRING NOT NULL,
  category STRING NOT NULL,           -- e.g., "Dresses", "Tops", "Jeans"
  subcategory STRING,                 -- e.g., "Midi Dress", "Blouse", "Skinny Jeans"

  -- Attributes
  base_color STRING NOT NULL,
  secondary_color STRING,
  pattern STRING,                     -- e.g., "Solid", "Striped", "Floral"
  fabric STRING,                      -- e.g., "Cotton", "Polyester", "Silk Blend"
  fit STRING,                         -- e.g., "Regular", "Slim", "Oversized"
  sleeve_length STRING,               -- e.g., "Short", "Long", "Sleeveless"
  neck_style STRING,                  -- e.g., "Round", "V-Neck", "Turtleneck"

  -- Context
  season STRING NOT NULL,             -- e.g., "Spring", "Summer", "Fall", "Winter"
  occasion STRING,                    -- e.g., "Casual", "Formal", "Party", "Work"
  style STRING,                       -- e.g., "Modern", "Classic", "Bohemian"
  gender STRING NOT NULL,             -- Always "Women" for this catalog

  -- Pricing
  price_original FLOAT64 NOT NULL,
  price_discounted FLOAT64,

  -- Description
  description STRING,

  -- Metadata
  created_at TIMESTAMP NOT NULL
)
OPTIONS(
  description="Synthetic women's fashion catalog with H&M aesthetic - flattened schema for easy querying"
);
