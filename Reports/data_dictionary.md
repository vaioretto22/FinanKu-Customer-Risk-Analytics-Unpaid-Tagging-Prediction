# Data Dictionary

Source: MySkill, course *Data Analysis*, project *Prediction Model* (May 9, 2024). No official data dictionary was provided.
Definitions below are **unconfirmed** working assumptions unless stated.
Data All uses Q1-Q4; Data Validasi uses Q2-Q5.

## 1. Raw columns (standardized names)
| Raw column | Standardized | Type | Notes |
|---|---|---|---|
| Customer ID | customer_id | identifier | Index only; never a predictor |
| Branch Code | branch_code | categorical (string) | 18 values; each branch belongs to one city |
| City | city | categorical | Surabaya, Bandung, Jakarta |
| Age | age | numeric | 22-70 |
| Avg. Annual Income/Month | income_measure | numeric | Label ambiguous; unit/currency unconfirmed; 251 zeros |
| Balance Qn | balance_qn | numeric | Currency unconfirmed; non-negative |
| NumOfProducts Qn | num_products_qn | integer | 1-5 in Q1-Q4; up to 7 in Q5 |
| HasCrCard Qn | has_credit_card_qn | binary | Identical Q1-Q3; all 1 from Q4 |
| ActiveMember Qn | active_member_qn | binary | Definition unconfirmed |
| Unpaid Tagging | unpaid_tagging | binary | Definition unconfirmed; 1 = tagged, 0 = non-tagged |

## 2. Engineered features (same definitions in both windows)
"start" = first quarter of the 4-quarter window, "end" = last quarter.

| Group | Feature | Definition |
|---|---|---|
| Profile | age, branch_code, city, income_measure | Copied from clean data |
| Profile | income_is_zero | 1 if income_measure = 0 |
| Balance | balance_mean / min / max | Over the 4 quarters |
| Balance | balance_std | Sample standard deviation (ddof=1) |
| Balance | balance_start / balance_end | First / last quarter balance |
| Balance | balance_change_abs | end - start |
| Balance | balance_change_pct | (end - start) / start; **NaN when start = 0** |
| Balance | balance_start_is_zero | 1 if start balance = 0 |
| Balance | n_zero_balance_quarters | Count of zero-balance quarters (0-4) |
| Products | products_mean / min / max / start / end | Over the 4 quarters |
| Products | products_change | end - start |
| Activity | active_rate | Mean of active_member over 4 quarters |
| Activity | active_start / active_end / active_change | First, last, end - start |
| Activity | n_active_quarters | Count of active quarters (0-4) |
| Credit card | card_rate, n_card_quarters, card_start, card_end | Mean, count, first, last of card indicator |

## 3. Known caveats
- `card_end` is constant (1) in both windows: exclude from models.
- Redundant pairs (|r| >= 0.95): `active_rate`/`n_active_quarters`, `card_rate`/`n_card_quarters`,
  `products_min`/`products_start`, `products_max`/`products_end`, and the balance level features
  (balance changes very little within a customer over a window). Reduce these in modeling.
- Card features mean different things per window (the 611 customers without a card until Q4 have
  `n_card_quarters` = 1 in Q1-Q4 but 2 in Q2-Q5).
- `balance_change_pct` is undefined for customers with a zero starting balance (34.8% in Q1-Q4,
  26.4% in Q2-Q5); imputation is done only inside the modeling pipeline (fit on training data).
