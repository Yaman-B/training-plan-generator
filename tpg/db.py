import psycopg2
from tpg.schemas.profile import TraineeProfile
from tpg.schemas.yearly_plan import YearlyPlan
from tpg.schemas.monthly_plan import MonthlyPlan
from tpg.schemas.weekly_plan import WeeklyPlan
from tpg.schemas.exercise import Exercise
from tpg.schemas.session_plan import SessionPlan
from psycopg2.extras import RealDictCursor
from typing import List


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
                timeframe_months, training_days, equipment_access, injuries,
                goal_description, injury_description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                profile.goal_description,
                profile.injury_description,
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


def load_yearly_plan(yearly_plan_id: int) -> YearlyPlan:
    """Read a yearly plan row from Postgres and rebuild it as a validated YearlyPlan."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT plan_data FROM plans WHERE id = %s;", (yearly_plan_id,))
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"No yearly plan found with id {yearly_plan_id}")

        # plan_data already comes back as a dict (psycopg2 auto-deserializes jsonb),
        # and it holds the full YearlyPlan (profile_id, generated_at, phases, ...).
        return YearlyPlan.model_validate(row["plan_data"])
    finally:
        conn.close()


def save_monthly_plan(plan: MonthlyPlan) -> int:
    """Serialize a validated MonthlyPlan to JSONB and store it in the monthly_plans table."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO monthly_plans (profile_id, yearly_plan_id, plan_data, generated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (
                plan.profile_id,
                plan.yearly_plan_id,
                plan.model_dump_json(),
                plan.generated_at,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()


def load_monthly_plan(monthly_plan_id: int) -> MonthlyPlan:
    """Read a monthly plan row from Postgres and rebuild it as a validated MonthlyPlan."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT plan_data FROM monthly_plans WHERE id = %s;", (monthly_plan_id,)
        )
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"No monthly plan found with id {monthly_plan_id}")

        return MonthlyPlan.model_validate(row["plan_data"])
    finally:
        conn.close()


def save_weekly_plan(plan: WeeklyPlan) -> int:
    """Serialize a validated WeeklyPlan to JSONB and store it in the weekly_plans table."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO weekly_plans (profile_id, monthly_plan_id, plan_data, generated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (
                plan.profile_id,
                plan.monthly_plan_id,
                plan.model_dump_json(),
                plan.generated_at,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()


def load_weekly_plan(weekly_plan_id: int) -> WeeklyPlan:
    """Read a weekly plan row from Postgres and rebuild it as a validated WeeklyPlan."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT plan_data FROM weekly_plans WHERE id = %s;", (weekly_plan_id,)
        )
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"No weekly plan found with id {weekly_plan_id}")

        return WeeklyPlan.model_validate(row["plan_data"])
    finally:
        conn.close()


def load_exercises() -> List[Exercise]:
    """Read every row from the exercises table and rebuild it as a validated Exercise."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM exercises;")
        rows = cur.fetchall()
        return [Exercise(**row) for row in rows]
    finally:
        conn.close()


def save_session_plan(plan: SessionPlan) -> int:
    """Serialize a validated SessionPlan to JSONB and store it in the session_plans table."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO session_plans (profile_id, weekly_plan_id, plan_data, generated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (
                plan.profile_id,
                plan.weekly_plan_id,
                plan.model_dump_json(),
                plan.generated_at,
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()


def load_session_plan(session_plan_id: int) -> SessionPlan:
    """Read a session plan row from Postgres and rebuild it as a validated SessionPlan."""
    conn = psycopg2.connect(
        dbname="training_plan",
        user="postgres",
        host="localhost",
    )
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT plan_data FROM session_plans WHERE id = %s;", (session_plan_id,)
        )
        row = cur.fetchone()

        if row is None:
            raise ValueError(f"No session plan found with id {session_plan_id}")

        return SessionPlan.model_validate(row["plan_data"])
    finally:
        conn.close()
