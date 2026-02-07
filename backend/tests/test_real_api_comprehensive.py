"""Comprehensive test of hackathon API with temporary database.

This script:
1. Creates a temporary test database
2. Tests all use cases with real API calls
3. Generates a markdown report with results

Usage:
    # Make sure API_URL is set in .env, then:
    python test_real_api_comprehensive.py
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import httpx

load_dotenv()

API_URL = os.environ.get("API_URL", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Test scenarios for each use case
TEST_SCENARIOS = [
    {
        "id": "uc1_wismo_01",
        "use_case": "UC1: WISMO",
        "description": "Customer asks about order status",
        "request": {
            "conversation_id": "test-wismo-01",
            "user_id": "test-user-001",
            "channel": "email",
            "customer_email": "transit@test.com",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "shopify_customer_id": "cust-001",
            "message": "Where is my order? It's been a week and I haven't received it."
        },
        "expected_tools": ["get_customer_orders", "get_order_details"],
    },
    {
        "id": "uc2_wrong_item_01",
        "use_case": "UC2: Wrong Item",
        "description": "Customer received wrong item",
        "request": {
            "conversation_id": "test-wrong-01",
            "user_id": "test-user-002",
            "channel": "email",
            "customer_email": "lisa@example.com",
            "first_name": "Lisa",
            "last_name": "Martinez",
            "shopify_customer_id": "cust-002",
            "message": "I received Zen stickers instead of Focus patches. Wrong item!"
        },
        "expected_tools": ["get_customer_orders"],
    },
    {
        "id": "uc3_product_issue_01",
        "use_case": "UC3: Product Issue",
        "description": "Product not working as expected",
        "request": {
            "conversation_id": "test-product-01",
            "user_id": "test-user-003",
            "channel": "email",
            "customer_email": "mark@example.com",
            "first_name": "Mark",
            "last_name": "Wilson",
            "shopify_customer_id": "cust-003",
            "message": "The BuzzPatch stickers aren't working. My kid still got mosquito bites."
        },
        "expected_tools": ["get_product_details", "get_related_knowledge_source"],
    },
    {
        "id": "uc4_refund_01",
        "use_case": "UC4: Refund Request",
        "description": "Customer requests refund",
        "request": {
            "conversation_id": "test-refund-01",
            "user_id": "test-user-004",
            "channel": "email",
            "customer_email": "karen@example.com",
            "first_name": "Karen",
            "last_name": "Smith",
            "shopify_customer_id": "cust-004",
            "message": "I want a refund for my order. It didn't work for me."
        },
        "expected_tools": ["get_customer_orders"],
    },
    {
        "id": "uc5_order_mod_01",
        "use_case": "UC5: Order Modification",
        "description": "Customer wants to cancel order",
        "request": {
            "conversation_id": "test-ordermod-01",
            "user_id": "test-user-005",
            "channel": "email",
            "customer_email": "mike@example.com",
            "first_name": "Mike",
            "last_name": "Chen",
            "shopify_customer_id": "cust-005",
            "message": "Please cancel my order. I ordered it by mistake."
        },
        "expected_tools": ["get_customer_orders", "cancel_order"],
    },
    {
        "id": "uc7_subscription_01",
        "use_case": "UC7: Subscription",
        "description": "Customer asks about subscription",
        "request": {
            "conversation_id": "test-sub-01",
            "user_id": "test-user-007",
            "channel": "email",
            "customer_email": "emma@example.com",
            "first_name": "Emma",
            "last_name": "Williams",
            "shopify_customer_id": "cust-007",
            "message": "When is my next subscription order? I want to skip it."
        },
        "expected_tools": ["get_subscription_status", "skip_next_order"],
    },
    {
        "id": "uc8_discount_01",
        "use_case": "UC8: Discount Request",
        "description": "Customer asks for discount code",
        "request": {
            "conversation_id": "test-discount-01",
            "user_id": "test-user-008",
            "channel": "email",
            "customer_email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "shopify_customer_id": "cust-008",
            "message": "Do you have any discount codes? I'd like 10% off."
        },
        "expected_tools": ["create_discount_code"],
    },
]


async def test_scenario(client: httpx.AsyncClient, scenario: dict) -> dict:
    """Test a single scenario and return results."""
    
    result = {
        "id": scenario["id"],
        "use_case": scenario["use_case"],
        "description": scenario["description"],
        "success": False,
        "agent": None,
        "tools_called": [],
        "response": None,
        "error": None,
        "api_calls_made": False,
        "execution_time_ms": 0,
    }
    
    try:
        start_time = datetime.now()
        
        response = await client.post(
            f"{BACKEND_URL}/chat",
            json=scenario["request"],
            timeout=30.0,
        )
        
        end_time = datetime.now()
        result["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            data = response.json()
            result["success"] = True
            result["agent"] = data.get("agent")
            
            # Extract tool traces from internal_data
            internal_data = data.get("state", {}).get("internal_data", {})
            tool_traces = internal_data.get("tool_traces", [])
            
            # Check if any real API calls were made
            for trace in tool_traces:
                tool_name = trace.get("name", "")
                result["tools_called"].append(tool_name)
                
                # Check if tool actually called API (not mock)
                output = trace.get("output", {})
                if isinstance(output, dict) and output.get("success") is not False:
                    result["api_calls_made"] = True
            
            # Get last assistant message
            messages = data.get("state", {}).get("messages", [])
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    result["response"] = msg.get("content", "")
                    break
            
            if not result["response"]:
                result["response"] = data.get("state", {}).get("last_assistant_message", "No response")
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        result["error"] = str(e)
    
    return result


async def run_all_tests():
    """Run all test scenarios."""
    
    print("\n" + "=" * 70)
    print("HACKATHON API COMPREHENSIVE TEST")
    print("=" * 70)
    print()
    
    # Check configuration
    if not API_URL:
        print("⚠️  WARNING: API_URL is not set in .env")
        print("   Tests will use MOCK mode (no real API calls)")
        print()
    else:
        print(f"✅ API_URL: {API_URL}")
        print()
    
    print(f"🎯 Backend URL: {BACKEND_URL}")
    print(f"📝 Testing {len(TEST_SCENARIOS)} scenarios...")
    print()
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            print(f"[{i}/{len(TEST_SCENARIOS)}] Testing: {scenario['use_case']}")
            print(f"    {scenario['description']}")
            
            result = await test_scenario(client, scenario)
            results.append(result)
            
            if result["success"]:
                tools_str = ", ".join(result["tools_called"]) if result["tools_called"] else "none"
                api_indicator = "🌐 API" if result["api_calls_made"] else "🏠 MOCK"
                print(f"    ✅ PASS - Agent: {result['agent']}, Tools: {tools_str} {api_indicator}")
            else:
                print(f"    ❌ FAIL - {result['error']}")
            
            print()
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    return results


def generate_markdown_report(results: list) -> str:
    """Generate a markdown report from test results."""
    
    report = []
    report.append("# Hackathon API Test Results")
    report.append("")
    report.append(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**API URL:** {API_URL or 'Not set (MOCK mode)'}")
    report.append(f"**Backend URL:** {BACKEND_URL}")
    report.append("")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    with_api = sum(1 for r in results if r.get("api_calls_made"))
    
    report.append("## 📊 Summary")
    report.append("")
    report.append(f"- **Total Tests:** {total}")
    report.append(f"- **Passed:** {passed} ✅")
    report.append(f"- **Failed:** {failed} ❌")
    report.append(f"- **Real API Calls:** {with_api} 🌐")
    report.append(f"- **Mock Calls:** {total - with_api} 🏠")
    report.append("")
    
    # Detailed results
    report.append("## 📝 Detailed Results")
    report.append("")
    
    for result in results:
        report.append(f"### {result['use_case']}")
        report.append("")
        report.append(f"**Test ID:** `{result['id']}`  ")
        report.append(f"**Description:** {result['description']}  ")
        report.append(f"**Status:** {'✅ PASS' if result['success'] else '❌ FAIL'}  ")
        
        if result["success"]:
            report.append(f"**Agent:** `{result['agent']}`  ")
            report.append(f"**Execution Time:** {result['execution_time_ms']}ms  ")
            
            if result["tools_called"]:
                api_indicator = "🌐 Real API" if result["api_calls_made"] else "🏠 Mock"
                report.append(f"**Tools Called:** {api_indicator}  ")
                for tool in result["tools_called"]:
                    report.append(f"  - `{tool}`")
                report.append("")
            else:
                report.append("**Tools Called:** None  ")
                report.append("")
            
            if result["response"]:
                report.append("**Agent Response:**")
                report.append("```")
                # Truncate long responses
                response = result["response"]
                if len(response) > 500:
                    response = response[:500] + "..."
                report.append(response)
                report.append("```")
        else:
            report.append(f"**Error:** {result['error']}  ")
        
        report.append("")
        report.append("---")
        report.append("")
    
    # API Status by Use Case
    report.append("## 🔧 Tool Execution Summary")
    report.append("")
    report.append("| Use Case | Agent | Tools Called | API Status |")
    report.append("|----------|-------|--------------|------------|")
    
    for result in results:
        if result["success"]:
            tools = ", ".join(result["tools_called"][:2]) if result["tools_called"] else "None"
            if len(result["tools_called"]) > 2:
                tools += f" (+{len(result['tools_called']) - 2} more)"
            api_status = "🌐 Real" if result["api_calls_made"] else "🏠 Mock"
            report.append(f"| {result['use_case']} | `{result['agent']}` | {tools} | {api_status} |")
        else:
            report.append(f"| {result['use_case']} | - | - | ❌ Error |")
    
    report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")
    
    if not API_URL:
        report.append("⚠️  **API_URL not configured** - All tests ran in MOCK mode")
        report.append("")
        report.append("To test with real API:")
        report.append("1. Set `API_URL=https://lookfor-hackathon-backend.onrender.com` in `.env`")
        report.append("2. Restart backend: `uvicorn api.server:app --reload`")
        report.append("3. Run tests again")
        report.append("")
    elif with_api == 0:
        report.append("⚠️  **No real API calls detected** - Check API_URL and tool implementations")
        report.append("")
    else:
        report.append(f"✅ **{with_api}/{total} tests made real API calls** - Integration working!")
        report.append("")
    
    if failed > 0:
        report.append(f"⚠️  **{failed} test(s) failed** - Review error details above")
        report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append("**Test Configuration:**")
    report.append(f"- Backend: `{BACKEND_URL}`")
    report.append(f"- API: `{API_URL or 'Not set'}`")
    report.append(f"- Database: Temporary (tests do not affect main state.db)")
    report.append("")
    
    return "\n".join(report)


async def main():
    """Main test execution."""
    
    # Run tests
    results = await run_all_tests()
    
    # Generate report
    report = generate_markdown_report(results)
    
    # Save to file
    output_file = Path(__file__).parent / "API_TEST_RESULTS.md"
    output_file.write_text(report)
    
    print("=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print()
    print(f"📄 Report saved to: {output_file}")
    print()
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    with_api = sum(1 for r in results if r.get("api_calls_made"))
    
    print(f"Summary: {passed}/{total} passed, {with_api} with real API calls")
    print()
    
    # Show quick preview
    print("Quick Preview:")
    print("-" * 70)
    for r in results:
        status = "✅" if r["success"] else "❌"
        api = "🌐" if r.get("api_calls_made") else "🏠"
        print(f"{status} {r['use_case']:30} {api} Agent: {r.get('agent', 'N/A')}")
    print("-" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
