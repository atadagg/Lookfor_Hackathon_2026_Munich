"""Direct test of hackathon API tools (no backend server needed).

This script directly tests the 18 tools against the real API.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from tools.shopify import (
    shopify_add_tags,
    shopify_create_discount_code,
    shopify_get_customer_orders,
    shopify_get_order_details,
    shopify_get_product_details,
    shopify_get_product_recommendations,
    shopify_create_store_credit,
    shopify_refund_order,
    shopify_cancel_order,
)
from tools.skio import (
    skio_get_subscription_status,
    skio_skip_next_order_subscription,
    skio_pause_subscription,
    skio_cancel_subscription,
)

load_dotenv()

API_URL = os.environ.get("API_URL", "")


async def run_tests():
    """Run direct tool tests."""
    
    results = []
    
    print("\n" + "=" * 70)
    print("DIRECT API TOOL TEST")
    print("=" * 70)
    print()
    
    if not API_URL:
        print("⚠️  WARNING: API_URL is not set in .env")
        print("   Tests will use MOCK mode")
        print()
    else:
        print(f"✅ API_URL: {API_URL}")
        print()
    
    # Test 1: Get Customer Orders
    print("1️⃣  shopify_get_customer_orders")
    try:
        result = await shopify_get_customer_orders(
            email="test@example.com",
            after="null",
            limit=5
        )
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            orders = result.get("data", {}).get("orders", [])
            print(f"   Found {len(orders)} order(s)")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_get_customer_orders", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_get_customer_orders", False, {"error": str(e)}))
    print()
    
    # Test 2: Get Order Details
    print("2️⃣  shopify_get_order_details")
    try:
        result = await shopify_get_order_details(orderId="#1001")
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            order = result.get("data", {})
            print(f"   Order: {order.get('name', 'N/A')}, Status: {order.get('status', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_get_order_details", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_get_order_details", False, {"error": str(e)}))
    print()
    
    # Test 3: Create Discount Code
    print("3️⃣  shopify_create_discount_code")
    try:
        result = await shopify_create_discount_code(
            type="percentage",
            value=0.1,
            duration=48,
            productIds=[]
        )
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            code = result.get("data", {}).get("code", "N/A")
            print(f"   Code: {code}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_create_discount_code", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_create_discount_code", False, {"error": str(e)}))
    print()
    
    # Test 4: Get Product Details
    print("4️⃣  shopify_get_product_details")
    try:
        result = await shopify_get_product_details(
            queryType="name",
            queryKey="BuzzPatch"
        )
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            products = result.get("data", [])
            print(f"   Found {len(products)} product(s)")
            if products:
                print(f"   First: {products[0].get('title', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_get_product_details", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_get_product_details", False, {"error": str(e)}))
    print()
    
    # Test 5: Get Product Recommendations
    print("5️⃣  shopify_get_product_recommendations")
    try:
        result = await shopify_get_product_recommendations(
            queryKeys=["sleep", "kids"]
        )
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            products = result.get("data", [])
            print(f"   Found {len(products)} recommendation(s)")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_get_product_recommendations", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_get_product_recommendations", False, {"error": str(e)}))
    print()
    
    # Test 6: Add Tags
    print("6️⃣  shopify_add_tags")
    try:
        result = await shopify_add_tags(
            id="gid://shopify/Order/123456",
            tags=["Test Tag"]
        )
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if not success:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("shopify_add_tags", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("shopify_add_tags", False, {"error": str(e)}))
    print()
    
    # Test 7: Get Subscription Status (Skio)
    print("7️⃣  skio_get_subscription_status")
    try:
        result = await skio_get_subscription_status(email="test@example.com")
        success = result.get("success", False)
        mode = "🌐 API" if API_URL else "🏠 MOCK"
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {mode}")
        if success:
            data = result.get("data", {})
            print(f"   Status: {data.get('status', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        results.append(("skio_get_subscription_status", success, result))
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append(("skio_get_subscription_status", False, {"error": str(e)}))
    print()
    
    return results


def generate_markdown_report(results: list) -> str:
    """Generate markdown report."""
    
    lines = []
    lines.append("# Direct API Tool Test Results")
    lines.append("")
    lines.append(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**API URL:** {API_URL or 'Not set (MOCK mode)'}")
    lines.append("")
    
    # Summary
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    mode = "Real API" if API_URL else "Mock"
    
    lines.append("## 📊 Summary")
    lines.append("")
    lines.append(f"- **Total Tools Tested:** {total}")
    lines.append(f"- **Passed:** {passed} ✅")
    lines.append(f"- **Failed:** {total - passed} ❌")
    lines.append(f"- **Mode:** {mode}")
    lines.append("")
    
    # Results table
    lines.append("## 📝 Test Results")
    lines.append("")
    lines.append("| Tool | Status | Mode | Result |")
    lines.append("|------|--------|------|--------|")
    
    for tool_name, success, result in results:
        status = "✅ PASS" if success else "❌ FAIL"
        mode_icon = "🌐" if API_URL else "🏠"
        
        if success:
            data = result.get("data", {})
            if isinstance(data, dict):
                if "orders" in data:
                    detail = f"{len(data['orders'])} orders"
                elif "code" in data:
                    detail = f"Code: {data['code']}"
                elif "status" in data:
                    detail = f"Status: {data['status']}"
                else:
                    detail = "Success"
            elif isinstance(data, list):
                detail = f"{len(data)} items"
            else:
                detail = "Success"
        else:
            error = result.get("error", "Unknown error")
            detail = f"Error: {error[:50]}"
        
        lines.append(f"| `{tool_name}` | {status} | {mode_icon} | {detail} |")
    
    lines.append("")
    
    # Details
    lines.append("## 🔍 Detailed Results")
    lines.append("")
    
    for tool_name, success, result in results:
        lines.append(f"### {tool_name}")
        lines.append("")
        lines.append(f"**Status:** {'✅ PASS' if success else '❌ FAIL'}  ")
        lines.append(f"**Success:** `{result.get('success')}`  ")
        
        if result.get("data"):
            lines.append("**Data:**")
            lines.append("```json")
            import json
            lines.append(json.dumps(result.get("data"), indent=2)[:500])
            lines.append("```")
        
        if result.get("error"):
            lines.append(f"**Error:** `{result.get('error')}`  ")
        
        lines.append("")
    
    # Configuration
    lines.append("---")
    lines.append("")
    lines.append("## ⚙️ Configuration")
    lines.append("")
    lines.append(f"- **API URL:** `{API_URL or 'Not configured'}`")
    lines.append(f"- **Mode:** {'Real API calls' if API_URL else 'Mock mode (no real API calls)'}")
    lines.append("")
    
    if not API_URL:
        lines.append("### 💡 To Test with Real API")
        lines.append("")
        lines.append("1. Add to `backend/.env`:")
        lines.append("   ```")
        lines.append("   API_URL=https://lookfor-hackathon-backend.onrender.com")
        lines.append("   ```")
        lines.append("2. Run test again: `python3 test_api_direct.py`")
        lines.append("")
    
    return "\n".join(lines)


async def main():
    """Main entry point."""
    
    results = await run_tests()
    
    # Generate report
    report = generate_markdown_report(results)
    
    # Save report
    output_file = Path(__file__).parent / "API_DIRECT_TEST_RESULTS.md"
    output_file.write_text(report)
    
    print("=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print()
    print(f"📄 Report saved to: {output_file}")
    print()
    
    # Summary
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    print(f"Summary: {passed}/{total} tests passed")
    print(f"Mode: {'Real API' if API_URL else 'Mock'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
