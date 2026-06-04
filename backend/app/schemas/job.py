from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

class JobContextOut(BaseModel):
    label: str | None = None
    dataset_id: str | None = None
    dataset_name: str | None = None
    dataset_status: str | None = None
    experiment_id: str | None = None
    target_column: str | None = None
    problem_type: str | None = None
    best_model: str | None = None

class JobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    celery_task_id: str
    payload: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime | None = None

