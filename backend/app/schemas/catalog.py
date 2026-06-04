from pydantic import BaseModel


class ProblemTypeOut(BaseModel):
    code: str
    name: str
    description: str | None = None


class ModelDefinitionOut(BaseModel):
    code: str
    display_name: str
    estimator_key: str