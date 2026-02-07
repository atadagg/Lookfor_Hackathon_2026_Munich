"""MAS behavior config: single file (YAML) that defines policies and overrides.

The runtime reads this file when building prompts and when evaluating
behavior overrides (e.g. order_mod address_update -> escalate + tag).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# Path to config/mas_behavior.yaml relative to this file (backend/core/mas_behavior.py).
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mas_behavior.yaml"


def _default_config() -> Dict[str, Any]:
    """Return the default config structure (used when file is missing or invalid)."""
    return {"prompt_policies": [], "agent_prompt_policies": {}, "behavior_overrides": {}}


def _load_raw() -> Dict[str, Any]:
    """Load and parse the YAML file. Returns normalized dict with correct types."""
    default = _default_config()
    if not yaml:
        return default
    if not _CONFIG_PATH.exists():
        return default
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return default
        # Normalize so prompt_policies is always a list, etc.
        prompt_policies = data.get("prompt_policies")
        if not isinstance(prompt_policies, list):
            prompt_policies = []
        else:
            # Preserve all items (only strip/coerce) so we never drop existing policies when saving
            prompt_policies = [str(p).strip() for p in prompt_policies]
        agent_prompt_policies = data.get("agent_prompt_policies")
        if not isinstance(agent_prompt_policies, dict):
            agent_prompt_policies = {}
        else:
            agent_prompt_policies = {
                k: [str(p).strip() for p in v] if isinstance(v, list) else []
                for k, v in agent_prompt_policies.items()
                if isinstance(k, str)
            }
        behavior_overrides = data.get("behavior_overrides")
        if not isinstance(behavior_overrides, dict):
            behavior_overrides = {}
        return {
            "prompt_policies": prompt_policies,
            "agent_prompt_policies": agent_prompt_policies,
            "behavior_overrides": behavior_overrides,
        }
    except Exception:
        return default


def _save_raw(data: Dict[str, Any]) -> None:
    """Write the config back to the YAML file."""
    if not yaml:
        raise RuntimeError("PyYAML is required to update mas_behavior.yaml")
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_prompt_policies(agent: Optional[str] = None) -> List[str]:
    """Return policy strings to inject: global prompt_policies + (if agent given) that agent's agent_prompt_policies."""
    data = _load_raw()
    out: List[str] = []
    policies = data.get("prompt_policies")
    if isinstance(policies, list):
        out.extend(str(p).strip() for p in policies if p)
    if agent:
        per_agent = data.get("agent_prompt_policies")
        if isinstance(per_agent, dict):
            agent_list = per_agent.get(agent)
            if isinstance(agent_list, list):
                out.extend(str(p).strip() for p in agent_list if p)
    return out


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


def inject_policies_into_prompt(system_prompt: str, agent: Optional[str] = None) -> str:
    """Append MAS policies (global + per-agent) to the given system prompt. Idempotent if no policies."""
    policies = get_prompt_policies(agent=agent)
    if not policies:
        return system_prompt
    block = "\n\nADDITIONAL POLICIES (you must follow these):\n" + "\n".join("- " + p for p in policies)
    return system_prompt + block


def add_prompt_policy(instruction: str, agent: Optional[str] = None) -> None:
    """Append one policy: to prompt_policies (global) if agent is None, else to agent_prompt_policies[agent]."""
    data = _load_raw()
    if agent:
        data.setdefault("agent_prompt_policies", {})
        if not isinstance(data["agent_prompt_policies"], dict):
            data["agent_prompt_policies"] = {}
        data["agent_prompt_policies"].setdefault(agent, [])
        if not isinstance(data["agent_prompt_policies"][agent], list):
            data["agent_prompt_policies"][agent] = []
        data["agent_prompt_policies"][agent].append(instruction.strip())
    else:
        # Global: work with a copy of the list so we never replace or drop existing policies
        existing = data.get("prompt_policies")
        if not isinstance(existing, list):
            existing = []
        else:
            existing = list(existing)  # copy
        existing.append(instruction.strip())
        data["prompt_policies"] = existing
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


def remove_prompt_policy_at(index: int) -> bool:
    """Remove the global prompt policy at the given index (0-based). Returns True if removed."""
    data = _load_raw()
    policies = data.get("prompt_policies")
    if not isinstance(policies, list) or index < 0 or index >= len(policies):
        return False
    data["prompt_policies"] = [p for i, p in enumerate(policies) if i != index]
    _save_raw(data)
    return True


def remove_agent_prompt_policy_at(agent: str, index: int) -> bool:
    """Remove the policy at index for the given agent. Returns True if removed."""
    data = _load_raw()
    per_agent = data.get("agent_prompt_policies")
    if not isinstance(per_agent, dict):
        return False
    policies = per_agent.get(agent)
    if not isinstance(policies, list) or index < 0 or index >= len(policies):
        return False
    data["agent_prompt_policies"][agent] = [p for i, p in enumerate(policies) if i != index]
    _save_raw(data)
    return True


def remove_behavior_override(agent: str, trigger: str) -> bool:
    """Remove the first override rule for this agent with the given trigger. Returns True if removed."""
    data = _load_raw()
    overrides = data.get("behavior_overrides")
    if not isinstance(overrides, dict):
        return False
    rules = overrides.get(agent)
    if not isinstance(rules, list):
        return False
    new_rules = [r for r in rules if not (isinstance(r, dict) and r.get("trigger") == trigger)]
    if len(new_rules) == len(rules):
        return False
    data["behavior_overrides"][agent] = new_rules
    _save_raw(data)
    return True


def remove_behavior_override_at(agent: str, index: int) -> bool:
    """Remove the override rule at index for the given agent. Returns True if removed."""
    data = _load_raw()
    overrides = data.get("behavior_overrides")
    if not isinstance(overrides, dict):
        return False
    rules = overrides.get(agent)
    if not isinstance(rules, list) or index < 0 or index >= len(rules):
        return False
    data["behavior_overrides"][agent] = [r for i, r in enumerate(rules) if i != index]
    _save_raw(data)
    return True


def get_full_config() -> Dict[str, Any]:
    """Return the full parsed config (for GET /mas/behavior)."""
    return _load_raw()
