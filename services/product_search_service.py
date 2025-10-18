from typing import List, Dict, Any, Optional
from services.gcp_client import get_gcp_client
from config import get_settings
import re


class ProductSearchService:
    """Service for searching products using BigQuery vector search."""

    def __init__(self):
        self.gcp_client = get_gcp_client()
        self.settings = get_settings()

    def _convert_gcs_uri_to_url(self, gcs_uri: str) -> str:
        """
        Convert GCS URI (gs://bucket/path) to public HTTPS URL.

        Args:
            gcs_uri: GCS URI like gs://bucket-name/path/to/file.jpg

        Returns:
            Public HTTPS URL like https://storage.googleapis.com/bucket-name/path/to/file.jpg
        """
        if not gcs_uri or not gcs_uri.startswith('gs://'):
            return gcs_uri

        # Convert gs://bucket/path to https://storage.googleapis.com/bucket/path
        gcs_uri_without_prefix = gcs_uri.replace('gs://', '')
        return f"https://storage.googleapis.com/{gcs_uri_without_prefix}"

    async def search_products_by_text(
        self,
        query: str,
        parsed_attributes: Dict[str, Any],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search products using text query and parsed attributes.

        Args:
            query: Original search query
            parsed_attributes: Parsed attributes from NLU service
            limit: Maximum number of results to return

        Returns:
            List of matching products with similarity scores
        """

        try:
            # Generate embedding for the query using multimodal embedding model
            query_embedding = await self._generate_text_embedding(query)

            # Build SQL query for BigQuery vector search
            sql_query = self._build_vector_search_query(
                query_embedding,
                parsed_attributes,
                limit
            )

            # Execute query
            query_job = self.gcp_client.bigquery.query(sql_query)
            results = query_job.result()

            # Format results
            products = []
            for row in results:
                # Extract metadata from JSON column
                metadata = row.get("metadata", {})
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)

                product = {
                    "id": row.get("product_id"),
                    "name": metadata.get("productDisplayName", "Unknown Product"),
                    "description": metadata.get("productDescriptors", {}).get("description", {}).get("value", ""),
                    "price": metadata.get("price", {}).get("mrp", 0),
                    "image_url": row.get("gcs_uri", ""),
                    "color": metadata.get("baseColour", ""),
                    "category": metadata.get("articleType", {}).get("typeName", ""),
                    "brand": metadata.get("brandName", ""),
                    "season": metadata.get("season", ""),
                    "gender": metadata.get("gender", ""),
                    "similarity_score": float(row.get("similarity_score", 0))
                }
                products.append(product)

            return products

        except Exception as e:
            print(f"Error searching products: {e}")
            return []

    async def search_products_by_image(
        self,
        image_url: str,
        parsed_attributes: Dict[str, Any],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search products using the generated concept image and multimodal embedding.

        Args:
            image_url: URL/path to the generated concept image
            parsed_attributes: Parsed attributes from NLU service
            limit: Maximum number of results to return

        Returns:
            List of matching products with similarity scores
        """

        try:
            print(f"\n{'='*60}")
            print(f"PRODUCT SEARCH - Starting search")
            print(f"{'='*60}")
            print(f"Image URL: {image_url}")
            print(f"Parsed Attributes: {parsed_attributes}")
            print(f"Limit: {limit}")

            # Generate embedding from the actual image
            print(f"\n[1/4] Generating embedding from concept image...")
            query_embedding = await self._generate_image_embedding(image_url)
            print(f"✓ Generated embedding with {len(query_embedding)} dimensions")
            print(f"  First 5 values: {query_embedding[:5]}")
            print(f"  Embedding magnitude: {sum(x*x for x in query_embedding)**0.5:.4f}")

            # Build SQL query
            print(f"\n[2/4] Building SQL query...")
            sql_query = self._build_vector_search_query(
                query_embedding,
                parsed_attributes,
                limit
            )
            print(f"✓ SQL Query built")
            print(f"  Using vector index: {self.settings.use_vector_index}")
            print(f"\n--- SQL Query ---")
            print(sql_query)
            print(f"--- End SQL Query ---\n")

            # Execute query
            print(f"[3/4] Executing BigQuery search...")
            query_job = self.gcp_client.bigquery.query(sql_query)
            results = query_job.result()
            print(f"✓ Query executed successfully")

            # Format results
            print(f"\n[4/4] Processing results...")
            products = []
            row_count = 0
            for row in results:
                row_count += 1

                # Get GCS URI and convert to public URL
                gcs_uri = row.get("gcs_uri", "")
                image_url = self._convert_gcs_uri_to_url(gcs_uri)

                # Get price (use discounted if available, otherwise original)
                price_discounted = row.get("price_discounted")
                price_original = row.get("price_original", 0)
                price = price_discounted if price_discounted else price_original

                # Calculate similarity score from distance (lower distance = higher similarity)
                distance = float(row.get("distance", 1.0))
                # Convert cosine distance to similarity (0-1 range, where 1 is perfect match)
                similarity_score = max(0.0, 1.0 - distance)

                # Map all fields from the synthetic_products table
                product = {
                    "id": row.get("product_id", ""),
                    "name": row.get("product_name", "Product"),
                    "description": row.get("description", ""),
                    "price": float(price) if price else 0.0,
                    "price_original": float(price_original) if price_original else 0.0,
                    "price_discounted": float(price_discounted) if price_discounted else None,
                    "image_url": image_url,
                    "color": row.get("base_color", ""),
                    "secondary_color": row.get("secondary_color"),
                    "category": row.get("category", ""),
                    "subcategory": row.get("subcategory"),
                    "brand": row.get("brand_name", ""),
                    "pattern": row.get("pattern"),
                    "fabric": row.get("fabric"),
                    "fit": row.get("fit"),
                    "sleeve_length": row.get("sleeve_length"),
                    "neck_style": row.get("neck_style"),
                    "season": row.get("season", ""),
                    "occasion": row.get("occasion"),
                    "style": row.get("style"),
                    "gender": "Women",
                    "similarity_score": similarity_score
                }
                products.append(product)

                if row_count <= 3:
                    print(f"\n  Product {row_count}:")
                    print(f"    ID: {product['id']}")
                    print(f"    Name: {product['name']}")
                    print(f"    Price: ${product['price']}")
                    print(f"    Color: {product['color']}")
                    print(f"    Fabric: {product['fabric']}")
                    print(f"    Fit: {product['fit']}")
                    print(f"    Pattern: {product['pattern']}")
                    print(f"    GCS URI: {gcs_uri}")
                    print(f"    Image URL: {image_url}")
                    print(f"    Distance: {distance:.4f} -> Similarity: {similarity_score:.2%}")

            print(f"\n✓ Found {len(products)} matching products")
            print(f"{'='*60}\n")
            return products

        except Exception as e:
            print(f"\n✗ Error searching products by image: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return []

    async def search_products_multi_category(
        self,
        image_url: str,
        parsed_attributes: Dict[str, Any],
        limit_per_category: int = 5
    ) -> Dict[str, Any]:
        """
        Search products across multiple categories using garment region analysis.

        Args:
            image_url: URL/path to the generated concept image
            parsed_attributes: Parsed attributes from NLU service
            limit_per_category: Maximum number of results per category

        Returns:
            Dictionary containing:
            - products_by_category: Dict[category -> List[products]]
            - all_products: Flat list of all products (for backward compatibility)
            - search_mode: "multi_category" or "single"
        """

        try:
            print(f"\n{'='*80}")
            print(f"MULTI-CATEGORY PRODUCT SEARCH")
            print(f"{'='*80}")
            print(f"Image URL: {image_url}")
            print(f"Limit per category: {limit_per_category}")

            # Step 1: Analyze garment regions using Gemini vision
            from services.nlu_service import NLUService
            nlu_service = NLUService()

            print(f"\n[1/4] Analyzing garment regions...")
            garments = await nlu_service.analyze_garment_regions(image_url)

            if not garments or len(garments) == 0:
                print(f"[!] No garments detected, falling back to single-embedding search")
                # Fallback to single embedding search
                products = await self.search_products_by_image(
                    image_url,
                    parsed_attributes,
                    limit=limit_per_category * 2
                )
                return {
                    "products_by_category": {},
                    "all_products": products,
                    "search_mode": "single"
                }

            print(f"[✓] Detected {len(garments)} garment(s)")

            # Step 2: Generate a single image embedding from the concept image
            # Use the SAME image embedding for all categories to match product embeddings
            print(f"\n[2/4] Generating image embedding from concept image...")
            print(f"  [!] Using IMAGE embedding (not text) to match product database embedding space")
            query_embedding = await self._generate_image_embedding(image_url)
            print(f"  [✓] Image embedding generated (magnitude: {sum(x*x for x in query_embedding)**0.5:.4f})")

            # Create garment data with the shared image embedding
            garment_embeddings = []
            for garment in garments:
                garment_embeddings.append({
                    "category": garment['category'],
                    "subcategory": garment['subcategory'],
                    "description": garment['description'],
                    "embedding": query_embedding  # Same image embedding for all categories
                })
            print(f"  [✓] Using shared image embedding for {len(garment_embeddings)} categories")

            # Step 3: Search products for each category
            print(f"\n[3/4] Searching products for each category...")
            products_by_category = {}
            all_products = []

            for i, garment_data in enumerate(garment_embeddings, 1):
                category = garment_data['category']
                embedding = garment_data['embedding']

                print(f"  [{i}/{len(garment_embeddings)}] Searching for {category}...")

                # Build category-specific query
                sql_query = self._build_category_specific_query(
                    embedding,
                    category,
                    garment_data['subcategory'],
                    limit_per_category
                )

                print(f"\n--- SQL Query for {category} ---")
                print(sql_query)
                print(f"--- End SQL Query ---\n")

                # Execute query
                query_job = self.gcp_client.bigquery.query(sql_query)
                results = query_job.result()

                # Format results
                category_products = []
                for row in results:
                    gcs_uri = row.get("gcs_uri", "")
                    image_url_converted = self._convert_gcs_uri_to_url(gcs_uri)

                    price_discounted = row.get("price_discounted")
                    price_original = row.get("price_original", 0)
                    price = price_discounted if price_discounted else price_original

                    distance = float(row.get("distance", 1.0))
                    similarity_score = max(0.0, 1.0 - distance)

                    product = {
                        "id": row.get("product_id", ""),
                        "name": row.get("product_name", "Product"),
                        "description": row.get("description", ""),
                        "price": float(price) if price else 0.0,
                        "price_original": float(price_original) if price_original else 0.0,
                        "price_discounted": float(price_discounted) if price_discounted else None,
                        "image_url": image_url_converted,
                        "color": row.get("base_color", ""),
                        "secondary_color": row.get("secondary_color"),
                        "category": row.get("category", ""),
                        "subcategory": row.get("subcategory"),
                        "brand": row.get("brand_name", ""),
                        "pattern": row.get("pattern"),
                        "fabric": row.get("fabric"),
                        "fit": row.get("fit"),
                        "sleeve_length": row.get("sleeve_length"),
                        "neck_style": row.get("neck_style"),
                        "season": row.get("season", ""),
                        "occasion": row.get("occasion"),
                        "style": row.get("style"),
                        "gender": "Women",
                        "similarity_score": similarity_score,
                        "matched_category": category  # Add category label
                    }
                    category_products.append(product)
                    all_products.append(product)

                products_by_category[category] = category_products
                print(f"  [✓] Found {len(category_products)} products for {category}")

            print(f"\n[4/4] Total products found: {len(all_products)}")
            print(f"{'='*80}\n")

            return {
                "products_by_category": products_by_category,
                "all_products": all_products,
                "search_mode": "multi_category"
            }

        except Exception as e:
            print(f"\n[✗] Error in multi-category search: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to single-embedding search
            print(f"[!] Falling back to single-embedding search")
            products = await self.search_products_by_image(
                image_url,
                parsed_attributes,
                limit=limit_per_category * 2
            )
            return {
                "products_by_category": {},
                "all_products": products,
                "search_mode": "single"
            }

    def _build_category_specific_query(
        self,
        query_embedding: List[float],
        category: str,
        subcategory: str,
        limit: int
    ) -> str:
        """
        Build BigQuery query for category-specific search.

        Args:
            query_embedding: Embedding vector for the garment
            category: Main category (Tops, Bottoms, etc.)
            subcategory: Specific garment type
            limit: Max results

        Returns:
            SQL query string
        """
        dataset = self.settings.bigquery_dataset
        table = self.settings.bigquery_table

        # Convert embedding to string for SQL
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Build category filter in the subquery BEFORE vector search
        category_filter = f"LOWER(category) = '{category.lower()}'"

        # Filter the table first, then do vector search on filtered results
        # VECTOR_SEARCH creates an implicit 'base' table reference
        query = f"""
        SELECT
            base.product_id,
            base.product_name,
            base.brand_name,
            base.category,
            base.subcategory,
            base.base_color,
            base.secondary_color,
            base.pattern,
            base.fabric,
            base.fit,
            base.sleeve_length,
            base.neck_style,
            base.season,
            base.occasion,
            base.style,
            base.price_original,
            base.price_discounted,
            base.description,
            base.gcs_uri,
            distance
        FROM VECTOR_SEARCH(
            (SELECT * FROM `{dataset}.{table}` WHERE {category_filter}),
            'embedding',
            (SELECT {embedding_str} AS embedding),
            top_k => {limit},
            distance_type => 'COSINE'
        )
        """

        return query

    async def _generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Google's multimodal embedding model.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector (1408-dimensional to match product_embeddings table)
        """

        try:
            from vertexai.vision_models import MultiModalEmbeddingModel

            model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            embeddings = model.get_embeddings(
                contextual_text=text,
                dimension=1408
            )

            if embeddings and embeddings.text_embedding:
                return embeddings.text_embedding

            # Fallback: return zero vector if embedding fails
            return [0.0] * 1408

        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback (1408 dimensions)
            return [0.0] * 1408

    async def _generate_image_embedding(self, image_url: str) -> List[float]:
        """
        Generate embedding for an image using Google's multimodal embedding model.

        Args:
            image_url: Path to the image file (e.g., /images/concept_123.png)

        Returns:
            Embedding vector (1408-dimensional to match product_embeddings table)

        Raises:
            ValueError: If image file not found or embedding generation fails
        """

        try:
            from vertexai.vision_models import MultiModalEmbeddingModel, Image
            import os

            print(f"  [Embedding] Processing image URL: {image_url}")

            # Convert URL path to local file path
            if image_url.startswith('/images/'):
                filename = image_url.replace('/images/', '')
                filepath = os.path.join('generated_images', filename)
            else:
                filepath = image_url

            print(f"  [Embedding] Resolved file path: {filepath}")
            print(f"  [Embedding] File exists: {os.path.exists(filepath)}")

            if not os.path.exists(filepath):
                error_msg = f"Image file not found at {filepath}. Cannot generate embedding."
                print(f"  [Embedding] ERROR: {error_msg}")
                raise ValueError(error_msg)

            # Load image
            print(f"  [Embedding] Loading image from file...")
            image = Image.load_from_file(filepath)
            print(f"  [Embedding] Image loaded successfully")

            # Generate embedding using the image
            print(f"  [Embedding] Generating multimodal embedding...")
            model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            embeddings = model.get_embeddings(
                image=image,
                dimension=1408
            )

            if embeddings and embeddings.image_embedding:
                embedding_magnitude = sum(x*x for x in embeddings.image_embedding)**0.5
                print(f"  [Embedding] ✓ Embedding generated successfully")
                print(f"  [Embedding] Magnitude: {embedding_magnitude:.4f}")

                # Verify it's not a zero vector
                if embedding_magnitude < 0.0001:
                    raise ValueError("Generated embedding is a zero vector")

                return embeddings.image_embedding

            # If no embedding returned, raise error
            raise ValueError("Embedding model returned no image_embedding")

        except Exception as e:
            print(f"  [Embedding] ✗ Error generating image embedding: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise the error instead of returning zero vector
            raise ValueError(f"Failed to generate image embedding: {str(e)}")

    def _build_vector_search_query(
        self,
        query_embedding: List[float],
        parsed_attributes: Dict[str, Any],
        limit: int
    ) -> str:
        """
        Build BigQuery SQL query for vector similarity search with attribute filtering.
        Works with product_embeddings table schema.

        Uses VECTOR_SEARCH if use_vector_index is enabled, otherwise uses manual cosine similarity.

        Args:
            query_embedding: Query embedding vector (1408-dimensional)
            parsed_attributes: Parsed attributes for filtering
            limit: Maximum number of results

        Returns:
            SQL query string
        """

        dataset = self.settings.bigquery_dataset
        table = self.settings.bigquery_table

        # Convert embedding to string for SQL
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Check if vector index should be used
        use_index = self.settings.use_vector_index

        if use_index:
            return self._build_vector_index_query(
                embedding_str,
                parsed_attributes,
                limit,
                dataset,
                table
            )
        else:
            return self._build_manual_similarity_query(
                embedding_str,
                parsed_attributes,
                limit,
                dataset,
                table
            )

    def _build_vector_index_query(
        self,
        embedding_str: str,
        parsed_attributes: Dict[str, Any],
        limit: int,
        dataset: str,
        table: str
    ) -> str:
        """Build query using VECTOR_SEARCH with index."""

        # Correct VECTOR_SEARCH syntax - fetch all needed columns
        query = f"""
        SELECT
            base.product_id,
            base.product_name,
            base.brand_name,
            base.category,
            base.subcategory,
            base.base_color,
            base.secondary_color,
            base.pattern,
            base.fabric,
            base.fit,
            base.sleeve_length,
            base.neck_style,
            base.season,
            base.occasion,
            base.style,
            base.price_original,
            base.price_discounted,
            base.description,
            base.gcs_uri,
            distance
        FROM VECTOR_SEARCH(
            (SELECT * FROM `{dataset}.{table}`),
            'embedding',
            (SELECT {embedding_str} AS embedding),
            top_k => {limit},
            distance_type => 'COSINE'
        )
        """

        return query

    def _build_manual_similarity_query(
        self,
        embedding_str: str,
        parsed_attributes: Dict[str, Any],
        limit: int,
        dataset: str,
        table: str
    ) -> str:
        """Build query using manual cosine similarity calculation."""

        where_clauses = self._build_where_clauses(parsed_attributes)
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)

        # Build full query with manual cosine similarity
        query = f"""
        WITH query_embedding AS (
            SELECT {embedding_str} AS embedding
        )
        SELECT
            p.product_id,
            p.gcs_uri,
            p.metadata,
            -- Calculate cosine similarity
            (
                SELECT SUM(a * b) / (
                    SQRT(SUM(a * a)) * SQRT(SUM(b * b))
                )
                FROM UNNEST(p.embedding) AS a WITH OFFSET pos1
                JOIN UNNEST(q.embedding) AS b WITH OFFSET pos2
                ON pos1 = pos2
            ) AS similarity_score
        FROM
            `{dataset}.{table}` AS p,
            query_embedding q
        {where_clause}
        ORDER BY
            similarity_score DESC
        LIMIT {limit}
        """

        return query

    def _build_where_clauses(self, parsed_attributes: Dict[str, Any]) -> List[str]:
        """Build WHERE clause conditions from parsed attributes."""
        where_clauses = []

        explicit_attrs = parsed_attributes.get("explicit_attributes", {})

        # Price filter (from metadata.price.mrp)
        if explicit_attrs.get("price_max"):
            where_clauses.append(f"CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) <= {explicit_attrs['price_max']}")
        if explicit_attrs.get("price_min"):
            where_clauses.append(f"CAST(JSON_VALUE(metadata, '$.price.mrp') AS FLOAT64) >= {explicit_attrs['price_min']}")

        # Color filter (from metadata.baseColour)
        if explicit_attrs.get("colors"):
            colors = explicit_attrs["colors"]
            color_conditions = " OR ".join([
                f"LOWER(JSON_VALUE(metadata, '$.baseColour')) LIKE '%{c.lower()}%'"
                for c in colors
            ])
            where_clauses.append(f"({color_conditions})")

        # Category/Garment type filter (from metadata.articleType.typeName)
        inferred = parsed_attributes.get("inferred_needs", {})
        if inferred.get("garment_types"):
            garment_types = inferred["garment_types"]
            type_conditions = " OR ".join([
                f"LOWER(JSON_VALUE(metadata, '$.articleType.typeName')) LIKE '%{t.lower()}%'"
                for t in garment_types
            ])
            where_clauses.append(f"({type_conditions})")

        # Gender filter if specified
        if explicit_attrs.get("gender"):
            where_clauses.append(f"LOWER(JSON_VALUE(metadata, '$.gender')) = '{explicit_attrs['gender'].lower()}'")

        # Season filter if specified
        if explicit_attrs.get("season"):
            where_clauses.append(f"LOWER(JSON_VALUE(metadata, '$.season')) LIKE '%{explicit_attrs['season'].lower()}%'")

        return where_clauses

    def generate_match_description(
        self,
        products: List[Dict[str, Any]],
        parsed_attributes: Dict[str, Any]
    ) -> str:
        """Generate a natural language description of the product matches."""

        if not products:
            return "No matching products found. Please try refining your search criteria."

        count = len(products)
        avg_similarity = sum(p.get("similarity_score", 0) for p in products) / count if count > 0 else 0

        description_parts = [
            f"Found {count} products that match your refined style concept"
        ]

        explicit = parsed_attributes.get("explicit_attributes", {})
        if explicit.get("price_max"):
            description_parts.append(f"within your budget of ${explicit['price_max']}")

        if avg_similarity > 0.8:
            description_parts.append("with excellent similarity to your vision")
        elif avg_similarity > 0.6:
            description_parts.append("with good matches to your preferences")

        return ". ".join(description_parts) + "."
