"""Product Issue Test Suite 05: Multi-Turn Workflow Complexity

Tests the full multi-turn Product Issue – No Effect flow:

Turn 1: "Patches don't work" → check_order → ask_goal → END
         workflow_step = "awaiting_goal"

Turn 2: customer provides goal → ask_usage → END
         workflow_step = "awaiting_usage"

Turn 3: customer provides usage → route → END
         workflow_step = "routed_usage_fix" | "routed_product_swap"

Turn 4 (still disappointed): → offer store credit → END
         workflow_step = "offered_store_credit"

Turn 5a (accepts): → issue credit + tag "No Effect – Recovered"
         workflow_step = "recovered"

Turn 5b (declines): → cash refund + tag "No Effect – Cash Refund"
         workflow_step = "cash_refunded"

ALL tests MUST FAIL against the current ConversationalAgent.
"""

import pathlib
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _payload(conv_id=None, email="test@example.com", message="Focus patches aren't helping.", **kwargs):
    return {
        "conversation_id": conv_id or f"pi-{uuid.uuid4().hex[:8]}",
        "user_id": "user-test",
        "channel": "email",
        "customer_email": email,
        "first_name": kwargs.get("first_name", "Jane"),
        "last_name": kwargs.get("last_name", "Doe"),
        "shopify_customer_id": kwargs.get("shopify_customer_id", "cust-test"),
        "message": message,
    }


async def _post_chat(client, payload):
    resp = await client.post("/chat", json=payload)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    return resp.json()


async def _get_thread(client, conv_id):
    resp = await client.get(f"/thread/{conv_id}")
    assert resp.status_code == 200
    return resp.json()


# ── Test 05.01: Turn 1 complaint → awaiting_goal ────────────────────────────


@pytest.mark.asyncio
async def test_05_01_turn1_awaiting_goal(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Turn 1: complaint → check order → ask goal → workflow_step='awaiting_goal'."""
    from api.server import app

    conv_id = f"pi-t1-{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(conv_id=conv_id, message="Sleep patches aren't working."),
        )

    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 05.02: Turn 2 goal provided → awaiting_usage ───────────────────────


@pytest.mark.asyncio
async def test_05_02_turn2_goal_then_awaiting_usage(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Turn 2: customer shares goal → workflow_step='awaiting_usage'."""
    from api.server import app

    conv_id = f"pi-t2-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Sleep patches aren't working."})
        assert t1["state"]["workflow_step"] == "awaiting_goal"

        t2 = await _post_chat(
            client,
            {**base, "message": "The goal is helping her fall asleep faster."},
        )

    assert t2["state"]["workflow_step"] == "awaiting_usage"


# ── Test 05.03: Turn 3 usage off → routed_usage_fix ─────────────────────────


@pytest.mark.asyncio
async def test_05_03_turn3_usage_off_routes_to_usage_fix(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Turn 3: usage is wrong → share correct usage, ask to try 3 nights."""
    from api.server import app

    conv_id = f"pi-t3-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Sleep patches aren't working."})
        await _post_chat(
            client,
            {**base, "message": "Trying to help her fall asleep."},
        )
        t3 = await _post_chat(
            client,
            {**base, "message": "She puts 1 patch on right before bed, tried it 1 night."},
        )

    assert t3["state"]["workflow_step"] == "routed_usage_fix"
    msg = (t3["state"]["last_assistant_message"] or "").lower()
    assert "3 night" in msg or "three night" in msg, "Must ask to try for 3 nights"


# ── Test 05.04: Turn 3 product mismatch → routed_product_swap ────────────────


@pytest.mark.asyncio
async def test_05_04_product_mismatch_routes_to_swap(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """When the product doesn't match the goal → offer better-fit product."""
    from api.server import app

    conv_id = f"pi-swap-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(
            client,
            {**base, "message": "BuzzPatch isn't helping my kid focus in school."},
        )
        await _post_chat(
            client,
            {**base, "message": "Goal is focus and concentration during classes."},
        )
        t3 = await _post_chat(
            client,
            {**base, "message": "1 sticker in the morning, every school day for 2 weeks."},
        )

    assert t3["state"]["workflow_step"] == "routed_product_swap"
    # product_recommendations tool should have been called
    traces = t3["state"]["internal_data"]["tool_traces"]
    rec_calls = [t for t in traces if t["name"] == "shopify_get_product_recommendations"]
    assert len(rec_calls) >= 1, "Must call shopify_get_product_recommendations for product swap"


# ── Test 05.05: Still disappointed → offered_store_credit ────────────────────


@pytest.mark.asyncio
async def test_05_05_disappointed_after_fix_offers_credit(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """After guidance, if still disappointed → offer store credit with 10% bonus."""
    from api.server import app

    conv_id = f"pi-credit-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Sleep patches not working."})
        await _post_chat(client, {**base, "message": "Goal: falling asleep."})
        await _post_chat(client, {**base, "message": "1 patch at bedtime, 1 night."})
        t4 = await _post_chat(
            client,
            {**base, "message": "I tried that and it still didn't help. I want my money back."},
        )

    assert t4["state"]["workflow_step"] == "offered_store_credit"
    msg = (t4["state"]["last_assistant_message"] or "").lower()
    assert "store credit" in msg or "credit" in msg, "Must offer store credit"
    assert "10%" in msg or "bonus" in msg, "Must mention 10% bonus"


# ── Test 05.06: Accept store credit → recovered + tag ────────────────────────


@pytest.mark.asyncio
async def test_05_06_accept_credit_recovered_and_tagged(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Customer accepts store credit → issue it, tag 'No Effect – Recovered'."""
    from api.server import app

    conv_id = f"pi-recover-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Sleep patches not working."})
        await _post_chat(client, {**base, "message": "Goal: falling asleep."})
        await _post_chat(client, {**base, "message": "1 patch at bedtime, 1 night."})
        await _post_chat(client, {**base, "message": "Tried again, still nothing. Refund?"})
        t5 = await _post_chat(
            client,
            {**base, "message": "OK, store credit sounds good."},
        )

    assert t5["state"]["workflow_step"] == "recovered"
    traces = t5["state"]["internal_data"]["tool_traces"]

    # Must have called shopify_create_store_credit
    credit_calls = [t for t in traces if t["name"] == "shopify_create_store_credit"]
    assert len(credit_calls) >= 1, "Must call shopify_create_store_credit"

    # Must have tagged "No Effect – Recovered"
    tag_calls = [t for t in traces if t["name"] == "shopify_add_tags"]
    assert len(tag_calls) >= 1, "Must call shopify_add_tags"
    tag_args = tag_calls[-1]["inputs"]
    assert "No Effect – Recovered" in tag_args.get("tags", [])


# ── Test 05.07: Decline store credit → cash_refunded + tag ──────────────────


@pytest.mark.asyncio
async def test_05_07_decline_credit_cash_refund_and_tagged(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Customer declines store credit → cash refund, tag 'No Effect – Cash Refund'."""
    from api.server import app

    conv_id = f"pi-refund-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Sleep patches not working."})
        await _post_chat(client, {**base, "message": "Goal: falling asleep."})
        await _post_chat(client, {**base, "message": "1 patch at bedtime, 1 night."})
        await _post_chat(client, {**base, "message": "Tried again, still nothing. Refund?"})
        t5 = await _post_chat(
            client,
            {**base, "message": "No thanks, I'd rather have cash back."},
        )

    assert t5["state"]["workflow_step"] == "cash_refunded"
    traces = t5["state"]["internal_data"]["tool_traces"]

    # Must have called shopify_refund_order with ORIGINAL_PAYMENT_METHODS
    refund_calls = [t for t in traces if t["name"] == "shopify_refund_order"]
    assert len(refund_calls) >= 1, "Must call shopify_refund_order"
    assert refund_calls[-1]["inputs"].get("refundMethod") == "ORIGINAL_PAYMENT_METHODS"

    # Must have tagged "No Effect – Cash Refund"
    tag_calls = [t for t in traces if t["name"] == "shopify_add_tags"]
    assert len(tag_calls) >= 1, "Must call shopify_add_tags"
    tag_args = tag_calls[-1]["inputs"]
    assert "No Effect – Cash Refund" in tag_args.get("tags", [])


# ── Test 05.08: Duplicate message detection ──────────────────────────────────


@pytest.mark.asyncio
async def test_05_08_duplicate_message_detected(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Sending identical message twice → 'duplicate' agent, no re-processing."""
    from api.server import app

    conv_id = f"pi-dup-{uuid.uuid4().hex[:8]}"
    payload = _payload(conv_id=conv_id, message="Focus patches aren't helping.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await _post_chat(client, payload)
        second = await _post_chat(client, payload)

    assert first["agent"] == "product_issue"
    assert second["agent"] == "duplicate"


# ── Test 05.09: State consistency across turns ───────────────────────────────


@pytest.mark.asyncio
async def test_05_09_state_consistency(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """conversation_id, agent, current_workflow must be consistent across turns."""
    from api.server import app

    conv_id = f"pi-consist-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t1 = await _post_chat(client, {**base, "message": "Patches don't work."})
        t2 = await _post_chat(client, {**base, "message": "Goal is sleep."})
        t3 = await _post_chat(client, {**base, "message": "1 patch, 1 night."})

    for t in [t1, t2, t3]:
        assert t["conversation_id"] == conv_id
        assert t["agent"] == "product_issue"
        assert t["state"]["current_workflow"] == "product_issue"

    # Workflow must have progressed through steps
    assert t1["state"]["workflow_step"] == "awaiting_goal"
    assert t2["state"]["workflow_step"] == "awaiting_usage"
    assert t3["state"]["workflow_step"] in ("routed_usage_fix", "routed_product_swap")


# ── Test 05.10: Messages preserved in thread ────────────────────────────────


@pytest.mark.asyncio
async def test_05_10_messages_preserved(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """All user + assistant messages must be preserved in thread history."""
    from api.server import app

    conv_id = f"pi-hist-{uuid.uuid4().hex[:8]}"
    base = _payload(conv_id=conv_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _post_chat(client, {**base, "message": "Patches don't work."})
        await _post_chat(client, {**base, "message": "Goal is better sleep."})
        await _post_chat(client, {**base, "message": "1 patch, bedtime, 1 night."})

        thread = await _get_thread(client, conv_id)

    assert len(thread["messages"]) >= 6  # 3 user + 3 assistant
    user_msgs = [m["content"] for m in thread["messages"] if m["role"] == "user"]
    assert "don't work" in user_msgs[0].lower()
    assert "goal" in user_msgs[1].lower() or "sleep" in user_msgs[1].lower()
