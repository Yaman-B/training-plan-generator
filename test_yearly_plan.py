from yearly_plan import YearlyPlan, Phase, PhaseType, LiftTarget

plan = YearlyPlan(
    profile_id=1,
    yearly_goal=LiftTarget(weight_kg=100, reps=5),
    phases=[
        Phase(
            phase_type=PhaseType.mass,
            start_month=1,
            duration_months=5,
            phase_goal=LiftTarget(weight_kg=85, reps=5),
        ),
        Phase(
            phase_type=PhaseType.base,
            start_month=6,
            duration_months=4,
            phase_goal=LiftTarget(weight_kg=92, reps=5),
        ),
        Phase(
            phase_type=PhaseType.strong,
            start_month=10,
            duration_months=3,
            phase_goal=LiftTarget(weight_kg=100, reps=5),
        ),
    ],
)
print("Valid plan constructed OK")
print(plan.phases[0].end_month)  # should print 5

try:
    plan2 = YearlyPlan(
        profile_id=2,
        yearly_goal=LiftTarget(weight_kg=100, reps=5),
        phases=[
            Phase(
                phase_type=PhaseType.mass,
                start_month=1,
                duration_months=7,
                phase_goal=LiftTarget(weight_kg=85, reps=5),
            ),
            Phase(
                phase_type=PhaseType.base,
                start_month=6,
                duration_months=4,
                phase_goal=LiftTarget(weight_kg=92, reps=5),
            ),
            Phase(
                phase_type=PhaseType.strong,
                start_month=10,
                duration_months=3,
                phase_goal=LiftTarget(weight_kg=100, reps=5),
            ),
        ],
    )
except ValueError as e:
    print(f"Caught expected ValueError: {e}")


try:
    plan3 = YearlyPlan(
        profile_id=2,
        yearly_goal=LiftTarget(weight_kg=100, reps=5),
        phases=[
            Phase(
                phase_type=PhaseType.base,
                start_month=1,
                duration_months=5,
                phase_goal=LiftTarget(weight_kg=85, reps=5),
            ),
            Phase(
                phase_type=PhaseType.mass,
                start_month=6,
                duration_months=4,
                phase_goal=LiftTarget(weight_kg=92, reps=5),
            ),
            Phase(
                phase_type=PhaseType.strong,
                start_month=10,
                duration_months=3,
                phase_goal=LiftTarget(weight_kg=100, reps=5),
            ),
        ],
    )
except ValueError as e:
    print(f"Caught expected ValueError: {e}")
