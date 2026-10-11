from privacyshield.detectors import detect_text, detect_words
from privacyshield.models import Word


def test_text_detector_finds_core_types():
    text = "Email a@example.com Phone +886 912-345-678 api_key: sk_live_ABCDEF123456 ID A123456789"
    kinds = {kind for kind, _ in detect_text(text)}
    assert {"email", "phone", "api_key", "national_id"} <= kinds


def test_custom_term_is_literal_and_boxed():
    words = [
        Word("Project", (10, 10, 70, 30), 0, "0"),
        Word("ORION", (75, 10, 130, 30), 0, "0"),
    ]
    results = detect_words(words, {"internal_project": ["Project ORION"]})
    assert len(results) == 1
    assert results[0].bbox == (10, 10, 130, 30)


def test_ambiguous_numbers_are_not_sensitive():
    kinds = {kind for kind, _ in detect_text("Meeting 12:30. Invoice 20261014001. Version 1.2.3")}
    assert not kinds
