from datetime import date
from fastapi import FastAPI
from tpg.db import (
    load_exercises,
    load_monthly_plan,
    load_profile,
    load_session_plan,
    load_weekly_plan,
    load_yearly_plan,
    save_monthly_plan,
    save_profile,
    save_session_plan,
    save_weekly_plan,
    save_yearly_plan,
)
from tpg.planning.monthly import generate_monthly_plan
from tpg.planning.weekly import generate_weekly_plan
from tpg.planning.yearly import generate_yearly_plan
from tpg.schemas.profile import TraineeProfile
from tpg.session.session import generate_todays_session

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Training Plan Generator API is running"}


# Profile
@app.post("/profile")
def save_profile_api(profile: TraineeProfile):
    profile_id = save_profile(profile)
    return {"message": "Profile saved successfully", "profile_id": profile_id}


@app.get("/profile/{profile_id}")
def load_profile_api(profile_id: int):
    profile = load_profile(profile_id)
    return {"profile": profile}


# Full Plan (yearly + monthly + weekly, generated together)
@app.post("/profile/{profile_id}/plan")
def generate_full_plan_api(profile_id: int):
    profile = load_profile(profile_id)

    yearly_plan = generate_yearly_plan(profile, profile_id)
    yearly_plan_id = save_yearly_plan(yearly_plan)

    monthly_plan = generate_monthly_plan(
        profile=profile,
        yearly_plan=yearly_plan,
        profile_id=profile_id,
        yearly_plan_id=yearly_plan_id,
    )
    monthly_plan_id = save_monthly_plan(monthly_plan)

    weekly_plan = generate_weekly_plan(
        profile=profile,
        monthly_plan=monthly_plan,
        profile_id=profile_id,
        monthly_plan_id=monthly_plan_id,
    )
    weekly_plan_id = save_weekly_plan(weekly_plan)

    return {
        "message": "Full plan generated and saved successfully",
        "yearly_plan_id": yearly_plan_id,
        "monthly_plan_id": monthly_plan_id,
        "weekly_plan_id": weekly_plan_id,
    }


@app.get("/yearly-plan/{yearly_plan_id}")
def load_yearly_plan_api(yearly_plan_id: int):
    yearly_plan = load_yearly_plan(yearly_plan_id)
    return {"yearly_plan": yearly_plan}


@app.get("/monthly-plan/{monthly_plan_id}")
def load_monthly_plan_api(monthly_plan_id: int):
    monthly_plan = load_monthly_plan(monthly_plan_id)
    return {"monthly_plan": monthly_plan}


@app.get("/weekly-plan/{weekly_plan_id}")
def load_weekly_plan_api(weekly_plan_id: int):
    weekly_plan = load_weekly_plan(weekly_plan_id)
    return {"weekly_plan": weekly_plan}


# Session
@app.post("/weekly-plan/{weekly_plan_id}/session/today")
def generate_session_plan_api(weekly_plan_id: int, target_date: date | None = None):
    # load weekly
    weekly_plan = load_weekly_plan(weekly_plan_id)
    profile = load_profile(weekly_plan.profile_id)

    # load monthly to get yearly_plan_id
    monthly_plan = load_monthly_plan(weekly_plan.monthly_plan_id)

    # then load yearly plan
    yearly_plan = load_yearly_plan(monthly_plan.yearly_plan_id)

    all_exercises = load_exercises()

    # generate session
    session_plan = generate_todays_session(
        profile,
        yearly_plan,
        weekly_plan,
        all_exercises,
        profile_id=weekly_plan.profile_id,
        weekly_plan_id=weekly_plan_id,
        today=target_date,
    )

    if session_plan is None:
        return {"message": "Rest day — no session generated.", "rest_day": True}

    session_plan_id = save_session_plan(session_plan)
    return {
        "message": "Session plan generated and saved successfully",
        "session_plan_id": session_plan_id,
    }


@app.get("/session/{session_plan_id}")
def load_session_plan_api(session_plan_id: int):
    session_plan = load_session_plan(session_plan_id)
    return {"session_plan": session_plan}
