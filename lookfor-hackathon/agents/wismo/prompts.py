"""Prompts for WISMO shipping delay flows.

You mentioned different logic for Mon–Wed vs Thu–Sun; you can express
that branching here or inside the graph itself.
"""

from datetime import datetime


def wismo_system_prompt() -> str:
    return (
        "You are a shipping support specialist. Help customers understand "
        "where their order is, set expectations, and provide clear next steps."
    )


def current_wismo_policy_prompt(now: datetime | None = None) -> str:
    """Return the policy text depending on day-of-week.

    This is a thin helper so you can later swap in PDF / RAG logic.
    """

    now = now or datetime.utcnow()
    weekday = now.weekday()  # 0=Mon

    if 0 <= weekday <= 2:
        return "Mon–Wed shipping policy placeholder."
    return "Thu–Sun shipping policy placeholder."


__all__ = ["wismo_system_prompt", "current_wismo_policy_prompt"]
