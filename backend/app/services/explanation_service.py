def explain_metrics(problem_type: str, metrics: dict) -> str:
    if problem_type == "classification":
        acc = metrics.get("accuracy", 0.0)
        f1 = metrics.get("f1_weighted", 0.0)
        prec = metrics.get("precision_weighted", 0.0)
        rec = metrics.get("recall_weighted", 0.0)
        auc_val = metrics.get("roc_auc")
        base = (
            f"Classification: accuracy={acc:.3f}, F1={f1:.3f}, "
            f"precision={prec:.3f}, recall={rec:.3f}."
        )
        if auc_val is not None:
            base += f" ROC AUC={auc_val:.3f}."
        return base + " Inspect confusion matrix and class balance for error patterns."

    rmse = metrics.get("rmse", 0.0)
    r2 = metrics.get("r2", 0.0)
    mae = metrics.get("mae", 0.0)
    return (
        f"Regression: RMSE={rmse:.3f}, MAE={mae:.3f}, R²={r2:.3f}. "
        "Check predicted vs actual and residual distribution for systematic bias."
    )


def explain_evaluation(evaluation: dict) -> str:
    return explain_metrics(
        evaluation.get("problem_type", "regression"),
        evaluation.get("metrics", {}),
    )