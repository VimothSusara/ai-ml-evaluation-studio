import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.models import Dataset, Job, User
from app.db.session import get_db
from app.schemas.dataset import ValidateIn
from app.services.recommendation_service import get_recommendations as fetch_recommendations
from app.services.storage_service import StorageService
from app.services.validation_service import (
    infer_problem_type_from_profile,
    validate_dataset_profile,
    validate_target,
)
from app.workers.tasks import run_dataset_profile

router = APIRouter()
settings = get_settings()
storage = StorageService()


class RecommendIn(BaseModel):
    target_column: str
    problem_type_override: str | None = None


def _serialize_dataset(ds: Dataset) -> dict:
    profile = json.loads(ds.profile_json) if ds.profile_json else None
    validation = json.loads(ds.validation_json) if ds.validation_json else None
    return {
        "id": str(ds.id),
        "name": ds.name,
        "status": ds.status,
        "profile": profile,
        "validation": validation,
        "created_at": ds.created_at,
    }


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported in V1")

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")

    storage.ensure_bucket(settings.S3_BUCKET_DATASETS)
    storage.ensure_bucket(settings.S3_BUCKET_ARTIFACTS)

    dataset_id = uuid.uuid4()
    key = f"{user.id}/{dataset_id}/{file.filename}"
    storage.upload_bytes(settings.S3_BUCKET_DATASETS, key, content, "text/csv")

    dataset = Dataset(
        id=dataset_id,
        owner_id=user.id,
        name=file.filename,
        s3_key=key,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        owner_id=user.id,
        job_type="eda_profile",
        status="queued",
        celery_task_id="pending",
        payload_json=json.dumps({"dataset_id": str(dataset.id)}),
    )
    db.add(job)
    db.commit()

    async_result = run_dataset_profile.delay(
        job_id=str(job_id),
        dataset_id=str(dataset.id),
    )
    job.celery_task_id = async_result.id
    db.commit()
    db.refresh(job)

    return {
        "dataset_id": str(dataset.id),
        "job_id": str(job.id),
        "task_id": job.celery_task_id,
    }


@router.get("/")
def list_my_datasets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Dataset).where(Dataset.owner_id == user.id).order_by(Dataset.created_at.desc())
    ).all()
    return [_serialize_dataset(ds) for ds in rows]


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = db.get(Dataset, dataset_id)
    if not ds or ds.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _serialize_dataset(ds)


@router.get("/{dataset_id}/columns")
def get_dataset_columns(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = db.get(Dataset, dataset_id)
    if not ds or ds.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not ds.profile_json:
        raise HTTPException(status_code=409, detail="Dataset profiling not complete")

    profile = json.loads(ds.profile_json)
    return {
        "dataset_id": str(ds.id),
        "columns": profile.get("column_names", []),
        "dtypes": profile.get("dtypes", {}),
        "missing": profile.get("missing", {}),
        "column_stats": profile.get("column_stats", {}),
    }


@router.post("/{dataset_id}/validate")
def validate_dataset_for_target(
    dataset_id: uuid.UUID,
    payload: ValidateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = db.get(Dataset, dataset_id)
    if not ds or ds.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not ds.profile_json:
        raise HTTPException(status_code=409, detail="Profiling not complete")

    profile = json.loads(ds.profile_json)
    dataset_check = validate_dataset_profile(profile)
    inferred = infer_problem_type_from_profile(profile, payload.target_column)
    problem_type = payload.problem_type_override or inferred
    target_check = validate_target(profile, payload.target_column, problem_type, db)

    result = {
        "dataset_id": str(ds.id),
        "inferred_problem_type": inferred,
        "problem_type": problem_type,
        "dataset_validation": dataset_check,
        "target_validation": target_check,
        "ready_to_train": dataset_check["is_valid"] and target_check["is_valid"],
    }
    ds.validation_json = json.dumps(result)
    db.commit()
    return result


@router.post("/{dataset_id}/recommendations")
def dataset_recommendations(
    dataset_id: uuid.UUID,
    payload: RecommendIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ds = db.get(Dataset, dataset_id)
    if not ds or ds.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not ds.profile_json:
        raise HTTPException(status_code=409, detail="Dataset profiling not complete")

    try:
        return fetch_recommendations(
            db,
            ds.profile_json,
            payload.target_column,
            payload.problem_type_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc