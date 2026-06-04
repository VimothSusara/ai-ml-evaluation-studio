from __future__ import annotations

import io
import json
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.core.config import get_settings
from app.db.models import Dataset, Experiment, ModelRun
from app.services.storage_service import StorageService
from app.services.training_service import pick_best_run

settings = get_settings()
storage = StorageService()

SUPPORTED_PROBLEM_TYPES = {"classification", "regression"}


def get_owned_model_run(run: ModelRun | None, experiment: Experiment | None, user_id) -> tuple[ModelRun, Experiment]:
    if not run or not experiment or experiment.owner_id != user_id:
        raise ValueError("Model run not found")
    if run.status != "completed" or not run.model_s3_key:
        raise ValueError("Model is not ready for inference")
    if experiment.problem_type not in SUPPORTED_PROBLEM_TYPES:
        raise ValueError(f"Problem type '{experiment.problem_type}' is not supported for inference yet")
    return run, experiment


def load_pipeline(model_s3_key: str) -> Pipeline:
    raw = storage.download_bytes(settings.S3_BUCKET_ARTIFACTS, model_s3_key)
    pipe = joblib.load(io.BytesIO(raw))
    if not isinstance(pipe, Pipeline):
        raise ValueError("Invalid artifact format")
    return pipe


def get_feature_columns(pipe: Pipeline) -> list[str]:
    pre = pipe.named_steps.get("pre")
    if pre is not None and hasattr(pre, "feature_names_in_"):
        return [str(c) for c in pre.feature_names_in_]
    raise ValueError("Cannot infer feature columns from saved model")


def build_manifest(run: ModelRun, experiment: Experiment, dataset: Dataset | None, pipe: Pipeline) -> dict[str, Any]:
    metrics = json.loads(run.metrics_json) if run.metrics_json else {}
    evaluation = json.loads(run.evaluation_json) if run.evaluation_json else None
    return {
        "version": 1,
        "model_run_id": str(run.id),
        "experiment_id": str(experiment.id),
        "dataset_id": str(experiment.dataset_id),
        "dataset_name": dataset.name if dataset else None,
        "model_code": run.model_code,
        "problem_type": experiment.problem_type,
        "target_column": experiment.target_column,
        "feature_columns": get_feature_columns(pipe),
        "metrics": metrics,
        "evaluation_schema_version": evaluation.get("schema_version") if evaluation else None,
        "artifact": {
            "format": "joblib",
            "s3_key": run.model_s3_key,
            "content_type": "application/octet-stream",
        },
        "usage": {
            "python": "joblib.load(path); pipe.predict(dataframe[feature_columns])",
            "note": "Use the same feature columns as training; do not include the target column.",
        },
    }


def run_predict(
    pipe: Pipeline,
    problem_type: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_columns = get_feature_columns(pipe)
    df = pd.DataFrame(rows)
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    extra = [c for c in df.columns if c not in feature_columns]
    if extra:
        df = df[feature_columns]
    else:
        df = df[feature_columns]

    preds = pipe.predict(df)
    proba = None
    if problem_type == "classification" and hasattr(pipe, "predict_proba"):
        try:
            proba = pipe.predict_proba(df)
            classes = pipe.named_steps["model"].classes_
        except Exception:
            proba = None
            classes = None
    else:
        classes = None

    out: list[dict[str, Any]] = []
    for i, pred in enumerate(preds):
        item: dict[str, Any] = {"prediction": _json_friendly(pred)}
        if proba is not None and classes is not None:
            item["probabilities"] = {
                str(classes[j]): float(proba[i][j]) for j in range(len(classes))
            }
        out.append(item)
    return out


def _json_friendly(value: Any) -> str | float | int | bool:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value if isinstance(value, (str, float, int, bool)) else str(value)


def resolve_best_model_run(db, experiment: Experiment) -> ModelRun | None:
    runs = experiment.model_runs
    summaries = [
        {
            "model_run_id": str(r.id),
            "status": r.status,
            "metrics": json.loads(r.metrics_json) if r.metrics_json else None,
        }
        for r in runs
    ]
    best = pick_best_run(summaries, experiment.problem_type)
    if not best:
        return None
    for r in runs:
        if str(r.id) == best["model_run_id"]:
            return r
    return None