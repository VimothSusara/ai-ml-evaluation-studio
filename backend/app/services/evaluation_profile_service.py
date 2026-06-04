import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EvaluationProfile, ProblemType
from app.services.evaluation_service import DEFAULT_PROFILES, load_profile_config


def get_evaluation_profile(db: Session, problem_type_code: str) -> dict[str, list[str]]:
    row = db.scalar(
        select(EvaluationProfile)
        .join(ProblemType, EvaluationProfile.problem_type_id == ProblemType.id)
        .where(
            ProblemType.code == problem_type_code,
            EvaluationProfile.is_active.is_(True),
        )
        .order_by(EvaluationProfile.schema_version.desc())
    )
    return load_profile_config(row, problem_type_code)