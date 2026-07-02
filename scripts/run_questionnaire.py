from tpg.questionnaire import run_questionnaire
from tpg.db import save_profile

print("=== Training Plan Questionnaire ===\n")

profile = run_questionnaire()  # collect + validate
new_id = save_profile(profile)  # store in Postgres

print(f"\nProfile saved id = {new_id}")
print(profile)
