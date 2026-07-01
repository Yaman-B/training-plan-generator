from profile import TraineeProfile
from pydantic import ValidationError

# 1. A valid profile,  should pass
good = TraineeProfile(
    age=25,
    sex="male",
    bodyweight=80,
    experience_level="intermediate",
    goal_lift="bench",
    rep_target=5,
    baseline_weight=60,
    target_weight=100,
    training_days=["mon", "wed", "fri"],
    equipment_access="full gym",
    injuries=["knees"],
)
print("VALID profile accepted:")
print(good)
print()

# 2. Broken profile; each should be REJECTED
broken_profiles = {
    "target not above baseline": dict(
        age=25,
        sex="male",
        bodyweight=80,
        experience_level="intermediate",
        goal_lift="bench",
        rep_target=5,
        baseline_weight=100,
        target_weight=100,  # equal → no gap
        training_days=["mon", "wed", "fri"],
        equipment_access="full gym",
        injuries=[],
    ),
    "bad goal_lift enum": dict(
        age=25,
        sex="male",
        bodyweight=80,
        experience_level="intermediate",
        goal_lift="chest press",  # not in the enum
        rep_target=5,
        baseline_weight=60,
        target_weight=100,
        training_days=["mon", "wed", "fri"],
        equipment_access="full gym",
        injuries=[],
    ),
    "only one training day": dict(
        age=25,
        sex="male",
        bodyweight=80,
        experience_level="intermediate",
        goal_lift="bench",
        rep_target=5,
        baseline_weight=60,
        target_weight=100,
        training_days=["mon"],  # below min_length=2
        equipment_access="full gym",
        injuries=[],
    ),
    "age too low": dict(
        age=10,  # below 13
        sex="male",
        bodyweight=80,
        experience_level="intermediate",
        goal_lift="bench",
        rep_target=5,
        baseline_weight=60,
        target_weight=100,
        training_days=["mon", "wed", "fri"],
        equipment_access="full gym",
        injuries=[],
    ),
}

for label, data in broken_profiles.items():
    try:
        TraineeProfile(**data)
        print(f"[{label}] -> WRONGLY ACCEPTED (this is a problem)")
    except ValidationError as e:
        first_error = e.errors()[0]
        print(f"[{label}] -> correctly rejected: {first_error['msg']}")
