from tpg.llm import generate_structured
from tpg.schemas.monthly_plan import MonthlyPlan, PhaseMonthlyGeneration
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import LiftTarget, YearlyPlan


def _build_phase_prompt(
    profile: TraineeProfile,
    from_target: LiftTarget,
    phase_goal: LiftTarget,
    start_month: int,
    duration_months: int,
) -> str:
    end_month = start_month + duration_months - 1
    return f"""You are an expert strength coach using Paul Carter's methodology.

You are planning the month-by-month progression for ONE phase of a training year on the trainee's primary lift.

This phase covers months {start_month} to {end_month} ({duration_months} months).

Starting point (end of the previous phase): {from_target.weight_kg} kg for {from_target.reps} reps.
Phase goal, to reach by the final month: {phase_goal.weight_kg} kg for {phase_goal.reps} reps.

Produce one target per month, for every month from {start_month} to {end_month}. Each target is a weight (kg) and rep count on the primary lift. Progress sensibly from the starting point up to the phase goal. The final month's target must equal the phase goal exactly.

Here is the trainee's profile:
- Experience level: {profile.experience_level.value}
- Primary lift: {profile.goal_lift.value}

Return only the JSON object, with no extra text, explanation, or formatting."""


def generate_phase_months(
    profile: TraineeProfile,
    from_target: LiftTarget,
    phase_goal: LiftTarget,
    start_month: int,
    duration_months: int,
) -> PhaseMonthlyGeneration:
    """Generate one phase's month-by-month targets, validated."""
    prompt = _build_phase_prompt(
        profile, from_target, phase_goal, start_month, duration_months
    )
    return generate_structured(prompt, PhaseMonthlyGeneration)


def generate_monthly_plan(
    profile: TraineeProfile,
    yearly_plan: YearlyPlan,
    profile_id: int,
    yearly_plan_id: int,
) -> MonthlyPlan:
    """Generate all 12 months by running each phase in order and chaining them."""
    # Mass starts at the trainee's current baseline.
    from_target = LiftTarget(weight_kg=profile.baseline_weight, reps=profile.rep_target)

    all_months = []
    for phase in yearly_plan.phases:
        phase_result = generate_phase_months(
            profile=profile,
            from_target=from_target,
            phase_goal=phase.phase_goal,
            start_month=phase.start_month,
            duration_months=phase.duration_months,
        )
        all_months.extend(phase_result.monthly_targets)
        # Next phase starts where this one ended.
        from_target = phase.phase_goal

    return MonthlyPlan(
        profile_id=profile_id,
        yearly_plan_id=yearly_plan_id,
        months=all_months,
    )


# testing
if __name__ == "__main__":
    from tpg.db import load_profile, save_monthly_plan, save_yearly_plan
    from tpg.planning.yearly import generate_yearly_plan

    pid = 4
    profile = load_profile(pid)

    # Need a real yearly plan (and its saved id) to feed the monthly step.
    yearly_plan = generate_yearly_plan(profile, pid)
    yearly_plan_id = save_yearly_plan(yearly_plan)

    monthly_plan = generate_monthly_plan(
        profile=profile,
        yearly_plan=yearly_plan,
        profile_id=pid,
        yearly_plan_id=yearly_plan_id,
    )
    monthly_plan_id = save_monthly_plan(monthly_plan)
    print(f"Saved monthly plan with id {monthly_plan_id}")
    print(monthly_plan.model_dump_json(indent=2))
