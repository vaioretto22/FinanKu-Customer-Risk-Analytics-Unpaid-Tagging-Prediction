"""Model building for Phase 6 (Unpaid Tagging classification).

Design rules:
- The preprocessing (imputation, scaling, encoding) lives INSIDE the sklearn Pipeline, so it is fitted only on training data
  (inside every cross-validation fold as well). No information from validation/test rows leaks into preprocessing.
- Customer ID and the target are never features. Feature sets come from src.feature_engineering.get_feature_set.
- Data Validasi is not used anywhere in this module or in the Phase 6 notebook.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .feature_engineering import CATEGORICAL_FEATURES

RANDOM_STATE = 42


def build_preprocessor(feature_names: list[str], scale: bool = True) -> ColumnTransformer:
    """Numeric: median imputation (only balance_change_pct has NaN, flagged by balance_start_is_zero) + optional standard scaling.
    Categorical (city, branch_code): one-hot, unseen categories ignored.
    Scaling is skipped for tree-based models (they are scale-invariant, and raw thresholds stay readable)."""
    categorical = [c for c in feature_names if c in CATEGORICAL_FEATURES]
    numeric = [c for c in feature_names if c not in CATEGORICAL_FEATURES]
    steps = [("impute", SimpleImputer(strategy="median"))] + ([("scale", StandardScaler())] if scale else [])
    return ColumnTransformer([
        ("num", Pipeline(steps), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])


TREE_BASED = ("Decision tree", "Random forest", "Gradient boosting")


def make_pipeline(estimator, feature_names: list[str], scale: bool = True) -> Pipeline:
    """Preprocessing -> constant-feature removal -> estimator."""
    return Pipeline([
        ("prep", build_preprocessor(feature_names, scale=scale)),
        ("constant", VarianceThreshold(0.0)),
        ("model", estimator),
    ])


def base_models() -> dict:
    """Baselines and alternative models (tuned later with GridSearchCV)."""
    return {
        "Dummy (class prior)": DummyClassifier(strategy="prior"),
        "Logistic regression": LogisticRegression(max_iter=2000),
        "Decision tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "Random forest": RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
    }


def param_grids() -> dict:
    """Small, deliberate grids (regularised settings, because associations are weak and overfitting is a risk)."""
    return {
        "Dummy (class prior)": {},
        "Logistic regression": {"model__C": [0.01, 0.1, 1.0, 10.0]},
        "Decision tree": {"model__max_depth": [2, 3, 4, 6], "model__min_samples_leaf": [20, 50, 100]},
        "Random forest": {"model__max_depth": [4, 6, 10], "model__min_samples_leaf": [10, 30, 60]},
        "Gradient boosting": {"model__n_estimators": [100, 200], "model__max_depth": [2, 3],
                              "model__learning_rate": [0.03, 0.1]},
    }


def cv_splitter(n_splits: int = 5) -> StratifiedKFold:
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def tune_model(name: str, X_train: pd.DataFrame, y_train: pd.Series, feature_names: list[str],
               scoring: str = "roc_auc", n_splits: int = 5) -> GridSearchCV:
    """Grid search with stratified CV on the TRAINING set only. Returns the fitted GridSearchCV."""
    pipe = make_pipeline(base_models()[name], feature_names, scale=name not in TREE_BASED)
    grid = param_grids()[name] or {"model__strategy": ["prior"]}      # Dummy has nothing to tune
    gs = GridSearchCV(pipe, grid, scoring=scoring, cv=cv_splitter(n_splits), n_jobs=-1, refit=True)
    return gs.fit(X_train[feature_names], y_train)


def out_of_fold_proba(best_pipeline: Pipeline, X_train: pd.DataFrame, y_train: pd.Series,
                      feature_names: list[str], n_splits: int = 5) -> np.ndarray:
    """Out-of-fold predicted probabilities on the training set (to choose a threshold without touching the test set)."""
    return cross_val_predict(best_pipeline, X_train[feature_names], y_train, cv=cv_splitter(n_splits),
                             method="predict_proba", n_jobs=-1)[:, 1]
