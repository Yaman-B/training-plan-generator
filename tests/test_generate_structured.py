from tpg.llm import generate_structured
from tpg.schemas.yearly_plan import YearlyPlanGeneration

# Shape-valid, and the final phase DOES reach the yearly goal — the one and only
# defect is that the durations sum to 11, which trips the "12-month" cross-field
# validator. Keeping it to a single defect is what makes the assertions below mean
# something.
BAD_JSON = """
{
  "yearly_goal": {"weight_kg": 100.0, "reps": 5},
  "phases": [
    {"phase_type": "mass",   "start_month": 1, "duration_months": 4, "phase_goal": {"weight_kg": 65.0, "reps": 5}},
    {"phase_type": "base",   "start_month": 5, "duration_months": 4, "phase_goal": {"weight_kg": 80.0, "reps": 5}},
    {"phase_type": "strong", "start_month": 9, "duration_months": 3, "phase_goal": {"weight_kg": 100.0, "reps": 5}}
  ]
}
"""

# Durations sum to 12, and the final phase equals the yearly goal (100 kg x 5), so
# this satisfies every validator.
GOOD_JSON = """
{
  "yearly_goal": {"weight_kg": 100.0, "reps": 5},
  "phases": [
    {"phase_type": "mass",   "start_month": 1, "duration_months": 4, "phase_goal": {"weight_kg": 65.0, "reps": 5}},
    {"phase_type": "base",   "start_month": 5, "duration_months": 4, "phase_goal": {"weight_kg": 80.0, "reps": 5}},
    {"phase_type": "strong", "start_month": 9, "duration_months": 4, "phase_goal": {"weight_kg": 100.0, "reps": 5}}
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
