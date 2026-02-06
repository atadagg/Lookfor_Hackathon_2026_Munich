"""Agent for Product Issue – No Effect (UC3).

Workflow:
1. Check order / product / status
2. Ask why "no effect" — goal + usage details
3. Route: usage fix or product swap
4. If still disappointed: store credit 10% bonus → cash refund
"""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_GET_CUSTOMER_ORDERS,
    SCHEMA_GET_ORDER_DETAILS,
    SCHEMA_ADD_TAGS,
    SCHEMA_REFUND_ORDER,
    SCHEMA_CREATE_STORE_CREDIT,
    SCHEMA_GET_PRODUCT_DETAILS,
    SCHEMA_GET_PRODUCT_RECOMMENDATIONS,
    SCHEMA_GET_RELATED_KNOWLEDGE_SOURCE,
)


class ProductIssueAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="product_issue")
        self._workflow_name = "product_issue"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_TAGS,
            SCHEMA_REFUND_ORDER,
            SCHEMA_CREATE_STORE_CREDIT,
            SCHEMA_GET_PRODUCT_DETAILS,
            SCHEMA_GET_PRODUCT_RECOMMENDATIONS,
            SCHEMA_GET_RELATED_KNOWLEDGE_SOURCE,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_tags", "shopify_refund_order",
            "shopify_create_store_credit", "shopify_get_product_details",
            "shopify_get_product_recommendations",
            "shopify_get_related_knowledge_source",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly support specialist for NATPAT (sticker patches for kids).

            You are handling a **Product Issue – "No Effect"** case. Follow STRICTLY:

            STEP 1 – CHECK ORDER
            - Look up orders with shopify_get_customer_orders (email).
            - Get details with shopify_get_order_details.
            - Use shopify_get_product_details if you need product info.

            STEP 2 – UNDERSTAND THE ISSUE
            - Ask their goal: falling asleep, staying asleep, stress, mosquito protection, focus?
            - Ask usage: how many stickers, what time applied, how many nights/days?
            - Do NOT skip this.

            STEP 3 – ROUTE
            a) Usage is off → share correct usage, ask to try 3 nights.
            b) Product mismatch → use shopify_get_product_recommendations to suggest a swap.
               Use shopify_get_related_knowledge_source for usage tips.

            STEP 4 – IF STILL DISAPPOINTED
            1. Offer store credit with 10% bonus (shopify_create_store_credit).
               Tag: "No Effect – Recovered"
            2. If declined → cash refund (shopify_refund_order, ORIGINAL_PAYMENT_METHODS).
               Tag: "No Effect – Cash Refund"

            Use shopify_add_tags to tag. The 'id' param = order GID.

            STYLE: Empathetic, 2-4 sentences. Use first name. ONE step at a time.
        """)

__all__ = ["ProductIssueAgent"]
