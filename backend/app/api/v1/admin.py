from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.api.deps import require_roles
from app.core.roles import Role
from app.db.models import User, Dataset, Experiment
from app.db.session import get_db

router = APIRouter()


@router.get("/stats")
def admin_stats(
    _: User = Depends(require_roles(Role.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    user_count = db.scalar(select(func.count()).select_from(User))
    dataset_count = db.scalar(select(func.count()).select_from(Dataset))
    experiment_count = db.scalar(select(func.count()).select_from(Experiment))
    return {
        "users": user_count,
        "datasets": dataset_count,
        "experiments": experiment_count,
    }