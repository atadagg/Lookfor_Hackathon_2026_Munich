#!/bin/bash

# Quick test with REAL Hackathon API
# API_URL is now set to: https://lookfor-hackathon-backend.onrender.com

echo "🎯 Testing with REAL Hackathon API"
echo "=================================="
echo ""
echo "API URL: https://lookfor-hackathon-backend.onrender.com"
echo ""

# Make sure backend is using the API_URL from .env
echo "📝 Checking .env configuration:"
grep "^API_URL=" .env
echo ""

BACKEND_URL="http://localhost:8000"

echo "🚀 Sending test request..."
echo ""

# Test 1: Discount Code (simple and quick)
curl -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "real-api-test-001",
    "user_id": "test-user",
    "customer_email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "shopify_customer_id": "cust-test-001",
    "message": "I need a 10% discount code please"
  }' | jq '{
    "🎯 Agent": .agent,
    "📝 Response": .state.last_assistant_message,
    "🔧 Tools Called": [.state.internal_data.tool_traces[]? | .name],
    "✅ Tool Success": .state.internal_data.tool_traces[0]?.output.success,
    "❌ Tool Error": .state.internal_data.tool_traces[0]?.output.error,
    "🌐 API Mode": (if .state.internal_data.tool_traces[0]?.output.success == true then "REAL API ✅" else "Check error" end),
    "📊 Discount Code": .state.internal_data.tool_traces[0]?.output.data.code
  }'

echo ""
echo ""
echo "=================================="
echo "✅ Test Complete!"
echo ""
echo "Check above for:"
echo "  - Tool Success: true = Real API worked!"
echo "  - Tool Error: null = No errors"
echo "  - Discount Code: Should show real code from API"
echo ""
