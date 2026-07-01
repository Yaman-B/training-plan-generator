from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator


class Sex(str, Enum):
    male = "male"
    female = "female"


class ExperienceLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class GoalLift(str, Enum):
    bench = "bench"
    squat = "squat"
    deadlift = "deadlift"
    overhead_press = "overhead press"
    barbell_row = "barbell row"


class EquipmentAccess(str, Enum):
    full_gym = "full gym"
    home_basic = "home basic"
    bodyweight_only = "bodyweight only"


class InjuryRegion(str, Enum):
    neck = "neck"
    shoulders = "shoulders"
    elbows = "elbows"
    wrists = "wrists"
    lower_back = "lower back"
    upper_back = "upper back"
    hips = "hips"
    knees = "knees"
    ankles = "ankles"


class Weekday(str, Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class TraineeProfile(BaseModel):
    # basics + experience
    age: int = Field(ge=13, le=100)
    sex: Sex
    bodyweight: float = Field(gt=0)
    experience_level: ExperienceLevel

    # goal + baseline
    goal_lift: GoalLift
    rep_target: int = Field(ge=1, le=12)
    baseline_weight: float = Field(gt=0)
    target_weight: float = Field(gt=0)
    timeframe_months: int = 12

    # logistics + constraints
    training_days: List[Weekday] = Field(min_length=2)
    equipment_access: EquipmentAccess
    injuries: List[InjuryRegion] = Field(default_factory=list)

    @field_validator("target_weight")
    @classmethod
    def target_must_exceed_baseline(cls, target, info):
        baseline = info.data.get("baseline_weight")
        if baseline is not None and target <= baseline:
            raise ValueError("target_weight must be greater than baseline_weight")
        return target
