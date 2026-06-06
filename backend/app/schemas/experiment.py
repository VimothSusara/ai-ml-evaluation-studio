from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrainIn(BaseModel):
    dataset_id: UUID
    target_column: str
    problem_type_override: str | None = Field(
        default=None,
        description="classification or regression; overrides auto-detect",
    )
    model_codes: list[str] | None = Field(
        default=None,
        description="Train only these models; default = all for problem type",
    )


class ModelRunOut(BaseModel):
    id: UUID
    model_code: str
    status: str
    metrics: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    error: str | None = None
    train_duration_ms: int | None = None


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dataset_id: UUID
    target_column: str
    problem_type: str
    problem_type_override: str | None = None
    pipeline_kind: str | None = None
    status: str
    metrics: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    explanation: str | None = None
    model_runs: list[ModelRunOut] = []
    created_at: datetime | None = None