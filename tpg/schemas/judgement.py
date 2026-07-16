from pydantic import Field

from tpg.schemas.yearly_plan import StrictModel


class CriterionJudgement(StrictModel):
    """One criterion's review: the reasoning, and the score that follows from it.

    rationale is declared first on purpose. Fields are generated in schema order, so the
    model reasons through the evidence before committing to a number, rather than picking
    a score and then writing a justification for it.
    """

    rationale: str = Field(
        ...,
        description=(
            "Why this score. Be specific and quantitative: cite the actual kilograms and "
            "months rather than talking in generalities. One or two sentences."
        ),
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Score for this criterion, 1 (worst) to 10 (best), using the bands in the prompt.",
    )


class JudgementGeneration(StrictModel):
    """A review of a yearly plan, covering only what the validators structurally cannot see.
    Deliberately excludes anything Pydantic already guarantees.
    """

    progression_rate: CriterionJudgement = Field(
        ...,
        description="Is the climb from baseline to goal spread sensibly across the year?",
    )
    phase_proportioning: CriterionJudgement = Field(
        ...,
        description="Do the three phase durations suit this trainee's experience level?",
    )

    @property
    def overall(self) -> int:
        """The plan's score: its weakest criterion."""
        return min(self.progression_rate.score, self.phase_proportioning.score)
