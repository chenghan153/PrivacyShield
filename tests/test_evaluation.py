from privacyshield.evaluation import run_synthetic_evaluation


def test_synthetic_evaluation_has_required_scale_and_metrics():
    result = run_synthetic_evaluation()
    assert result["cases"] >= 20
    assert result["positive_labels"] >= 20
    assert result["tp"] >= 20
    assert result["fp"] == 0
    assert result["fn"] == 0
