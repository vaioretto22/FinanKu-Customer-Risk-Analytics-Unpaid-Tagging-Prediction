# Data Quality Report

Checks were run on the two supplied files (7,561 rows x 22 columns each). Aggregate results only.
Source: course assignment data, no data dictionary (see `assumptions_and_limitations.md`).

## Passed checks
- No missing values; no duplicate rows or Customer IDs.
- Identical customer population and order in both files.
- Profile columns and Q2-Q4 behavioural columns are identical across files.
- No negative balances; binary columns are strictly 0/1.

## Anomalies and decisions
| Anomaly | Evidence | Decision |
|---|---|---|
| Different target distribution | 26.70% vs 35.83% tagged; 2,042 labels differ (1,366 0->1, 676 1->0) | Retain both labels separately; observed features do not explain the change (EDA section H) |
| HasCrCard constant in Q4/Q5 | All values = 1 | Retain with documentation; `card_end` excluded from model features |
| HasCrCard static Q1-Q3 | Identical in Q1-Q3; 611 customers without card until Q4 | Retain; **all 611 are tagged in Data All (66.0% in Data Validasi)**; compare models with and without card information |
| Zero income | 251 customers (3.3%) | Retain; `income_is_zero` flag; no imputation |
| Zero balances | 2,633 / 1,997 / 1,548 / 1,163 for Q1-Q4; 1,163 in Q5 | Retain; zero-start handled in percentage change (NaN + flag) |
| Products never decrease; max 7 in Q5 | No downward movement in any consecutive quarters | Retain with documentation |
| Q5 level shift | Mean balance 53.3M -> 58.5M; all 3,468 balance changes Q4->Q5 are increases; active rate 58.1% -> 45.9% | Retain; investigate as potential drift in Phase 7 |
| Balance nearly constant within a window | Balance level features correlate > 0.99 | Keep one or two representatives in model feature sets |
| Branch nested in City | 18 branches, each in one city | Treat as categorical; very weak association with the tag |

## Not verifiable without the data owner
Tag definition and assignment rule, meaning of quarters, units/currency, ActiveMember definition, reason for the card pattern.
