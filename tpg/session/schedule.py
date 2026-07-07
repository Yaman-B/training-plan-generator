from datetime import date
from typing import Optional, Tuple
from tpg.schemas.profile import TraineeProfile, Weekday
from tpg.schemas.yearly_plan import YearlyPlan, PhaseType
from tpg.schemas.weekly_plan import WEEKS_PER_MONTH, WEEKS_PER_YEAR

WEEKDAY_ORDER = [
    Weekday.mon,
    Weekday.tue,
    Weekday.wed,
    Weekday.thu,
    Weekday.fri,
    Weekday.sat,
    Weekday.sun,
]


def compute_training_context(
    yearly_plan: YearlyPlan, profile: TraineeProfile, today: date
) -> Optional[Tuple[int, int]]:
    """Returns (week_number, day_index) for today, or None if today is a rest day."""
    elapsed_days = (today - yearly_plan.start_date).days
    if elapsed_days < 0:
        raise ValueError("today is before the plan's start_date")
    week_number = elapsed_days // 7 + 1
    if week_number > WEEKS_PER_YEAR:
        raise ValueError("today is past the end of the 48-week plan")

    todays_weekday = WEEKDAY_ORDER[today.weekday()]
    if todays_weekday not in profile.training_days:
        return None

    ordered_training_days = sorted(profile.training_days, key=WEEKDAY_ORDER.index)
    day_index = ordered_training_days.index(todays_weekday) + 1
    return week_number, day_index


def phase_for_week(yearly_plan: YearlyPlan, week_number: int) -> PhaseType:
    """Which of the three yearly phases a given week number falls in."""
    month_number = (week_number - 1) // WEEKS_PER_MONTH + 1
    for phase in yearly_plan.phases:
        if phase.start_month <= month_number <= phase.end_month:
            return phase.phase_type
    raise ValueError(f"No phase found for month {month_number}")
