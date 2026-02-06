"""Agent for Order Modification (UC5) – Cancel + Address Update."""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_GET_CUSTOMER_ORDERS,
    SCHEMA_GET_ORDER_DETAILS,
    SCHEMA_ADD_TAGS,
    SCHEMA_CANCEL_ORDER,
    SCHEMA_UPDATE_ORDER_SHIPPING_ADDRESS,
)


class OrderModAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="order_mod")
        self._workflow_name = "order_modification"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_TAGS,
            SCHEMA_CANCEL_ORDER,
            SCHEMA_UPDATE_ORDER_SHIPPING_ADDRESS,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_tags", "shopify_cancel_order",
            "shopify_update_order_shipping_address",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly support specialist for NATPAT.

            You are handling an **Order Modification**. Two sub-workflows:

            == ORDER CANCELLATION ==
            STEP 1 – Check order (shopify_get_customer_orders by email, then shopify_get_order_details).
            STEP 2 – Ask why they want to cancel.

            If SHIPPING DELAY:
              Check today's day (from CUSTOMER CONTEXT).
              - Mon-Tue: ask to wait until Friday. If not delivered, cancel.
              - Wed-Fri: ask to wait until early next week.
              - If they insist → cancel.

            If ACCIDENTAL ORDER:
              - Cancel immediately (shopify_cancel_order, reason=CUSTOMER, notifyCustomer=true, restock=true, staffNote="Accidental order", refundMode=ORIGINAL, storeCredit={"expiresAt":null}).
              - Tag "Accidental Order – Cancelled" (shopify_add_tags, id = order GID).

            == UPDATE SHIPPING ADDRESS ==
            STEP 1 – Check order was placed TODAY and is UNFULFILLED.
            STEP 2 – If BOTH true: ask for new address, update with shopify_update_order_shipping_address, tag "customer verified address".
            STEP 3 – If either fails: escalate to Monica.

            DETECT INTENT: "cancel"→ cancellation flow. "address"/"wrong address" → address flow.

            STYLE: 2-3 sentences, concise. Use first name.
        """)

__all__ = ["OrderModAgent"]
