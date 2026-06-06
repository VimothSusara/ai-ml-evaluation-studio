from __future__ import annotations

from typing import Any

from app.services.pipeline_registry import register_trainer
from app.services.training_service import train_single_model

PIPELINE_KIND = "tabular_sklearn"


def train_tabular_sklearn(
    *,
    csv_bytes: bytes,
    target_column: str,
    problem_type: str,
    estimator_key: str,
    params_json: str | None,
    pipeline_config_json: str | None,
    profile_config: dict[str, list[str]],
) -> tuple[dict[str, float], bytes, dict[str, Any]]:
    # pipeline_config_json is reserved for future trainer-specific options.
    _ = pipeline_config_json
    return train_single_model(
        csv_bytes=csv_bytes,
        target_column=target_column,
        problem_type=problem_type,
        estimator_key=estimator_key,
        params_json=params_json,
        profile_config=profile_config,
    )


register_trainer(PIPELINE_KIND, train_tabular_sklearn)
