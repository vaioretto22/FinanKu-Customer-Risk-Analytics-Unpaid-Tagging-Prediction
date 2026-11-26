"""Loading, column standardization, validation and light cleaning.

Design rules (Phase 2):
- Never delete rows silently. Anomalies are flagged/documented, not removed.
- Customer ID is kept as an identifier, never as a predictive feature.
- Branch Code is categorical (string), not numeric.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ID_COL = "customer_id"
TARGET = "unpaid_tagging"
PROFILE_COLS = ["branch_code", "city", "age", "income_measure"]

_BASE_RENAME = {
    "Customer ID": "customer_id",
    "Branch Code": "branch_code",
    "City": "city",
    "Age": "age",
    "Avg. Annual Income/Month": "income_measure",
    "Unpaid Tagging": "unpaid_tagging",
}
_QUARTER_PREFIX = {
    "Balance": "balance",
    "NumOfProducts": "num_products",
    "HasCrCard": "has_credit_card",
    "ActiveMember": "active_member",
}
_QUARTER_PATTERN = re.compile(r"(Balance|NumOfProducts|HasCrCard|ActiveMember) Q(\d+)")

BINARY_PREFIXES = ("has_credit_card", "active_member")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw columns to snake_case, e.g. 'Balance Q1' -> 'balance_q1'."""
    rename = dict(_BASE_RENAME)
    for col in df.columns:
        m = _QUARTER_PATTERN.fullmatch(col)
        if m:
            rename[col] = f"{_QUARTER_PREFIX[m.group(1)]}_q{m.group(2)}"
    unmapped = [c for c in df.columns if c not in rename]
    if unmapped:
        raise ValueError(f"Unexpected columns, cannot standardize: {unmapped}")
    return df.rename(columns=rename)


def quarter_columns(df: pd.DataFrame, prefix: str) -> list[str]:
    """All quarterly columns for a prefix, in quarter order (e.g. balance_q1..q4)."""
    cols = [c for c in df.columns if re.fullmatch(rf"{prefix}_q\d+", c)]
    return sorted(cols, key=lambda c: int(c.rsplit("q", 1)[1]))


def validate(df: pd.DataFrame) -> list[str]:
    """Return a list of data issues (empty list = no issue). Does not modify data."""
    issues: list[str] = []
    if df.isna().any().any():
        issues.append("missing values present")
    if df[ID_COL].duplicated().any():
        issues.append("duplicate customer_id")
    if (df["age"] <= 0).any():
        issues.append("non-positive age")
    if (df["income_measure"] < 0).any():
        issues.append("negative income_measure")
    for col in quarter_columns(df, "balance"):
        if (df[col] < 0).any():
            issues.append(f"negative values in {col}")
    for col in quarter_columns(df, "num_products"):
        if (df[col] < 0).any() or (df[col] % 1 != 0).any():
            issues.append(f"{col} is not a non-negative integer")
    for prefix in BINARY_PREFIXES:
        for col in quarter_columns(df, prefix):
            if not set(df[col].unique()) <= {0, 1}:
                issues.append(f"{col} is not binary")
    if TARGET in df.columns and not set(df[TARGET].unique()) <= {0, 1}:
        issues.append("unpaid_tagging is not binary")
    return issues


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Type fixes only; no rows are dropped and no values are imputed."""
    out = df.copy()
    out["branch_code"] = out["branch_code"].astype(str)   # identifier-like categorical
    out["city"] = out["city"].astype(str).str.strip()
    for prefix in ("num_products",) + BINARY_PREFIXES:
        for col in quarter_columns(out, prefix):
            out[col] = out[col].astype(int)
    if TARGET in out.columns:
        out[TARGET] = out[TARGET].astype(int)
    issues = validate(out)
    if issues:
        raise ValueError(f"Data validation failed: {issues}")
    return out


def load_clean(path: str | Path) -> pd.DataFrame:
    """Read a raw CSV, standardize columns, fix types, validate."""
    return clean_data(standardize_columns(pd.read_csv(path)))
