import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Dataset, Experiment, Job, ModelRun, User
from app.db.session import get_db
from app.schemas.experiment import TrainIn
from app.services.validation_service import (
    infer_problem_type_from_profile,
    validate_target,
)
from app.workers.tasks import train_experiment
from sqlalchemy.orm import selectinload
from app.services.inference_service import (
    build_manifest,
    get_feature_columns,
    get_owned_model_run,
    load_pipeline,
    run_predict,
    resolve_best_model_run,
)
from app.schemas.inference import PredictIn
from app.services.storage_service import StorageService
from app.core.config import get_settings

router = APIRouter()

_export_storage = StorageService()
_settings = get_settings()


def _get_best_run(db: Session, exp: Experiment, user: User) -> ModelRun:
    if not exp or exp.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    runs = db.scalars(
        select(ModelRun).where(ModelRun.experiment_id == exp.id)
    ).all()
    exp.model_runs = runs  # attach for resolver
    run = resolve_best_model_run(db, exp)
    if not run:
        raise HTTPException(status_code=400, detail="No completed model run available")
    try:
        get_owned_model_run(run, exp, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return run

def _serialize_model_run(run: ModelRun) -> dict:
    metrics = json.loads(run.metrics_json) if run.metrics_json else None
    evaluation = json.loads(run.evaluation_json) if run.evaluation_json else None
    return {
        "id": str(run.id),
        "model_code": run.model_code,
        "status": run.status,
        "metrics": metrics,
        "evaluation": evaluation,
        "error": run.error_text,
        "train_duration_ms": run.train_duration_ms,
        "model_s3_key": run.model_s3_key,
    }


def _serialize_experiment(exp: Experiment, db: Session) -> dict:
    metrics = json.loads(exp.metrics_json) if exp.metrics_json else None
    evaluation = json.loads(exp.evaluation_json) if exp.evaluation_json else None
    runs = db.scalars(
        select(ModelRun).where(ModelRun.experiment_id == exp.id).order_by(ModelRun.created_at)
    ).all()
    return {
        "id": str(exp.id),
        "dataset_id": str(exp.dataset_id),
        "target_column": exp.target_column,
        "problem_type": exp.problem_type,
        "problem_type_override": exp.problem_type_override,
        "pipeline_kind": exp.pipeline_kind,
        "status": exp.status,
        "metrics": metrics,
        "evaluation": evaluation,
        "explanation": exp.explanation_text,
        "model_s3_key": exp.model_s3_key,
        "model_runs": [_serialize_model_run(r) for r in runs],
        "created_at": exp.created_at,
    }


@router.post("/train")
def train_model(
    payload: TrainIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dataset = db.get(Dataset, payload.dataset_id)
    if not dataset or dataset.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.status != "profiled":
        raise HTTPException(status_code=409, detail="Wait for dataset profiling to complete")
    if not dataset.profile_json:
        raise HTTPException(status_code=409, detail="Dataset profile missing")

    profile = json.loads(dataset.profile_json)
    inferred = infer_problem_type_from_profile(profile, payload.target_column)
    problem_type = payload.problem_type_override or inferred

    target_check = validate_target(profile, payload.target_column, problem_type, db)
    if not target_check["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Target validation failed", "errors": target_check["errors"]},
        )

    exp = Experiment(
        id=uuid.uuid4(),
        owner_id=user.id,
        dataset_id=dataset.id,
        target_column=payload.target_column,
        problem_type=problem_type,
        problem_type_override=payload.problem_type_override,
        status="queued",
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        owner_id=user.id,
        job_type="train_experiment",
        status="queued",
        celery_task_id="pending",
        payload_json=json.dumps({
            "experiment_id": str(exp.id),
            "model_codes": payload.model_codes,
        }),
    )
    db.add(job)
    db.commit()

    async_result = train_experiment.delay(
        job_id=str(job_id),
        experiment_id=str(exp.id),
        model_codes=payload.model_codes,
    )
    job.celery_task_id = async_result.id
    db.commit()
    db.refresh(job)

    return {
        "experiment_id": str(exp.id),
        "job_id": str(job.id),
        "task_id": job.celery_task_id,
        "problem_type": problem_type,
    }


@router.get("/")
def list_experiments(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Experiment)
        .where(Experiment.owner_id == user.id)
        .order_by(Experiment.created_at.desc())
    ).all()
    return [_serialize_experiment(exp, db) for exp in rows]


@router.get("/{experiment_id}")
def get_experiment(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.get(Experiment, experiment_id)
    if not exp or exp.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return _serialize_experiment(exp, db)


@router.get("/{experiment_id}/inference-schema")
def experiment_inference_schema(
    experiment_id: uuid.UUID,
    model_run_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.get(Experiment, experiment_id)
    if not exp or exp.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    run = db.get(ModelRun, model_run_id) if model_run_id else _get_best_run(db, exp, user)
    if model_run_id and (not run or run.experiment_id != exp.id):
        raise HTTPException(status_code=404, detail="Model run not found")
    if not model_run_id:
        run = _get_best_run(db, exp, user)
    pipe = load_pipeline(run.model_s3_key)
    return {
        "model_run_id": str(run.id),
        "model_code": run.model_code,
        "problem_type": exp.problem_type,
        "target_column": exp.target_column,
        "feature_columns": get_feature_columns(pipe),
        "dataset_id": str(exp.dataset_id),
    }


@router.get("/{experiment_id}/export")
def experiment_export(
    experiment_id: uuid.UUID,
    format: str = Query("joblib", pattern="^(joblib|manifest)$"),
    model_run_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.get(Experiment, experiment_id)
    if not exp or exp.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    run = db.get(ModelRun, model_run_id) if model_run_id else None
    if model_run_id:
        if not run or run.experiment_id != exp.id:
            raise HTTPException(status_code=404, detail="Model run not found")
    else:
        run = _get_best_run(db, exp, user)
    get_owned_model_run(run, exp, user.id)
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
    url = _export_storage.generate_presigned_download_url(
        _settings.S3_BUCKET_ARTIFACTS,
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


@router.post("/{experiment_id}/predict")
def experiment_predict(
    experiment_id: uuid.UUID,
    payload: PredictIn,
    model_run_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.get(Experiment, experiment_id)
    if not exp or exp.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if model_run_id:
        run = db.get(ModelRun, model_run_id)
        if not run or run.experiment_id != exp.id:
            raise HTTPException(status_code=404, detail="Model run not found")
    else:
        run = _get_best_run(db, exp, user)
    run, exp = get_owned_model_run(run, exp, user.id)
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