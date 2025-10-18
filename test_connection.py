#!/usr/bin/env python3
"""
Test script to verify GCP connection and configuration.
Run this after setup to ensure everything is configured correctly.
"""

import sys
from services.gcp_client import get_gcp_client
from config import get_settings


def test_configuration():
    """Test configuration loading."""
    print("=" * 60)
    print("Testing Configuration...")
    print("=" * 60)

    try:
        settings = get_settings()
        print(f"✓ Configuration loaded")
        print(f"  - Project ID: {settings.gcp_project_id}")
        print(f"  - Location: {settings.gcp_location}")
        print(f"  - Dataset: {settings.bigquery_dataset}")
        print(f"  - Table: {settings.bigquery_table}")
        print(f"  - Gemini Model: {settings.gemini_model}")
        print(f"  - Gemini Image Model: {settings.gemini_image_model}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_gcp_client():
    """Test GCP client initialization."""
    print("\n" + "=" * 60)
    print("Testing GCP Client Initialization...")
    print("=" * 60)

    try:
        client = get_gcp_client()
        print("✓ GCP Client initialized successfully")
        return True, client
    except FileNotFoundError as e:
        print(f"✗ Service account key file not found: {e}")
        print("\nPlease ensure:")
        print("  1. You've created a service account in GCP")
        print("  2. Downloaded the JSON key file")
        print("  3. Updated GOOGLE_APPLICATION_CREDENTIALS in .env")
        return False, None
    except Exception as e:
        print(f"✗ GCP Client initialization error: {e}")
        return False, None


def test_bigquery(client):
    """Test BigQuery connection and table access."""
    print("\n" + "=" * 60)
    print("Testing BigQuery Connection...")
    print("=" * 60)

    try:
        settings = get_settings()
        bq_client = client.bigquery

        # Test table existence and count
        query = f"""
        SELECT COUNT(*) as count
        FROM `{settings.gcp_project_id}.{settings.bigquery_dataset}.{settings.bigquery_table}`
        """

        print(f"Querying: {settings.bigquery_dataset}.{settings.bigquery_table}")
        query_job = bq_client.query(query)
        result = query_job.result()

        for row in result:
            count = row.count
            print(f"✓ BigQuery connection successful")
            print(f"  - Products found: {count:,}")

            if count == 0:
                print("\n⚠ Warning: No products in table")
                print("  Please load your product data with embeddings")

        # Test if embeddings column exists
        table_ref = bq_client.get_table(
            f"{settings.gcp_project_id}.{settings.bigquery_dataset}.{settings.bigquery_table}"
        )

        has_embedding = any(field.name == "embedding" for field in table_ref.schema)
        if has_embedding:
            print("✓ Embedding column exists")
        else:
            print("✗ Embedding column not found")
            print("  Please add embedding column to your table")

        return True

    except Exception as e:
        print(f"✗ BigQuery error: {e}")
        print("\nPlease ensure:")
        print("  1. BigQuery API is enabled")
        print("  2. Service account has bigquery.dataViewer role")
        print("  3. Service account has bigquery.jobUser role")
        print("  4. Dataset and table names are correct in .env")
        return False


def test_vertex_ai(client):
    """Test Vertex AI / Gemini access."""
    print("\n" + "=" * 60)
    print("Testing Vertex AI / Gemini...")
    print("=" * 60)

    try:
        # Test Gemini model
        model = client.get_gemini_model()
        print("✓ Gemini model loaded")

        # Test with a simple prompt
        print("  Testing with simple prompt...")
        response = model.generate_content("Say 'Hello from Gemini!'")
        print(f"  Response: {response.text[:50]}...")
        print("✓ Gemini API is working")

        # Test Gemini Image model
        image_model = client.get_gemini_image_model()
        print("✓ Gemini Image model loaded")

        return True

    except Exception as e:
        print(f"✗ Vertex AI error: {e}")
        print("\nPlease ensure:")
        print("  1. Vertex AI API is enabled")
        print("  2. Service account has aiplatform.user role")
        print("  3. Gemini models are available in your region")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ATHENA FASHION SEARCH - CONNECTION TEST" + " " * 9 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Test configuration
    results.append(test_configuration())

    # Test GCP client
    success, client = test_gcp_client()
    results.append(success)

    if not success:
        print("\n" + "=" * 60)
        print("TESTS FAILED - Cannot proceed without GCP client")
        print("=" * 60)
        sys.exit(1)

    # Test BigQuery
    results.append(test_bigquery(client))

    # Test Vertex AI
    results.append(test_vertex_ai(client))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        print("\nYour application is ready to run!")
        print("Start the server with: python main.py")
    else:
        print(f"⚠ {total - passed} test(s) failed ({passed}/{total} passed)")
        print("\nPlease fix the issues above before running the application.")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
