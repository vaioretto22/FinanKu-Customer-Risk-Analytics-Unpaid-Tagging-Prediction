"""Evaluation helpers for Phase 6-7: threshold metrics, ranking metrics, calibration, threshold sweep and plots."""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, brier_score_loss,
                             confusion_matrix, precision_recall_curve, roc_auc_score, roc_curve)


def threshold_metrics(y_true, proba, threshold: float = 0.5) -> dict:
    """Metrics that depend on a decision threshold. Positive class = tagged (1)."""
    y_true = np.asarray(y_true)
    pred = (np.asarray(proba) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if (tp + fp) else np.nan
    recall = tp / (tp + fn) if (tp + fn) else np.nan
    specificity = tn / (tn + fp) if (tn + fp) else np.nan
    f1 = 2 * precision * recall / (precision + recall) if (tp and precision + recall) else 0.0
    return {"threshold": threshold, "accuracy": (tp + tn) / len(y_true), "precision": precision, "recall": recall,
            "specificity": specificity, "f1": f1, "balanced_accuracy": balanced_accuracy_score(y_true, pred),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp), "flagged_share": float(pred.mean())}


def expected_calibration_error(y_true, proba, n_bins: int = 10) -> float:
    """Average absolute gap between predicted probability and observed rate, weighted by bin size."""
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    bins = np.minimum((proba * n_bins).astype(int), n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            ece += m.mean() * abs(y_true[m].mean() - proba[m].mean())
    return float(ece)


def ranking_metrics(y_true, proba) -> dict:
    """Threshold-free metrics: ROC-AUC, PR-AUC (average precision), Brier score and expected calibration error."""
    return {"roc_auc": roc_auc_score(y_true, proba), "pr_auc": average_precision_score(y_true, proba),
            "brier": brier_score_loss(y_true, proba), "ece": expected_calibration_error(y_true, proba),
            "prevalence": float(np.mean(y_true))}


def evaluate(y_true, proba, threshold: float = 0.5) -> dict:
    """All metrics in one dictionary (ranking metrics + threshold metrics)."""
    return {**ranking_metrics(y_true, proba), **threshold_metrics(y_true, proba, threshold)}


def threshold_sweep(y_true, proba, thresholds=None) -> pd.DataFrame:
    """Metrics over many thresholds, including the share of customers flagged (operational workload)."""
    thresholds = np.round(np.arange(0.05, 0.951, 0.01), 2) if thresholds is None else thresholds
    return pd.DataFrame([threshold_metrics(y_true, proba, t) for t in thresholds])


def fbeta_column(sweep: pd.DataFrame, beta: float) -> pd.Series:
    p, r = sweep["precision"], sweep["recall"]
    return (1 + beta ** 2) * p * r / (beta ** 2 * p + r)


# ---------- plots ----------
def plot_roc_pr(y_true, proba_by_name: dict, fig_path=None):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for name, p in proba_by_name.items():
        fpr, tpr, _ = roc_curve(y_true, p)
        ax[0].plot(fpr, tpr, label=f"{name} (AUC {roc_auc_score(y_true, p):.3f})")
        pr, rc, _ = precision_recall_curve(y_true, p)
        ax[1].plot(rc, pr, label=f"{name} (AP {average_precision_score(y_true, p):.3f})")
    ax[0].plot([0, 1], [0, 1], "--", color="grey")
    ax[0].set_xlabel("False positive rate"); ax[0].set_ylabel("True positive rate")
    ax[0].set_title("ROC curve", fontweight="bold"); ax[0].legend(fontsize=7)
    ax[1].axhline(np.mean(y_true), ls="--", color="grey")
    ax[1].set_xlabel("Recall"); ax[1].set_ylabel("Precision")
    ax[1].set_title("Precision-recall curve (dashed = prevalence)", fontweight="bold"); ax[1].legend(fontsize=7)
    fig.tight_layout()
    if fig_path:
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    return fig


def plot_confusion(metrics: dict, title: str, fig_path=None):
    cm = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]])
    fig, ax = plt.subplots(figsize=(4.4, 3.6))
    ax.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, f"{v:,}", ha="center", va="center", color="white" if v > cm.max() / 2 else "black")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Pred non-tagged", "Pred tagged"], fontsize=8)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Actual non-tagged", "Actual tagged"], fontsize=8)
    ax.set_title(title, fontsize=10, fontweight="bold"); fig.tight_layout()
    if fig_path:
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    return fig


def plot_calibration(y_true, proba_by_name: dict, fig_path=None, n_bins: int = 10):
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.plot([0, 1], [0, 1], "--", color="grey", label="perfect calibration")
    for name, p in proba_by_name.items():
        frac, mean_pred = calibration_curve(y_true, p, n_bins=n_bins, strategy="quantile")
        ax.plot(mean_pred, frac, marker="o", label=name)
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Observed tagging rate")
    ax.set_title("Calibration (quantile bins)", fontweight="bold"); ax.legend(fontsize=7); fig.tight_layout()
    if fig_path:
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    return fig


def plot_threshold_tradeoff(sweep: pd.DataFrame, chosen: float | None = None, fig_path=None):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for col, lab in [("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"),
                     ("flagged_share", "Share of customers flagged")]:
        ax.plot(sweep["threshold"], sweep[col], label=lab)
    if chosen is not None:
        ax.axvline(chosen, ls="--", color="black", label=f"chosen threshold {chosen:.2f}")
    ax.set_xlabel("Decision threshold"); ax.set_ylabel("Value")
    ax.set_title("Threshold trade-off (out-of-fold, training data)", fontweight="bold")
    ax.legend(fontsize=7); fig.tight_layout()
    if fig_path:
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    return fig
