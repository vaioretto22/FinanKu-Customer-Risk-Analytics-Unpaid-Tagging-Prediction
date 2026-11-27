"""Window-agnostic feature engineering.

The same function builds features for Data All (q1..q4) and Data Validasi (q2..q5).
Features are named by meaning ("balance start/end of the 4-quarter window"), not by
calendar quarter, so both windows have identical column names and order.

The target is never read here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .preprocessing import ID_COL

WINDOW_ALL = ("q1", "q2", "q3", "q4")
WINDOW_VALIDASI = ("q2", "q3", "q4", "q5")

CATEGORICAL_FEATURES = ["branch_code", "city"]


def _matrix(df: pd.DataFrame, prefix: str, quarters) -> np.ndarray:
    cols = [f"{prefix}_{q}" for q in quarters]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns for window {quarters}: {missing}")
    return df[cols].to_numpy(dtype=float)


def build_features(df: pd.DataFrame, quarters) -> pd.DataFrame:
    """Build predictors for one 4-quarter window. Returns a frame indexed by customer_id.

    Zero starting balance: balance_change_pct is NaN (undefined), and
    balance_start_is_zero flags those customers. Imputation, if any, happens
    later inside the modeling pipeline (fit on training data only).
    """
    quarters = tuple(quarters)
    if len(quarters) != 4:
        raise ValueError("Exactly four consecutive quarters are required")

    bal = _matrix(df, "balance", quarters)
    prod = _matrix(df, "num_products", quarters)
    act = _matrix(df, "active_member", quarters)
    card = _matrix(df, "has_credit_card", quarters)

    bal_start, bal_end = bal[:, 0], bal[:, -1]
    with np.errstate(divide="ignore", invalid="ignore"):
        bal_pct = np.where(bal_start > 0, (bal_end - bal_start) / bal_start, np.nan)

    f = {
        # A. Customer profile
        "age": df["age"].to_numpy(dtype=float),
        "branch_code": df["branch_code"].astype(str).to_numpy(),
        "city": df["city"].astype(str).to_numpy(),
        "income_measure": df["income_measure"].to_numpy(dtype=float),
        "income_is_zero": (df["income_measure"].to_numpy() == 0).astype(int),
        # B. Account balance
        "balance_mean": bal.mean(axis=1),
        "balance_min": bal.min(axis=1),
        "balance_max": bal.max(axis=1),
        "balance_std": bal.std(axis=1, ddof=1),
        "balance_start": bal_start,
        "balance_end": bal_end,
        "balance_change_abs": bal_end - bal_start,
        "balance_change_pct": bal_pct,
        "balance_start_is_zero": (bal_start == 0).astype(int),
        "n_zero_balance_quarters": (bal == 0).sum(axis=1),
        # C. Product ownership
        "products_mean": prod.mean(axis=1),
        "products_min": prod.min(axis=1),
        "products_max": prod.max(axis=1),
        "products_start": prod[:, 0],
        "products_end": prod[:, -1],
        "products_change": prod[:, -1] - prod[:, 0],
        # D. Customer activity
        "active_rate": act.mean(axis=1),
        "active_start": act[:, 0],
        "active_end": act[:, -1],
        "active_change": act[:, -1] - act[:, 0],
        "n_active_quarters": act.sum(axis=1),
        # E. Credit card
        "card_rate": card.mean(axis=1),
        "n_card_quarters": card.sum(axis=1),
        "card_start": card[:, 0],
        "card_end": card[:, -1],
    }
    out = pd.DataFrame(f, index=pd.Index(df[ID_COL].to_numpy(), name=ID_COL))
    count_cols = [
        "income_is_zero", "balance_start_is_zero", "n_zero_balance_quarters",
        "products_min", "products_max", "products_start", "products_end",
        "products_change", "active_start", "active_end", "active_change",
        "n_active_quarters", "n_card_quarters", "card_start", "card_end",
    ]
    out[count_cols] = out[count_cols].astype(int)
    return out


def detect_constant_features(features: pd.DataFrame) -> list[str]:
    """Columns with a single unique value (NaN ignored)."""
    return [c for c in features.columns if features[c].nunique(dropna=True) <= 1]


def assert_same_schema(a: pd.DataFrame, b: pd.DataFrame) -> None:
    """Same columns, same order, same dtypes in both windows."""
    if list(a.columns) != list(b.columns):
        raise AssertionError("Feature names/order differ between windows")
    if not (a.dtypes == b.dtypes).all():
        raise AssertionError("Feature dtypes differ between windows")


def redundant_pairs(features: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """Highly correlated numeric feature pairs (candidates to drop in modeling)."""
    corr = features.select_dtypes("number").corr().abs()
    rows = []
    cols = list(corr.columns)
    for i, ci in enumerate(cols):
        for cj in cols[i + 1:]:
            if corr.loc[ci, cj] >= threshold:
                rows.append({"feature_1": ci, "feature_2": cj, "abs_corr": corr.loc[ci, cj]})
    return pd.DataFrame(rows).sort_values("abs_corr", ascending=False, ignore_index=True)


# ---------------------------------------------------------------------------
# Model feature sets (used from Phase 5/6)
# ---------------------------------------------------------------------------
# The meaning of the credit-card indicator is unknown and it is strongly tied to the
# tag (see reports/eda_findings.md), so two sets are defined and BOTH are evaluated:
#   - "no_card"   : conservative primary set, no credit-card information
#   - "with_card" : adds card_start (n_card_quarters / card_rate carry the same information
#                   as card_start; card_end is constant and excluded)
# Redundant duplicates are removed (products_min == products_start, products_max == products_end,
# active_rate == n_active_quarters / 4, balance level features are almost collinear).
NO_CARD_FEATURES = [
    "age", "branch_code", "city", "income_measure", "income_is_zero",
    "balance_mean", "balance_std", "balance_change_abs", "balance_change_pct",
    "balance_start_is_zero", "n_zero_balance_quarters",
    "products_mean", "products_start", "products_end", "products_change",
    "active_rate", "active_start", "active_end", "active_change",
]
WITH_CARD_FEATURES = NO_CARD_FEATURES + ["card_start"]


def get_feature_set(name: str) -> list[str]:
    """Return the feature list for 'no_card' or 'with_card'."""
    sets = {"no_card": NO_CARD_FEATURES, "with_card": WITH_CARD_FEATURES}
    if name not in sets:
        raise ValueError(f"Unknown feature set '{name}'. Choose from {list(sets)}")
    return list(sets[name])
