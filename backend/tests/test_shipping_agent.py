import asyncio
import pathlib
import sys
from datetime import date, timedelta

import pytest

# Ensure the project root is on sys.path so imports work when running tests directly.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.wismo import graph as shipping_graph
from agents.wismo.graph import node_check_order_status, node_decide_wait_or_escalate
from agents.wismo.graph import WismoAgent
from core.state import AgentState, Message
from schemas.internal import ToolResponse


def _run(coro):
    """Helper to execute async callables in sync tests."""

    return asyncio.run(coro)


@pytest.mark.asyncio
async def test_check_order_status_records_tool_trace_and_internal_fields(monkeypatch):
    """Successful tool call populates internal fields and tool_traces."""

    async def fake_get_order_status(*, email: str) -> ToolResponse:
        assert email == "test@example.com"
        return ToolResponse(
            success=True,
            data={
                "order_id": "#1001",
                "status": "IN_TRANSIT",
                "tracking_url": "https://tracking.example.com/demo123",
            },
        )

    monkeypatch.setattr(
        shipping_graph, "get_order_status", fake_get_order_status, raising=True
    )

    state: AgentState = {
        "messages": [Message(role="user", content="Where is my order?")],
        "customer_info": {"email": "test@example.com"},
    }

    new_state = await node_check_order_status(state)

    internal = new_state.get("internal_data") or {}
    assert internal.get("order_id") == "#1001"
    assert internal.get("order_status") == "IN_TRANSIT"
    assert internal.get("tracking_url") == "https://tracking.example.com/demo123"

    traces = internal.get("tool_traces")
    assert isinstance(traces, list)
    assert len(traces) == 1
    trace = traces[0]
    assert trace["name"] == "get_order_status"
    assert trace["inputs"] == {"email": "test@example.com"}
    assert trace["output"]["success"] is True


@pytest.mark.asyncio
async def test_check_order_status_escalates_on_tool_failure(monkeypatch):
    """Tool failure should escalate with a clear summary and message."""

    async def failing_get_order_status(*, email: str) -> ToolResponse:
        return ToolResponse(success=False, error="boom")

    monkeypatch.setattr(
        shipping_graph, "get_order_status", failing_get_order_status, raising=True
    )

    state: AgentState = {
        "messages": [Message(role="user", content="Where is my order?")],
        "customer_info": {"email": "test@example.com"},
    }

    new_state = await node_check_order_status(state)

    assert new_state.get("is_escalated") is True
    assert new_state.get("workflow_step") == "escalated_tool_error"

    internal = new_state.get("internal_data") or {}
    summary = internal.get("escalation_summary") or {}
    assert summary.get("reason") == "order_lookup_failed"
    assert summary.get("details", {}).get("error") == "boom"

    # Last assistant message should mention Monica taking over.
    messages = new_state.get("messages") or []
    assert messages, "Expected at least one assistant message after escalation"
    last = messages[-1]
    assert last["role"] == "assistant"
    assert "Monica" in last["content"]


class _FixedDate(date):
    """Helper date subclass to control today() in tests."""

    @classmethod
    def today(cls) -> date:  # type: ignore[override]
        # Wednesday, Jan 3 2024 (weekday = 2)
        return date(2024, 1, 3)


@pytest.mark.asyncio
async def test_decide_wait_or_escalate_sets_promise_for_in_transit(monkeypatch):
    """IN_TRANSIT orders get a wait promise and explanatory message."""

    # Patch the date used inside the shipping graph module.
    monkeypatch.setattr(shipping_graph, "date", _FixedDate, raising=True)

    state: AgentState = {
        "messages": [Message(role="user", content="Where is my order?")],
        "internal_data": {
            "order_status": "IN_TRANSIT",
            "order_id": "#1001",
            "tracking_url": "https://tracking.example.com/demo123",
        },
    }

    new_state = await node_decide_wait_or_escalate(state)

    internal = new_state.get("internal_data") or {}
    # Wednesday -> promise until Friday of the same week.
    assert internal.get("wait_promise_until") == "2024-01-05"
    assert internal.get("decided_action") == "wait_promise"
    assert internal.get("promise_day_label") == "Friday"
    assert new_state.get("workflow_step") == "action_decided"


@pytest.mark.asyncio
async def test_decide_wait_or_escalate_escalates_after_missed_promise(monkeypatch):
    """If the wait promise has passed and not delivered, we escalate."""

    today = date(2024, 1, 10)

    class _LateDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return today

    monkeypatch.setattr(shipping_graph, "date", _LateDate, raising=True)

    promised = today - timedelta(days=1)

    state: AgentState = {
        "messages": [Message(role="user", content="Any update?")],
        "internal_data": {
            "order_status": "IN_TRANSIT",
            "order_id": "#1001",
            "wait_promise_until": promised.isoformat(),
        },
    }

    new_state = await node_decide_wait_or_escalate(state)

    assert new_state.get("is_escalated") is True
    assert new_state.get("workflow_step") == "escalated_missed_promise"

    internal = new_state.get("internal_data") or {}
    summary = internal.get("escalation_summary") or {}
    assert summary.get("reason") == "wismo_missed_promise"
    assert summary.get("details", {}).get("order_id") == "#1001"


@pytest.mark.asyncio
async def test_wismo_agent_sets_current_workflow_and_delegates(monkeypatch):
    """WismoAgent should tag the workflow and delegate to the graph app."""

    class DummyApp:
        def __init__(self) -> None:
            self.invoked_with = None

        async def ainvoke(self, state: AgentState) -> AgentState:  # type: ignore[override]
            self.invoked_with = state
            # Tag that we went through the dummy app.
            state["through_dummy_app"] = True
            return state

    dummy_app = DummyApp()

    # Ensure WismoAgent.build_graph returns our DummyApp.
    monkeypatch.setattr(
        "agents.wismo.graph.build_wismo_graph", lambda: dummy_app, raising=True
    )

    agent = WismoAgent()
    state: AgentState = {
        "messages": [Message(role="user", content="Where is my order?")],
    }

    new_state = await agent.handle(state)

    # WismoAgent should tag the workflow and call into the app.
    assert new_state.get("current_workflow") == "shipping"
    assert new_state.get("through_dummy_app") is True
