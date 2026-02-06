"""Agent for Refund Request – Standard (UC4).

Routes by reason: expectations, shipping delay, damaged/wrong, changed mind.
"""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_GET_CUSTOMER_ORDERS,
    SCHEMA_GET_ORDER_DETAILS,
    SCHEMA_ADD_TAGS,
    SCHEMA_CANCEL_ORDER,
    SCHEMA_REFUND_ORDER,
    SCHEMA_CREATE_STORE_CREDIT,
    SCHEMA_CREATE_RETURN,
)


class RefundAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="refund")
        self._workflow_name = "refund"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_TAGS,
            SCHEMA_CANCEL_ORDER,
            SCHEMA_REFUND_ORDER,
            SCHEMA_CREATE_STORE_CREDIT,
            SCHEMA_CREATE_RETURN,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_tags", "shopify_cancel_order",
            "shopify_refund_order", "shopify_create_store_credit",
            "shopify_create_return",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly support specialist for NATPAT.

            You are handling a **Refund Request**. Follow STRICTLY:

            STEP 1 – CHECK ORDER (shopify_get_customer_orders by email, then shopify_get_order_details)
            STEP 2 – ASK FOR REASON

            STEP 3 – ROUTE BY REASON:

            A) PRODUCT DIDN'T MEET EXPECTATIONS:
               1. Ask one follow-up to identify cause.
               2. Share correct usage tip.
               3. Offer product swap.
               4. If still wants refund: store credit 10% bonus first (shopify_create_store_credit).
               5. If declined: cash refund (shopify_refund_order, ORIGINAL_PAYMENT_METHODS).

            B) SHIPPING DELAY:
               Check today's day (from CUSTOMER CONTEXT).
               - Mon-Tue: ask to wait until Friday. If not delivered, offer free replacement.
               - Wed-Fri: ask to wait until early next week.
               - If REFUSE to wait: offer free replacement, then escalate.
                 Tell customer: "Hey, I'm looping in Monica, who is our Head of CS, she'll take it from there."

            C) DAMAGED OR WRONG ITEM:
               1. Offer free replacement OR store credit.
               2. Replacement → escalate for processing.
               3. Store credit → issue with bonus (shopify_create_store_credit).

            D) CHANGED MIND:
               1. If unfulfilled → cancel (shopify_cancel_order, reason=CUSTOMER). Tag it.
               2. If fulfilled → store credit with bonus, then cash refund if declined.

            Use shopify_add_tags to tag orders (id = order GID).

            STYLE: 2-4 sentences, warm. Use first name. ONE step at a time.
        """)

__all__ = ["RefundAgent"]
