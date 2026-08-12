from pydantic import BaseModel

class ResearchResult(BaseModel):
    question: str
    answer: str
    sources: list[str]