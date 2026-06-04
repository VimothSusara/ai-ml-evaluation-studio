import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelDefinition, ProblemType, ProblemTypeModel
from app.services.validation_service import infer_problem_type_from_profile, validate_target


def get_recommendations(
    db: Session,
    profile_json: str,
    target_column: str,
    problem_type_override: str | None = None,
) -> dict:
    profile = json.loads(profile_json)
    inferred = infer_problem_type_from_profile(profile, target_column)
    problem_type = problem_type_override or inferred

    target_validation = validate_target(profile, target_column, problem_type, db)

    pt = db.scalar(select(ProblemType).where(ProblemType.code == problem_type, ProblemType.is_active == True))
    if not pt:
        raise ValueError(f"Problem type not supported: {problem_type}")

    links = db.scalars(
        select(ProblemTypeModel)
        .where(ProblemTypeModel.problem_type_id == pt.id)
        .order_by(ProblemTypeModel.priority)
    ).all()

    recommendations = []
    for link in links:
        model = db.get(ModelDefinition, link.model_id)
        if not model or not model.is_active:
            continue
        recommendations.append({
            "model_code": model.code,
            "display_name": model.display_name,
            "priority": link.priority,
            "is_default": link.is_default,
            "reason": link.reason,
            "estimator_key": model.estimator_key,
        })

    return {
        "target_column": target_column,
        "inferred_problem_type": inferred,
        "problem_type": problem_type,
        "target_validation": target_validation,
        "recommendations": recommendations,
    }


def resolve_model_codes(
    db: Session,
    problem_type: str,
    requested_codes: list[str] | None,
) -> list[tuple[str, str, str | None]]:
    """Returns list of (model_code, estimator_key, params_json)."""
    pt = db.scalar(select(ProblemType).where(ProblemType.code == problem_type))
    if not pt:
        raise ValueError(f"Unknown problem type: {problem_type}")

    links = db.scalars(
        select(ProblemTypeModel).where(ProblemTypeModel.problem_type_id == pt.id)
    ).all()

    allowed = {}
    for link in links:
        m = db.get(ModelDefinition, link.model_id)
        if m and m.is_active:
            allowed[m.code] = (m.estimator_key, m.default_params_json)

    if requested_codes:
        codes = [c for c in requested_codes if c in allowed]
        if not codes:
            raise ValueError("None of the requested models are valid for this problem type")
    else:
        codes = [c for c, _ in allowed.items()]

    return [(code, allowed[code][0], allowed[code][1]) for code in codes]