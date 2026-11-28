# Statistical Findings (Phase 5)

Terms: *tagged* = Unpaid Tagging 1, *non-tagged* = 0 (definition unconfirmed, not interpreted as default).
All results are **associations in observational data**, not causal effects. p-values are Holm-adjusted where many tests
are run, and effect sizes and confidence intervals are reported alongside. Data All uses the Q1-Q4 label, Data Validasi the Q2-Q5 label.
Notebook: `notebooks/04_statistical_analysis.ipynb`; figures `11a`, `11b`, `12` in `figures/`.

## 1. Methods and why they were chosen
| Question | Method | Assumption check |
|---|---|---|
| Is a categorical variable associated with the tag? | Chi-square test of independence + bias-corrected Cramer's V | Smallest expected cell count was 50 or more in every table (rule of thumb: at least 5), so the approximation is adequate |
| Do tagged and non-tagged customers differ on a numeric variable? | Mann-Whitney U (primary), Welch t-test (reference), rank-biserial correlation and Cohen's d with CI | Variables are skewed (skewness 0.7-0.9 for balance, income, products) and normality is rejected, so a rank-based test is primary |
| How large is a group difference? | Risk difference (Newcombe-Wilson CI), risk ratio and odds ratio (log CI) | Odds ratio flagged as not estimable when a cell is zero |
| Which variables matter jointly? | Logistic regression, odds ratios with 95% CI, likelihood-ratio tests for groups of terms | VIF at most 4.0 (no serious collinearity); product count and balance entered as categories because their relationship is not linear |

## 2. Results
### Categorical variables (chi-square, Holm-adjusted)
| Variable | Data All: Cramer's V, adj. p | Data Validasi: Cramer's V, adj. p |
|---|---|---|
| Card status at window start | 0.49, p < 0.0001 | 0.19, p < 0.0001 |
| Number of products (1, 2, 3, 4+) | 0.23, p < 0.0001 | 0.06, p < 0.0001 |
| Balance tier | 0.12, p < 0.0001 | 0.03, p = 0.11 |
| Active quarters (0-4) | 0.04, p = 0.035 | 0.02, p = 0.85 |
| City, branch, age group, income group | about 0 to 0.03, adj. p >= 0.59 | 0 to 0.02, p = 1.00 |

Card status, product count and (in Data All) balance tier are associated with the tag; city, branch, age group and income group show no
detectable association in either window. In Data Validasi every association is much weaker.

### Numeric variables (Mann-Whitney, Holm-adjusted; positive d = larger in tagged)
- **Data All:** balance level d = +0.24 (95% CI 0.19-0.29), number of zero-balance quarters d = -0.27 (-0.32 to -0.22),
  active-status change d = +0.33 (0.28-0.38), balance change d = -0.15; age (d = 0.02) and income (d = 0.02) are essentially zero.
  Effects are small by conventional standards.
- **Data Validasi:** all |d| <= 0.08; only balance level (adj. p = 0.006) and product count (adj. p = 0.033) remain nominally significant
  after adjustment, with negligible effect sizes.

### Group differences with confidence intervals
| Comparison | Data All | Data Validasi |
|---|---|---|
| No card at window start vs card (n = 611 vs 6,950) | 100.0% vs 20.3%; risk difference +79.7 pp (78.6 to 80.7); odds ratio not estimable (every no-card customer is tagged) | 66.0% vs 33.2%; difference +32.8 pp (28.8 to 36.6); odds ratio 3.9 (3.3 to 4.6) |
| 4+ products vs 1 product (n = 190 vs 3,029 / 433 vs 2,736) | 63.2% vs 34.9%; +28.2 pp (21.0 to 35.0); OR 3.2 (2.4 to 4.3) | 40.0% vs 38.8%; +1.2 pp (-3.7 to 6.2); OR 1.05 (0.85 to 1.29) |
| 2 products vs 1 product | 16.9% vs 34.9%; -18.0 pp (-20.2 to -15.9) | 32.3% vs 38.8%; -6.5 pp (-9.0 to -4.1) |
| High balance vs no balance | 31.7% vs 18.8%; +12.9 pp (9.8 to 15.8) | 38.3% vs 33.1%; +5.2 pp (1.8 to 8.5) |

### Logistic regression
Fit statistics are descriptive: in-sample AUC is **not** an estimate of predictive performance (that comes in Phases 6-7).

| Model | Data All: n, McFadden R2, in-sample AUC | Data Validasi: n, McFadden R2, in-sample AUC |
|---|---|---|
| M1: all customers, no card information | 7,561; 0.062; 0.67 | 7,561; 0.004; 0.55 |
| M2: card holders only | 6,950; 0.063; 0.67 | 6,950; 0.003; 0.54 |
| M3: all customers + card indicator | not estimable (perfect separation) | 7,561; 0.028; 0.59 |

Selected odds ratios (95% CI), M2 card holders only, holding other variables fixed:

| Term | Data All | Data Validasi |
|---|---|---|
| Balance tier Mid vs No balance | 3.03 (2.36 to 3.88) | 1.10 (0.89 to 1.37) |
| Balance tier High vs No balance | 3.16 (2.46 to 4.05) | 1.22 (0.98 to 1.52) |
| 2 vs 1 products | 0.40 (0.35 to 0.46) | 0.80 (0.72 to 0.90) |
| 4+ vs 1 products | 3.45 (2.46 to 4.83) | 1.08 (0.86 to 1.35) |
| Each additional active quarter | 0.74 (0.70 to 0.80) | 0.98 (0.93 to 1.04) |
| Age (per 10 years) | 1.03 (0.99 to 1.08) | 1.00 (0.96 to 1.04) |
| Income measure (per 10M, unit unconfirmed) | 1.05 (0.99 to 1.11) | 1.03 (0.98 to 1.08) |
| City (Jakarta vs Surabaya) | 0.91 (0.78 to 1.05) | 0.95 (0.84 to 1.07) |

In M3 (Data Validasi) having a card at window start has an odds ratio of 0.26 (0.22 to 0.31) versus no card, consistent with the 3.9 odds ratio above.
Joint likelihood-ratio tests: product count is significant in both windows (Data All p < 0.0001; Data Validasi adj. p = 0.003);
balance tier is significant in Data All (p < 0.0001) but not in Data Validasi (p = 0.25); city is not significant in any model (adj. p = 0.75).

## 3. Interpretation
**Observed facts**
- Card status, product count and balance tier are associated with the tag in Data All; demographics (age, income band, city, branch) are not.
- The relationship with product count is non-linear: 2 products have the lowest tagging rate, 4+ products the highest.
- Most associations shrink strongly in Data Validasi; logistic-regression fit falls from McFadden R2 0.06 to 0.004.

**Statistical associations**
- Among card holders in Data All, mid and high balance tiers have about 3 times the odds of being tagged relative to customers with no balance,
  and each additional active quarter lowers the odds by about 26%. These patterns do not persist in Data Validasi.

**Practical relevance**
- Even where significant, most effects are small to moderate (Cramer's V <= 0.23 apart from card status; |d| <= 0.33). Knowing these variables
  gives limited ability to separate tagged from non-tagged customers, especially in Data Validasi (in-sample AUC about 0.55).

**Caution (not conclusions)**
- The very strong card-status association (100% tagged without a card in Data All) may reflect how the label or the card variable was defined; it is
  not treated as a behavioural driver. Models in Phase 6 will be compared with and without card information.
- The tag differs for 2,042 customers between windows and unexplained by the observed features (see EDA findings), which is consistent with
  weak associations in Data Validasi but does not explain them.
- Statistical significance with n = 7,561 can be reached by small effects, so effect sizes are interpreted first.
- No causal or default-risk claims are made.

## 4. Implications for Phase 6-7
- Expect weak predictive performance, particularly on the shifted window; set baselines accordingly (DummyClassifier and logistic regression first).
- Treat product count and balance as non-linear (trees and categorical encoding are justified).
- Use the `no_card` feature set as the primary model and `with_card` as a sensitivity comparison.
- Investigate in Phase 7 why associations weaken in Data Validasi (label differences, Q5 shift).
