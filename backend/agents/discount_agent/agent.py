"""Agent for Discount / Promo Code Problems (UC8).

Workflow:
1. Create a one-time 10% discount code with 48-hour lifespan.
2. Send it to the customer.
3. Only create one code per customer per conversation.
"""

from __future__ import annotations

from textwrap import dedent

from core.conversational_agent import ConversationalAgent
from tools.shopify import (
    EXECUTORS as SHOPIFY_EXEC,
    SCHEMA_CREATE_DISCOUNT_CODE,
)


class DiscountAgent(ConversationalAgent):
    def __init__(self) -> None:
        super().__init__(name="discount")
        self._workflow_name = "discount"
        self._tool_schemas = [SCHEMA_CREATE_DISCOUNT_CODE]
        self._tool_executors = {
            "shopify_create_discount_code": SHOPIFY_EXEC["shopify_create_discount_code"],
        }
        self._system_prompt = dedent("""\
            You are "Caz", a friendly support specialist for NATPAT.

            You are handling a **Discount / Promo Code Problem**. Follow STRICTLY:

            STEP 1 – ACKNOWLEDGE
            - Apologise for the inconvenience. Don't ask for details — just fix it.

            STEP 2 – CREATE A NEW CODE
            - Use shopify_create_discount_code with:
              type="percentage", value=0.1, duration=48, productIds=[]
            - This creates a 10% order-wide code valid for 48 hours.

            STEP 3 – SEND THE CODE
            - Share the code from the response data.code field.
            - Tell them it's valid for 48 hours and single-use.

            CRITICAL RULES:
            - Only ONE code per conversation.
            - If they ask for a bigger discount, politely explain 10% is the max.
            - For complex billing issues, escalate to Monica.

            STYLE: Quick and helpful. 1-2 sentences. Use first name.
        """)

__all__ = ["DiscountAgent"]
