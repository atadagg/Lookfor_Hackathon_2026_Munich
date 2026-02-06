"""Product Issue Test Suite 04: Escalation Scenarios

Tests all deterministic escalation paths in the graph:
- Missing customer email → immediate escalation (check_order node)
- Tool failure → escalation (check_order node)
- Already-escalated thread blocks further agent processing (server-level)
- Escalation sets is_escalated, escalated_at, escalation_summary, workflow_step

ALL tests MUST FAIL against the current ConversationalAgent (except
04.04 which tests server-level behavior).
"""

import pathlib
import sys
import uuid
from datetime import datetime, timezone

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


# ── Test 04.01: Missing email → escalated with correct workflow_step ─────────


@pytest.mark.asyncio
async def test_04_01_missing_email_escalates(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Empty customer_email → graph escalates in check_order node."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    st = data["state"]
    assert st["is_escalated"] is True
    assert st["workflow_step"] == "escalated_missing_email"


# ── Test 04.02: Escalation includes summary with reason ─────────────────────


@pytest.mark.asyncio
async def test_04_02_escalation_has_summary(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Escalation must include escalation_summary with a machine-readable reason."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    st = data["state"]
    assert st["is_escalated"] is True
    summary = st.get("escalation_summary")
    assert summary is not None, "escalation_summary must be set"
    assert "reason" in summary, "escalation_summary must contain 'reason'"


# ── Test 04.03: Escalation message mentions Monica ──────────────────────────


@pytest.mark.asyncio
async def test_04_03_escalation_mentions_monica(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Customer-facing escalation message must mention Monica (Head of CS)."""
    from api.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(email=""))

    msg = (data["state"]["last_assistant_message"] or "").lower()
    assert "monica" in msg, "Escalation must mention Monica"


# ── Test 04.04: Already-escalated thread blocks further replies ──────────────


@pytest.mark.asyncio
async def test_04_04_escalated_thread_blocked(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Once escalated, new messages → agent='escalated', no re-processing."""
    from api.server import app
    from core.state import Message

    conv_id = f"pi-esc-{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First turn: normal response
        t1 = await _post_chat(client, _payload(conv_id=conv_id, message="Patches don't work."))
        assert t1["agent"] == "product_issue"

        # Manually mark as escalated (simulate the graph escalating)
        prev = temp_db.load_state(conv_id) or {}
        prev["is_escalated"] = True
        prev["escalated_at"] = datetime.now(timezone.utc)
        prev.setdefault("internal_data", {})["escalation_summary"] = {
            "reason": "customer_insists",
            "details": {},
        }
        prev.setdefault("messages", []).append(
            Message(role="assistant", content="Looping in Monica."),
        )
        temp_db.save_state(conv_id, prev)

        # Second turn: should be blocked
        t2 = await _post_chat(client, _payload(conv_id=conv_id, message="Hello?"))

    assert t2["agent"] == "escalated"
    assert t2["state"]["status"] == "escalated"
    assert "already escalated" in t2["state"].get("reason", "").lower()


# ── Test 04.05: Escalation timestamp set ─────────────────────────────────────


@pytest.mark.asyncio
async def test_04_05_escalation_timestamp(temp_db, mock_route_to_product_issue, mock_product_issue_llm):
    """Graph must set escalated_at when escalating."""
    from api.server import app

    conv_id = f"pi-ts-{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _post_chat(client, _payload(conv_id=conv_id, email=""))

    assert data["state"]["is_escalated"] is True
    # Verify via checkpointer that escalated_at was persisted
    thread = temp_db.get_thread(conv_id)
    assert thread is not None
    assert thread.is_escalated is True
    assert thread.escalated_at is not None
