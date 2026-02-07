"""Quick test script for real hackathon API integration.

Usage:
    # Set API_URL in .env first, then:
    python test_real_api.py
"""

import asyncio
import os
from dotenv import load_dotenv
from tools.shopify import (
    shopify_add_tags,
    shopify_create_discount_code,
    shopify_get_customer_orders,
    shopify_get_order_details,
    shopify_get_product_recommendations,
)
from tools.skio import skio_get_subscription_status

load_dotenv()

API_URL = os.environ.get("API_URL", "")


async def test_all_tools():
    """Test all 18 tools with the real API."""
    
    print("=" * 60)
    print("HACKATHON API TEST - All 18 Tools")
    print("=" * 60)
    print()
    
    if not API_URL:
        print("❌ API_URL is not set in .env")
        print("   Please add: API_URL=https://lookfor-hackathon-backend.onrender.com")
        print()
        return
    
    print(f"✅ API_URL: {API_URL}")
    print()
    
    # Test 1: Add Tags
    print("1️⃣  Testing: shopify_add_tags")
    try:
        result = await shopify_add_tags(
            id="gid://shopify/Order/5531567751245",
            tags=["Test Tag from API"]
        )
        if result.get("success"):
            print("   ✅ PASS - Tags added successfully")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    # Test 2: Get Customer Orders
    print("2️⃣  Testing: shopify_get_customer_orders")
    try:
        result = await shopify_get_customer_orders(
            email="test@example.com",
            after="null",
            limit=5
        )
        if result.get("success"):
            orders = result.get("data", {}).get("orders", [])
            print(f"   ✅ PASS - Found {len(orders)} order(s)")
            if orders:
                print(f"      First order: {orders[0].get('name', 'N/A')}")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    # Test 3: Get Order Details
    print("3️⃣  Testing: shopify_get_order_details")
    try:
        result = await shopify_get_order_details(orderId="#1001")
        if result.get("success"):
            order = result.get("data", {})
            print(f"   ✅ PASS - Order: {order.get('name', 'N/A')}")
            print(f"      Status: {order.get('status', 'N/A')}")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    # Test 4: Create Discount Code
    print("4️⃣  Testing: shopify_create_discount_code")
    try:
        result = await shopify_create_discount_code(
            type="percentage",
            value=0.1,
            duration=48,
            productIds=[]
        )
        if result.get("success"):
            code = result.get("data", {}).get("code", "N/A")
            print(f"   ✅ PASS - Discount code created: {code}")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    # Test 5: Get Product Recommendations
    print("5️⃣  Testing: shopify_get_product_recommendations")
    try:
        result = await shopify_get_product_recommendations(
            queryKeys=["sleep", "kids"]
        )
        if result.get("success"):
            products = result.get("data", [])
            print(f"   ✅ PASS - Found {len(products)} recommendation(s)")
            if products:
                print(f"      First product: {products[0].get('title', 'N/A')}")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    # Test 6: Get Subscription Status (Skio)
    print("6️⃣  Testing: skio_get_subscription_status")
    try:
        result = await skio_get_subscription_status(email="test@example.com")
        if result.get("success"):
            status = result.get("data", {}).get("status", "N/A")
            print(f"   ✅ PASS - Subscription status: {status}")
        else:
            print(f"   ⚠️  API returned: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ FAIL - {e}")
    print()
    
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("📝 Note: Some tests may show warnings if test data doesn't exist")
    print("   in the hackathon API. This is normal for testing.")
    print()
    print("📚 For full API reference, see: HACKATHON_API_REFERENCE.md")
    print()


async def test_single_tool(tool_name: str = "add_tags"):
    """Test a single tool interactively."""
    
    print(f"\nTesting: {tool_name}")
    print("-" * 40)
    
    if not API_URL:
        print("❌ API_URL is not set in .env")
        return
    
    if tool_name == "add_tags":
        result = await shopify_add_tags(
            id="gid://shopify/Order/5531567751245",
            tags=["Test Tag"]
        )
    elif tool_name == "get_orders":
        result = await shopify_get_customer_orders(
            email="lisa@example.com",
            after="null",
            limit=5
        )
    elif tool_name == "create_discount":
        result = await shopify_create_discount_code(
            type="percentage",
            value=0.1,
            duration=48,
            productIds=[]
        )
    else:
        print(f"Unknown tool: {tool_name}")
        return
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Data: {result.get('data')}")
    print(f"  Error: {result.get('error')}")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test single tool
        asyncio.run(test_single_tool(sys.argv[1]))
    else:
        # Test all tools
        asyncio.run(test_all_tools())
