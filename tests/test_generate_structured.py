from tpg.llm import generate_structured
from tpg.schemas.yearly_plan import YearlyPlanGeneration

# Shape-valid, but durations sum to 11 → fails the "12-month" cross-field
# validator.
BAD_JSON = """
{
  "yearly_goal": {"weight_kg": 100.0, "reps": 5},
  "phases": [
    {"phase_type": "mass",   "start_month": 1, "duration_months": 4, "phase_goal": {"weight_kg": 65.0, "reps": 5}},
    {"phase_type": "base",   "start_month": 5, "duration_months": 4, "phase_goal": {"weight_kg": 80.0, "reps": 5}},
    {"phase_type": "strong", "start_month": 9, "duration_months": 3, "phase_goal": {"weight_kg": 95.0, "reps": 5}}
  ]
}
"""

# durations sum to 12.
GOOD_JSON = """
{
  "yearly_goal": {"weight_kg": 100.0, "reps": 5},
  "phases": [
    {"phase_type": "mass",   "start_month": 1, "duration_months": 4, "phase_goal": {"weight_kg": 65.0, "reps": 5}},
    {"phase_type": "base",   "start_month": 5, "duration_months": 4, "phase_goal": {"weight_kg": 80.0, "reps": 5}},
    {"phase_type": "strong", "start_month": 9, "duration_months": 4, "phase_goal": {"weight_kg": 95.0, "reps": 5}}
  ]
}
"""


def test_retry_recovers_after_validation_failure(monkeypatch):
    calls = []

    def fake_generate(prompt, format_schema=None):
        calls.append(prompt)
        return BAD_JSON if len(calls) == 1 else GOOD_JSON

    monkeypatch.setattr("tpg.llm.generate", fake_generate)

    plan = generate_structured("build a yearly plan", YearlyPlanGeneration)

    assert isinstance(plan, YearlyPlanGeneration)  # it recovered
    assert len(calls) == 2  # it took a second attempt
    assert "invalid" in calls[1].lower()  # the retry carried feedback
