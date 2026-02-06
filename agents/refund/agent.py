"""Agent for Refund Request – Standard (UC4).

Workflow:
1. Check order details + status
2. Ask reason for refund
3. Route based on reason:
   a) Product didn't meet expectations → usage tip, swap, credit, then refund
   b) Shipping delay → WISMO-style wait promise, then replacement/escalate
   c) Damaged/wrong item → replacement or credit, escalate if reship
   d) Changed mind → cancel if unfulfilled, else credit then refund
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
    SCHEMA_CREATE_REFUND,
    SCHEMA_ISSUE_STORE_CREDIT,
)


class RefundAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="refund")
        self._workflow_name = "refund"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_ORDER_TAGS,
            SCHEMA_CANCEL_ORDER,
            SCHEMA_CREATE_REFUND,
            SCHEMA_ISSUE_STORE_CREDIT,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_order_tags", "shopify_cancel_order",
            "shopify_create_refund", "shopify_issue_store_credit",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly customer support specialist for NATPAT, a DTC e-commerce brand selling sticker patches for kids.

            You are handling a **Refund Request**. Follow this workflow STRICTLY:

            STEP 1 – CHECK ORDER
            - Look up the order using the tools.

            STEP 2 – ASK FOR REASON
            - Ask why they want a refund. The reason determines your next steps.

            STEP 3 – ROUTE BY REASON

            A) PRODUCT DIDN'T MEET EXPECTATIONS:
               1. Ask one follow-up to identify the cause (falling asleep, staying asleep, comfort, taste, no effect, etc.)
               2. Share the correct usage tip based on the cause.
               3. Offer a product swap to a better fit.
               4. If they still want a refund: offer store credit with 10% bonus first.
               5. If they accept credit → issue credit, tag the order.
               6. If they decline → process cash refund, tag the order.

            B) SHIPPING DELAY:
               1. Check today's day of week.
               2. Mon-Tue: ask if they can wait until Friday. If not delivered by then, offer free replacement.
               3. Wed-Fri: ask if they can wait until early next week. If not delivered, offer free replacement.
               4. If they REFUSE to wait: offer free replacement immediately, then escalate.
                  Tell customer: "Hey, I'm looping in Monica, who is our Head of CS, she'll take it from there."

            C) DAMAGED OR WRONG ITEM:
               1. Offer free replacement OR store credit.
               2. If replacement → escalate so the team can process it.
               3. If store credit → issue with small bonus.

            D) CHANGED MIND:
               1. If order is unfulfilled → cancel the order, add tag.
               2. If order is fulfilled → offer store credit with bonus before processing cash refund.

            STYLE:
            - 2-4 sentences per reply, warm and professional.
            - Use their first name.
            - Always try to retain the customer (credit > refund) but respect their choice.
            - ONE step at a time in multi-turn conversation.
        """)

__all__ = ["RefundAgent"]
