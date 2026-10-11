from pathlib import Path

from privacyshield.models import Detection
from privacyshield.policies import apply_policy, load_policy


POLICY = Path(__file__).parents[1] / "configs" / "demo_policies.yaml"


def make(kind: str) -> Detection:
    return Detection(kind, "value", (0, 0, 10, 10), 0, 1.0, "test")


def test_audience_policies_differ():
    policy = load_policy(POLICY)
    internal = apply_policy([make("email"), make("api_key")], "Internal Team", policy)
    external = apply_policy([make("email"), make("api_key")], "External Client", policy)
    public = apply_policy([make("client_name")], "Public", policy)
    assert [item.action for item in internal] == ["allow", "redact"]
    assert [item.action for item in external] == ["redact", "redact"]
    assert public[0].action == "redact"


def test_review_is_selected_by_default():
    policy = load_policy(POLICY)
    result = apply_policy([make("unknown")], "Internal Team", policy)[0]
    assert result.action == "review"
    assert result.selected is True
