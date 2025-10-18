"""
Main Catalog Creator - Orchestrates the entire synthetic catalog generation pipeline.

Pipeline:
1. Load product specifications (from JSON)
2. For each product:
   - Generate image with Imagen 4
   - Upload to GCS
   - Generate embedding
   - Insert into BigQuery
3. Create vector index
4. Generate summary report
"""

import json
import os
import sys
import time
import uuid
import argparse
from typing import List, Dict, Any
from datetime import datetime
from google.cloud import bigquery

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from synthetic_catalog.image_generator import ImageGenerator


class CatalogCreator:
    """Orchestrate synthetic catalog creation."""

    def __init__(
        self,
        gcs_bucket: str = "assortment_automation",
        gcs_prefix: str = "synthetic_catalog/images",
        bq_dataset: str = "products",
        bq_table: str = "synthetic_products"
    ):
        self.settings = get_settings()
        self.image_generator = ImageGenerator(gcs_bucket, gcs_prefix)

        # BigQuery setup
        self.bq_client = bigquery.Client(project=self.settings.gcp_project_id)
        self.bq_dataset = bq_dataset
        self.bq_table = bq_table
        self.table_ref = f"{self.settings.gcp_project_id}.{bq_dataset}.{bq_table}"

        # Logging
        self.log_file = os.path.join(os.path.dirname(__file__), "output/generation_log.jsonl")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        self.success_count = 0
        self.failure_count = 0
        self.start_time = None

    def create_catalog(self, product_specs: List[Dict[str, Any]], resume_from: int = 0):
        """
        Create complete synthetic catalog.

        Args:
            product_specs: List of product specifications
            resume_from: Index to resume from (for retries)
        """
        self.start_time = datetime.now()
        total = len(product_specs)

        print(f"\n{'='*80}")
        print(f"SYNTHETIC CATALOG CREATION")
        print(f"{'='*80}")
        print(f"Total products: {total}")
        print(f"BigQuery table: {self.table_ref}")
        print(f"Starting from index: {resume_from}")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        for i, spec in enumerate(product_specs[resume_from:], start=resume_from):
            try:
                print(f"\n[{i+1}/{total}] Processing: {spec['product_name']}")
                print(f"  Category: {spec['category']} | Color: {spec['base_color']} | Price: ${spec['price_original']}")

                # Generate unique product ID
                product_id = f"SYN-{uuid.uuid4().hex[:8].upper()}"
                print(f"  Product ID: {product_id}")

                # Step 1: Generate image
                image_result = self.image_generator.generate_product_image(spec, product_id)
                if not image_result:
                    raise Exception("Image generation failed")

                # Step 2: Generate embedding
                print(f"  [Embedding] Generating multimodal embedding...")
                embedding = self.image_generator.generate_embedding(image_result['gcs_uri'])
                print(f"  ✓ Embedding generated ({len(embedding)} dimensions)")

                # Step 3: Insert into BigQuery
                print(f"  [BigQuery] Inserting into {self.bq_table}...")
                self._insert_into_bigquery(
                    product_id=product_id,
                    image_filename=image_result['image_filename'],
                    gcs_uri=image_result['gcs_uri'],
                    embedding=embedding,
                    spec=spec
                )
                print(f"  ✓ Inserted into BigQuery")

                # Log success
                self._log_success(i, product_id, spec, image_result)
                self.success_count += 1

                print(f"  ✅ SUCCESS ({self.success_count}/{i+1})")

                # Rate limiting (avoid hitting quotas)
                time.sleep(2)

            except Exception as e:
                print(f"  ❌ FAILED: {e}")
                self._log_failure(i, spec, str(e))
                self.failure_count += 1

                # Continue to next product
                continue

        # Generate summary report
        self._generate_report(total)

    def _insert_into_bigquery(
        self,
        product_id: str,
        image_filename: str,
        gcs_uri: str,
        embedding: List[float],
        spec: Dict[str, Any]
    ):
        """Insert product into BigQuery table."""

        row = {
            "product_id": product_id,
            "image_filename": image_filename,
            "gcs_uri": gcs_uri,
            "embedding": embedding,
            "product_name": spec["product_name"],
            "brand_name": spec["brand_name"],
            "category": spec["category"],
            "subcategory": spec.get("subcategory"),
            "base_color": spec["base_color"],
            "secondary_color": spec.get("secondary_color"),
            "pattern": spec.get("pattern"),
            "fabric": spec.get("fabric"),
            "fit": spec.get("fit"),
            "sleeve_length": spec.get("sleeve_length"),
            "neck_style": spec.get("neck_style"),
            "season": spec["season"],
            "occasion": spec.get("occasion"),
            "style": spec.get("style"),
            "gender": spec["gender"],
            "price_original": spec["price_original"],
            "price_discounted": spec.get("price_discounted"),
            "description": spec.get("description"),
            "created_at": datetime.utcnow().isoformat()
        }

        # Insert
        errors = self.bq_client.insert_rows_json(self.table_ref, [row])

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def _log_success(self, index: int, product_id: str, spec: Dict[str, Any], image_result: Dict[str, Any]):
        """Log successful product creation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "index": index,
            "status": "success",
            "product_id": product_id,
            "product_name": spec["product_name"],
            "category": spec["category"],
            "gcs_uri": image_result["gcs_uri"]
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _log_failure(self, index: int, spec: Dict[str, Any], error: str):
        """Log failed product creation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "index": index,
            "status": "failure",
            "product_name": spec.get("product_name", "Unknown"),
            "category": spec.get("category", "Unknown"),
            "error": error
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _generate_report(self, total: int):
        """Generate summary report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
{'='*80}
SYNTHETIC CATALOG CREATION - SUMMARY REPORT
{'='*80}

Execution Time:
  Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
  Duration: {duration}

Results:
  Total Products:    {total}
  Successful:        {self.success_count} ({self.success_count/total*100:.1f}%)
  Failed:            {self.failure_count} ({self.failure_count/total*100:.1f}%)

BigQuery Table: {self.table_ref}
Log File: {self.log_file}

Next Steps:
  1. Create vector index:
     python synthetic_catalog/create_vector_index.py

  2. Update application config to use new table:
     Update config.py: BIGQUERY_TABLE = "synthetic_products"

  3. Restart application and test searches

{'='*80}
"""

        print(report)

        # Save report
        report_path = os.path.join(os.path.dirname(__file__), "output/summary_report.txt")
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"✓ Report saved to: {report_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Create synthetic product catalog")
    parser.add_argument("--specs", type=str, required=True, help="Path to product specifications JSON")
    parser.add_argument("--gcs-bucket", type=str, default="assortment_automation", help="GCS bucket name")
    parser.add_argument("--gcs-prefix", type=str, default="synthetic_catalog/images", help="GCS path prefix")
    parser.add_argument("--bq-dataset", type=str, default="products", help="BigQuery dataset")
    parser.add_argument("--bq-table", type=str, default="synthetic_products", help="BigQuery table")
    parser.add_argument("--resume-from", type=int, default=0, help="Resume from index (for retries)")

    args = parser.parse_args()

    # Load product specifications
    with open(args.specs, 'r') as f:
        product_specs = json.load(f)

    print(f"✓ Loaded {len(product_specs)} product specifications from: {args.specs}")

    # Create catalog
    creator = CatalogCreator(
        gcs_bucket=args.gcs_bucket,
        gcs_prefix=args.gcs_prefix,
        bq_dataset=args.bq_dataset,
        bq_table=args.bq_table
    )

    creator.create_catalog(product_specs, resume_from=args.resume_from)


if __name__ == "__main__":
    main()
