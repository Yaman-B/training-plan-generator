from datetime import date, datetime
from typing import List
from pydantic import Field
from tpg.schemas.yearly_plan import LiftTarget, StrictModel
from tpg.schemas.weekly_plan import WEEKS_PER_YEAR


class SessionExercise(StrictModel):
    """One prescribed accessory movement for a session."""

    name: str
    sets: int = Field(ge=1, le=10)
    reps: int = Field(ge=1, le=30)


class SessionGeneration(StrictModel):
    """The part the LLM produces: picks and prescribes accessories from the eligible list."""

    accessories: List[SessionExercise] = Field(min_length=2, max_length=5)


class SessionPlan(StrictModel):
    """One day's full workout: primary lift (deterministic) + accessories (LLM-picked)."""

    profile_id: int
    weekly_plan_id: int
    week: int = Field(ge=1, le=WEEKS_PER_YEAR)
    day_index: int = Field(ge=1)  # which of this week's training days this is
    session_date: date
    primary_lift: LiftTarget
    accessories: List[SessionExercise]
    generated_at: datetime = Field(default_factory=datetime.now)
