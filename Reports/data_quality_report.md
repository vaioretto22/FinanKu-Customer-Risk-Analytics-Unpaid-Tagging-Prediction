# Data Quality Report (Phase 1)

Checks were run on the two supplied files (7,561 rows x 22 columns each). Aggregate results only.

## Passed checks
- No missing values; no duplicate rows or Customer IDs.
- Identical customer population and order in both files.
- Profile columns and Q2-Q4 behavioral columns are identical across files.

## Anomalies and decisions
| Anomaly | Evidence | Decision |
|---|---|---|
| Different target distribution | 26.70% vs 35.83% tagged; 2,042 labels differ (1,366 0->1, 676 1->0) | Retain both labels separately; ask data owner how the tag is assigned per window |
| HasCrCard constant in Q4/Q5 | All values = 1 | Retain with documentation; do not use as raw feature; handle in Phase 2 |
| HasCrCard static Q1-Q3 | Identical in Q1-Q3; 611 customers without card then all have card in Q4 | Data-owner question |
| Zero income | 251 customers | Retain; add `income_is_zero` flag; do not impute |
| Zero balances | 2,633 / 1,997 / 1,548 / 1,163 for Q1-Q4; 1,163 in Q5 | Retain; handle zero starting balance in % change |
| Products never decrease; max 7 in Q5 | No downward movement in any consecutive quarters | Retain; data-owner question |
| Q5 level shift | Higher mean balance and lower active rate vs Q4 | Investigate as potential drift (Phase 7) |
| Branch nested in City | 18 branches, each in one city | Treat as categorical; watch redundancy with City |

## Open questions for the data owner
1. Official definition of Unpaid Tagging and how it is assigned in each window.
2. Calendar meaning of Q1-Q5.
3. Units/currency of income and balance; meaning of "Avg. Annual Income/Month".
4. Definition of ActiveMember.
5. Why card status is static in Q1-Q3 and universal from Q4.
