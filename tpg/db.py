import psycopg2
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import YearlyPlan
from psycopg2.extras import RealDictCursor


def save_profile(profile: TraineeProfile) -> int:
    # 1. Connect to the training_plan database
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor()

        # 3. Execute a parameterized INSERT.
        cur.execute(
            """
            INSERT INTO profiles (
                age, sex, bodyweight, experience_level,
                goal_lift, rep_target, baseline_weight, target_weight,
                timeframe_months, training_days, equipment_access, injuries
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                profile.age,
                profile.sex.value,
                profile.bodyweight,
                profile.experience_level.value,
                profile.goal_lift.value,
                profile.rep_target,
                profile.baseline_weight,
                profile.target_weight,
                profile.timeframe_months,
                [d.value for d in profile.training_days],
                profile.equipment_access.value,
                [i.value for i in profile.injuries],
            ),
        )

        # The INSERT returns the new row's auto-generated id
        new_id = cur.fetchone()[0]

        conn.commit()
        return new_id
    finally:
        conn.close()

def load_profile(profile_id: int) -> TraineeProfile:
    """Read a profile row from Postgres and rebuild it as a validated TraineeProfile."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        # RealDictCursor -> row comes back as a dict keyed by column name,
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM profiles WHERE id = %s;", (profile_id,))
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"No profile found with id {profile_id}")

        # drop id
        row.pop("id")

        # Reconstruct. Pydantic coerces the stored strings back into enums
        # and the TEXT[] arrays back into lists of enums, re-validating as it goes.
        return TraineeProfile(**row)
    finally:
        conn.close()


def save_yearly_plan(plan: YearlyPlan) -> int:
    """Serialize a validated YearlyPlan to JSONB and store it in the plans table."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO plans (profile_id, plan_data, generated_at)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                plan.profile_id,
                plan.model_dump_json(),
                plan.generated_at,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()
