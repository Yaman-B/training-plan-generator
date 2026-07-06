from typing import List
from pydantic import Field, model_validator
from tpg.schemas.yearly_plan import LiftTarget, StrictModel
from datetime import datetime

# set these variables for PoC simplicity
WEEKS_PER_MONTH = 4
WEEKS_PER_YEAR = 12 * WEEKS_PER_MONTH  # 48


class WeeklyTarget(StrictModel):
    """One checkpoint on the progression: the lift amount to achieve by the end of this week."""

    week: int = Field(
        ge=1, le=WEEKS_PER_YEAR
    )  # absolute week across the year, not within-month
    target: LiftTarget


class MonthWeeklyGeneration(StrictModel):
    """One month's week-by-week targets, returned by a single per-month call."""

    start_week: int = Field(ge=1, le=WEEKS_PER_YEAR)
    month_goal: LiftTarget
    weekly_targets: List[WeeklyTarget]

    @model_validator(mode="after")
    def validate_weeks_contiguous(self):
        for i in range(len(self.weekly_targets) - 1):
            if self.weekly_targets[i + 1].week != self.weekly_targets[i].week + 1:
                raise ValueError("Weeks must be contiguous, increasing by exactly 1.")
        return self

    @model_validator(mode="after")
    def validate_load_non_decreasing(self):
        for i in range(len(self.weekly_targets) - 1):
            curr = self.weekly_targets[i].target.weight_kg
            nxt = self.weekly_targets[i + 1].target.weight_kg
            if nxt < curr:
                raise ValueError("Load must not decrease from one week to the next.")
        return self

    @model_validator(mode="after")
    def validate_week_count(self):
        if len(self.weekly_targets) != WEEKS_PER_MONTH:
            raise ValueError(
                f"Expected {WEEKS_PER_MONTH} weeks, got {len(self.weekly_targets)}."
            )
        return self

    @model_validator(mode="after")
    def validate_first_week(self):
        if self.weekly_targets and self.weekly_targets[0].week != self.start_week:
            raise ValueError(
                f"First week must be {self.start_week}, got {self.weekly_targets[0].week}."
            )
        return self

    @model_validator(mode="after")
    def validate_ends_at_month_goal(self):
        if self.weekly_targets and self.weekly_targets[-1].target != self.month_goal:
            raise ValueError("The last week's target must equal the month goal.")
        return self


class WeeklyPlan(StrictModel):
    """The full 48-week plan, assembled from the twelve per-month results."""

    profile_id: int
    monthly_plan_id: int
    weeks: List[WeeklyTarget]
    generated_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_48_weeks(self):
        if len(self.weeks) != WEEKS_PER_YEAR:
            raise ValueError(f"Expected {WEEKS_PER_YEAR} weeks, got {len(self.weeks)}.")
        return self

    @model_validator(mode="after")
    def validate_weeks_run_1_to_48(self):
        for i, weekly_target in enumerate(self.weeks):
            if weekly_target.week != i + 1:
                raise ValueError(
                    f"Week at position {i} should be {i + 1}, got {weekly_target.week}."
                )
        return self
