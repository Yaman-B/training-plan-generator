from profile import TraineeProfile
from db import load_profile, save_yearly_plan
from yearly_plan import YearlyPlan, YearlyPlanGeneration
from llm import generate


def _build_prompt(profile: TraineeProfile) -> str:
    return f"""You are an expert strength coach who designs training plans using Paul Carter's methodology.

Carter's system splits a training year into three ordered phases:
1. Mass (Big-15): hypertrophy focus — build muscle through high-rep work.
2. Base Building: a bridge phase — build work capacity at sub-maximal intensity.
3. Strong (Strong-15): strength peaking — realize strength on the muscle built.

Your task: given a trainee's profile, produce a one-year training plan divided into these three phases, in this exact order.

The yearly plan is a high-level roadmap only. For each of the three phases, it specifies:
- which phase it is,
- when it starts and how many months it lasts,
- a single measurable strength goal to reach by the end of that phase, expressed as a target weight (kg) for a fixed number of reps on the trainee's primary lift.

The yearly plan does NOT contain individual workouts, exercises, sets, or weekly schedules. Those are decided later at finer levels of detail. Do not include them.

The three phases together must cover exactly 12 months with no gaps or overlaps.

Here is the trainee's profile:
- Experience level: {profile.experience_level.value}
- Primary lift: {profile.goal_lift.value}
- Current baseline: {profile.baseline_weight} kg for {profile.rep_target} reps
- One-year goal: {profile.target_weight} kg for {profile.rep_target} reps

Design the three phases so the trainee progresses sensibly from their current baseline toward their one-year goal, with each phase's goal building on the previous one.

Use these exact phase_type values: "mass", "base", "strong".
Return only the JSON object, with no extra text, explanation, or formatting."""


def generate_yearly_plan(profile: TraineeProfile, profile_id: int) -> YearlyPlan:
    """Generate a validated yearly plan for a profile using the LLM."""
    prompt = _build_prompt(profile)
    schema = YearlyPlanGeneration.model_json_schema()

    # Call the LLM with the schema constraint (structured output).
    raw_json = generate(prompt, format_schema=schema)

    # Parse + validate the LLM's output.
    generated = YearlyPlanGeneration.model_validate_json(raw_json)

    # Attach profile_id and other fields to produce the final YearlyPlan object.
    plan = YearlyPlan(
        profile_id=profile_id,
        yearly_goal=generated.yearly_goal,
        phases=generated.phases,
    )
    return plan


# testing
if __name__ == "__main__":
    pid = 1
    profile = load_profile(pid)
    plan = generate_yearly_plan(profile, pid)
    plan_id = save_yearly_plan(plan)
    print(f"Saved yearly plan with id {plan_id}")
    print(plan.model_dump_json(indent=2))
