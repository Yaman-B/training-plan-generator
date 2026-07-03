from typing import List
from pydantic import Field, model_validator
from tpg.schemas.yearly_plan import LiftTarget, StrictModel
from datetime import datetime


class MonthlyTarget(StrictModel):
    """One checkpoint on the progression: the lift amount to achieve by the end of this month."""

    month: int = Field(ge=1, le=12)  # absolute month across the year, not within-phase
    target: LiftTarget


class PhaseMonthlyGeneration(StrictModel):
    """One phase's month-by-month targets, returned by a single per-phase call."""

    start_month: int = Field(ge=1, le=12)
    duration_months: int = Field(ge=2, le=7)
    phase_goal: LiftTarget
    monthly_targets: List[MonthlyTarget]

    @model_validator(mode="after")
    def validate_months_contiguous(self):
        for i in range(len(self.monthly_targets) - 1):
            if self.monthly_targets[i + 1].month != self.monthly_targets[i].month + 1:
                raise ValueError("Months must be contiguous, increasing by exactly 1.")
        return self

    @model_validator(mode="after")
    def validate_load_non_decreasing(self):
        for i in range(len(self.monthly_targets) - 1):
            curr = self.monthly_targets[i].target.weight_kg
            nxt = self.monthly_targets[i + 1].target.weight_kg
            if nxt < curr:
                raise ValueError("Load must not decrease from one month to the next.")
        return self

    @model_validator(mode="after")
    def validate_month_count(self):
        # Number of months must match the phase length.
        if len(self.monthly_targets) != self.duration_months:
            raise ValueError(
                f"Expected {self.duration_months} months, got {len(self.monthly_targets)}."
            )
        return self

    @model_validator(mode="after")
    def validate_first_month(self):
        # First month must be the phase's start month.
        if self.monthly_targets and self.monthly_targets[0].month != self.start_month:
            raise ValueError(
                f"First month must be {self.start_month}, got {self.monthly_targets[0].month}."
            )
        return self

    @model_validator(mode="after")
    def validate_ends_at_phase_goal(self):
        # Last month's target must equal the phase goal.
        if self.monthly_targets and self.monthly_targets[-1].target != self.phase_goal:
            raise ValueError("The last month's target must equal the phase goal.")
        return self


class MonthlyPlan(StrictModel):
    """The full 12-month plan, assembled from the three per-phase results."""

    profile_id: int
    yearly_plan_id: int
    months: List[MonthlyTarget]
    generated_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_twelve_months(self):
        # The whole year must be exactly 12 months.
        if len(self.months) != 12:
            raise ValueError(f"Expected 12 months, got {len(self.months)}.")
        return self

    @model_validator(mode="after")
    def validate_months_run_1_to_12(self):
        # Months must run 1, 2, ... 12 in order.
        for i, monthly_target in enumerate(self.months):
            if monthly_target.month != i + 1:
                raise ValueError(
                    f"Month at position {i} should be {i + 1}, got {monthly_target.month}."
                )
        return self
