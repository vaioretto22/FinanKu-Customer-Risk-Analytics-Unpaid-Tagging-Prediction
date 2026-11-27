# EDA Findings (Phase 3)

Terms: *tagged* = Unpaid Tagging 1, *non-tagged* = 0. The indicator has no official definition and is
not interpreted as default. All results are **associations**, not causes. Group sizes are in the notebook
tables and charts; Data All uses the Q1-Q4 label, Data Validasi the Q2-Q5 label.
Figures are in `figures/`.

## 1. Observed facts
**Customer profile**
- 7,561 customers: Surabaya 3,767 (49.8%), Bandung 1,898 (25.1%), Jakarta 1,896 (25.1%).
- 18 branches with 196-977 customers each; age 22-70 (median 45); income measure median 23M
  (unit unconfirmed), 251 customers (3.3%) with zero income.

**Tagging rate**
- Data All: 2,019 of 7,561 tagged (26.70%). Data Validasi: 2,709 (35.83%).
- By city, age group and income group the rates are close to the overall rate in both windows
  (e.g. Data All by city 25.8%-27.4%; by age group 25.7%-27.7%; by income band 25.1%-28.3%).
- By branch the range is 19.2%-31.2% (All) and 29.4%-40.2% (Validasi). Only 1 of 18 branches has a
  95% interval excluding the overall rate in each window (branch 1003 in All, 1022 in Validasi).
  With 18 branches, about one such result is expected by chance, so branch differences are weak evidence.

**Quarterly behaviour (Q1 to Q5)**
- Mean balance is almost flat Q1-Q4 (53.17M to 53.34M) and then 58.49M in Q5.
- Zero-balance customers fall 34.8% -> 26.4% -> 20.5% -> 15.4% (Q1-Q4) and stay 15.4% in Q5.
- Mean products rise every quarter (1.52, 1.60, 1.69, 1.78, 1.92); no customer ever loses a product.
- Active-member rate rises Q1-Q4 (50.4% -> 58.1%), then drops to 45.9% in Q5.
- Card ownership is 91.9% in Q1-Q3 and 100% from Q4.
- Q4->Q5 balance moves are all increases (3,468 up, 0 down), unlike Q1->Q4 where balances both rise and fall.

## 2. Statistical associations with the tag
Strongest signal (Data All): **customers without a card until the final quarter (n = 611) are
100% tagged**, versus 20.3% among card holders. They are 8.1% of customers but 30.3% of tagged customers.
In Data Validasi the same 611 customers are 66.0% tagged (403 tagged, 208 non-tagged), versus 33.2% among
the rest.

Other associations (Data All):
- **Products:** non-monotonic. 1 product 34.9%, 2 products 16.9%, 3 products 27.8%, 4 products 58.5% (n=164),
  5 products 92.3% (n=26). In Data Validasi the pattern is much flatter (32.3% for 2 products, 38.9% for 4).
- **Balance:** the lowest tiers (no balance 18.8%, low 21.4%) are below the mid/high tiers (31.3%, 31.7%).
  In Data Validasi the spread is smaller (33.1% to 38.3%).
- **Activity:** weak (22.2% for 4 active quarters vs 26%-29% otherwise).
- **Age, income, city:** essentially no association (Spearman |r| < 0.02; Cramer's V for city 0.002).
- Spearman with tag, Data All vs Data Validasi: card_start -0.49 vs -0.19; n_zero_balance_quarters
  -0.13 vs -0.03; products_mean -0.12 vs -0.03; balance_mean 0.12 vs 0.04.

**Associations are clearly weaker in Data Validasi than in Data All.** This anticipates lower predictive
performance in Phase 7.

## 3. Segmentation (rule-based; same rules in both windows)
Seven segments from card status, product count and whether the customer has any balance.
- Data All: segment rates range from 5.9% (2 products, no balance) to 100% (no card until final quarter).
- Data Validasi: 27.5% to 66.0%. The ranking of segments is identical in both windows (Spearman 1.00 across 7 segments),
  but the spread shrinks a lot.
- The two highest-rate segments in Data All hold 10.8% of customers and 33.9% of tagged customers.
- Interpretation: segmentation is useful for describing where tags concentrate, but a large part of the
  contrast comes from the card-status group, which needs the data owner's explanation before it is used operationally.

## 4. Cautions and open questions
1. **Possible leakage or definitional link between card status and the tag.** A perfect 100% tag rate in a group
   of 611 customers is unusual. It may mean the card variable is affected by the tagging process itself
   (e.g. cards issued or changed after tagging), or that the data was generated with that rule. Do not treat
   it as a behavioural driver until the data owner explains it. In Phase 6 we will evaluate models with and without
   card-based features.
2. The two label sets differ for 2,042 customers, so the tag is not a stable customer attribute across windows.
3. Q5 differs from Q1-Q4 in balance and activity levels; the cause (real behaviour vs data construction) is unknown.
4. Income/balance units, activity definition and calendar meaning of the quarters are unconfirmed.
5. Small groups (4+ products, branches) have wide intervals; do not over-read them.

## 5. Sensitivity checks added after review
**Card holders only (n = 6,950).** Removing the no-card group leaves the other patterns essentially unchanged
(Spearman with the tag in Data All: products_mean -0.12 -> -0.11, n_zero_balance_quarters -0.13 -> -0.12,
balance_mean 0.12 -> 0.11). The product-count and balance patterns are therefore not just a by-product of
the card group, but they remain weak in Data Validasi (|r| <= 0.03).

**Why labels differ between windows.** 4,176 customers are non-tagged in both files, 1,343 tagged in both,
1,366 changed from non-tagged to tagged and 676 from tagged to non-tagged. On the observed features, customers
who changed look like the customers who did not change from the same starting label (e.g. mean products
1.80 vs 1.80 for 0->1 vs 0->0; 1.71 vs 1.76 for 1->0 vs 1->1; share with a Q4->Q5 product increase about 9% in all four groups).
So the observed behaviour does not explain the label change. We cannot tell whether this reflects different
tagging rules per window, noise, or information not in the data.

## 6. Implications for later phases
- Phase 5: formal tests (chi-square, logistic regression) for product count, balance tier, card status; treat
  product count as non-linear.
- Phase 6: handle the card features explicitly (ablation); expect weaker performance on the shifted window.
- Phase 7: investigate the shrinking associations and the Q5 shift as potential drift.
