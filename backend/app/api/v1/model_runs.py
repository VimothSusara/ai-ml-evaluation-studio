import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.models import Dataset, Experiment, ModelRun, User
from app.db.session import get_db
from app.schemas.inference import PredictIn
from app.services.inference_service import (
    build_manifest,
    get_feature_columns,
    get_owned_model_run,
    load_pipeline,
    run_predict,
)
from app.services.storage_service import StorageService

router = APIRouter()
settings = get_settings()
storage = StorageService()


def _get_run_and_experiment(db: Session, user: User, run_id: uuid.UUID) -> tuple[ModelRun, Experiment]:
    run = db.get(ModelRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Model run not found")
    exp = db.get(Experiment, run.experiment_id)
    try:
        return get_owned_model_run(run, exp, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{model_run_id}/schema")
def inference_schema(
    model_run_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, exp = _get_run_and_experiment(db, user, model_run_id)
    pipe = load_pipeline(run.model_s3_key)
    return {
        "model_run_id": str(run.id),
        "model_code": run.model_code,
        "problem_type": exp.problem_type,
        "target_column": exp.target_column,
        "feature_columns": get_feature_columns(pipe),
        "dataset_id": str(exp.dataset_id),
    }


@router.get("/{model_run_id}/export")
def export_model(
    model_run_id: uuid.UUID,
    format: str = Query("joblib", pattern="^(joblib|manifest)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, exp = _get_run_and_experiment(db, user, model_run_id)
    dataset = db.get(Dataset, exp.dataset_id)
    pipe = load_pipeline(run.model_s3_key)

    if format == "manifest":
        return {
            "model_run_id": str(run.id),
            "model_code": run.model_code,
            "format": "manifest",
            "manifest": build_manifest(run, exp, dataset, pipe),
        }

    filename = f"{run.model_code}.joblib"
    url = storage.generate_presigned_download_url(
        settings.S3_BUCKET_ARTIFACTS,
        run.model_s3_key,
        expires_in=3600,
        filename=filename,
    )
    return {
        "model_run_id": str(run.id),
        "model_code": run.model_code,
        "format": "joblib",
        "download_url": url,
        "expires_in_seconds": 3600,
        "filename": filename,
    }


@router.post("/{model_run_id}/predict")
def predict(
    model_run_id: uuid.UUID,
    payload: PredictIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, exp = _get_run_and_experiment(db, user, model_run_id)
    pipe = load_pipeline(run.model_s3_key)
    try:
        predictions = run_predict(pipe, exp.problem_type, payload.rows)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "model_run_id": str(run.id),
        "model_code": run.model_code,
        "problem_type": exp.problem_type,
        "predictions": predictions,
    }