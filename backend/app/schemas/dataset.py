from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    profile: dict[str, Any] | None = None
    created_at: datetime | None = None

class ValidateIn(BaseModel):
    target_column: str
    problem_type_override: str | None = None