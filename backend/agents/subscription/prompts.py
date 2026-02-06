"""Retention scripts and subscription-specific prompts."""


def subscription_system_prompt() -> str:
    return (
        "You are a retention specialist focused on subscription orders. "
        "Help customers manage skips, schedule changes, discounts, and "
        "cancellations while maximizing retention."
    )


__all__ = ["subscription_system_prompt"]
