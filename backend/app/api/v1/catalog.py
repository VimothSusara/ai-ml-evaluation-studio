from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelDefinition, ProblemType
from app.db.session import get_db

router = APIRouter()


@router.get("/problem-types")
def list_problem_types(db: Session = Depends(get_db)):
    rows = db.scalars(select(ProblemType).where(ProblemType.is_active == True)).all()
    return [
        {"code": r.code, "name": r.name, "description": r.description}
        for r in rows
    ]


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    rows = db.scalars(select(ModelDefinition).where(ModelDefinition.is_active == True)).all()
    return [
        {"code": r.code, "display_name": r.display_name, "estimator_key": r.estimator_key}
        for r in rows
    ]