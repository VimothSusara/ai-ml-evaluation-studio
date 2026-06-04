from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PredictIn(BaseModel):
    rows: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Feature rows; keys must match training feature columns",
    )


class PredictionItem(BaseModel):
    prediction: str | float | int | bool
    probabilities: dict[str, float] | None = None


class PredictOut(BaseModel):
    model_run_id: UUID
    model_code: str
    problem_type: str
    predictions: list[PredictionItem]


class InferenceSchemaOut(BaseModel):
    model_run_id: UUID
    model_code: str
    problem_type: str
    target_column: str
    feature_columns: list[str]
    dataset_id: str | None = None


class ModelExportOut(BaseModel):
    model_run_id: UUID
    model_code: str
    format: str
    download_url: str | None = None
    expires_in_seconds: int | None = None
    filename: str | None = None
    manifest: dict[str, Any] | None = None