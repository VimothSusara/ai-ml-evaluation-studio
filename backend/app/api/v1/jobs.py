import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Job, User
from app.db.session import get_db
from app.services.job_service import list_jobs_for_user, serialize_job

router = APIRouter()


@router.get("/")
def list_jobs(
    active_only: bool = Query(False, description="Only queued and running jobs"),
    status: str | None = Query(None, description="Comma-separated: queued,running,completed,failed"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = list_jobs_for_user(
        db,
        user.id,
        status=status,
        active_only=active_only,
        limit=limit,
    )
    return [serialize_job(job, db) for job in rows]


@router.get("/{job_id}")
def job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.get(Job, job_id)
    if not job or job.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job, db)