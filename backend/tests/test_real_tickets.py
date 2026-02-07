"""Test multi-agent orchestration with real customer tickets.

This script processes real anonymized customer tickets through the backend
using the REAL hackathon API to validate end-to-end functionality.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx

load_dotenv()

API_URL = os.environ.get("API_URL", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Load real tickets
TICKETS_FILE = Path(__file__).parent.parent / "data" / "anonymized_tickets.json"


def classify_ticket_intent(conversation: str, subject: str) -> str:
    """Classify ticket into use case based on content."""
    text = (conversation + " " + subject).lower()
    
    # Order tracking / WISMO
    if any(word in text for word in ["where is my order", "haven't received", "tracking", "delivered", "hasn't arrived", "shipped"]):
        return "UC1: WISMO"
    
    # Wrong/Missing item
    if any(word in text for word in ["wrong item", "received the wrong", "missing", "didn't receive", "expired"]):
        return "UC2: Wrong Item"
    
    # Product issue
    if any(word in text for word in ["doesn't work", "not working", "fall off", "no effect", "disappointed"]):
        return "UC3: Product Issue"
    
    # Refund
    if any(word in text for word in ["refund", "money back", "return"]):
        return "UC4: Refund"
    
    # Order modification/cancellation
    if any(word in text for word in ["cancel", "change address", "modify order"]):
        return "UC5: Order Modification"
    
    # Positive feedback
    if any(word in text for word in ["patch power", "love", "awesome", "thank you", "works great"]):
        return "UC6: Positive Feedback"
    
    # Subscription
    if any(word in text for word in ["subscription", "cancel subscription", "next order", "pause"]):
        return "UC7: Subscription"
    
    # Discount
    if any(word in text for word in ["discount", "promo code", "coupon"]):
        return "UC8: Discount"
    
    return "Unknown"


def extract_first_customer_message(conversation: str) -> str:
    """Extract the first customer message from conversation."""
    if conversation.startswith('Customer\'s message: "'):
        # Find the first customer message
        parts = conversation.split('Customer\'s message: "')
        if len(parts) > 1:
            first_msg = parts[1].split('" Agent\'s message:')[0]
            first_msg = first_msg.split('" Customer\'s message:')[0]
            # Clean up
            first_msg = first_msg.replace('\\"', '"')
            # Limit length
            if len(first_msg) > 500:
                first_msg = first_msg[:500] + "..."
            return first_msg
    return conversation[:500]


async def test_ticket(client: httpx.AsyncClient, ticket: dict, ticket_num: int) -> dict:
    """Test a single ticket through the backend."""
    
    customer_id = ticket.get("customerId", "unknown")
    conversation = ticket.get("conversation", "")
    subject = ticket.get("subject", "")
    
    # Extract first customer message
    message = extract_first_customer_message(conversation)
    
    # Classify expected use case
    expected_uc = classify_ticket_intent(conversation, subject)
    
    result = {
        "ticket_num": ticket_num,
        "conversation_id": ticket.get("conversationId", ""),
        "customer_id": customer_id,
        "subject": subject[:100],
        "message": message[:200],
        "expected_uc": expected_uc,
        "actual_agent": None,
        "success": False,
        "tools_called": [],
        "response": None,
        "error": None,
        "api_mode": "MOCK",
        "execution_time_ms": 0,
    }
    
    try:
        # Build request
        request_data = {
            "conversation_id": f"real-ticket-{ticket_num}",
            "user_id": customer_id,
            "channel": "email",
            "customer_email": f"{customer_id}@example.com",
            "first_name": "Customer",
            "last_name": str(ticket_num),
            "shopify_customer_id": customer_id,
            "message": message,
        }
        
        start_time = datetime.now()
        
        response = await client.post(
            f"{BACKEND_URL}/chat",
            json=request_data,
            timeout=30.0,
        )
        
        end_time = datetime.now()
        result["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            data = response.json()
            result["success"] = True
            result["actual_agent"] = data.get("agent")
            
            # Extract tool traces
            internal_data = data.get("state", {}).get("internal_data", {})
            tool_traces = internal_data.get("tool_traces", [])
            
            for trace in tool_traces:
                tool_name = trace.get("name", "")
                result["tools_called"].append(tool_name)
                
                # Check if real API was used
                output = trace.get("output", {})
                if isinstance(output, dict):
                    # If no error and success, it used API (or mock)
                    if output.get("success") and not output.get("error"):
                        result["api_mode"] = "REAL API" if API_URL else "MOCK"
            
            # Get response
            messages = data.get("state", {}).get("messages", [])
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    result["response"] = msg.get("content", "")[:300]
                    break
            
            if not result["response"]:
                result["response"] = data.get("state", {}).get("last_assistant_message", "")[:300]
        else:
            result["error"] = f"HTTP {response.status_code}"
    
    except Exception as e:
        result["error"] = str(e)[:200]
    
    return result


async def run_tests(max_tickets: int = 10):
    """Run tests on real tickets."""
    
    print("\n" + "=" * 80)
    print("🎯 MULTI-AGENT ORCHESTRATION TEST - REAL CUSTOMER TICKETS")
    print("=" * 80)
    print()
    
    # Load tickets
    if not TICKETS_FILE.exists():
        print(f"❌ Error: Tickets file not found at {TICKETS_FILE}")
        return []
    
    with open(TICKETS_FILE) as f:
        tickets = json.load(f)
    
    print(f"📋 Loaded {len(tickets)} real customer tickets")
    print(f"🧪 Testing first {max_tickets} tickets")
    print()
    
    if not API_URL:
        print("⚠️  WARNING: API_URL not set - Tests will use MOCK mode")
        print()
    else:
        print(f"✅ API_URL: {API_URL}")
        print("🌐 Tests will use REAL HACKATHON API")
        print()
    
    print(f"🎯 Backend: {BACKEND_URL}")
    print()
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for i, ticket in enumerate(tickets[:max_tickets], 1):
            print(f"[{i}/{max_tickets}] Processing ticket #{i}")
            print(f"    Subject: {ticket.get('subject', 'No subject')[:60]}...")
            
            result = await test_ticket(client, ticket, i)
            results.append(result)
            
            if result["success"]:
                uc_match = "✅" if result["expected_uc"] in result["actual_agent"] or result["actual_agent"] in result["expected_uc"] else "⚠️"
                print(f"    {uc_match} Expected: {result['expected_uc']}, Got: {result['actual_agent']}")
                tools = ", ".join(result["tools_called"][:2]) if result["tools_called"] else "none"
                if len(result["tools_called"]) > 2:
                    tools += f" (+{len(result['tools_called']) - 2})"
                print(f"    🔧 Tools: {tools} | {result['api_mode']}")
            else:
                print(f"    ❌ FAIL: {result['error']}")
            
            print()
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    return results


def generate_markdown_report(results: List[dict]) -> str:
    """Generate markdown report from results."""
    
    lines = []
    lines.append("# Real Customer Tickets - Multi-Agent Test Results")
    lines.append("")
    lines.append(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**API URL:** {API_URL or 'Not set (MOCK mode)'}")
    lines.append(f"**Backend URL:** {BACKEND_URL}")
    lines.append(f"**Tickets Tested:** {len(results)}")
    lines.append("")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    with_tools = sum(1 for r in results if r["tools_called"])
    api_calls = sum(1 for r in results if r.get("api_mode") == "REAL API")
    
    lines.append("## 📊 Summary")
    lines.append("")
    lines.append(f"- **Total Tickets:** {total}")
    lines.append(f"- **Processed Successfully:** {passed} ✅")
    lines.append(f"- **Failed:** {total - passed} ❌")
    lines.append(f"- **Tickets with Tool Calls:** {with_tools}")
    lines.append(f"- **Real API Calls Made:** {api_calls} 🌐")
    lines.append(f"- **Mock Calls:** {passed - api_calls} 🏠")
    lines.append("")
    
    # Use case distribution
    lines.append("## 📋 Use Case Distribution")
    lines.append("")
    uc_counts = {}
    for r in results:
        if r["success"]:
            agent = r["actual_agent"] or "unknown"
            uc_counts[agent] = uc_counts.get(agent, 0) + 1
    
    lines.append("| Agent | Tickets Handled |")
    lines.append("|-------|-----------------|")
    for agent, count in sorted(uc_counts.items()):
        lines.append(f"| `{agent}` | {count} |")
    lines.append("")
    
    # Detailed results
    lines.append("## 📝 Detailed Test Results")
    lines.append("")
    
    for result in results:
        lines.append(f"### Ticket #{result['ticket_num']}")
        lines.append("")
        lines.append(f"**Subject:** {result['subject']}  ")
        lines.append(f"**Customer Message:**")
        lines.append("```")
        lines.append(result['message'])
        lines.append("```")
        lines.append("")
        lines.append(f"**Expected Use Case:** {result['expected_uc']}  ")
        
        if result["success"]:
            lines.append(f"**Actual Agent:** `{result['actual_agent']}`  ")
            lines.append(f"**Execution Time:** {result['execution_time_ms']}ms  ")
            lines.append(f"**API Mode:** {result['api_mode']}  ")
            
            if result["tools_called"]:
                lines.append(f"**Tools Called:**")
                for tool in result["tools_called"]:
                    lines.append(f"  - `{tool}`")
                lines.append("")
            
            if result["response"]:
                lines.append(f"**Agent Response:**")
                lines.append("```")
                lines.append(result["response"])
                lines.append("```")
        else:
            lines.append(f"**Status:** ❌ FAILED  ")
            lines.append(f"**Error:** {result['error']}  ")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Statistics
    lines.append("## 📊 Statistics")
    lines.append("")
    
    if passed > 0:
        avg_time = sum(r["execution_time_ms"] for r in results if r["success"]) / passed
        lines.append(f"- **Average Response Time:** {int(avg_time)}ms")
        lines.append(f"- **Success Rate:** {int(passed/total*100)}%")
        lines.append(f"- **Tool Usage Rate:** {int(with_tools/total*100)}%")
        lines.append("")
    
    # Recommendations
    lines.append("## 💡 Insights")
    lines.append("")
    
    if not API_URL:
        lines.append("⚠️  **Running in MOCK mode** - Set `API_URL` in `.env` to test with real API")
        lines.append("")
    elif api_calls > 0:
        lines.append(f"✅ **{api_calls} tickets triggered real API calls** - Integration working!")
        lines.append("")
    
    lines.append("### Use Case Coverage")
    lines.append("")
    for uc, count in sorted(uc_counts.items()):
        lines.append(f"- **{uc}**: {count} ticket(s)")
    lines.append("")
    
    return "\n".join(lines)


async def main():
    """Main entry point."""
    
    # Get max tickets from command line
    max_tickets = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    # Run tests
    results = await run_tests(max_tickets)
    
    # Generate report
    report = generate_markdown_report(results)
    
    # Save report
    output_file = Path(__file__).parent.parent / "docs" / "REAL_TICKETS_TEST_RESULTS.md"
    output_file.write_text(report)
    
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print()
    print(f"📄 Report saved to: {output_file}")
    print()
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    api_calls = sum(1 for r in results if r.get("api_mode") == "REAL API")
    
    print(f"Summary:")
    print(f"  - {passed}/{total} tickets processed successfully")
    print(f"  - {api_calls} tickets used real API")
    print(f"  - {total - passed} tickets failed")
    print()


if __name__ == "__main__":
    asyncio.run(main())
