from tpg.llm import generate_structured
from tpg.schemas.weekly_plan import MonthWeeklyGeneration, WeeklyPlan, WEEKS_PER_MONTH
from tpg.schemas.monthly_plan import MonthlyPlan
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import LiftTarget


def _build_month_prompt(
    profile: TraineeProfile,
    from_target: LiftTarget,
    month_goal: LiftTarget,
    start_week: int,
) -> str:
    end_week = start_week + WEEKS_PER_MONTH - 1
    return f"""You are an expert strength coach using Paul Carter's methodology.

You are planning the week-by-week progression for ONE month of a training year on the trainee's primary lift.

This month covers weeks {start_week} to {end_week} ({WEEKS_PER_MONTH} weeks).

Starting point (end of the previous month): {from_target.weight_kg} kg for {from_target.reps} reps.
Month goal, to reach by the final week: {month_goal.weight_kg} kg for {month_goal.reps} reps.

Produce one target per week, for every week from {start_week} to {end_week}. Each target is a weight (kg) and rep count on the primary lift. Progress sensibly from the starting point up to the month goal. The final week's target must equal the month goal exactly.

Here is the trainee's profile:
- Experience level: {profile.experience_level.value}
- Primary lift: {profile.goal_lift.value}

Return only the JSON object, with no extra text, explanation, or formatting."""


def generate_month_weeks(
    profile: TraineeProfile,
    from_target: LiftTarget,
    month_goal: LiftTarget,
    start_week: int,
) -> MonthWeeklyGeneration:
    """Generate one month's week-by-week targets, validated."""
    prompt = _build_month_prompt(profile, from_target, month_goal, start_week)
    return generate_structured(prompt, MonthWeeklyGeneration)


def generate_weekly_plan(
    profile: TraineeProfile,
    monthly_plan: MonthlyPlan,
    profile_id: int,
    monthly_plan_id: int,
) -> WeeklyPlan:
    """Generate all 48 weeks by running each month in order and chaining them."""
    # The first month starts at the trainee's current baseline.
    from_target = LiftTarget(weight_kg=profile.baseline_weight, reps=profile.rep_target)

    all_weeks = []
    for monthly_target in monthly_plan.months:
        start_week = (monthly_target.month - 1) * WEEKS_PER_MONTH + 1
        month_result = generate_month_weeks(
            profile=profile,
            from_target=from_target,
            month_goal=monthly_target.target,
            start_week=start_week,
        )
        all_weeks.extend(month_result.weekly_targets)
        # Next month starts where this one ended.
        from_target = monthly_target.target

    return WeeklyPlan(
        profile_id=profile_id,
        monthly_plan_id=monthly_plan_id,
        weeks=all_weeks,
    )


# testing
if __name__ == "__main__":
    from tpg.db import (
        load_profile,
        save_monthly_plan,
        save_weekly_plan,
        save_yearly_plan,
    )
    from tpg.planning.monthly import generate_monthly_plan
    from tpg.planning.yearly import generate_yearly_plan

    pid = 4
    profile = load_profile(pid)

    yearly_plan = generate_yearly_plan(profile, pid)
    yearly_plan_id = save_yearly_plan(yearly_plan)

    monthly_plan = generate_monthly_plan(
        profile=profile,
        yearly_plan=yearly_plan,
        profile_id=pid,
        yearly_plan_id=yearly_plan_id,
    )
    monthly_plan_id = save_monthly_plan(monthly_plan)

    weekly_plan = generate_weekly_plan(
        profile=profile,
        monthly_plan=monthly_plan,
        profile_id=pid,
        monthly_plan_id=monthly_plan_id,
    )
    weekly_plan_id = save_weekly_plan(weekly_plan)
    print(f"Saved weekly plan with id {weekly_plan_id}")
    print(weekly_plan.model_dump_json(indent=2))
