from datetime import date
from typing import List, Optional
from tpg.llm import generate_structured
from tpg.schemas.session_plan import SessionGeneration, SessionPlan
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import YearlyPlan, LiftTarget, PhaseType
from tpg.schemas.weekly_plan import WeeklyPlan
from tpg.schemas.exercise import Exercise
from tpg.session.schedule import compute_training_context, phase_for_week
from tpg.session.eligibility import eligible_exercises


def _build_session_prompt(
    profile: TraineeProfile,
    phase: PhaseType,
    primary_lift_target: LiftTarget,
    eligible: List[Exercise],
) -> str:
    exercise_list = "\n".join(f"- {ex.name} ({ex.muscle_group})" for ex in eligible)
    return f"""You are an expert strength coach using Paul Carter's methodology.

You are building today's accessory work for a trainee currently in the {phase.value} phase.
Their primary lift today is {profile.goal_lift.value}: {primary_lift_target.weight_kg} kg for {primary_lift_target.reps} reps.

Choose 2 to 5 accessory exercises ONLY from this list (use the exact names given):
{exercise_list}

Prescribe sets and reps appropriate for the {phase.value} phase. Pick a balanced combination — do not repeat the same muscle group for every exercise.

Return only the JSON object, with no extra text, explanation, or formatting."""


def generate_session_accessories(
    profile: TraineeProfile,
    phase: PhaseType,
    primary_lift_target: LiftTarget,
    eligible: List[Exercise],
) -> SessionGeneration:
    """Generate one session's accessory work, validated."""
    prompt = _build_session_prompt(profile, phase, primary_lift_target, eligible)
    return generate_structured(prompt, SessionGeneration)


def generate_todays_session(
    profile: TraineeProfile,
    yearly_plan: YearlyPlan,
    weekly_plan: WeeklyPlan,
    all_exercises: List[Exercise],
    profile_id: int,
    weekly_plan_id: int,
    today: Optional[date] = None,
) -> Optional[SessionPlan]:
    """Build today's full workout, or return None on a rest day."""
    today = today or date.today()
    context = compute_training_context(yearly_plan, profile, today)
    if context is None:
        return None
    week_number, day_index = context

    weekly_target = weekly_plan.weeks[week_number - 1]
    phase = phase_for_week(yearly_plan, week_number)
    eligible = eligible_exercises(profile, all_exercises)

    generation = generate_session_accessories(
        profile, phase, weekly_target.target, eligible
    )

    return SessionPlan(
        profile_id=profile_id,
        weekly_plan_id=weekly_plan_id,
        week=week_number,
        day_index=day_index,
        session_date=today,
        primary_lift=weekly_target.target,
        accessories=generation.accessories,
    )


# testing
if __name__ == "__main__":
    from tpg.db import (
        load_profile,
        load_yearly_plan,
        load_weekly_plan,
        load_exercises,
        save_session_plan,
    )

    pid, yearly_plan_id, weekly_plan_id = (
        4,
        6,
        4,
    )  # existing saved plans from this session

    profile = load_profile(pid)
    yearly_plan = load_yearly_plan(yearly_plan_id)
    weekly_plan = load_weekly_plan(weekly_plan_id)
    all_exercises = load_exercises()

    session = generate_todays_session(
        profile,
        yearly_plan,
        weekly_plan,
        all_exercises,
        profile_id=pid,
        weekly_plan_id=weekly_plan_id,
    )
    if session is None:
        print("Rest day — no session generated.")
    else:
        session_id = save_session_plan(session)
        print(f"Saved session plan with id {session_id}")
        print(session.model_dump_json(indent=2))
