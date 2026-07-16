"""Manual smoke check for the judge and the refine loop. Hits Claude and Postgres, so it
lives in scripts/ and is deliberately not named test_* — pytest must never collect it.

    uv run python -m scripts.smoke_judge

Run it with -m, not as a file path. `python scripts/smoke_judge.py` puts scripts/ on
sys.path instead of the repo root, so `import tpg` fails. This affects every script in
here, not just this one.

Two parts:

  1. The teeth test. Two structurally identical plans — one sensibly paced, one absurdly
     front-loaded — that every Pydantic validator accepts. The judge should separate them.
     A judge that scores both the same is worthless, and handing it something you already
     know is bad is the only way to find that out.

  2. The refine loop, end to end on a real profile. Costs up to 8 LLM calls: generate,
     judge, then generate+judge per revision round.
"""

from tpg.db import load_profile
from tpg.eval.judge import judge_yearly_plan
from tpg.schemas.judgement import JudgementGeneration
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import LiftTarget, Phase, PhaseType, YearlyPlan
from tpg.planning.yearly import generate_reviewed_yearly_plan

PROFILE_ID = 1
CRITERIA = ("progression_rate", "phase_proportioning")

# Measured, not aspirational: the judge scored a deliberately absurd plan 2/10 and a
# deliberately sensible one 6/10, and never awarded 9 to anything. At 9 every plan burned
# all its rounds and exited unchanged. Keep this in one place — a threshold that disagrees
# with the one the loop actually used prints a nonsense verdict.
TARGET_SCORE = 7
MAX_ROUNDS = 3


def lift(weight_kg: float) -> LiftTarget:
    return LiftTarget(weight_kg=weight_kg, reps=5)


def synthetic(baseline, target, mass_goal, base_goal, durations=(4, 4, 4)):
    """Build a profile + plan that every validator accepts, however silly the numbers are.

    Phases are contiguous, total 12 months, and end exactly on the goal — so the structural
    gates have no objection. That is precisely the gap the judge exists to cover.
    """
    profile = TraineeProfile(
        age=28, sex="male", bodyweight=85.0, experience_level="intermediate",
        goal_lift="bench", rep_target=5,
        baseline_weight=baseline, target_weight=target,
        training_days=["mon", "wed", "fri"], equipment_access="full gym", injuries=[],
    )
    starts = [1, 1 + durations[0], 1 + durations[0] + durations[1]]
    plan = YearlyPlan(
        profile_id=1,
        yearly_goal=lift(target),
        phases=[
            Phase(phase_type=PhaseType.mass, start_month=starts[0],
                  duration_months=durations[0], phase_goal=lift(mass_goal)),
            Phase(phase_type=PhaseType.base, start_month=starts[1],
                  duration_months=durations[1], phase_goal=lift(base_goal)),
            Phase(phase_type=PhaseType.strong, start_month=starts[2],
                  duration_months=durations[2], phase_goal=lift(target)),
        ],
    )
    return profile, plan


def report(label: str, plan: YearlyPlan, judgement: JudgementGeneration) -> None:
    print("=" * 78)
    print(label)
    for phase in plan.phases:
        print(f"    {phase.phase_type.value:6} months {phase.start_month}-{phase.end_month}: "
              f"{phase.phase_goal.weight_kg} kg")
    print(f"\n  OVERALL {judgement.overall}/10 (the weakest criterion)\n")
    for name in CRITERIA:
        criterion = getattr(judgement, name)
        print(f"  [{criterion.score:>2}/10]  {name}")
        print(f"           {criterion.rationale}\n")


# 1. The teeth test.
even_profile, even_plan = synthetic(100.0, 115.0, mass_goal=105.0, base_goal=110.0)
report("SENSIBLE — 100->115kg spread evenly (5kg per phase)",
       even_plan, judge_yearly_plan(even_profile, even_plan))

# Same goal, same validators, all the gain dumped into the first four months.
front_profile, front_plan = synthetic(100.0, 115.0, mass_goal=114.0, base_goal=114.5)
report("FRONT-LOADED — 14 of the 15kg crammed into the mass phase",
       front_plan, judge_yearly_plan(front_profile, front_plan))

# 2. The refine loop on a real profile.
print("=" * 78)
print(f"REFINE LOOP — profile {PROFILE_ID}, target {TARGET_SCORE}/10, max {MAX_ROUNDS} rounds")
print("(check Langfuse to watch the score climb round by round)\n")

profile = load_profile(PROFILE_ID)
final_plan, final_review = generate_reviewed_yearly_plan(
    profile, PROFILE_ID, max_rounds=MAX_ROUNDS, target_score=TARGET_SCORE
)
outcome = (
    "cleared the bar"
    if final_review.overall >= TARGET_SCORE
    else f"ran out of rounds, still {final_review.overall}/10"
)
report(f"FINAL — {outcome}", final_plan, final_review)
