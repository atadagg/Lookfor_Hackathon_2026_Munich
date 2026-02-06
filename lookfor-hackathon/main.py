"""Entrypoint wiring router to specialist graphs.

`get_agent_registry` exposes a simple mapping from agent name to
instance. The FastAPI server imports this to dispatch routed requests.
"""

from __future__ import annotations

from typing import Dict

from core.base_agent import BaseAgent
from agents.wismo.graph import WismoAgent
from agents.subscription.graph import SubscriptionAgent
from agents.defect.graph import DefectAgent


def get_agent_registry() -> Dict[str, BaseAgent]:
    """Return the mapping from agent name to concrete instance.

    Add additional agents here as you build the remaining 6 specialists.
    """

    return {
        "wismo": WismoAgent(),
        "subscription": SubscriptionAgent(),
        "defect": DefectAgent(),
    }


if __name__ == "__main__":  # pragma: no cover - manual smoke test helper
    agents = get_agent_registry()
    print("Registered agents:", ", ".join(sorted(agents.keys())))
