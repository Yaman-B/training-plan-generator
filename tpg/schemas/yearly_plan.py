from datetime import date, datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Closed-schema base: forbids extra fields, so model_json_schema()
    emits `additionalProperties: false` — required by Claude's structured outputs."""

    model_config = ConfigDict(extra="forbid")


class PhaseType(str, Enum):
    mass = "mass"
    base = "base"
    strong = "strong"


class LiftTarget(StrictModel):
    """Weight x reps on the primary lift; same as the profile baseline."""

    weight_kg: float = Field(gt=0)
    reps: int = Field(ge=1, le=20)


class Phase(StrictModel):
    phase_type: PhaseType
    start_month: int = Field(ge=1, le=12)
    duration_months: int = Field(ge=2, le=7)  # loose global bounds
    phase_goal: LiftTarget

    @property
    def end_month(self) -> int:
        # Derived, not stored
        return self.start_month + self.duration_months - 1


class YearlyPlanGeneration(StrictModel):
    """The part of a yearly plan the LLM generates; no bookkeeping fields.

    Holds all phase-validation logic so both the LLM output and the stored
    plan are refereed by the same rules."""

    yearly_goal: LiftTarget
    phases: List[Phase] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_phase_order(self):
        phase_order = [phase.phase_type for phase in self.phases]
        if phase_order != [PhaseType.mass, PhaseType.base, PhaseType.strong]:
            raise ValueError("Phases must be in the order: mass, base, strong.")
        return self

    @model_validator(mode="after")
    def validate_first_phase_start(self):
        if self.phases[0].start_month != 1:
            raise ValueError("The first phase must start at month 1.")
        return self

    @model_validator(mode="after")
    def validate_phase_continuity(self):
        for i in range(len(self.phases) - 1):
            if self.phases[i].end_month + 1 != self.phases[i + 1].start_month:
                raise ValueError("Phases must be continuous without gaps or overlaps.")
        return self

    @model_validator(mode="after")
    def validate_total_duration(self):
        total_duration = sum(phase.duration_months for phase in self.phases)
        if total_duration != 12:
            raise ValueError("Total duration of all phases must equal 12 months.")
        return self


class YearlyPlan(YearlyPlanGeneration):
    """Full stored plan: generated content plus bookkeeping fields."""

    profile_id: int
    generated_at: datetime = Field(default_factory=datetime.now)
    start_date: date = Field(default_factory=date.today)
