#!/bin/bash

# Test multi-agent orchestration with real customer tickets
# Uses the REAL hackathon API (if API_URL is set in .env)

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🎯 MULTI-AGENT ORCHESTRATION TEST - REAL TICKETS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check backend
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
echo "🔍 Checking backend at $BACKEND_URL..."

if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "❌ Backend not running!"
    echo "   Start it with: cd backend && uvicorn api.server:app --reload"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Check API configuration
cd "$(dirname "$0")/.."
if [ -f .env ]; then
    API_URL=$(grep "^API_URL=" .env | cut -d '=' -f2)
    if [ -z "$API_URL" ]; then
        echo "⚠️  API_URL not set - Using MOCK mode"
    else
        echo "✅ API_URL: $API_URL"
        echo "🌐 Will use REAL HACKATHON API"
    fi
else
    echo "⚠️  .env not found"
fi
echo ""

# Get number of tickets to test (default 10)
NUM_TICKETS=${1:-10}

echo "📋 Testing $NUM_TICKETS real customer tickets..."
echo ""

# Run test
python3 tests/test_real_tickets.py $NUM_TICKETS

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Check docs/REAL_TICKETS_TEST_RESULTS.md for full report"
echo "════════════════════════════════════════════════════════════════"
