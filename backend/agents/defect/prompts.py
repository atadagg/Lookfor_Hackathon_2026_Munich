"""Defect handling policy prompts."""


def defect_system_prompt() -> str:
    return (
        "You handle orders with missing, wrong, or damaged items. Collect "
        "photos when needed and follow policy to reship, refund, or credit."
    )


__all__ = ["defect_system_prompt"]
