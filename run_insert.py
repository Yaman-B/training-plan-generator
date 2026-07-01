from profile import TraineeProfile
from db import save_profile

# Build a validated profile
profile = TraineeProfile(
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

# insert profile
new_id = save_profile(profile)
print(f"Profile saved with id = {new_id}")
