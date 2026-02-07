#!/bin/bash

# Verify backend tools match the hackathon API spec

echo "🔍 Verifying Backend vs Hackathon API Spec"
echo "=========================================="
echo ""

cd backend

echo "✅ Checking tool endpoints in code..."
echo ""

# Check Shopify tools
echo "📦 Shopify Tools (13):"
grep -n "post_tool.*hackathon" tools/shopify.py | head -20 | sed 's/^/  /'

echo ""
echo "📦 Skio Tools (5):"
grep -n "post_tool.*hackathon" tools/skio.py | sed 's/^/  /'

echo ""
echo "=========================================="
echo ""

# Check critical tool updates
echo "🔧 Key Updates:"
echo ""

# Check if get-subscriptions is correct (not get-subscription-status)
if grep -q "get-subscriptions" tools/skio.py; then
    echo "  ✅ skio_get_subscriptions endpoint: /hackathon/get-subscriptions"
else
    echo "  ⚠️  skio_get_subscriptions endpoint not found!"
fi

# Check if all tools use /hackathon/ not /hackhaton/
if grep -q "hackhaton" tools/shopify.py tools/skio.py; then
    echo "  ❌ OLD typo 'hackhaton' still exists!"
else
    echo "  ✅ All tools use '/hackathon/' (correct spelling)"
fi

echo ""
echo "=========================================="
echo "✅ Verification Complete!"
echo ""
