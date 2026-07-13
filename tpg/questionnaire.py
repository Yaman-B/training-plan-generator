from tpg.schemas.profile import (
    TraineeProfile,
    Sex,
    ExperienceLevel,
    GoalLift,
    EquipmentAccess,
    Weekday,
    InjuryRegion,
)
from pydantic import ValidationError


def ask_number(question, number_type=int):
    """
    Ask the user a question and return a valid number.
    Re-asks until the input can be converted to number_type.
    number_type is int for whole numbers (age, reps),
    or float for weights.
    """
    while True:
        answer = input(question + " ").strip()
        try:
            return number_type(answer)
        except ValueError:
            print(f"  Please enter a valid {number_type.__name__}.")


def ask_text(question):
    """
    Ask an optional free-text question.
    Returns the trimmed answer, or None if the user just pressed Enter.
    """
    answer = input(question + " (optional, press Enter to skip) ").strip()
    return answer or None


def ask_choice(question, enum_class):
    """
    Ask the user to pick one option from an enum.
    Shows the valid options, re-asks until a valid one is chosen.
    Returns the chosen string value.
    """
    options = [member.value for member in enum_class]
    while True:
        print(question)
        for i, option in enumerate(options, start=1):
            print(f"  {i}. {option}")
        answer = input("Enter the number of your choice: ").strip()
        try:
            index = int(answer) - 1
            if 0 <= index < len(options):
                return options[index]
        except ValueError:
            pass
        print("  Invalid choice, try again.")


def ask_multi_choice(question, enum_class, allow_empty=False):
    """
    Ask the user to pick zero or more options from an enum.
    Shows options; user enters comma-separated numbers (e.g. "1,3,4").
    allow_empty=True permits picking nothing (returns []).
    Returns a list of chosen string values.
    """
    options = [member.value for member in enum_class]
    while True:
        print(question)
        for i, option in enumerate(options, start=1):
            print(f"  {i}. {option}")
        prompt = "Enter numbers separated by commas"
        if allow_empty:
            prompt += " (or leave blank for none)"
        answer = input(prompt + ": ").strip()

        # Handle the empty case
        if answer == "":
            if allow_empty:
                return []
            print("  You must pick at least one, try again.")
            continue

        # Parse the comma-separated numbers
        try:
            picks = [int(part.strip()) - 1 for part in answer.split(",")]
        except ValueError:
            print("  Please enter numbers only, e.g. 1,3. Try again.")
            continue

        # Check every pick is in range
        if all(0 <= p < len(options) for p in picks):
            chosen = [options[p] for p in picks]
            # Remove accidental duplicates while keeping order
            return list(dict.fromkeys(chosen))
        print("  One or more choices are out of range, try again.")


def run_questionnaire():
    """Walk through all questions, return a validated TraineeProfile."""
    while True:
        # Basics + experience
        age = ask_number("How old are you?", int)
        sex = ask_choice("What's your sex?", Sex)
        bodyweight = ask_number("What's your bodyweight (kg)?", float)
        experience_level = ask_choice(
            "How would you describe your training experience?", ExperienceLevel
        )

        # Goal + baseline
        goal_lift = ask_choice("Which lift do you want to focus on?", GoalLift)
        rep_target = ask_number("How many reps do you want to hit your goal at?", int)
        baseline_weight = ask_number(
            "What can you currently lift on that move, for that many reps (kg)?", float
        )
        target_weight = ask_number(
            "What's your goal weight for that lift, for that many reps (kg)?", float
        )
        goal_description = ask_text(
            "Anything else about what you're training for, in your own words?"
        )

        # Logistics + constraints
        training_days = ask_multi_choice(
            "Which days can you train?", Weekday, allow_empty=False
        )
        equipment_access = ask_choice(
            "What equipment do you have access to?", EquipmentAccess
        )
        injuries = ask_multi_choice(
            "Any areas you need to avoid loading?", InjuryRegion, allow_empty=True
        )
        injury_description = ask_text(
            "Anything more about those injuries (when they hurt, what's still fine)?"
        )

        # Assemble + validate
        try:
            profile = TraineeProfile(
                age=age,
                sex=sex,
                bodyweight=bodyweight,
                experience_level=experience_level,
                goal_lift=goal_lift,
                rep_target=rep_target,
                baseline_weight=baseline_weight,
                target_weight=target_weight,
                training_days=training_days,
                equipment_access=equipment_access,
                injuries=injuries,
                goal_description=goal_description,
                injury_description=injury_description,
            )
            return profile
        except ValidationError as e:
            print("\nThat profile isn't valid:")
            for err in e.errors():
                field = err["loc"][0] if err["loc"] else "(profile)"
                print(f"  - {field}: {err['msg']}")
            print("Let's go through it again.\n")
