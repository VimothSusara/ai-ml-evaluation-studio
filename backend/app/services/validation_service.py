import json
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelRequirement, ProblemType
from app.services.training_service import detect_problem_type


def validate_dataset_profile(profile: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    rows = profile.get("rows", 0)
    cols = profile.get("columns", 0)

    sanitization = profile.get("sanitization") or {}
    for w in sanitization.get("warnings", []):
        warnings.append(w)

    if sanitization.get("ready_for_ml") is False:
        errors.append(
            "Dataset is not ready for ML after automatic cleaning. "
            "Check dropped columns and column count."
        )

    if rows < 5:
        warnings.append("Very few rows; metrics may be unreliable.")
    if cols < 2:
        errors.append("Dataset needs at least 2 columns (features + target).")

    for name, stats in profile.get("column_stats", {}).items():
        if stats.get("is_constant"):
            warnings.append(f"Column '{name}' is constant and may be dropped at train time.")
        if stats.get("is_id_like"):
            warnings.append(f"Column '{name}' looks like an ID; excluded from features when training.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_target(profile: dict, target_column: str, problem_type: str, db: Session) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if target_column not in profile.get("column_names", []):
        errors.append(f"Target column '{target_column}' not found.")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    stats = profile.get("column_stats", {}).get(target_column, {})
    missing = stats.get("missing", 0)
    rows = profile.get("rows", 1)
    if missing / max(rows, 1) > 0:
        errors.append("Target column contains missing values.")

    pt = db.scalar(select(ProblemType).where(ProblemType.code == problem_type))
    if not pt:
        errors.append(f"Unknown problem type '{problem_type}'.")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    req = db.scalar(select(ModelRequirement).where(ModelRequirement.problem_type_id == pt.id))
    if req:
        if rows < req.min_rows:
            errors.append(f"Need at least {req.min_rows} rows for {problem_type}.")
        feature_count = profile.get("columns", 0) - 1
        if feature_count < req.min_features:
            errors.append(f"Need at least {req.min_features} feature column(s).")

        nunique = stats.get("nunique", 0)
        if problem_type == "classification":
            if stats.get("is_likely_text"):
                errors.append(
                    f"Target '{target_column}' looks like free text (too many unique values). "
                    "Choose a label column (e.g. Category, class, spam/ham), not Message/body text."
                )
            elif rows > 0 and nunique / rows > 0.5:
                errors.append(
                    f"Target '{target_column}' has {nunique} unique values in {rows} rows — "
                    "likely not class labels. Pick a categorical label column instead."
                )
            if req.min_classes and nunique < req.min_classes:
                errors.append(f"Classification needs at least {req.min_classes} classes.")
            if req.max_classes and nunique > req.max_classes:
                errors.append(f"Too many classes (>{req.max_classes}) for classification.")
            value_counts = stats.get("value_counts") or {}
            singletons = [label for label, count in value_counts.items() if count < 2]
            if singletons:
                preview = ", ".join(repr(s) for s in singletons[:3])
                more = len(singletons) - 3
                suffix = f" (+{more} more)" if more > 0 else ""
                errors.append(
                    f"Some classes appear only once (e.g. {preview}{suffix}) — "
                    "fix malformed CSV rows or choose a different target column."
                )
        if problem_type == "regression" and req.target_must_be_numeric:
            dtype = stats.get("dtype", "")
            if dtype == "object":
                errors.append("Regression target must be numeric.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def infer_problem_type_from_profile(profile: dict, target_column: str) -> str:
    dtypes = profile.get("dtypes", {})
    stats = profile.get("column_stats", {}).get(target_column, {})
    nunique = stats.get("nunique", 1)
    dtype = dtypes.get(target_column, "float64")

    series = pd.Series([0] * min(nunique, 3))
    if dtype == "object" or dtype == "bool":
        series = pd.Series(["a"] * min(nunique, 3))
    return detect_problem_type(series)