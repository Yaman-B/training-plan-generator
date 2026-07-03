# tpg/tests/smoke_generate_structured.py
from tpg.db import load_profile
from tpg.planning.yearly import _build_prompt
from tpg.llm import generate_structured
from tpg.schemas.yearly_plan import YearlyPlanGeneration

profile = load_profile(profile_id=3)
prompt = _build_prompt(profile)

plan = generate_structured(prompt, YearlyPlanGeneration)
print(plan.model_dump_json(indent=2))
