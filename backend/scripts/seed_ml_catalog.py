import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ProblemType, ModelDefinition, ProblemTypeModel, ModelRequirement, EvaluationProfile

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, future=True)

PROBLEM_TYPES = [
    ("classification", "Classification", "Predict discrete class labels"),
    ("regression", "Regression", "Predict continuous numeric values"),
]

MODELS = [
    ("random_forest_classifier", "Random Forest", "random_forest_classifier", {"n_estimators": 100, "random_state": 42}),
    ("logistic_regression", "Logistic Regression", "logistic_regression", {"max_iter": 1000, "random_state": 42}),
    ("random_forest_regressor", "Random Forest Regressor", "random_forest_regressor", {"n_estimators": 100, "random_state": 42}),
    ("ridge_regression", "Ridge Regression", "ridge_regression", {"alpha": 1.0, "random_state": 42}),
]

LINKS = [
    ("classification", "random_forest_classifier", 1, True, "Strong default for tabular classification"),
    ("classification", "logistic_regression", 2, True, "Fast interpretable baseline"),
    ("regression", "random_forest_regressor", 1, True, "Handles non-linear patterns"),
    ("regression", "ridge_regression", 2, True, "Stable linear baseline"),
]

REQUIREMENTS = [
    ("classification", 10, 1, 2, 50, False, 0.0),
    ("regression", 10, 1, None, None, True, 0.0),
]

EVALUATION_PROFILES = [
    (
        "classification",
        1,
        ["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
        ["confusion_matrix", "class_distribution"],
        ["roc"],
    ),
    (
        "regression",
        1,
        ["rmse", "r2", "mae"],
        ["pred_vs_actual", "residual_hist"],
        [],
    ),
]

def main():
    with Session(engine) as db:
        pt_map = {}
        for code, name, desc in PROBLEM_TYPES:
            row = db.scalar(select(ProblemType).where(ProblemType.code == code))
            if not row:
                row = ProblemType(code=code, name=name, description=desc, is_active=True)
                db.add(row)
                db.flush()
            pt_map[code] = row

        md_map = {}
        for code, display, est, params in MODELS:
            row = db.scalar(select(ModelDefinition).where(ModelDefinition.code == code))
            if not row:
                row = ModelDefinition(
                    code=code,
                    display_name=display,
                    estimator_key=est,
                    default_params_json=json.dumps(params),
                    is_active=True,
                )
                db.add(row)
                db.flush()
            md_map[code] = row

        for pt_code, md_code, priority, is_default, reason in LINKS:
            exists = db.scalar(
                select(ProblemTypeModel).where(
                    ProblemTypeModel.problem_type_id == pt_map[pt_code].id,
                    ProblemTypeModel.model_id == md_map[md_code].id,
                )
            )
            if not exists:
                db.add(
                    ProblemTypeModel(
                        problem_type_id=pt_map[pt_code].id,
                        model_id=md_map[md_code].id,
                        priority=priority,
                        is_default=is_default,
                        reason=reason,
                    )
                )

        for pt_code, min_rows, min_feat, min_cls, max_cls, numeric, miss in REQUIREMENTS:
            exists = db.scalar(
                select(ModelRequirement).where(ModelRequirement.problem_type_id == pt_map[pt_code].id)
            )
            if not exists:
                db.add(
                    ModelRequirement(
                        problem_type_id=pt_map[pt_code].id,
                        min_rows=min_rows,
                        min_features=min_feat,
                        min_classes=min_cls,
                        max_classes=max_cls,
                        target_must_be_numeric=numeric,
                        max_missing_target_ratio=miss,
                    )
                )

        db.commit()
        print("ML catalog seeded.")


if __name__ == "__main__":
    main()