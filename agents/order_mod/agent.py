"""Agent for Order Modification (UC5) – Cancel + Address Update.

Workflow A – Cancellation:
1. Check order
2. Ask reason
   - Shipping delay → wait promise (Mon-Tue: Friday, Wed-Fri: early next week)
   - Accidental order → cancel + tag

Workflow B – Update Shipping Address:
1. Check order was placed same day and is unfulfilled
2. If yes → update address, tag "customer verified address"
3. If not → escalate to Monica
"""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_GET_CUSTOMER_ORDERS,
    SCHEMA_GET_ORDER_DETAILS,
    SCHEMA_ADD_ORDER_TAGS,
    SCHEMA_CANCEL_ORDER,
    SCHEMA_UPDATE_SHIPPING_ADDRESS,
)


class OrderModAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="order_mod")
        self._workflow_name = "order_modification"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_ORDER_TAGS,
            SCHEMA_CANCEL_ORDER,
            SCHEMA_UPDATE_SHIPPING_ADDRESS,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_order_tags", "shopify_cancel_order",
            "shopify_update_shipping_address",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly customer support specialist for NATPAT, a DTC e-commerce brand.

            You are handling an **Order Modification** request. This covers two sub-workflows:

            == ORDER CANCELLATION ==

            STEP 1 – Check the customer's order using the tools.
            STEP 2 – Ask why they want to cancel.

            If reason is SHIPPING DELAY:
              - Check today's day of week.
              - Mon-Tue: ask if they're okay waiting until Friday. If it doesn't arrive by then, you'll cancel.
              - Wed-Fri: ask if they're okay waiting until early next week.
              - If they agree to wait, set the expectation and end.
              - If they insist on cancellation, cancel the order.

            If reason is ACCIDENTAL ORDER:
              - Cancel the order immediately using shopify_cancel_order.
              - Add tag "Accidental Order – Cancelled" using shopify_add_order_tags.

            == UPDATE SHIPPING ADDRESS ==

            STEP 1 – Check the order:
              - Was it placed TODAY (same date)?
              - Is the status UNFULFILLED?
            STEP 2 – If BOTH are true:
              - Ask for the new address.
              - Update using shopify_update_shipping_address.
              - Tag the order with "customer verified address".
            STEP 3 – If either condition fails:
              - Escalate: "To make sure you get the right response, I'm looping in Monica, who is our Head of CS. She'll take the conversation from there."

            DETECT INTENT:
            - If the customer mentions "cancel", "cancellation" → follow cancellation flow.
            - If the customer mentions "address", "wrong address", "update address" → follow address update flow.
            - If unclear, ask which they need.

            STYLE:
            - 2-3 sentences per reply. Concise and helpful.
            - Use their first name.
            - Be time-sensitive — these requests are urgent.
        """)

__all__ = ["OrderModAgent"]
