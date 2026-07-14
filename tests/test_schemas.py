"""Every Pydantic validator in the project.

These are the project's real invariants: they are the only thing standing between a
plausible-looking LLM response and a plan that is quietly wrong.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from tpg.schemas.monthly_plan import MonthlyPlan, MonthlyTarget, PhaseMonthlyGeneration
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.session_plan import SessionExercise, SessionGeneration, SessionPlan
from tpg.schemas.weekly_plan import MonthWeeklyGeneration, WeeklyPlan, WeeklyTarget
from tpg.schemas.yearly_plan import (
    LiftTarget,
    Phase,
    PhaseType,
    YearlyPlanGeneration,
)

# ── helpers ───────────────────────────────────────────────────────────────────

PROFILE = dict(
    age=30,
    sex="male",
    bodyweight=80.0,
    experience_level="intermediate",
    goal_lift="squat",
    rep_target=5,
    baseline_weight=100.0,
    target_weight=140.0,
    training_days=["mon", "wed", "fri"],
    equipment_access="full gym",
    injuries=[],
)


def lift(weight, reps=5):
    return LiftTarget(weight_kg=weight, reps=reps)


def phases(final_goal=140.0):
    """A valid mass/base/strong trio covering 12 months."""
    return [
        Phase(phase_type=PhaseType.mass, start_month=1, duration_months=4, phase_goal=lift(115)),
        Phase(phase_type=PhaseType.base, start_month=5, duration_months=4, phase_goal=lift(128)),
        Phase(phase_type=PhaseType.strong, start_month=9, duration_months=4, phase_goal=lift(final_goal)),
    ]


# ── TraineeProfile ────────────────────────────────────────────────────────────


def test_profile_valid():
    assert TraineeProfile(**PROFILE).goal_lift.value == "squat"


def test_profile_target_must_exceed_baseline():
    with pytest.raises(ValidationError):
        TraineeProfile(**{**PROFILE, "baseline_weight": 140.0, "target_weight": 100.0})


@pytest.mark.parametrize("age", [12, 101])
def test_profile_rejects_age_out_of_range(age):
    with pytest.raises(ValidationError):
        TraineeProfile(**{**PROFILE, "age": age})


@pytest.mark.parametrize("reps", [0, 13])
def test_profile_rejects_rep_target_out_of_range(reps):
    with pytest.raises(ValidationError):
        TraineeProfile(**{**PROFILE, "rep_target": reps})


def test_profile_requires_at_least_two_training_days():
    with pytest.raises(ValidationError):
        TraineeProfile(**{**PROFILE, "training_days": ["mon"]})


def test_profile_free_text_is_optional():
    p = TraineeProfile(**PROFILE)
    assert p.goal_description is None and p.injury_description is None


def test_profile_free_text_accepted():
    p = TraineeProfile(
        **PROFILE,
        goal_description="Chest is lagging.",
        injury_description="Left knee hurts on deep flexion.",
    )
    assert p.injury_description.startswith("Left knee")


@pytest.mark.parametrize("field", ["goal_description", "injury_description"])
def test_profile_free_text_capped_at_500_chars(field):
    TraineeProfile(**{**PROFILE, field: "x" * 500})  # at the cap: fine
    with pytest.raises(ValidationError):
        TraineeProfile(**{**PROFILE, field: "x" * 501})


# ── YearlyPlanGeneration ──────────────────────────────────────────────────────


def test_yearly_valid():
    plan = YearlyPlanGeneration(yearly_goal=lift(140), phases=phases())
    assert [p.phase_type for p in plan.phases] == [PhaseType.mass, PhaseType.base, PhaseType.strong]


def test_yearly_rejects_wrong_phase_order():
    swapped = phases()
    swapped[0], swapped[1] = swapped[1], swapped[0]
    with pytest.raises(ValidationError):
        YearlyPlanGeneration(yearly_goal=lift(140), phases=swapped)


def test_yearly_first_phase_must_start_at_month_1():
    late = phases()
    late[0] = Phase(phase_type=PhaseType.mass, start_month=2, duration_months=4, phase_goal=lift(115))
    with pytest.raises(ValidationError):
        YearlyPlanGeneration(yearly_goal=lift(140), phases=late)


def test_yearly_rejects_gap_between_phases():
    gapped = phases()
    # base starts at 6 instead of 5 -> month 5 belongs to nobody
    gapped[1] = Phase(phase_type=PhaseType.base, start_month=6, duration_months=4, phase_goal=lift(128))
    with pytest.raises(ValidationError):
        YearlyPlanGeneration(yearly_goal=lift(140), phases=gapped)


def test_yearly_durations_must_total_12_months():
    short = phases()
    short[2] = Phase(phase_type=PhaseType.strong, start_month=9, duration_months=3, phase_goal=lift(140))
    with pytest.raises(ValidationError):
        YearlyPlanGeneration(yearly_goal=lift(140), phases=short)


def test_yearly_final_phase_must_reach_the_yearly_goal():
    """Regression test for a real bug.

    A stored plan ran 75 -> 80 -> 90 kg while claiming a 100 kg yearly goal: it never
    reached the goal it was built around, and nothing caught it.
    """
    with pytest.raises(ValidationError, match="final phase's goal must equal the yearly goal"):
        YearlyPlanGeneration(yearly_goal=lift(140), phases=phases(final_goal=130.0))


# ── PhaseMonthlyGeneration / MonthlyPlan ──────────────────────────────────────


def month_targets(start, count, weights):
    return [MonthlyTarget(month=start + i, target=lift(w)) for i, w in enumerate(weights)]


def test_phase_months_valid():
    gen = PhaseMonthlyGeneration(
        start_month=1, duration_months=4, phase_goal=lift(115),
        monthly_targets=month_targets(1, 4, [103, 107, 111, 115]),
    )
    assert len(gen.monthly_targets) == 4


def test_phase_months_rejects_load_going_backwards():
    with pytest.raises(ValidationError):
        PhaseMonthlyGeneration(
            start_month=1, duration_months=4, phase_goal=lift(115),
            monthly_targets=month_targets(1, 4, [103, 100, 111, 115]),  # dips
        )


def test_phase_months_count_must_match_duration():
    with pytest.raises(ValidationError):
        PhaseMonthlyGeneration(
            start_month=1, duration_months=4, phase_goal=lift(115),
            monthly_targets=month_targets(1, 3, [107, 111, 115]),
        )


def test_phase_months_must_end_on_the_phase_goal():
    with pytest.raises(ValidationError):
        PhaseMonthlyGeneration(
            start_month=1, duration_months=4, phase_goal=lift(115),
            monthly_targets=month_targets(1, 4, [103, 107, 111, 114]),  # stops short
        )


def test_monthly_plan_requires_exactly_12_months_in_order():
    twelve = month_targets(1, 12, list(range(100, 112)))
    MonthlyPlan(profile_id=1, yearly_plan_id=1, months=twelve)

    with pytest.raises(ValidationError):
        MonthlyPlan(profile_id=1, yearly_plan_id=1, months=twelve[:11])


# ── MonthWeeklyGeneration / WeeklyPlan ────────────────────────────────────────


def week_targets(start, weights):
    return [WeeklyTarget(week=start + i, target=lift(w)) for i, w in enumerate(weights)]


def test_month_weeks_valid():
    gen = MonthWeeklyGeneration(
        start_week=1, month_goal=lift(104), weekly_targets=week_targets(1, [101, 102, 103, 104])
    )
    assert len(gen.weekly_targets) == 4


def test_month_weeks_must_be_exactly_four():
    with pytest.raises(ValidationError):
        MonthWeeklyGeneration(
            start_week=1, month_goal=lift(103), weekly_targets=week_targets(1, [101, 102, 103])
        )


def test_month_weeks_must_end_on_the_month_goal():
    with pytest.raises(ValidationError):
        MonthWeeklyGeneration(
            start_week=1, month_goal=lift(104), weekly_targets=week_targets(1, [101, 102, 103, 103])
        )


def test_weekly_plan_requires_exactly_48_weeks():
    weeks = week_targets(1, [100 + i for i in range(48)])
    WeeklyPlan(profile_id=1, monthly_plan_id=1, weeks=weeks)

    with pytest.raises(ValidationError):
        WeeklyPlan(profile_id=1, monthly_plan_id=1, weeks=weeks[:47])


# ── Session ───────────────────────────────────────────────────────────────────


def test_session_generation_accessory_count_bounds():
    ok = [SessionExercise(name=f"Ex{i}", sets=3, reps=10) for i in range(2)]
    assert len(SessionGeneration(accessories=ok).accessories) == 2

    with pytest.raises(ValidationError):  # fewer than 2
        SessionGeneration(accessories=ok[:1])

    with pytest.raises(ValidationError):  # more than 5
        SessionGeneration(
            accessories=[SessionExercise(name=f"Ex{i}", sets=3, reps=10) for i in range(6)]
        )


def test_session_plan_valid():
    plan = SessionPlan(
        profile_id=1, weekly_plan_id=1, week=3, day_index=2,
        session_date=date(2026, 7, 13), primary_lift=lift(100),
        accessories=[SessionExercise(name="Leg Press", sets=3, reps=12)],
    )
    assert plan.week == 3


@pytest.mark.parametrize("week", [0, 49])
def test_session_plan_rejects_week_outside_the_48_week_plan(week):
    with pytest.raises(ValidationError):
        SessionPlan(
            profile_id=1, weekly_plan_id=1, week=week, day_index=1,
            session_date=date(2026, 7, 13), primary_lift=lift(100), accessories=[],
        )
