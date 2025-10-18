import os
from typing import Optional
from google.cloud import bigquery
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
from config import get_settings


class GCPClient:
    """Handles all GCP service clients with proper authentication."""

    def __init__(self):
        self.settings = get_settings()
        self._bigquery_client: Optional[bigquery.Client] = None
        self._credentials = None
        self._initialize_credentials()
        self._initialize_vertex_ai()

    def _initialize_credentials(self):
        """Initialize GCP credentials from service account key."""
        credentials_path = self.settings.google_application_credentials

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Service account key not found at: {credentials_path}\n"
                f"Please create a service account key and update the path in .env"
            )

        self._credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/bigquery'
            ]
        )

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI for Gemini models."""
        vertexai.init(
            project=self.settings.gcp_project_id,
            location=self.settings.gcp_location,
            credentials=self._credentials
        )

    @property
    def bigquery(self) -> bigquery.Client:
        """Get or create BigQuery client."""
        if self._bigquery_client is None:
            self._bigquery_client = bigquery.Client(
                project=self.settings.gcp_project_id,
                credentials=self._credentials
            )
        return self._bigquery_client

    def get_gemini_model(self, model_name: Optional[str] = None) -> GenerativeModel:
        """Get a Gemini model instance."""
        model_name = model_name or self.settings.gemini_model
        return GenerativeModel(model_name)

    def get_gemini_image_model(self) -> GenerativeModel:
        """Get Gemini Flash 2.5 Image model for image generation/editing."""
        return GenerativeModel(self.settings.gemini_image_model)


# Singleton instance
_gcp_client: Optional[GCPClient] = None


def get_gcp_client() -> GCPClient:
    """Get or create GCP client singleton."""
    global _gcp_client
    if _gcp_client is None:
        _gcp_client = GCPClient()
    return _gcp_client
