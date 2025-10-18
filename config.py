from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # GCP Configuration
    gcp_project_id: str
    gcp_location: str = "us-central1"
    google_application_credentials: str

    # BigQuery Configuration
    bigquery_dataset: str
    bigquery_table: str = "synthetic_products"

    # Gemini Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_image_model: str = "gemini-2.5-flash-preview-0205"

    # Server Configuration
    port: int = 8000

    # Vector Search Configuration
    use_vector_index: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
