-- Snapshot of the training_plan database schema.
-- Not a migration chain — this is a single file capturing the current shape of the DB,
-- so it can be recreated from scratch on a new machine or after data loss.
--
-- Usage:
--   createdb training_plan
--   psql -d training_plan -f schema.sql

CREATE TABLE profiles (
    id                SERIAL PRIMARY KEY,
    age               INTEGER NOT NULL CHECK (age >= 13 AND age <= 100),
    sex               TEXT NOT NULL CHECK (sex IN ('male', 'female')),
    bodyweight        REAL NOT NULL CHECK (bodyweight > 0),
    experience_level  TEXT NOT NULL CHECK (experience_level IN ('beginner', 'intermediate', 'advanced')),
    goal_lift         TEXT NOT NULL CHECK (goal_lift IN ('bench', 'squat', 'deadlift', 'overhead press', 'barbell row')),
    rep_target        INTEGER NOT NULL CHECK (rep_target >= 1 AND rep_target <= 12),
    baseline_weight   REAL NOT NULL CHECK (baseline_weight > 0),
    target_weight     REAL NOT NULL,
    timeframe_months  INTEGER NOT NULL DEFAULT 12,
    training_days     TEXT[] NOT NULL CHECK (array_length(training_days, 1) >= 2),
    equipment_access  TEXT NOT NULL CHECK (equipment_access IN ('full gym', 'home basic', 'bodyweight only')),
    injuries          TEXT[] NOT NULL DEFAULT '{}',
    CHECK (target_weight > 0 AND target_weight > baseline_weight)
);

CREATE TABLE plans (
    id            SERIAL PRIMARY KEY,
    profile_id    INTEGER NOT NULL REFERENCES profiles(id),
    plan_data     JSONB NOT NULL,
    generated_at  TIMESTAMP NOT NULL
);

CREATE TABLE monthly_plans (
    id             SERIAL PRIMARY KEY,
    profile_id     INTEGER NOT NULL REFERENCES profiles(id),
    yearly_plan_id INTEGER NOT NULL REFERENCES plans(id),
    plan_data      JSONB NOT NULL,
    generated_at   TIMESTAMP NOT NULL
);
