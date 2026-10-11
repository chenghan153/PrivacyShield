"""Synthetic detector evaluation; never presented as production accuracy."""

from __future__ import annotations

from dataclasses import dataclass

from .detectors import detect_text


@dataclass(frozen=True)
class EvalCase:
    text: str
    expected: frozenset[str]


CASES = [
    EvalCase("Email alice@example.com", frozenset({"email"})),
    EvalCase("Reach bob.smith+demo@company.co.uk", frozenset({"email"})),
    EvalCase("Call +886 912-345-678", frozenset({"phone"})),
    EvalCase("Office 02-1234-5678", frozenset({"phone"})),
    EvalCase("api_key: sk_live_ABCDEF1234567890", frozenset({"api_key"})),
    EvalCase("token=abcdefghijklmnop1234", frozenset({"api_key"})),
    EvalCase("ID A123456789", frozenset({"national_id"})),
    EvalCase("cost: USD 12,500", frozenset({"financial"})),
    EvalCase("margin = 31%", frozenset({"financial"})),
    EvalCase("budget: $75,000", frozenset({"financial"})),
    EvalCase("Project ORION is confidential", frozenset({"internal_project"})),
    EvalCase("Client ACME HEALTH", frozenset({"client_name"})),
    EvalCase("alice@example.com / 0912-345-678", frozenset({"email", "phone"})),
    EvalCase("secret: topsecretvalue999", frozenset({"api_key"})),
    EvalCase("salary = NTD 85,000", frozenset({"financial"})),
    EvalCase("pk_test_0123456789ABCDEF", frozenset({"api_key"})),
    EvalCase("Supplier email: ap@vendor.io", frozenset({"email"})),
    EvalCase("Project ORION; budget: 500000", frozenset({"internal_project", "financial"})),
    EvalCase("ACME HEALTH hotline +1 415-555-0132", frozenset({"client_name", "phone"})),
    EvalCase("A223456789 and qa@example.dev", frozenset({"national_id", "email"})),
    # Explicit negative / ambiguous cases.
    EvalCase("Meeting starts at 12:30", frozenset()),
    EvalCase("Invoice number 20261014001", frozenset()),
    EvalCase("Version 1.2.3 is approved", frozenset()),
]


def run_synthetic_evaluation() -> dict[str, float | int | str]:
    custom = {"internal_project": ["Project ORION"], "client_name": ["ACME HEALTH"]}
    tp = fp = fn = 0
    for case in CASES:
        predicted = {kind for kind, _value in detect_text(case.text, custom)}
        tp += len(predicted & case.expected)
        fp += len(predicted - case.expected)
        fn += len(case.expected - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "cases": len(CASES),
        "positive_labels": sum(len(case.expected) for case in CASES),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "scope": "synthetic text fragments only; not production accuracy",
    }
