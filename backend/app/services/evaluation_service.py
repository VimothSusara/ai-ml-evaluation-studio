from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_curve,
    root_mean_squared_error,
)

EVALUATION_SCHEMA_VERSION = 1

DEFAULT_PROFILES: dict[str, dict[str, list[str]]] = {
    "classification": {
        "required_metrics": [
            "accuracy",
            "f1_weighted",
            "precision_weighted",
            "recall_weighted",
        ],
        "required_plots": ["confusion_matrix", "class_distribution"],
        "optional_plots": ["roc"],
    },
    "regression": {
        "required_metrics": ["rmse", "r2", "mae"],
        "required_plots": ["pred_vs_actual", "residual_hist"],
        "optional_plots": [],
    },
}


def load_profile_config(profile_row: Any | None, problem_type: str) -> dict[str, list[str]]:
    if profile_row is not None:
        return {
            "required_metrics": json.loads(profile_row.required_metrics_json),
            "required_plots": json.loads(profile_row.required_plots_json),
            "optional_plots": json.loads(profile_row.optional_plots_json or "[]"),
        }
    return DEFAULT_PROFILES[problem_type]


def _label_str(values: pd.Series | np.ndarray) -> list[str]:
    if isinstance(values, pd.Series):
        return [str(v) for v in values.unique()]
    return [str(v) for v in np.unique(values)]


def _class_counts(y: pd.Series) -> dict[str, int]:
    counts = y.value_counts(dropna=False)
    return {str(k): int(v) for k, v in counts.items()}


def _subsample_xy(
    x: np.ndarray,
    y: np.ndarray,
    max_points: int = 500,
) -> list[dict[str, float]]:
    n = len(x)
    if n == 0:
        return []
    idx = np.arange(n)
    if n > max_points:
        rng = np.random.default_rng(42)
        idx = rng.choice(idx, size=max_points, replace=False)
    return [
        {"actual": float(x[i]), "predicted": float(y[i])}
        for i in idx
    ]


def _downsample_curve(fpr: np.ndarray, tpr: np.ndarray, max_points: int = 50) -> list[dict[str, float]]:
    if len(fpr) <= max_points:
        return [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)]
    idx = np.linspace(0, len(fpr) - 1, max_points, dtype=int)
    return [{"fpr": float(fpr[i]), "tpr": float(tpr[i])} for i in idx]


def build_classification_evaluation(
    y_train: pd.Series,
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None,
    split_meta: dict[str, Any],
    profile_config: dict[str, list[str]],
) -> dict[str, Any]:
    labels = sorted({str(v) for v in pd.concat([y_train, y_test]).unique()})
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    warnings: list[str] = []

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "precision_weighted": float(
            precision_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
    }

    train_counts = _class_counts(y_train)
    test_counts = _class_counts(y_test)
    imbalance_ratio = max(train_counts.values()) / max(min(train_counts.values()), 1)
    if imbalance_ratio > 3:
        warnings.append(
            f"Classes are imbalanced in the training split (~{imbalance_ratio:.1f}:1). "
            "Weighted F1 and the confusion matrix are more informative than accuracy alone."
        )

    tables = {
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm.astype(int).tolist(),
        },
        "class_distribution": {
            "labels": labels,
            "train": [train_counts.get(l, 0) for l in labels],
            "test": [test_counts.get(l, 0) for l in labels],
        },
    }

    plots: dict[str, Any] = {
        "confusion_matrix": {
            "type": "heatmap",
            "labels": labels,
            "matrix": cm.astype(int).tolist(),
        },
        "class_distribution": {
            "type": "grouped_bar",
            "labels": labels,
            "train": [train_counts.get(l, 0) for l in labels],
            "test": [test_counts.get(l, 0) for l in labels],
        },
    }

    if len(labels) == 2 and y_prob is not None:
        try:
            y_bin = (y_test.astype(str) == labels[1]).astype(int).to_numpy()
            if y_prob.ndim == 2 and y_prob.shape[1] >= 2:
                scores = y_prob[:, 1]
            else:
                scores = y_prob
            fpr, tpr, _ = roc_curve(y_bin, scores)
            roc_auc = float(auc(fpr, tpr))
            metrics["roc_auc"] = roc_auc
            plots["roc"] = {
                "type": "curve",
                "auc": roc_auc,
                "points": _downsample_curve(fpr, tpr),
            }
        except Exception as exc:
            warnings.append(f"ROC curve skipped: {exc}")
    elif len(labels) > 2:
        warnings.append(
            f"ROC curve is shown for binary targets only ({len(labels)} classes here). "
            "Use the confusion matrix, class distribution, and F1 for this model."
        )

    return {
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "problem_type": "classification",
        "evaluator": "sklearn_v1",
        "profile": profile_config,
        "split": split_meta,
        "metrics": metrics,
        "tables": tables,
        "plots": plots,
        "warnings": warnings,
    }


def build_regression_evaluation(
    y_test: pd.Series,
    y_pred: np.ndarray,
    split_meta: dict[str, Any],
    profile_config: dict[str, list[str]],
) -> dict[str, Any]:
    warnings: list[str] = []
    y_true = y_test.to_numpy(dtype=float)
    y_hat = np.asarray(y_pred, dtype=float)
    residuals = y_true - y_hat

    metrics = {
        "rmse": float(root_mean_squared_error(y_true, y_hat)),
        "r2": float(r2_score(y_true, y_hat)),
        "mae": float(mean_absolute_error(y_true, y_hat)),
    }

    if metrics["r2"] < 0:
        warnings.append("Negative R² indicates the model performs worse than a mean baseline.")

    hist_counts, bin_edges = np.histogram(residuals, bins=20)
    plots = {
        "pred_vs_actual": {
            "type": "scatter",
            "points": _subsample_xy(y_true, y_hat),
        },
        "residual_hist": {
            "type": "histogram",
            "bins": [float(x) for x in bin_edges.tolist()],
            "counts": [int(x) for x in hist_counts.tolist()],
        },
    }

    return {
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "problem_type": "regression",
        "evaluator": "sklearn_v1",
        "profile": profile_config,
        "split": split_meta,
        "metrics": metrics,
        "tables": {},
        "plots": plots,
        "warnings": warnings,
    }


def build_evaluation(
    problem_type: str,
    y_train: pd.Series,
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None,
    split_meta: dict[str, Any],
    profile_config: dict[str, list[str]],
) -> dict[str, Any]:
    if problem_type == "classification":
        return build_classification_evaluation(
            y_train, y_test, y_pred, y_prob, split_meta, profile_config
        )
    if problem_type == "regression":
        return build_regression_evaluation(y_test, y_pred, split_meta, profile_config)
    raise ValueError(f"Unsupported problem_type for evaluation: {problem_type}")


def validate_evaluation_payload(
    evaluation: dict[str, Any],
    profile_config: dict[str, list[str]],
) -> list[str]:
    missing: list[str] = []
    metrics = evaluation.get("metrics", {})
    plots = evaluation.get("plots", {})

    for key in profile_config.get("required_metrics", []):
        if key not in metrics:
            missing.append(f"missing metric: {key}")

    for key in profile_config.get("required_plots", []):
        if key not in plots:
            missing.append(f"missing plot: {key}")

    return missing