from pydantic import BaseModel, Field


class QuestionIssue(BaseModel):
    question: str = Field(description="The exact sub-question text this issue relates to")
    issue: str = Field(description="What is wrong or missing for this specific question's answer")


class CriticResult(BaseModel):
    score: int = Field(description="Overall quality score 0-100")
    coverage: int = Field(description="Coverage score 1-10")
    clarity: int = Field(description="Clarity score 1-10")
    structure: int = Field(description="Structure score 1-10")
    source_quality: int = Field(description="Source quality score 1-10")
    accuracy_issue_found: bool = Field(
        description="True if any factual inaccuracy was identified"
    )
    feedback: str = Field(description="Overall feedback summary")
    question_issues: list[QuestionIssue] = Field(
        default_factory=list,
        description="Specific issues tied to individual sub-questions, if any. Empty if all questions were handled well.",
    )