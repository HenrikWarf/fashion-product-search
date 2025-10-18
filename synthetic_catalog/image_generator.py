"""
Image Generator using Imagen 4 (Vertex AI).
Generates high-quality e-commerce product photography.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from google.cloud import storage
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings


class ImageGenerator:
    """Generate product images using Imagen 4."""

    def __init__(self, gcs_bucket: str = "assortment_automation", gcs_prefix: str = "synthetic_catalog/images"):
        self.settings = get_settings()
        self.gcs_bucket = gcs_bucket
        self.gcs_prefix = gcs_prefix

        # Initialize Vertex AI
        vertexai.init(
            project=self.settings.gcp_project_id,
            location=self.settings.gcp_location
        )

        # Initialize GCS client
        self.storage_client = storage.Client(project=self.settings.gcp_project_id)
        self.bucket = self.storage_client.bucket(self.gcs_bucket)

    def generate_product_image(
        self,
        product_spec: Dict[str, Any],
        product_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a product image using Imagen 4.

        Args:
            product_spec: Product specification dictionary
            product_id: Unique product ID

        Returns:
            Dictionary with gcs_uri, local_path, and image_filename
        """
        try:
            # Build Imagen 4 prompt
            prompt = self._build_imagen_prompt(product_spec)

            print(f"  [Image] Generating image for: {product_spec['product_name']}")
            print(f"    Prompt: {prompt[:100]}...")

            # Generate image with Imagen 4
            image_bytes = self._generate_with_imagen4(prompt)

            if not image_bytes:
                print(f"  ✗ Failed to generate image")
                return None

            print(f"  ✓ Image generated ({len(image_bytes)} bytes)")

            # Create filename
            image_filename = f"{product_id}.jpg"

            # Save locally (temp)
            local_dir = os.path.join(os.path.dirname(__file__), "output/images")
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, image_filename)

            with open(local_path, 'wb') as f:
                f.write(image_bytes)

            print(f"  ✓ Saved locally: {local_path}")

            # Upload to GCS
            gcs_uri = self._upload_to_gcs(image_bytes, image_filename)

            print(f"  ✓ Uploaded to GCS: {gcs_uri}")

            return {
                "gcs_uri": gcs_uri,
                "local_path": local_path,
                "image_filename": image_filename
            }

        except Exception as e:
            print(f"  ✗ Error generating image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _build_imagen_prompt(self, spec: Dict[str, Any]) -> str:
        """
        Build Imagen 4 prompt for product photography.

        Args:
            spec: Product specification

        Returns:
            Imagen 4 prompt string
        """
        product_name = spec['product_name']
        category = spec['category']
        subcategory = spec.get('subcategory', category)
        base_color = spec['base_color']
        secondary_color = spec.get('secondary_color')
        fabric = spec.get('fabric', 'fabric')
        pattern = spec.get('pattern', 'solid')
        fit = spec.get('fit', 'regular fit')
        style = spec.get('style', 'modern')

        # Build color description
        color_desc = base_color.lower()
        if secondary_color:
            color_desc = f"{base_color.lower()} with {secondary_color.lower()} accents"

        # Build detailed prompt
        prompt = f"""Professional e-commerce product photography of a {product_name.lower()}.

Product Details:
- Type: {category} - {subcategory}
- Color: {color_desc}
- Fabric: {fabric.lower()}
- Pattern: {pattern.lower()}
- Fit: {fit.lower()}
- Style: {style.lower()}

Photography Specifications:
- Female model wearing the garment
- Front-facing view, full body or 3/4 length depending on garment
- Clean minimalist background (white or soft grey)
- Professional studio lighting with soft, even illumination
- Sharp focus on garment details and texture
- Modern catalog/e-commerce quality
- Scandinavian minimalist aesthetic
- Contemporary fast-fashion photography style (H&M, Zara aesthetic)
- Natural, relaxed model pose
- Realistic, wearable, commercially viable design

The garment should look modern, stylish, and ready to purchase. Emphasize fabric texture, drape, and fit. Professional fashion catalog quality."""

        return prompt

    def _generate_with_imagen4(self, prompt: str) -> Optional[bytes]:
        """
        Generate image using Imagen 4 via Vertex AI.

        Args:
            prompt: Image generation prompt

        Returns:
            Image bytes or None if failed
        """
        try:
            # Initialize Imagen 4 model
            model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

            # Generate images
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                language="en",
                aspect_ratio="9:16",  # Portrait for fashion
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )

            if response and hasattr(response, 'images') and response.images:
                # Get first image
                image = response.images[0]
                # Convert to bytes
                return image._image_bytes

            return None

        except Exception as e:
            print(f"    Error calling Imagen 4: {e}")
            return None

    def _upload_to_gcs(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload image to Google Cloud Storage.

        Args:
            image_bytes: Image data
            filename: Target filename

        Returns:
            GCS URI (gs://bucket/path)
        """
        blob_path = f"{self.gcs_prefix}/{filename}"
        blob = self.bucket.blob(blob_path)

        # Upload with content type
        blob.upload_from_string(image_bytes, content_type='image/jpeg')

        # Return GCS URI
        return f"gs://{self.gcs_bucket}/{blob_path}"

    def generate_embedding(self, gcs_uri: str) -> List[float]:
        """
        Generate multimodal embedding for an image.

        Args:
            gcs_uri: GCS URI of the image

        Returns:
            1408-dimensional embedding vector
        """
        try:
            from vertexai.vision_models import MultiModalEmbeddingModel, Image

            # Load image from GCS
            image = Image.load_from_file(gcs_uri)

            # Generate embedding
            model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            embeddings = model.get_embeddings(
                image=image,
                dimension=1408
            )

            if embeddings and embeddings.image_embedding:
                return embeddings.image_embedding

            # Fallback
            print(f"  ⚠ Warning: No embedding generated, using zero vector")
            return [0.0] * 1408

        except Exception as e:
            print(f"  ✗ Error generating embedding: {e}")
            return [0.0] * 1408
