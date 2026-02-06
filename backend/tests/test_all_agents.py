#!/usr/bin/env python3
"""Test all agents with sample scenarios.

Run with: python3 test_all_agents.py
Requires backend server running (default: http://localhost:8000)
Set BACKEND_URL environment variable to override.
"""

import asyncio
import json
import os
from typing import Dict, Any

import httpx


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


async def test_agent(client: httpx.AsyncClient, scenario: Dict[str, Any]) -> None:
    """Test a single agent scenario."""
    print(f"\n{'='*80}")
    print(f"Testing: {scenario['name']}")
    print(f"Agent: {scenario['expected_agent']}")
    print(f"{'='*80}")
    
    for i, turn in enumerate(scenario['turns'], 1):
        print(f"\n--- Turn {i} ---")
        print(f"Customer: {turn['message']}")
        
        payload = {
            "conversation_id": scenario['conv_id'],
            "user_id": "test-user",
            "channel": "email",
            "customer_email": turn.get('email', 'test@example.com'),
            "first_name": turn.get('first_name', 'Alex'),
            "last_name": turn.get('last_name', 'Customer'),
            "shopify_customer_id": "cust-123",
            "message": turn['message'],
        }
        
        try:
            resp = await client.post(f"{BASE_URL}/chat", json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            
            print(f"Agent: {data['agent']}")
            print(f"Workflow Step: {data['state'].get('workflow_step', 'N/A')}")
            print(f"Escalated: {data['state'].get('is_escalated', False)}")
            print(f"\nAgent Reply:\n{data['state'].get('last_assistant_message', 'N/A')}")
            
            # Show tool traces
            traces = data['state'].get('internal_data', {}).get('tool_traces', [])
            if traces:
                print(f"\nTools Called: {', '.join([t['name'] for t in traces])}")
            
        except Exception as e:
            print(f"ERROR: {e}")


async def main():
    """Run all test scenarios."""
    
    scenarios = [
        # UC1: WISMO (Shipping Delay)
        {
            "name": "UC1: WISMO - In Transit",
            "conv_id": "test-wismo-1",
            "expected_agent": "wismo",
            "turns": [
                {
                    "message": "Where is my order? It's been a week and I haven't received it yet.",
                    "email": "transit@test.com",
                    "first_name": "Sarah"
                }
            ]
        },
        {
            "name": "UC1: WISMO - Unfulfilled",
            "conv_id": "test-wismo-2",
            "expected_agent": "wismo",
            "turns": [
                {
                    "message": "I ordered 3 days ago but haven't heard anything. When will it ship?",
                    "email": "unfulfilled@test.com",
                    "first_name": "Mike"
                }
            ]
        },
        {
            "name": "UC1: WISMO - Multi-turn with Order ID",
            "conv_id": "test-wismo-3",
            "expected_agent": "wismo",
            "turns": [
                {
                    "message": "My order hasn't arrived yet!",
                    "email": "noorders@test.com",
                    "first_name": "Emma"
                },
                {
                    "message": "It's order #43189",
                    "email": "noorders@test.com",
                    "first_name": "Emma"
                }
            ]
        },
        
        # UC2: Wrong/Missing Item
        {
            "name": "UC2: Wrong Item - Got wrong product",
            "conv_id": "test-wrong-1",
            "expected_agent": "wrong_item",
            "turns": [
                {
                    "message": "Got Zen stickers instead of Focus—kids need them for school!",
                    "email": "lisa@example.com",
                    "first_name": "Lisa"
                }
            ]
        },
        {
            "name": "UC2: Missing Item",
            "conv_id": "test-wrong-2",
            "expected_agent": "wrong_item",
            "turns": [
                {
                    "message": "My package arrived with only 2 of the 3 packs I paid for.",
                    "email": "lisa@example.com",
                    "first_name": "John"
                }
            ]
        },
        {
            "name": "UC2: Multi-turn - Wrong item with store credit",
            "conv_id": "test-wrong-3",
            "expected_agent": "wrong_item",
            "turns": [
                {
                    "message": "Received the pet collar but the tick stickers are missing.",
                    "email": "lisa@example.com",
                    "first_name": "Amy"
                },
                {
                    "message": "It's a missing item, here's the photo: [photo attached]",
                    "email": "lisa@example.com",
                    "first_name": "Amy"
                },
                {
                    "message": "I'll take the store credit, thanks!",
                    "email": "lisa@example.com",
                    "first_name": "Amy"
                }
            ]
        },
        
        # UC3: Product Issue (No Effect)
        {
            "name": "UC3: Product Issue - Not working",
            "conv_id": "test-product-1",
            "expected_agent": "product_issue",
            "turns": [
                {
                    "message": "The SleepyPatch doesn't work. My kid is still not sleeping.",
                    "email": "parent@example.com",
                    "first_name": "Rachel"
                }
            ]
        },
        
        # UC4: Refund Request
        {
            "name": "UC4: Refund - Didn't meet expectations",
            "conv_id": "test-refund-1",
            "expected_agent": "refund",
            "turns": [
                {
                    "message": "I'd like a refund. The patches didn't work for my child.",
                    "email": "refund@example.com",
                    "first_name": "Tom"
                }
            ]
        },
        {
            "name": "UC4: Refund - Changed mind",
            "conv_id": "test-refund-2",
            "expected_agent": "refund",
            "turns": [
                {
                    "message": "I want to cancel my order. I changed my mind.",
                    "email": "refund@example.com",
                    "first_name": "Kate"
                }
            ]
        },
        {
            "name": "UC4: Multi-turn - Refund with store credit",
            "conv_id": "test-refund-3",
            "expected_agent": "refund",
            "turns": [
                {
                    "message": "Can I get a refund? The product didn't work.",
                    "email": "refund@example.com",
                    "first_name": "David"
                },
                {
                    "message": "It didn't meet my expectations, my kid is still having trouble sleeping.",
                    "email": "refund@example.com",
                    "first_name": "David"
                },
                {
                    "message": "Sure, I'll take the store credit with bonus!",
                    "email": "refund@example.com",
                    "first_name": "David"
                }
            ]
        },
        
        # UC5: Order Modification
        {
            "name": "UC5: Order Mod - Cancel accidental order",
            "conv_id": "test-ordermod-1",
            "expected_agent": "order_mod",
            "turns": [
                {
                    "message": "I need to cancel my order. I placed it by accident.",
                    "email": "ordermod@example.com",
                    "first_name": "Chris"
                }
            ]
        },
        {
            "name": "UC5: Order Mod - Update address",
            "conv_id": "test-ordermod-2",
            "expected_agent": "order_mod",
            "turns": [
                {
                    "message": "Can I update my shipping address? I entered the wrong one.",
                    "email": "ordermod@example.com",
                    "first_name": "Nina"
                }
            ]
        },
        
        # UC6: Positive Feedback
        {
            "name": "UC6: Feedback - Happy customer",
            "conv_id": "test-feedback-1",
            "expected_agent": "feedback",
            "turns": [
                {
                    "message": "OMG! The BuzzPatch is AMAZING! My kids love them and no more mosquito bites! Thank you so much!",
                    "email": "happy@example.com",
                    "first_name": "Jessica"
                }
            ]
        },
        {
            "name": "UC6: Multi-turn - Feedback with review",
            "conv_id": "test-feedback-2",
            "expected_agent": "feedback",
            "turns": [
                {
                    "message": "Just wanted to say the FocusPatch is incredible! My son's grades improved!",
                    "email": "happy@example.com",
                    "first_name": "Maria"
                },
                {
                    "message": "Yes! I'd love to leave a review!",
                    "email": "happy@example.com",
                    "first_name": "Maria"
                }
            ]
        },
        
        # UC8: Discount Code
        {
            "name": "UC8: Discount - Promo code not working",
            "conv_id": "test-discount-1",
            "expected_agent": "discount",
            "turns": [
                {
                    "message": "My promo code isn't working at checkout!",
                    "email": "discount@example.com",
                    "first_name": "Peter"
                }
            ]
        },
        {
            "name": "UC8: Discount - Expired code",
            "conv_id": "test-discount-2",
            "expected_agent": "discount",
            "turns": [
                {
                    "message": "I have a discount code that says it's expired. Can you help?",
                    "email": "discount@example.com",
                    "first_name": "Laura"
                }
            ]
        },
    ]
    
    async with httpx.AsyncClient() as client:
        # Test server health
        try:
            resp = await client.get(f"{BASE_URL}/health", timeout=5.0)
            print(f"Server health: {resp.status_code}")
        except Exception as e:
            print(f"ERROR: Server not responding at {BASE_URL}")
            print(f"Local: cd backend && uvicorn api.server:app --host 0.0.0.0 --port 8000")
            print(f"Or set BACKEND_URL env var: export BACKEND_URL=https://your-api.com")
            return
        
        # Run all scenarios
        for scenario in scenarios:
            await test_agent(client, scenario)
            await asyncio.sleep(0.5)  # Brief pause between tests
        
        print(f"\n{'='*80}")
        print(f"All tests completed! Tested {len(scenarios)} scenarios across all agents.")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
