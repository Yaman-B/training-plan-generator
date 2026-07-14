"""Calendar math: turning a real date into a plan week + training day.

Subtle, easy to get quietly wrong, and everything the user sees depends on it.
"""

from datetime import date, timedelta

import pytest

from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import LiftTarget, Phase, PhaseType, YearlyPlan
from tpg.session.schedule import (
    WEEKDAY_ORDER,
    compute_training_context,
    phase_for_week,
    week_dates,
)

MONDAY = date(2026, 1, 5)
WEDNESDAY = date(2026, 1, 7)

PROFILE = dict(
    age=30, sex="male", bodyweight=80.0, experience_level="intermediate",
    goal_lift="squat", rep_target=5, baseline_weight=100.0, target_weight=140.0,
    training_days=["mon", "wed", "fri"], equipment_access="full gym", injuries=[],
)


def plan(start=MONDAY):
    return YearlyPlan(
        profile_id=1,
        start_date=start,
        yearly_goal=LiftTarget(weight_kg=140, reps=5),
        phases=[
            Phase(phase_type=PhaseType.mass, start_month=1, duration_months=4,
                  phase_goal=LiftTarget(weight_kg=115, reps=5)),
            Phase(phase_type=PhaseType.base, start_month=5, duration_months=4,
                  phase_goal=LiftTarget(weight_kg=128, reps=5)),
            Phase(phase_type=PhaseType.strong, start_month=9, duration_months=4,
                  phase_goal=LiftTarget(weight_kg=140, reps=5)),
        ],
    )


def profile(**over):
    return TraineeProfile(**{**PROFILE, **over})


# ── the weekday table ─────────────────────────────────────────────────────────


def test_weekday_order_matches_pythons_weekday_index():
    """The whole mapping rests on this: date.weekday() is 0=Monday."""
    for i, day in enumerate(WEEKDAY_ORDER):
        assert (MONDAY + timedelta(days=i)).weekday() == i
        assert day.value == ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][i]


# ── compute_training_context ──────────────────────────────────────────────────


def test_training_day_returns_week_and_day_index():
    # start date is itself a Monday, the trainee's 1st training day
    assert compute_training_context(plan(), profile(), MONDAY) == (1, 1)


def test_day_index_counts_position_among_the_training_days():
    p = plan()
    assert compute_training_context(p, profile(), MONDAY + timedelta(days=2)) == (1, 2)  # Wed
    assert compute_training_context(p, profile(), MONDAY + timedelta(days=4)) == (1, 3)  # Fri


def test_rest_day_returns_none():
    assert compute_training_context(plan(), profile(), MONDAY + timedelta(days=1)) is None  # Tue


def test_week_number_advances_every_seven_days():
    p = plan()
    assert compute_training_context(p, profile(), MONDAY + timedelta(days=7))[0] == 2
    assert compute_training_context(p, profile(), MONDAY + timedelta(weeks=11))[0] == 12


def test_rejects_a_date_before_the_plan_starts():
    with pytest.raises(ValueError, match="before"):
        compute_training_context(plan(), profile(), MONDAY - timedelta(days=1))


def test_rejects_a_date_past_the_end_of_the_48_week_plan():
    with pytest.raises(ValueError, match="past the end"):
        compute_training_context(plan(), profile(), MONDAY + timedelta(weeks=48))


# ── phase_for_week ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "week, expected",
    [
        (1, PhaseType.mass),      # month 1
        (16, PhaseType.mass),     # month 4  — last week of mass
        (17, PhaseType.base),     # month 5  — first week of base
        (32, PhaseType.base),     # month 8  — last week of base
        (33, PhaseType.strong),   # month 9  — first week of strong
        (48, PhaseType.strong),   # month 12 — last week of all
    ],
)
def test_phase_boundaries(week, expected):
    assert phase_for_week(plan(), week) == expected


# ── week_dates ────────────────────────────────────────────────────────────────


def test_week_dates_returns_the_seven_days_of_the_current_plan_week():
    week, dates = week_dates(plan(), MONDAY + timedelta(days=3))
    assert week == 1
    assert len(dates) == 7
    assert dates[0] == MONDAY and dates[-1] == MONDAY + timedelta(days=6)


def test_week_dates_all_fall_inside_the_same_plan_week():
    """A plan-week is 7 days from start_date — not a calendar Mon-Sun week."""
    p = plan(start=WEDNESDAY)  # deliberately not a Monday
    week, dates = week_dates(p, WEDNESDAY + timedelta(days=5))
    assert week == 1
    for d in dates:
        assert (d - p.start_date).days // 7 + 1 == week
    # so the block runs Wed -> Tue, not Mon -> Sun
    assert [d.weekday() for d in dates] == [2, 3, 4, 5, 6, 0, 1]


def test_week_dates_advances_with_the_week():
    week, dates = week_dates(plan(), MONDAY + timedelta(days=9))
    assert week == 2
    assert dates[0] == MONDAY + timedelta(days=7)


def test_week_dates_rejects_a_date_before_the_plan_starts():
    with pytest.raises(ValueError, match="before"):
        week_dates(plan(), MONDAY - timedelta(days=1))
