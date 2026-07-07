from typing import List
from pydantic import BaseModel
from tpg.schemas.profile import GoalLift, EquipmentAccess, InjuryRegion


class Exercise(BaseModel):
    """One row from the exercises table: a hand-curated accessory movement."""

    id: int
    name: str
    muscle_group: str
    complements_lift: List[GoalLift]
    equipment_access: EquipmentAccess
    stresses: List[InjuryRegion]
