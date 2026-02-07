#!/bin/bash

# Run comprehensive API test with temporary database
# This ensures the main state.db is not affected

set -e

echo "════════════════════════════════════════════════════════════════"
echo "HACKATHON API COMPREHENSIVE TEST"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if backend is running
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
echo "🔍 Checking if backend is running at $BACKEND_URL..."

if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "❌ Backend is not running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd backend"
    echo "  uvicorn api.server:app --reload"
    echo ""
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Check API_URL configuration
if [ -f .env ]; then
    API_URL=$(grep "^API_URL=" .env | cut -d '=' -f2)
    if [ -z "$API_URL" ]; then
        echo "⚠️  WARNING: API_URL is not set in .env"
        echo "   Tests will run in MOCK mode (no real API calls)"
        echo ""
        echo "   To test with real API, add to .env:"
        echo "   API_URL=https://lookfor-hackathon-backend.onrender.com"
        echo ""
    else
        echo "✅ API_URL configured: $API_URL"
        echo ""
    fi
else
    echo "⚠️  WARNING: .env file not found"
    echo ""
fi

# Create temporary database for testing
TEMP_DB=$(mktemp -d)/test_state.db
export TEST_DB_PATH=$TEMP_DB

echo "📁 Using temporary database: $TEMP_DB"
echo "   (Main state.db will not be affected)"
echo ""

# Run the test
echo "🚀 Running tests..."
echo ""

python test_real_api_comprehensive.py

# Cleanup temp DB
rm -f "$TEMP_DB" 2>/dev/null || true

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Test Complete! Check API_TEST_RESULTS.md for full report"
echo "════════════════════════════════════════════════════════════════"
