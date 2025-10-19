# GEMINI.md

## Project Overview

This project, "Athena," is an AI-powered fashion search application. It leverages Google's Gemini AI to provide an intelligent and interactive shopping experience. Users can describe their desired fashion items in natural language, and the application will generate a visual concept, allow for interactive refinement, and then find matching products from a catalog.

The application is built with a Python FastAPI backend and a simple HTML/CSS/JavaScript frontend. It is tightly integrated with Google Cloud Platform services, particularly Vertex AI for the AI-powered features and BigQuery for the product catalog and vector search.

**Key Technologies:**

*   **Backend:** Python, FastAPI
*   **Frontend:** HTML, CSS, JavaScript
*   **AI:** Google Gemini (for NLU and image generation)
*   **Database:** Google BigQuery (with vector search)
*   **Cloud:** Google Cloud Platform (GCP)

## Building and Running

### 1. Prerequisites

*   Python 3.9+
*   A Google Cloud Platform (GCP) project with the following APIs enabled:
    *   Vertex AI API
    *   BigQuery API
*   A GCP Service Account with the following roles:
    *   `roles/aiplatform.user`
    *   `roles/bigquery.dataViewer`
    *   `roles/bigquery.jobUser`
*   A BigQuery dataset with a `product_embeddings` table containing product data and 1408-dimensional multimodal embeddings.

### 2. Installation

```bash
pip install -r requirements.txt
```

### 3. Configuration

1.  Create a `.env` file in the root of the project. You can copy the structure from a `.env.example` if one exists.
2.  Add the following environment variables to your `.env` file:

    ```env
    # GCP Configuration
    GCP_PROJECT_ID=your-gcp-project-id
    GCP_LOCATION=us-central1
    GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json

    # BigQuery Configuration
    BIGQUERY_DATASET=your_dataset_name
    BIGQUERY_TABLE=product_embeddings

    # Gemini Configuration
    GEMINI_MODEL=gemini-2.0-flash-exp
    GEMINI_IMAGE_MODEL=gemini-2.5-flash-preview-0205

    # Server Configuration
    PORT=8000
    ```

### 4. Running the Application

You can run the application using either of the following commands:

```bash
python main.py
```

or

```bash
./start.sh
```

The application will be available at `http://localhost:8000`.

## Development Conventions

*   **Modular Architecture:** The backend is organized into a `services` directory, with each service responsible for a specific domain (e.g., `NLUService`, `ImageGenerationService`, `ProductSearchService`). This promotes separation of concerns and makes the codebase easier to maintain.
*   **Configuration Management:** The application uses a `config.py` file with Pydantic's `BaseSettings` to manage configuration from environment variables. This provides a centralized and type-safe way to handle configuration.
*   **API Design:** The FastAPI application in `main.py` defines the API endpoints and uses Pydantic models for request and response validation.
*   **GCP Integration:** The `gcp_client.py` service provides a singleton client for interacting with GCP services, ensuring that a single authenticated client is used throughout the application.
*   **Vector Search:** The `ProductSearchService` is capable of performing vector similarity search in BigQuery, either using a pre-built index (`VECTOR_SEARCH`) or by calculating cosine similarity manually. This is controlled by the `use_vector_index` setting in the configuration.
*   **Frontend:** The frontend is kept simple with plain HTML, CSS, and JavaScript, served from the `static` directory.
