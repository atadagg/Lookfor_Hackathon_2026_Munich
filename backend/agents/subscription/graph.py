"""Agent for Subscription / Billing Issues (UC7).

Workflow:
1. Check subscription status (by email)
2. Ask reason → route:
   - "Too many on hand": skip → 20% discount → cancel
   - "Didn't like quality": product swap → cancel
   - Billing issue / credit card: escalate
"""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.skio import (
    EXECUTORS as SKIO_EXEC,
    SCHEMA_GET_SUBSCRIPTIONS,
    SCHEMA_GET_SUBSCRIPTION_STATUS,  # Legacy alias
    SCHEMA_SKIP_NEXT_ORDER,
    SCHEMA_PAUSE_SUBSCRIPTION,
    SCHEMA_CANCEL_SUBSCRIPTION,
    SCHEMA_UNPAUSE_SUBSCRIPTION,
)
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_GET_CUSTOMER_ORDERS,
    SCHEMA_ADD_TAGS,
    SCHEMA_CREATE_DISCOUNT_CODE,
    SCHEMA_GET_PRODUCT_RECOMMENDATIONS,
)


class SubscriptionAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="subscription")
        self._workflow_name = "subscription"
        self._tool_schemas = [
            SCHEMA_GET_CUSTOMER_ORDERS,
            SCHEMA_GET_SUBSCRIPTIONS,  # New: returns array of subscriptions
            SCHEMA_GET_SUBSCRIPTION_STATUS,  # Legacy: for backwards compatibility
            SCHEMA_SKIP_NEXT_ORDER,
            SCHEMA_PAUSE_SUBSCRIPTION,
            SCHEMA_CANCEL_SUBSCRIPTION,
            SCHEMA_UNPAUSE_SUBSCRIPTION,
            SCHEMA_ADD_TAGS,
            SCHEMA_CREATE_DISCOUNT_CODE,
            SCHEMA_GET_PRODUCT_RECOMMENDATIONS,
        ]
        self._tool_executors = {
            **{k: v for k, v in SHOPIFY_EXEC.items() if k in {
                "shopify_get_customer_orders", "shopify_add_tags",
                "shopify_create_discount_code", "shopify_get_product_recommendations",
            }},
            **SKIO_EXEC,
        }
        self._system_prompt = dedent("""\
            You are "Caz", a friendly support specialist for NATPAT.

            You are handling a **Subscription / Billing Issue**. Follow STRICTLY:

            STEP 1 – Check subscription status with skio_get_subscriptions (email). Returns array of all customer subscriptions.
            STEP 2 – Ask the reason.

            ROUTE A – "Too many on hand":
              1. Offer to skip next order (skio_skip_next_order_subscription).
              2. If they don't confirm skip, offer 20% discount on next 2 orders
                 (shopify_create_discount_code, type="percentage", value=0.2, duration=1440).
              3. If they still want to cancel → cancel (skio_cancel_subscription).

            ROUTE B – "Didn't like product quality":
              1. Offer product swap (use shopify_get_product_recommendations to suggest alternatives).
              2. If they don't want swap → cancel (skio_cancel_subscription).

            ROUTE C – Billing issue (double charge, unexpected charge):
              → Escalate to Monica immediately.

            ROUTE D – Credit card update:
              → Escalate to Monica.

            ROUTE E – Pause request:
              → Use skio_pause_subscription with the requested date.

            IMPORTANT:
            - skio tools need subscriptionId from the get_subscription_status response.
            - skio_cancel_subscription requires cancellationReasons array.
            - ALWAYS try to retain before cancelling.

            STYLE: 2-3 sentences, warm. Use first name.
        """)


__all__ = ["SubscriptionAgent"]
