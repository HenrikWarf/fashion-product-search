#!/bin/bash

# Athena Fashion Search - Quick Start Script

echo "=========================================="
echo "  Athena Fashion Search"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found"
    echo "Please create .env from .env.example and configure your settings"
    echo ""
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your GCP configuration"
    exit 1
fi

# Install/update dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies ready"
echo ""

# Run connection test
echo "Testing GCP connection..."
python test_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Starting Athena Fashion Search Server..."
    echo "=========================================="
    echo ""
    echo "Access the application at: http://localhost:8000"
    echo "Press CTRL+C to stop the server"
    echo ""
    python main.py
else
    echo ""
    echo "⚠ Connection test failed. Please fix the issues above."
    exit 1
fi
