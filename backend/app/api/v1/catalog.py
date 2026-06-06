from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelDefinition, ProblemType, ProblemTypeModel
from app.db.session import get_db

router = APIRouter()


@router.get("/problem-types")
def list_problem_types(db: Session = Depends(get_db)):
    rows = db.scalars(select(ProblemType).where(ProblemType.is_active == True)).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "pipeline_kind": r.pipeline_kind,
        }
        for r in rows
    ]


@router.get("/problem-types/{code}/models")
def list_models_for_problem_type(code: str, db: Session = Depends(get_db)):
    pt = db.scalar(select(ProblemType).where(ProblemType.code == code))
    if not pt:
        return {"problem_type": code, "models": []}

    links = db.scalars(
        select(ProblemTypeModel)
        .where(ProblemTypeModel.problem_type_id == pt.id)
        .order_by(ProblemTypeModel.priority)
    ).all()

    models = []
    for link in links:
        m = db.get(ModelDefinition, link.model_id)
        if not m or not m.is_active:
            continue
        models.append(
            {
                "code": m.code,
                "display_name": m.display_name,
                "estimator_key": m.estimator_key,
                "is_default": link.is_default,
                "reason": link.reason,
            }
        )

    return {
        "problem_type": code,
        "pipeline_kind": pt.pipeline_kind,
        "models": models,
    }


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    rows = db.scalars(select(ModelDefinition).where(ModelDefinition.is_active == True)).all()
    return [
        {"code": r.code, "display_name": r.display_name, "estimator_key": r.estimator_key}
        for r in rows
    ]