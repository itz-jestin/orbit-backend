from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    ambiguous: bool = Field(
        description="Whether the query could refer to more than one entity."
    )
    resolved_entity: str = Field(
        description="The single entity/topic the planner chose to research."
    )
    sub_questions: list[str] = Field(
        description="List of 2-4 research sub-questions, all scoped to resolved_entity."
    )