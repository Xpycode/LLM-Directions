"""Directions broker-only-v1 advertisement check; never grants runtime acceptance."""
from collections import Counter
import json

import runner

POLICY_ID = "directions-broker-only-v1"


def check_surface(body):
    """Validate captured Responses tools, including additional_tools, fail closed.

    App-server registration uses inputSchema; the provider wire must use parameters.
    This checks advertisement only. Dispatch and host isolation need separate evidence.
    """
    errors = []
    if not isinstance(body, dict):
        return ["request must be an object"]
    tools = body.get("tools", [])
    inputs = body.get("input", [])
    if not isinstance(tools, list) or not isinstance(inputs, list):
        return ["tools and input must be arrays"]
    tools = list(tools)
    for item in inputs:
        if not isinstance(item, dict):
            errors.append("input item must be an object")
        elif item.get("type") == "additional_tools":
            extra = item.get("tools")
            if not isinstance(extra, list):
                errors.append("additional_tools.tools must be an array")
            else:
                tools.extend(extra)
    expected = {t["name"]: t["inputSchema"] for t in runner.TOOLS}
    names = []
    for tool in tools:
        if not isinstance(tool, dict):
            errors.append("tool must be an object")
            continue
        name = tool.get("name")
        if tool.get("type") != "function" or not isinstance(name, str) or name not in expected:
            errors.append("only direct broker functions are permitted")
            continue
        names.append(name)
        # JSON types matter: Python considers 0 == False and 1 == True.
        if json.dumps(tool.get("parameters"), sort_keys=True) != json.dumps(expected[name], sort_keys=True):
            errors.append(f"schema mismatch: {name}")
        if set(tool) - {"type", "name", "description", "parameters", "strict"}:
            errors.append(f"unknown tool fields: {name}")
        if "description" in tool and not isinstance(tool["description"], str):
            errors.append(f"invalid description: {name}")
        if "strict" in tool and not isinstance(tool["strict"], bool):
            errors.append(f"invalid strict flag: {name}")
    counts = Counter(names)
    for name in expected:
        if counts[name] != 1:
            errors.append(f"expected exactly one {name}; found {counts[name]}")
    return errors
