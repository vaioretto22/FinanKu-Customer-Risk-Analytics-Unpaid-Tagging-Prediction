"""Statistical helpers for Phase 5.

Principles: report effect size and uncertainty (not only p-values), check test assumptions,
correct for multiple testing, and keep language associational (no causal claims).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from .eda import age_group, balance_tier, income_group, wilson_ci


# ---------- categorical associations ----------
def chi_square_test(group: pd.Series, y: pd.Series) -> dict:
    """Chi-square test of independence between a categorical variable and the tag.

    Returns the statistic, dof, p-value, bias-corrected Cramer's V and the smallest expected count
    (the chi-square approximation is questionable when expected counts are below 5)."""
    ct = pd.crosstab(group, y)
    chi2, p, dof, expected = stats.chi2_contingency(ct, correction=False)
    n = ct.to_numpy().sum()
    r, k = ct.shape
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    v = float(np.sqrt(phi2 / max(1e-12, min(kc - 1, rc - 1))))
    return {"n": int(n), "levels": int(r), "chi2": float(chi2), "dof": int(dof), "p_value": float(p),
            "cramers_v": v, "min_expected": float(expected.min()),
            "cells_expected_lt5": int((expected < 5).sum())}


def holm(pvalues, method: str = "holm") -> np.ndarray:
    """Multiple-testing adjustment (Holm by default; 'fdr_bh' for Benjamini-Hochberg)."""
    return multipletests(pvalues, method=method)[1]


def risk_comparison(k1: int, n1: int, k0: int, n0: int) -> dict:
    """Compare group 1 vs group 0 tagging rates: risk difference (Newcombe-Wilson CI),
    risk ratio and odds ratio (log-method CIs, 0.5 continuity added only if a cell is zero)."""
    p1, p0 = k1 / n1, k0 / n0
    l1, u1 = wilson_ci(k1, n1)
    l0, u0 = wilson_ci(k0, n0)
    d = p1 - p0
    rd_lo = d - np.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2)
    rd_hi = d + np.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)
    a, b, c, dd = k1, n1 - k1, k0, n0 - k0
    zero_cell = min(a, b, c, dd) == 0
    if zero_cell:
        a, b, c, dd = a + .5, b + .5, c + .5, dd + .5
    or_ = (a * dd) / (b * c)
    se_or = np.sqrt(1 / a + 1 / b + 1 / c + 1 / dd)
    rr = (a / (a + b)) / (c / (c + dd))
    se_rr = np.sqrt(1 / a - 1 / (a + b) + 1 / c - 1 / (c + dd))
    return {"rate_1": p1, "rate_0": p0, "risk_diff": d, "rd_low": rd_lo, "rd_high": rd_hi,
            "risk_ratio": rr, "rr_low": rr * np.exp(-1.96 * se_rr), "rr_high": rr * np.exp(1.96 * se_rr),
            "odds_ratio": or_, "or_low": or_ * np.exp(-1.96 * se_or), "or_high": or_ * np.exp(1.96 * se_or),
            "zero_cell": zero_cell}   # zero_cell=True: odds ratio is not reliably estimable (0.5 added)


# ---------- numeric comparisons ----------
def compare_numeric(x_tagged: pd.Series, x_non: pd.Series) -> dict:
    """Tagged vs non-tagged: Mann-Whitney U (primary, no normality needed), Welch t-test (for reference),
    effect sizes (rank-biserial correlation, Cohen's d with approximate CI) and Welch CI for the mean difference."""
    a, b = x_tagged.dropna().to_numpy(float), x_non.dropna().to_numpy(float)
    n1, n0 = len(a), len(b)
    u, p_u = stats.mannwhitneyu(a, b, alternative="two-sided")
    rank_biserial = 2 * u / (n1 * n0) - 1                      # > 0: tagged tend to have larger values
    t, p_t = stats.ttest_ind(a, b, equal_var=False)
    sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n0 - 1) * b.var(ddof=1)) / (n1 + n0 - 2))
    d = (a.mean() - b.mean()) / sp if sp > 0 else np.nan
    se_d = np.sqrt((n1 + n0) / (n1 * n0) + d ** 2 / (2 * (n1 + n0)))
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / n1 + b.var(ddof=1) / n0)
    df_w = se ** 4 / ((a.var(ddof=1) / n1) ** 2 / (n1 - 1) + (b.var(ddof=1) / n0) ** 2 / (n0 - 1))
    tcrit = stats.t.ppf(0.975, df_w)
    return {"median_tagged": float(np.median(a)), "median_non": float(np.median(b)),
            "mean_diff": float(diff), "mean_diff_low": float(diff - tcrit * se), "mean_diff_high": float(diff + tcrit * se),
            "mwu_p": float(p_u), "rank_biserial": float(rank_biserial),
            "welch_p": float(p_t), "cohens_d": float(d), "d_low": float(d - 1.96 * se_d), "d_high": float(d + 1.96 * se_d)}


def skewness_table(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Skewness and normality check (D'Agostino) used to justify rank-based tests."""
    rows = []
    for c in cols:
        x = df[c].dropna()
        rows.append({"feature": c, "skewness": stats.skew(x), "normaltest_p": stats.normaltest(x)[1]})
    return pd.DataFrame(rows)


# ---------- logistic regression ----------
def odds_ratio_table(result) -> pd.DataFrame:
    """Odds ratios with 95% CI and p-values from a fitted statsmodels Logit result."""
    ci = result.conf_int()
    out = pd.DataFrame({"odds_ratio": np.exp(result.params), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]),
                        "p_value": result.pvalues})
    return out.drop(index="const", errors="ignore")


def lr_test(full, reduced) -> dict:
    """Likelihood-ratio test between nested logit models (joint test for a group of terms)."""
    stat = 2 * (full.llf - reduced.llf)
    dof = int(full.df_model - reduced.df_model)
    return {"lr_stat": float(stat), "dof": dof, "p_value": float(stats.chi2.sf(stat, dof))}


def vif_table(X: pd.DataFrame) -> pd.DataFrame:
    """Variance inflation factors (values above ~5-10 signal problematic collinearity)."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import statsmodels.api as sm
    Xc = sm.add_constant(X.astype(float))
    return pd.DataFrame({"feature": X.columns,
                         "VIF": [variance_inflation_factor(Xc.values, i + 1) for i in range(X.shape[1])]})


# ---------- shared grouping and design matrix ----------
def categorical_frame(F: pd.DataFrame, cuts) -> pd.DataFrame:
    """Categorical versions of the main features (same rules in both windows)."""
    d = pd.DataFrame(index=F.index)
    d["city"] = F["city"]
    d["branch_code"] = F["branch_code"]
    d["age_group"] = age_group(F["age"])
    d["income_group"] = income_group(F["income_measure"])
    d["products"] = F["products_end"].clip(upper=4).map({1: "1", 2: "2", 3: "3", 4: "4+"})
    d["balance_tier"] = balance_tier(F, cuts)
    d["active_quarters"] = F["n_active_quarters"]
    d["card_status"] = F["card_start"].map({0: "no card at window start", 1: "card at window start"})
    return d


def logit_design(F: pd.DataFrame, cuts, include_card: bool = False) -> pd.DataFrame:
    """Design matrix for the interpretable logistic regression.

    Reference levels: balance tier 'No balance', products = 1, city = Surabaya.
    Product count and balance are categorical because their relationship with the tag is not linear."""
    X = pd.DataFrame(index=F.index)
    X["age_per_10y"] = F["age"] / 10
    X["income_per_10M"] = F["income_measure"] / 1e7        # unit unconfirmed
    X["income_is_zero"] = F["income_is_zero"]
    tier = pd.Series(balance_tier(F, cuts), index=F.index).astype(str)
    for level in ["Low", "Mid", "High"]:
        X[f"balance_{level}_vs_none"] = (tier == level).astype(int)
    prod = F["products_end"].clip(upper=4)
    for level, name in [(2, "2"), (3, "3"), (4, "4plus")]:
        X[f"products_{name}_vs_1"] = (prod == level).astype(int)
    X["active_quarters"] = F["n_active_quarters"]
    for c in ["Bandung", "Jakarta"]:
        X[f"city_{c}_vs_Surabaya"] = (F["city"] == c).astype(int)
    if include_card:
        X["card_at_start"] = F["card_start"]
    return X
