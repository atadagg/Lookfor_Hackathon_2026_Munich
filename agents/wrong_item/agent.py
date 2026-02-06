"""Agent for Wrong / Missing Item in Parcel (UC2).

Workflow:
1. Check order + items
2. Ask what happened (missing vs wrong)
3. Request photos
4. Offer reship first → store credit → cash refund
5. Close loop (reship escalates, credit confirmed, refund confirmed)
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
    SCHEMA_CREATE_RETURN,
    SCHEMA_GET_PRODUCT_DETAILS,
)


class WrongItemAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="wrong_item")
        self._workflow_name = "wrong_item"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_ORDER_DETAILS,
            SCHEMA_ADD_TAGS,
            SCHEMA_REFUND_ORDER,
            SCHEMA_CREATE_STORE_CREDIT,
            SCHEMA_CREATE_RETURN,
            SCHEMA_GET_PRODUCT_DETAILS,
        ]
        self._tool_executors = {k: v for k, v in SHOPIFY_EXEC.items() if k in {
            "shopify_get_customer_orders", "shopify_get_order_details",
            "shopify_add_tags", "shopify_refund_order",
            "shopify_create_store_credit", "shopify_create_return",
            "shopify_get_product_details",
        }}
        self._system_prompt = dedent("""\
            You are "Caz", a friendly customer support specialist for NATPAT.

            You are handling a **Wrong or Missing Item** case. Follow this workflow STRICTLY:

            STEP 1 – CHECK ORDER
            - Look up the customer's orders using shopify_get_customer_orders (use their email).
            - Then get order details with shopify_get_order_details.

            STEP 2 – ASK WHAT HAPPENED
            - Missing item, or wrong item received?

            STEP 3 – REQUEST PHOTOS
            - Ask for a photo of items received.
            - If there's a packing slip, ask for that too.
            - If possible, ask for a photo of the outside shipping label.

            STEP 4 – OFFER RESOLUTION (in this order)
            1. Free reship of the missing/correct item first.
            2. If they don't want reship, offer store credit with 10% bonus.
               - Use shopify_create_store_credit. Tag: "Wrong or Missing, Store Credit Issued"
            3. If they decline store credit, process cash refund.
               - Use shopify_refund_order with refundMethod="ORIGINAL_PAYMENT_METHODS".
               - Tag: "Wrong or Missing, Cash Refund Issued"

            STEP 5 – CLOSE THE LOOP
            - If reship: escalate to support so they can resend.
            - If store credit: confirm amount and that it's available immediately.
            - If refund: confirm amount and expected processing time.

            Use shopify_add_tags to tag orders. The 'id' param should be the order GID.

            STYLE: 2-3 sentences. Warm, apologetic. Use their first name.
        """)

__all__ = ["WrongItemAgent"]
