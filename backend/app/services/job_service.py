import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Dataset, Experiment, Job

JOB_TYPE_LABELS = {
    "eda_profile": "Dataset profiling",
    "train_experiment": "Model training",
}


def _parse_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _build_context(job: Job, db: Session) -> dict[str, Any]:
    payload = _parse_json(job.payload_json) or {}
    result = _parse_json(job.result_json) or {}
    context: dict[str, Any] = {"label": JOB_TYPE_LABELS.get(job.job_type, job.job_type)}

    if job.job_type == "eda_profile":
        dataset_id = payload.get("dataset_id") or result.get("dataset_id")
        if dataset_id:
            ds = db.get(Dataset, uuid.UUID(str(dataset_id)))
            if ds:
                context["dataset_id"] = str(ds.id)
                context["dataset_name"] = ds.name
                context["dataset_status"] = ds.status

    if job.job_type == "train_experiment":
        experiment_id = payload.get("experiment_id") or result.get("experiment_id")
        if experiment_id:
            exp = db.get(Experiment, uuid.UUID(str(experiment_id)))
            if exp:
                context["experiment_id"] = str(exp.id)
                context["target_column"] = exp.target_column
                context["problem_type"] = exp.problem_type
                ds = db.get(Dataset, exp.dataset_id)
                if ds:
                    context["dataset_name"] = ds.name
                    context["dataset_id"] = str(ds.id)
        if result.get("best_model"):
            context["best_model"] = result["best_model"]

    return context


def serialize_job(job: Job, db: Session) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "celery_task_id": job.celery_task_id,
        "payload": _parse_json(job.payload_json),
        "result": _parse_json(job.result_json),
        "error": job.error_text,
        "created_at": job.created_at,
        "context": _build_context(job, db),
    }


def list_jobs_for_user(
    db: Session,
    user_id: uuid.UUID,
    *,
    status: str | None = None,
    active_only: bool = False,
    limit: int = 50,
) -> list[Job]:
    q = select(Job).where(Job.owner_id == user_id).order_by(Job.created_at.desc()).limit(limit)

    if active_only:
        q = q.where(Job.status.in_(["queued", "running"]))
    elif status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if statuses:
            q = q.where(Job.status.in_(statuses))

    return list(db.scalars(q).all())