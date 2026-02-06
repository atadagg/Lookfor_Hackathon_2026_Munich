"""Reusable LLM-driven agent with OpenAI function calling.

Most non-WISMO agents share the same execution pattern:

1. Feed system prompt + conversation history to GPT-4o-mini.
2. If the LLM requests a tool call, execute it, feed the result back,
   and let the LLM continue.
3. Repeat until the LLM produces a text response or calls
   ``escalate_to_human``.
4. Return the updated ``AgentState``.

This base class implements that loop.  Concrete agents only need to
supply a system prompt, tool schemas, and tool executor mappings.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional

from core.base_agent import BaseAgent
from core.llm import get_async_openai_client
from core.state import AgentState, Message


# ── Built-in escalation tool (available to every agent) ────────────

ESCALATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "escalate_to_human",
        "description": (
            "Escalate the conversation to Monica, the Head of CS. "
            "Use this when the workflow requires human intervention, "
            "when you cannot safely proceed, or when the customer "
            "explicitly insists on speaking to a person."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Machine-readable reason (e.g. 'reship_needed', 'customer_insists').",
                },
                "customer_message": {
                    "type": "string",
                    "description": "The message to send to the customer about the escalation.",
                },
                "internal_summary": {
                    "type": "string",
                    "description": "A short structured summary for the support team.",
                },
            },
            "required": ["reason", "customer_message"],
        },
    },
}


# ── The base class ─────────────────────────────────────────────────


ToolExecutor = Callable[..., Coroutine[Any, Any, dict]]


class ConversationalAgent(BaseAgent):
    """LLM-driven agent using OpenAI function calling.

    Subclasses **must** set:
    - ``_system_prompt``  (str)
    - ``_tool_schemas``   (list of OpenAI tool dicts — may be empty)
    - ``_tool_executors`` (dict mapping function name → async callable)

    The executors should return plain ``dict`` (matching the hackathon
    ``ToolResponse`` shape).
    """

    _system_prompt: str = ""
    _tool_schemas: List[dict] = []
    _tool_executors: Dict[str, ToolExecutor] = {}
    _max_rounds: int = 6
    _model: str = "gpt-4o-mini"
    _temperature: float = 0.3
    _workflow_name: str = ""

    def build_graph(self) -> Any:
        return None  # conversational agents don't use LangGraph

    async def handle(self, state: AgentState) -> AgentState:
        """Run the conversational LLM loop for one turn."""

        # ---- prepare state copies ----------------------------------
        internal: Dict[str, Any] = dict(state.get("internal_data") or {})
        internal.setdefault("tool_traces", [])
        messages_history: List[Message] = list(state.get("messages") or [])
        customer = state.get("customer_info") or {}

        # ---- build OpenAI messages ---------------------------------
        # Inject customer context into the system prompt
        customer_ctx = self._build_customer_context(customer, state)
        full_system = self._system_prompt
        if customer_ctx:
            full_system += "\n\nCUSTOMER CONTEXT:\n" + customer_ctx

        openai_msgs: List[dict] = [{"role": "system", "content": full_system}]
        for m in messages_history:
            openai_msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        # ---- tool schemas (add built-in escalation) ----------------
        all_schemas = list(self._tool_schemas) + [ESCALATE_SCHEMA]
        all_executors = dict(self._tool_executors)

        # ---- LLM loop with function calling ------------------------
        client = get_async_openai_client()

        for _round in range(self._max_rounds):
            kwargs: Dict[str, Any] = {
                "model": self._model,
                "temperature": self._temperature,
                "max_tokens": 512,
                "messages": openai_msgs,
            }
            if all_schemas:
                kwargs["tools"] = all_schemas

            try:
                resp = await client.chat.completions.create(**kwargs)
            except Exception as exc:
                # LLM failure → escalate gracefully
                return self._escalate_state(
                    state, messages_history, internal,
                    reason="llm_error",
                    customer_msg=(
                        "I ran into a technical issue. To make sure you get "
                        "the right support, I'm looping in Monica, our Head "
                        "of CS, who will take it from here."
                    ),
                    summary="LLM call failed: %s" % exc,
                )

            choice = resp.choices[0]
            assistant_msg = choice.message

            # -- Case A: tool calls ----------------------------------
            if assistant_msg.tool_calls:
                # Append the assistant message with tool_calls to the
                # OpenAI conversation so it can be referenced.
                openai_msgs.append(assistant_msg.model_dump(exclude_none=True))

                for tc in assistant_msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}

                    # -- Escalation tool (special) -------------------
                    if fn_name == "escalate_to_human":
                        return self._escalate_state(
                            state, messages_history, internal,
                            reason=fn_args.get("reason", "agent_escalation"),
                            customer_msg=fn_args.get(
                                "customer_message",
                                "To make sure you get the right support, "
                                "I'm looping in Monica, our Head of CS, "
                                "who will take it from here.",
                            ),
                            summary=fn_args.get("internal_summary", ""),
                        )

                    # -- Regular tool --------------------------------
                    executor = all_executors.get(fn_name)
                    if executor:
                        try:
                            result = await executor(**fn_args)
                        except Exception as exc:
                            result = {"success": False, "error": str(exc)}
                    else:
                        result = {"success": False, "error": "Unknown tool: %s" % fn_name}

                    # Record trace
                    internal["tool_traces"].append({
                        "name": fn_name,
                        "inputs": fn_args,
                        "output": result,
                    })

                    # Feed result back to the LLM
                    openai_msgs.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })

                # Continue the loop → LLM will process tool results
                continue

            # -- Case B: text response (we're done) ------------------
            text = (assistant_msg.content or "").strip()
            if text:
                messages_history.append(Message(role="assistant", content=text))
            break

        # ---- finalise state ----------------------------------------
        state["messages"] = messages_history
        state["internal_data"] = internal
        if self._workflow_name:
            state["current_workflow"] = self._workflow_name
        return state

    # ── helpers ─────────────────────────────────────────────────────

    def _build_customer_context(self, customer: dict, state: AgentState) -> str:
        parts: List[str] = []
        if customer.get("first_name"):
            parts.append("First name: %s" % customer["first_name"])
        if customer.get("last_name"):
            parts.append("Last name: %s" % customer["last_name"])
        if customer.get("email"):
            parts.append("Email: %s" % customer["email"])
        if customer.get("shopify_customer_id"):
            parts.append("Shopify Customer ID: %s" % customer["shopify_customer_id"])
        return "\n".join(parts)

    @staticmethod
    def _escalate_state(
        state: AgentState,
        messages_history: List[Message],
        internal: Dict[str, Any],
        *,
        reason: str,
        customer_msg: str,
        summary: str = "",
    ) -> AgentState:
        """Set escalation flags and return the state."""
        state["is_escalated"] = True
        state["escalated_at"] = datetime.utcnow()
        internal["escalation_summary"] = {
            "reason": reason,
            "details": {"internal_summary": summary} if summary else {},
        }
        messages_history.append(Message(role="assistant", content=customer_msg))
        state["messages"] = messages_history
        state["internal_data"] = internal
        state["workflow_step"] = "escalated"
        return state
