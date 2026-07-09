from typing import List
from tpg.schemas.profile import TraineeProfile, EquipmentAccess
from tpg.schemas.exercise import Exercise

EQUIPMENT_TIER = {
    EquipmentAccess.bodyweight_only: 0,
    EquipmentAccess.home_basic: 1,
    EquipmentAccess.full_gym: 2,
}


def eligible_exercises(
    profile: TraineeProfile, all_exercises: List[Exercise]
) -> List[Exercise]:
    """Filter exercises down to what this trainee can actually do: matches their
    primary lift, fits their equipment (as a minimum-tier comparison, not an exact
    match), and avoids anything that stresses an injured region."""
    trainee_tier = EQUIPMENT_TIER[profile.equipment_access]
    return [
        ex
        for ex in all_exercises
        if profile.goal_lift in ex.complements_lift
        and EQUIPMENT_TIER[ex.equipment_access] <= trainee_tier
        and not set(ex.stresses) & set(profile.injuries)
    ]
