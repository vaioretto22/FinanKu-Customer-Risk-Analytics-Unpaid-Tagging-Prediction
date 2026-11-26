The project analyzes FinanKu customer demographics and quarterly behavior to find patterns associated with the Unpaid Tagging indicator. It then tests whether a classifier can reproduce that indicator on a shifted observation window (Q1–Q4 for development, Q2–Q5 for validation).

Three rules from your brief shape everything that follows:

Unpaid Tagging is undefined, so I'll say "tagged" and "non-tagged", never "default".
The validation set is the same customers on a shifted window, not unseen customers.
Associations are never presented as causes.
Initial findings re-verified

I re-ran your audit on the uploaded files in my own sandbox, not on your machine. Everything you listed holds:

Finding	Result
Shape	7,561 × 22 in both files
Missing values / duplicate IDs	0 / 0
Same IDs, same order	Yes
Profile columns identical	Yes
Q2, Q3, Q4 identical across files	Yes
Tagged in Data All	2,019 (26.70%)
Tagged in Data Validasi	2,709 (35.83%)
Customers whose label differs	2,042
Constant columns	HasCrCard Q4 (both files), HasCrCard Q5
Zero income	251
Max NumOfProducts Q5	7

The checks surfaced several things beyond your list. Some of them will affect the modeling:

Label churn is two-way. Of the 2,042 changed labels, 1,366 go 0→1 and 676 go 1→0. The prevalence rise (26.7% to 35.8%) is a net effect, and about 27% of customers changed status. This is central to Phase 7.
Credit card status is almost static. HasCrCard Q1, Q2 and Q3 are identical for every customer (611 have no card). In Q4 every customer has a card. So 611 customers flip from 0 to 1 at Q4, and the "constant" column is really a structural break.
Product counts never decrease. Between consecutive quarters, products go up for some customers and down for none (608 rose Q1→Q2, 704 rose Q4→Q5). Plausible, but it needs a data-owner explanation.
Q5 looks different from Q1–Q4.
Mean balance moves by roughly 0.1% per quarter through Q4, then jumps from about 53.3M to 58.5M in Q5.
3,468 customers' balances change from Q4 to Q5.
3,115 customers (about 41%) change active status from Q4 to Q5, and the active rate drops from 58.1% to 45.9%.
This is a possible regime change. It may be real or a data artifact, so we'll quantify it before modeling.
Zero balances fall steadily. The count goes 2,633 → 1,997 → 1,548 → 1,163 across Q1–Q4, and stays 1,163 in Q5.
Branch Code has 18 values, each in exactly one city. It is nested within City, so City and Branch are partly redundant in a model.
Zero-income customers have a 25.1% tagging rate in Data All, against 26.7% overall, so they don't look unusual on the target.
