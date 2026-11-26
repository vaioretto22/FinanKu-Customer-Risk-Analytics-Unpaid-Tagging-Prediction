# Data Dictionary (initial, Phase 1)

Definitions are **unconfirmed** unless stated; to be validated with the data owner.

| Column | Type | Notes |
|---|---|---|
| Customer ID | identifier | Never used as a predictor |
| Branch Code | categorical | 18 values; each branch belongs to exactly one city |
| City | categorical | Surabaya, Bandung, Jakarta |
| Age | numeric | 22-70 |
| Avg. Annual Income/Month | numeric | Label ambiguous (annual vs monthly); unit/currency unconfirmed; 251 zeros |
| Balance Qn | numeric | Currency unconfirmed; non-negative |
| NumOfProducts Qn | integer | 1-5 in Q1-Q4; up to 7 in Q5 |
| HasCrCard Qn | binary | Identical Q1-Q3; all 1 from Q4 |
| ActiveMember Qn | binary | Definition unconfirmed |
| Unpaid Tagging | binary | Definition unconfirmed; 1 = tagged, 0 = non-tagged |

Data All uses Q1-Q4; Data Validasi uses Q2-Q5.
