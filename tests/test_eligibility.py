"""The deterministic exercise filter.

This is the safety-critical half of the Session Flow: the enums decide what is *allowed*,
and the LLM only ever picks from what survives this filter. Free text cannot widen it.
"""

from tpg.schemas.exercise import Exercise
from tpg.schemas.profile import EquipmentAccess, TraineeProfile
from tpg.session.eligibility import EQUIPMENT_TIER, eligible_exercises

PROFILE = dict(
    age=30, sex="male", bodyweight=80.0, experience_level="intermediate",
    goal_lift="bench", rep_target=5, baseline_weight=80.0, target_weight=100.0,
    training_days=["mon", "wed", "fri"], equipment_access="full gym", injuries=[],
)


def ex(name, lift="bench", equipment="full gym", stresses=(), muscle="chest"):
    return Exercise(
        id=abs(hash(name)) % 10000, name=name, muscle_group=muscle,
        complements_lift=[lift], equipment_access=equipment, stresses=list(stresses),
    )


def names(result):
    return {e.name for e in result}


def test_equipment_tiers_are_ordered():
    # Keyed by the enum member, which is what eligible_exercises actually looks up with.
    assert (
        EQUIPMENT_TIER[EquipmentAccess.bodyweight_only]
        < EQUIPMENT_TIER[EquipmentAccess.home_basic]
        < EQUIPMENT_TIER[EquipmentAccess.full_gym]
    )


def test_keeps_only_exercises_for_the_trainees_goal_lift():
    profile = TraineeProfile(**PROFILE)  # bench
    pool = [ex("Cable Fly", lift="bench"), ex("Leg Press", lift="squat", muscle="quads")]
    assert names(eligible_exercises(profile, pool)) == {"Cable Fly"}


def test_equipment_is_a_minimum_tier_not_an_exact_match():
    """A full-gym trainee can still do bodyweight work — the tier is a floor, not a filter."""
    profile = TraineeProfile(**{**PROFILE, "equipment_access": "full gym"})
    pool = [
        ex("Push-ups", equipment="bodyweight only"),
        ex("Floor Press", equipment="home basic"),
        ex("Cable Fly", equipment="full gym"),
    ]
    assert names(eligible_exercises(profile, pool)) == {"Push-ups", "Floor Press", "Cable Fly"}


def test_equipment_excludes_anything_above_the_trainees_tier():
    profile = TraineeProfile(**{**PROFILE, "equipment_access": "home basic"})
    pool = [
        ex("Push-ups", equipment="bodyweight only"),
        ex("Floor Press", equipment="home basic"),
        ex("Cable Fly", equipment="full gym"),  # out of reach
    ]
    assert names(eligible_exercises(profile, pool)) == {"Push-ups", "Floor Press"}


def test_excludes_exercises_that_stress_an_injured_region():
    profile = TraineeProfile(**{**PROFILE, "injuries": ["shoulders"]})
    pool = [
        ex("Incline DB Press", stresses=["shoulders"]),
        ex("Tricep Pushdown", stresses=["elbows"]),
        ex("Floor Press", stresses=[]),
    ]
    assert names(eligible_exercises(profile, pool)) == {"Tricep Pushdown", "Floor Press"}


def test_excludes_an_exercise_stressing_any_one_of_several_injuries():
    profile = TraineeProfile(**{**PROFILE, "injuries": ["knees", "wrists"]})
    # stresses shoulders AND wrists -> the wrists overlap alone is disqualifying
    pool = [ex("Pike Push-ups", stresses=["shoulders", "wrists"]), ex("Floor Press")]
    assert names(eligible_exercises(profile, pool)) == {"Floor Press"}


def test_all_three_filters_apply_together():
    profile = TraineeProfile(
        **{**PROFILE, "equipment_access": "home basic", "injuries": ["shoulders"]}
    )
    pool = [
        ex("Keep Me", equipment="home basic", stresses=["elbows"]),
        ex("Wrong Lift", lift="squat", equipment="bodyweight only", muscle="quads"),
        ex("Too Much Kit", equipment="full gym"),
        ex("Hurts Shoulders", equipment="home basic", stresses=["shoulders"]),
    ]
    assert names(eligible_exercises(profile, pool)) == {"Keep Me"}


def test_returns_empty_when_nothing_qualifies():
    profile = TraineeProfile(**{**PROFILE, "injuries": ["shoulders"]})
    assert eligible_exercises(profile, [ex("Incline DB Press", stresses=["shoulders"])]) == []
