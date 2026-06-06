from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProblemType

TrainerFn = Callable[..., tuple[dict[str, float], bytes, dict[str, Any]]]

TRAINER_REGISTRY: dict[str, TrainerFn] = {}


def register_trainer(pipeline_kind: str, fn: TrainerFn) -> None:
    TRAINER_REGISTRY[pipeline_kind] = fn


def get_pipeline_kind(db: Session, problem_type_code: str) -> str:
    pt = db.scalar(
        select(ProblemType).where(
            ProblemType.code == problem_type_code,
            ProblemType.is_active.is_(True),
        )
    )
    if not pt:
        raise ValueError(f"Unknown or inactive problem type: {problem_type_code}")
    return pt.pipeline_kind or "tabular_sklearn"


def get_trainer(pipeline_kind: str) -> TrainerFn:
    fn = TRAINER_REGISTRY.get(pipeline_kind)
    if not fn:
        raise ValueError(
            f"No trainer registered for pipeline_kind '{pipeline_kind}'. "
            "Implement and register a trainer before enabling this problem type."
        )
    return fn


def train_with_pipeline(
    pipeline_kind: str,
    *,
    csv_bytes: bytes,
    target_column: str,
    problem_type: str,
    estimator_key: str,
    params_json: str | None,
    pipeline_config_json: str | None,
    profile_config: dict[str, list[str]],
) -> tuple[dict[str, float], bytes, dict[str, Any]]:
    trainer = get_trainer(pipeline_kind)
    return trainer(
        csv_bytes=csv_bytes,
        target_column=target_column,
        problem_type=problem_type,
        estimator_key=estimator_key,
        params_json=params_json,
        pipeline_config_json=pipeline_config_json,
        profile_config=profile_config,
    )
