from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    context: str


class AskResponse(BaseModel):
    answer: str
    model: str
