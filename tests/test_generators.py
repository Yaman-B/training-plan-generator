"""Orchestration: how the generators chain their steps together.

The LLM is stubbed at the per-unit seam (generate_phase_months / generate_month_weeks /
generate_session_accessories), because those receive the arguments the orchestrator
computed — so a fake can both return something valid AND record what it was asked for.
That's what lets us assert the chaining, which is the part that has no other coverage:
each unit must start from where the previous one finished.

No network, no database.
"""

from datetime import date, timedelta

from tpg.planning import monthly as monthly_mod
from tpg.planning import weekly as weekly_mod
from tpg.planning.monthly import generate_monthly_plan
from tpg.planning.weekly import generate_weekly_plan
from tpg.schemas.monthly_plan import MonthlyPlan, MonthlyTarget, PhaseMonthlyGeneration
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.session_plan import SessionExercise, SessionGeneration
from tpg.schemas.weekly_plan import MonthWeeklyGeneration, WeeklyPlan, WeeklyTarget
from tpg.schemas.yearly_plan import LiftTarget, Phase, PhaseType, YearlyPlan
from tpg.session import session as session_mod
from tpg.session.session import generate_todays_session, generate_week_sessions

MONDAY = date(2026, 1, 5)

PROFILE = TraineeProfile(
    age=30, sex="male", bodyweight=80.0, experience_level="intermediate",
    goal_lift="squat", rep_target=5, baseline_weight=100.0, target_weight=140.0,
    training_days=["mon", "wed", "fri"], equipment_access="full gym", injuries=[],
)


def lift(w):
    return LiftTarget(weight_kg=w, reps=5)


def yearly():
    return YearlyPlan(
        profile_id=1, start_date=MONDAY, yearly_goal=lift(140),
        phases=[
            Phase(phase_type=PhaseType.mass, start_month=1, duration_months=4, phase_goal=lift(115)),
            Phase(phase_type=PhaseType.base, start_month=5, duration_months=4, phase_goal=lift(128)),
            Phase(phase_type=PhaseType.strong, start_month=9, duration_months=4, phase_goal=lift(140)),
        ],
    )


def interpolate(from_target, to_target, n):
    """Evenly climb from -> to over n steps, landing exactly on `to`."""
    step = (to_target.weight_kg - from_target.weight_kg) / n
    return [
        LiftTarget(weight_kg=round(from_target.weight_kg + step * (i + 1), 2), reps=to_target.reps)
        for i in range(n)
    ]


# ── monthly: chains phase -> phase ────────────────────────────────────────────


def test_monthly_plan_chains_each_phase_from_the_previous_phases_goal(monkeypatch):
    seen = []

    def fake_phase_months(profile, from_target, phase_goal, start_month, duration_months):
        seen.append((start_month, from_target.weight_kg, phase_goal.weight_kg))
        targets = interpolate(from_target, phase_goal, duration_months)
        return PhaseMonthlyGeneration(
            start_month=start_month, duration_months=duration_months, phase_goal=phase_goal,
            monthly_targets=[
                MonthlyTarget(month=start_month + i, target=t) for i, t in enumerate(targets)
            ],
        )

    monkeypatch.setattr(monthly_mod, "generate_phase_months", fake_phase_months)

    plan = generate_monthly_plan(
        profile=PROFILE, yearly_plan=yearly(), profile_id=1, yearly_plan_id=1
    )

    # the chaining: mass starts at the profile's baseline, then each phase picks up
    # exactly where the previous one left off
    assert seen == [
        (1, 100.0, 115.0),   # from baseline -> mass goal
        (5, 115.0, 128.0),   # from mass goal -> base goal
        (9, 128.0, 140.0),   # from base goal -> strong goal
    ]

    assert isinstance(plan, MonthlyPlan)
    assert [m.month for m in plan.months] == list(range(1, 13))
    assert plan.months[-1].target.weight_kg == 140.0  # lands on the yearly goal


# ── weekly: chains month -> month ─────────────────────────────────────────────


def test_weekly_plan_chains_each_month_from_the_previous_months_target(monkeypatch):
    seen = []

    def fake_month_weeks(profile, from_target, month_goal, start_week):
        seen.append((start_week, from_target.weight_kg, month_goal.weight_kg))
        targets = interpolate(from_target, month_goal, 4)
        return MonthWeeklyGeneration(
            start_week=start_week, month_goal=month_goal,
            weekly_targets=[
                WeeklyTarget(week=start_week + i, target=t) for i, t in enumerate(targets)
            ],
        )

    monkeypatch.setattr(weekly_mod, "generate_month_weeks", fake_month_weeks)

    months = [MonthlyTarget(month=i, target=lift(100 + i)) for i in range(1, 13)]
    monthly_plan = MonthlyPlan(profile_id=1, yearly_plan_id=1, months=months)

    plan = generate_weekly_plan(
        profile=PROFILE, monthly_plan=monthly_plan, profile_id=1, monthly_plan_id=1
    )

    # month 1 starts at the baseline; every later month starts at the previous month's target
    assert seen[0] == (1, 100.0, 101.0)
    assert seen[1] == (5, 101.0, 102.0)
    assert seen[-1] == (45, 111.0, 112.0)
    assert [s[0] for s in seen] == [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45]

    assert isinstance(plan, WeeklyPlan)
    assert [w.week for w in plan.weeks] == list(range(1, 49))


# ── sessions ──────────────────────────────────────────────────────────────────


def stub_accessories(monkeypatch):
    def fake(profile, phase, primary_lift_target, eligible):
        return SessionGeneration(
            accessories=[
                SessionExercise(name="Leg Press", sets=3, reps=12),
                SessionExercise(name="Plank", sets=3, reps=1),
            ]
        )

    monkeypatch.setattr(session_mod, "generate_session_accessories", fake)


def weekly_plan_48():
    weeks = [WeeklyTarget(week=i, target=lift(100 + i)) for i in range(1, 49)]
    return WeeklyPlan(profile_id=1, monthly_plan_id=1, weeks=weeks)


def test_session_is_none_on_a_rest_day(monkeypatch):
    stub_accessories(monkeypatch)
    tuesday = MONDAY + timedelta(days=1)  # trainee only does mon/wed/fri
    assert generate_todays_session(
        PROFILE, yearly(), weekly_plan_48(), [], profile_id=1, weekly_plan_id=1, today=tuesday
    ) is None


def test_session_copies_the_primary_lift_from_the_weekly_plan_not_the_llm(monkeypatch):
    """The LLM only ever picks accessories; the primary lift is copied deterministically."""
    stub_accessories(monkeypatch)
    wp = weekly_plan_48()

    s = generate_todays_session(
        PROFILE, yearly(), wp, [], profile_id=1, weekly_plan_id=1, today=MONDAY
    )

    assert s is not None
    assert s.week == 1 and s.day_index == 1
    assert s.primary_lift == wp.weeks[0].target  # week 1's target, untouched
    assert [a.name for a in s.accessories] == ["Leg Press", "Plank"]


def test_week_sessions_produces_one_per_training_day_and_none_for_rest_days(monkeypatch):
    stub_accessories(monkeypatch)

    sessions = generate_week_sessions(
        PROFILE, yearly(), weekly_plan_48(), [], profile_id=1, weekly_plan_id=1, today=MONDAY
    )

    # mon/wed/fri within the 7-day block starting Monday
    assert len(sessions) == 3
    assert [s.session_date.weekday() for s in sessions] == [0, 2, 4]
    assert all(s.week == 1 for s in sessions)
    # every training day in a week shares the same primary lift (by design)
    assert len({s.primary_lift.weight_kg for s in sessions}) == 1


def test_week_sessions_follows_the_trainees_own_training_days(monkeypatch):
    stub_accessories(monkeypatch)
    weekend = TraineeProfile(
        **{**PROFILE.model_dump(mode="json"), "training_days": ["sat", "sun"]}
    )

    sessions = generate_week_sessions(
        weekend, yearly(), weekly_plan_48(), [], profile_id=1, weekly_plan_id=1, today=MONDAY
    )

    assert [s.session_date.weekday() for s in sessions] == [5, 6]  # sat, sun
