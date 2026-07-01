import psycopg2
from profile import TraineeProfile


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
