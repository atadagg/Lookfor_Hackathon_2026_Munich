"""Product Issue Test Suite 02: Edge Cases

Tests that the graph handles missing/malformed data deterministically.

Key contracts:
- Missing customer email → immediate escalation (can't look up order).
- Missing name fields → still works (name is optional).
- Empty/long/unicode messages → no crash, workflow_step still set.
- Various complaint phrasings → all reach awaiting_goal.

ALL of these tests MUST FAIL against the current ConversationalAgent
(which doesn't check email deterministically, doesn't set workflow_step).
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


# ── Test 02.01: Missing email → immediate escalation ────────────────────────


@pytest.mark.asyncio
async def test_02_01_missing_email_escalates(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Empty customer_email → graph must escalate (order lookup impossible)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    assert data["state"]["is_escalated"] is True
    assert data["state"]["workflow_step"].startswith("escalated")
    msg = (data["state"]["last_assistant_message"] or "").lower()
    assert "monica" in msg or "looping" in msg


# ── Test 02.02: Missing first_name → still reaches awaiting_goal ────────────


@pytest.mark.asyncio
async def test_02_02_missing_first_name_still_works(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Missing first_name should not crash; workflow proceeds to awaiting_goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(first_name=""))

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"
    assert data["state"]["is_escalated"] is False


# ── Test 02.03: Missing last_name → still reaches awaiting_goal ─────────────


@pytest.mark.asyncio
async def test_02_03_missing_last_name_still_works(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Missing last_name should not crash; workflow proceeds to awaiting_goal."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(last_name=""))

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 02.04: Empty message → no crash, still checks order ────────────────


@pytest.mark.asyncio
async def test_02_04_empty_message_no_crash(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Empty message body should not crash. Graph still checks order."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message=""))

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 02.05: Very long message → no crash ────────────────────────────────


@pytest.mark.asyncio
async def test_02_05_long_message_no_crash(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """10 KB message should not crash; workflow proceeds normally."""
    from api.server import app

    long_msg = "Patches don't work at all. " * 400
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(message=long_msg))

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 02.06: Unicode/emoji → no crash ────────────────────────────────────


@pytest.mark.asyncio
async def test_02_06_unicode_no_crash(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Unicode / emoji should not break the graph."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(message="Patches aren't working 😤 Ça ne marche pas!"),
        )

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 02.07: Email with plus/subdomain → works ───────────────────────────


@pytest.mark.asyncio
async def test_02_07_email_plus_sign_works(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Email user+tag@mail.example.com should work (mock returns order)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(email="user+tag@mail.example.com", message="No effect."),
        )

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"


# ── Test 02.08: Missing shopify_customer_id → no crash ──────────────────────


@pytest.mark.asyncio
async def test_02_08_missing_shopify_id_no_crash(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Missing shopify_customer_id should not crash; order lookup uses email."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(
            client,
            _payload(shopify_customer_id="", message="Product isn't working."),
        )

    assert data["agent"] == "product_issue"
    assert data["state"]["workflow_step"] == "awaiting_goal"
