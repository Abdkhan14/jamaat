from evals.summarize import build_summary

RUN_URL = "https://github.com/example/actions/runs/1"


def _make_result(description, success, field_accuracy, hallucinations, cost, reason):
    return {
        "description": description,
        "provider": {"label": "gpt-5.1"},
        "success": success,
        "score": field_accuracy,
        "namedScores": {"field_accuracy": field_accuracy, "hallucinations": hallucinations},
        "cost": cost,
        "tokenUsage": {"total": 2000},
        "gradingResult": {"reason": reason},
    }


PASSING = _make_result("simple_day: all prayers", True,  1.0, 0, 0.004, "16/16 fields correct")
FAILING = _make_result("odd_formats: glued",      False, 0.5, 2, 0.004, "8/16 fields correct — wrong: fajr_start")

FIXTURE = {
    "results": {
        "results": [PASSING, PASSING, PASSING, FAILING, FAILING, FAILING],
    }
}


def test_header_counts():
    out = build_summary(FIXTURE, RUN_URL)
    assert "1/2 cases passing" in out
    assert "(3/6 runs)" in out


def test_cost_in_header():
    out = build_summary(FIXTURE, RUN_URL)
    assert "$0.024" in out  # 6 results × 0.004


def test_failure_reason_in_details():
    out = build_summary(FIXTURE, RUN_URL)
    assert "fajr_start" in out
    assert "<details>" in out
