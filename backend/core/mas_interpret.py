"""Natural-language interpreter for MAS behavior updates.

Takes a free-form instruction (e.g. "If a customer wants to update their order
address, do not update it directly. Mark as NEEDS_ATTENTION and escalate.")
and uses an LLM to produce structured updates: prompt_policies and/or
behavior_overrides, then applies them to the MAS config.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from core.llm import get_async_openai_client
from core.mas_behavior import add_behavior_override, add_prompt_policy, get_full_config


INTERPRETER_SYSTEM_PROMPT = """You are an interpreter for a multi-agent customer support system (MAS). You receive a natural-language instruction that describes how the system should behave, and you must output a single JSON object that will be used to update the MAS configuration.

Available agents (use exactly these names): order_mod, wismo, wrong_item, product_issue, refund, feedback, discount, subscription.

Output JSON with exactly these keys (use null when not applicable):
- "instruction": string or null. The policy text to append to agent system prompts. Use this when the NL describes a rule agents should follow (tone, what to do/avoid). If the instruction applies to one agent only, set "agent". If it applies to all agents, set "agent" to null.
- "agent": string or null. If "instruction" is set, this is the target agent for that policy (or null for global / all agents).
- "behavior_override": object or null. Use this when the NL describes a specific rule like "when X happens, do Y instead of the default". Must have: "agent", "trigger", "action", "tag". "trigger" is snake_case (e.g. address_update, refund_request, cancel_order). "action" is usually "escalate". "tag" is the order/ticket tag (e.g. NEEDS_ATTENTION). Only use for agents that support overrides (e.g. order_mod has trigger "address_update").

You may set both "instruction" and "behavior_override" when the NL implies both a policy to show in prompts and a code-level override (e.g. "don't update address directly, mark NEEDS_ATTENTION and escalate" -> instruction text + behavior_override for order_mod, trigger address_update, action escalate, tag NEEDS_ATTENTION).

Output only valid JSON, no markdown or explanation."""


async def interpret_nl_to_mas_update(prompt: str) -> Dict[str, Any]:
    """Interpret natural-language instruction into MAS updates; apply and return new config + summary.

    Returns a dict with keys: config (full MAS config), applied (summary of what was added).
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return {"config": get_full_config(), "applied": {"instruction": False, "behavior_override": False}, "error": None}

    client = get_async_openai_client()
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=512,
            messages=[
                {"role": "system", "content": INTERPRETER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as e:
        return {"config": get_full_config(), "applied": {}, "error": str(e)}

    raw = (resp.choices[0].message.content or "").strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```\s*$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"config": get_full_config(), "applied": {}, "error": "Invalid JSON from LLM: " + str(e)}

    if not isinstance(data, dict):
        return {"config": get_full_config(), "applied": {}, "error": "LLM output was not a JSON object"}

    applied = {"instruction": False, "behavior_override": False}
    instruction = data.get("instruction")
    if instruction and isinstance(instruction, str):
        agent = data.get("agent")
        add_prompt_policy(instruction.strip(), agent=agent if isinstance(agent, str) else None)
        applied["instruction"] = True
        applied["agent"] = agent

    bo = data.get("behavior_override")
    if isinstance(bo, dict) and bo.get("agent") and bo.get("trigger"):
        add_behavior_override(bo["agent"], bo)
        applied["behavior_override"] = True
        applied["behavior_override_rule"] = bo

    return {"config": get_full_config(), "applied": applied, "error": None}
