"""Audience-aware redaction policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Detection


VALID_ACTIONS = {"allow", "redact", "review"}


class PolicyError(ValueError):
    pass


def load_policy(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict) or "audiences" not in policy:
        raise PolicyError("Policy must contain an 'audiences' mapping")
    for audience, settings in policy["audiences"].items():
        if not isinstance(settings, dict):
            raise PolicyError(f"Audience {audience!r} must be a mapping")
        for kind, action in settings.items():
            if action not in VALID_ACTIONS:
                raise PolicyError(f"Unsupported action {action!r} for {audience}.{kind}")
    return policy


def apply_policy(
    detections: list[Detection], audience: str, policy: dict[str, Any]
) -> list[Detection]:
    try:
        rules = policy["audiences"][audience]
    except KeyError as exc:
        raise PolicyError(f"Unknown audience: {audience}") from exc
    labels = policy.get("labels", {})
    for item in detections:
        action = rules.get(item.kind, rules.get("default", "review"))
        item.action = action
        item.selected = action != "allow"
        label = labels.get(item.kind, item.kind.replace("_", " ").title())
        if action == "redact":
            item.reason = f"{label} is blocked for {audience} sharing"
        elif action == "allow":
            item.reason = f"{label} is allowed by the {audience} demo policy"
        else:
            item.reason = f"{label} requires human review for {audience} sharing"
    return detections
