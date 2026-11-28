# Machine Learning Findings (Phase 6)

Target: tag (1 = tagged, 26.7% of customers). Development data: **Data All (Q1-Q4) only**, 80% stratified training / 20% test
(random_state 42). **Data Validasi was not touched**; it is used in Phase 7. Preprocessing is fitted inside the pipeline on training data
only. Model selection used stratified 5-fold CV on the training set; the test set was used once for reporting. Notebook:
`notebooks/05_machine_learning.ipynb`; aggregate metrics: `reports/ml_results_summary.csv`; figures `13`-`19`.
Results describe statistical patterns in this data and make no claim about default or credit risk.

## 1. Model comparison (primary feature set `no_card`, no credit-card information)
| Model | CV ROC-AUC (mean, sd) | Test ROC-AUC | Test PR-AUC (baseline 0.267) | Brier | ECE |
|---|---|---|---|---|---|
| Dummy (class prior) | 0.500 | 0.500 | 0.267 | 0.196 | 0.000 |
| Logistic regression | 0.635 (0.012) | 0.630 | 0.362 | 0.188 | 0.018 |
| Decision tree (depth 4) | 0.760 (0.017) | 0.775 | 0.550 | 0.154 | 0.008 |
| Random forest | 0.762 (0.018) | 0.772 | 0.589 | 0.157 | 0.044 |
| Gradient boosting | 0.768 (0.020) | 0.778 | 0.588 | 0.155 | 0.022 |

- Non-linear models clearly beat the linear baseline (AUC about 0.77 vs 0.63). This corrects the cautious expectation in Phase 5: the
  weak results there were for linear and one-variable associations; interactions between variables carry much more signal in Data All.
- Tree, forest and boosting are within one standard error of each other (0.760, 0.762, 0.768; SE about 0.009). By the one-standard-error rule the
  **simplest, a decision tree of depth 4, is selected**. PR-AUC slightly favours forest and boosting (0.59 vs 0.55), a trade-off noted as a limitation.
- Sensitivity, with the card indicator (`with_card`): test ROC-AUC rises to 0.85 (tree 0.847, forest 0.851, boosting 0.849, logistic regression 0.762).
  This gain comes from the variable that is perfectly tied to the tag in Data All (all 611 customers without a card are tagged), so it is **not** used as the primary result.

## 2. Selected model: decision tree, `no_card`
**Default threshold 0.50 (test set):** accuracy 0.775, precision 0.713, recall 0.265, specificity 0.961, F1 0.386, balanced accuracy 0.613; only 9.9% of
customers are flagged. Accuracy looks acceptable (the no-skill baseline is 0.733) but most tagged customers are missed, which is why accuracy is never used alone.

**Calibration:** the tree is well calibrated (ECE 0.008; Brier 0.154 vs 0.196 for the dummy). The forest is the least calibrated (ECE 0.044).
The tree produces few distinct probabilities (about 47 out-of-fold values), so thresholds between roughly 0.25 and 0.41 flag exactly the same customers.

## 3. Threshold choice
Rule (stated assumptions, not facts about FinanKu): a false negative is costlier than an extra review, so recall is weighted twice (F2); at most 40%
of customers can be flagged (hypothetical capacity). Maximise F2 under that cap, on **out-of-fold training predictions** (test set not used).

| Threshold (out-of-fold, training) | Precision | Recall | F1 | Customers flagged |
|---|---|---|---|---|
| 0.10 | 0.34 | 0.96 | 0.50 | 75% |
| 0.20 | 0.36 | 0.89 | 0.52 | 65% |
| **0.25 (chosen)** | 0.48 | 0.63 | 0.55 | 35% |
| 0.40 | 0.51 | 0.58 | 0.54 | 31% |
| 0.50 | 0.71 | 0.21 | 0.33 | 8% |
| 0.60 | 0.89 | 0.14 | 0.24 | 4% |

**Test set at 0.25:** accuracy 0.726, precision 0.490, recall 0.651, specificity 0.753, F1 0.559, balanced accuracy 0.702. 537 of 1,513 customers (35.5%) are flagged;
263 of 404 tagged customers are found, 274 flagged customers are non-tagged and 141 tagged customers are missed. About half of the flagged customers are tagged
(490 per 1,000 flagged). Lowering the threshold raises recall and workload; raising it gives a short, precise list that misses most tagged customers.
Meaning of the errors: a false positive is extra review workload for a non-tagged customer; a false negative is a missed tagged customer. Their real cost depends on the unknown meaning of the tag.

## 4. What the model uses (explainability; not causal)
- **Permutation importance (test ROC-AUC drop):** `products_start` 0.235, `active_start` 0.036, `balance_mean` 0.018; every other feature is close to 0 (age, income, city, branch, balance changes).
- **Tree rules (the exact rules and leaf counts are printed in the notebook):** the tree splits first on `products_start`, then on `active_start` and `balance_mean`.
  In an exploratory fit on all Data All customers (not the train-only tree), customers with 3 or more products at the start of the window were tagged in about 90% of cases
  (280 of 312), and customers with 1 product at the start, inactive in the first quarter and with a low balance were tagged in about 55% (222 of 404); 2 products at the start had low tagging rates.
- **Logistic regression coefficients** are small and mostly branch dummies; the linear model cannot represent the non-linear product pattern, which is why it is weak.
- **Important correction to earlier phases:** Phases 3 and 5 used the product count at the **end** of the window; the **start-of-window** count is a much stronger signal.
  The notebook also draws a SHAP summary if SHAP is available in your environment (optional). Feature importance shows what the model uses, not what causes tagging.

## 5. Cautions for Phase 7
- The dominant feature is the product count at the **start** of the window (Q1 in Data All, Q2 in Data Validasi). These are different quarters, and customers gain products over time, so the same feature may mean something different in Data Validasi.
- Associations were already much weaker in Data Validasi (Phase 5); a large drop in performance there is plausible and will be reported, not hidden.
- Test performance on Data All is an internal estimate; both the training and test customers also appear in Data Validasi.
- No resampling was used; class imbalance is mild and handled through PR-AUC and thresholding.
- Hyper-parameters, feature set, model and threshold are now fixed; **no tuning on Data Validasi labels**.
