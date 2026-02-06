"""Entrypoint wiring router to specialist agents.

``get_agent_registry`` exposes a mapping from agent name to instance.
The FastAPI server imports this to dispatch routed requests.
"""

from __future__ import annotations

from typing import Dict

from core.base_agent import BaseAgent

# Specialist agents
from agents.wismo.graph import WismoAgent
from agents.wrong_item import WrongItemAgent
from agents.product_issue import ProductIssueAgent
from agents.refund import RefundAgent
from agents.order_mod import OrderModAgent
from agents.feedback import FeedbackAgent
from agents.subscription.graph import SubscriptionAgent
from agents.discount_agent import DiscountAgent


def get_agent_registry() -> Dict[str, BaseAgent]:
    """Return the mapping from agent name to concrete instance."""

    return {
        "wismo": WismoAgent(),
        "wrong_item": WrongItemAgent(),
        "product_issue": ProductIssueAgent(),
        "refund": RefundAgent(),
        "order_mod": OrderModAgent(),
        "feedback": FeedbackAgent(),
        "subscription": SubscriptionAgent(),
        "discount": DiscountAgent(),
    }


if __name__ == "__main__":  # pragma: no cover
    agents = get_agent_registry()
    print("Registered agents:", ", ".join(sorted(agents.keys())))
