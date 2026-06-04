import json
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge


REGISTRY = {
    "random_forest_classifier": RandomForestClassifier,
    "logistic_regression": LogisticRegression,
    "random_forest_regressor": RandomForestRegressor,
    "ridge_regression": Ridge,
}


def build_estimator(estimator_key: str, params_json: str | None):
    cls = REGISTRY.get(estimator_key)
    if not cls:
        raise ValueError(f"Unknown estimator: {estimator_key}")
    params = json.loads(params_json) if params_json else {}
    return cls(**params)