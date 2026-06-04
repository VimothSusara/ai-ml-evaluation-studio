import io
import time
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.evaluation_service import build_evaluation
from app.services.model_registry import build_estimator
from app.services.profiling_service import is_id_like_column, is_junk_column, load_csv_bytes

TEST_SIZE = 0.2
RANDOM_STATE = 42


def stratify_labels(y: pd.Series) -> pd.Series | None:
    """Use stratified split only when every class has at least 2 samples."""
    if y.nunique(dropna=True) <= 1:
        return None
    counts = y.value_counts(dropna=True)
    if counts.empty or int(counts.min()) < 2:
        return None
    return y


def detect_problem_type(y: pd.Series) -> str:
    if y.dtype == "object" or str(y.dtype) == "bool" or y.nunique(dropna=True) <= 20:
        return "classification"
    return "regression"


def drop_bad_feature_columns(X: pd.DataFrame) -> pd.DataFrame:
    keep = []
    n_rows = len(X)
    for col in X.columns:
        if is_junk_column(col, X[col], n_rows):
            continue
        if X[col].nunique(dropna=True) <= 1:
            continue
        keep.append(col)
    if not keep:
        raise ValueError("No usable feature columns after cleaning")
    return X[keep]


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    num_cols = X.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    transformers = []
    if num_cols:
        transformers.append(
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]),
                num_cols,
            )
        )
    if cat_cols:
        transformers.append(
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore")),
                ]),
                cat_cols,
            )
        )
    if not transformers:
        raise ValueError("No usable feature columns found")
    return ColumnTransformer(transformers)


def compute_metrics(problem_type: str, y_test, pred) -> dict[str, float]:
    if problem_type == "classification":
        return {
            "accuracy": float(accuracy_score(y_test, pred)),
            "f1_weighted": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
        }
    return {
        "rmse": float(root_mean_squared_error(y_test, pred)),
        "r2": float(r2_score(y_test, pred)),
    }


def train_single_model(
    csv_bytes: bytes,
    target_column: str,
    problem_type: str,
    estimator_key: str,
    params_json: str | None,
    profile_config: dict[str, list[str]],
) -> tuple[dict[str, float], bytes, dict[str, Any]]:
    df = load_csv_bytes(csv_bytes)
    if target_column not in df.columns:
        raise ValueError("Target column not found")

    y = df[target_column]
    X = drop_bad_feature_columns(df.drop(columns=[target_column]))

    pre = build_preprocessor(X)
    model = build_estimator(estimator_key, params_json)
    pipe = Pipeline([("pre", pre), ("model", model)])

    stratify = (
        stratify_labels(y) if problem_type == "classification" else None
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )

    start = time.perf_counter()
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    duration_ms = int((time.perf_counter() - start) * 1000)

    y_prob = None
    if problem_type == "classification" and hasattr(pipe, "predict_proba"):
        try:
            y_prob = pipe.predict_proba(X_test)
        except Exception:
            y_prob = None

    split_meta = {
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
    }

    evaluation = build_evaluation(
        problem_type=problem_type,
        y_train=y_train,
        y_test=y_test,
        y_pred=pred,
        y_prob=y_prob,
        split_meta=split_meta,
        profile_config=profile_config,
    )

    metrics = dict(evaluation["metrics"])
    metrics["train_duration_ms"] = duration_ms

    buf = io.BytesIO()
    joblib.dump(pipe, buf)
    return metrics, buf.getvalue(), evaluation


def pick_best_run(runs: list[dict[str, Any]], problem_type: str) -> dict[str, Any] | None:
    ok = [r for r in runs if r.get("status") == "completed" and r.get("metrics")]
    if not ok:
        return None
    if problem_type == "classification":
        return max(ok, key=lambda r: r["metrics"].get("f1_weighted", 0))
    return max(ok, key=lambda r: r["metrics"].get("r2", -1e9))