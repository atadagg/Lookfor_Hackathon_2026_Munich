"""MAS behavior config: single file (YAML) that defines policies and overrides.

The runtime reads this file when building prompts and when evaluating
behavior overrides (e.g. order_mod address_update -> escalate + tag).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Path to config/mas_behavior.yaml relative to this file (backend/core/mas_behavior.py).
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mas_behavior.yaml"


def _load_raw() -> Dict[str, Any]:
    """Load and parse the YAML file. Returns empty dict if missing or invalid."""
    if not yaml:
        return {}
    if not _CONFIG_PATH.exists():
        return {"prompt_policies": [], "behavior_overrides": {}}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return {"prompt_policies": [], "behavior_overrides": {}}
        return data
    except Exception:
        return {"prompt_policies": [], "behavior_overrides": {}}


def _save_raw(data: Dict[str, Any]) -> None:
    """Write the config back to the YAML file."""
    if not yaml:
        raise RuntimeError("PyYAML is required to update mas_behavior.yaml")
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_prompt_policies() -> List[str]:
    """Return the list of policy strings to inject into agent system prompts."""
    data = _load_raw()
    policies = data.get("prompt_policies")
    if not isinstance(policies, list):
        return []
    return [str(p).strip() for p in policies if p]


def get_behavior_overrides(agent: str) -> List[Dict[str, Any]]:
    """Return list of override rules for the given agent.

    Each rule is a dict with at least 'trigger' and 'action';
    may include 'tag' or other keys.
    """
    data = _load_raw()
    overrides = data.get("behavior_overrides")
    if not isinstance(overrides, dict):
        return []
    agent_rules = overrides.get(agent)
    if not isinstance(agent_rules, list):
        return []
    return [r for r in agent_rules if isinstance(r, dict) and r.get("trigger")]


def inject_policies_into_prompt(system_prompt: str) -> str:
    """Append MAS prompt_policies to the given system prompt. Idempotent if no policies."""
    policies = get_prompt_policies()
    if not policies:
        return system_prompt
    block = "\n\nADDITIONAL POLICIES (you must follow these):\n" + "\n".join("- " + p for p in policies)
    return system_prompt + block


def add_prompt_policy(instruction: str) -> None:
    """Append one policy string to prompt_policies and save the file."""
    data = _load_raw()
    data.setdefault("prompt_policies", [])
    if not isinstance(data["prompt_policies"], list):
        data["prompt_policies"] = []
    data["prompt_policies"].append(instruction.strip())
    _save_raw(data)


def add_behavior_override(agent: str, rule: Dict[str, Any]) -> None:
    """Append one override rule for the given agent and save the file."""
    if not rule.get("trigger"):
        return
    data = _load_raw()
    data.setdefault("behavior_overrides", {})
    if not isinstance(data["behavior_overrides"], dict):
        data["behavior_overrides"] = {}
    data["behavior_overrides"].setdefault(agent, [])
    if not isinstance(data["behavior_overrides"][agent], list):
        data["behavior_overrides"][agent] = []
    data["behavior_overrides"][agent].append(rule)
    _save_raw(data)


def get_full_config() -> Dict[str, Any]:
    """Return the full parsed config (for GET /mas/behavior)."""
    return _load_raw()
