# Assumptions and Limitations

**Data provenance.** The two files were provided through a course assignment, with permission to use them in a
portfolio. No data dictionary or contact with a data owner is available, so none of the definitions below can be
confirmed. Every analysis in this project is written to be valid under the stated assumption, and where one
assumption is critical, sensitivity checks are reported.

## Assumption register
| # | Unknown | Working assumption | Risk if wrong | How it is handled |
|---|---|---|---|---|
| 1 | Meaning of Unpaid Tagging | A binary indicator; 1 = "tagged" | Business interpretation (default, delinquency, other) could differ | Neutral wording only; no claims about default or credit risk |
| 2 | Meaning of Q1-Q5 | Five consecutive quarters; Data All = Q1-Q4, Data Validasi = Q2-Q5 | "Shifted window" may be something else | Called a shifted-window evaluation of the same customers; no calendar claims |
| 3 | Why labels differ between files (2,042 customers) | Unknown; observed features do not explain it | Tag may not be a stable customer attribute | Labels kept separate; change analysed in EDA and Phase 7 |
| 4 | Credit-card indicator | Static Q1-Q3, all 1 from Q4; customers without a card are 100% tagged in Data All | Possible leakage or definitional link with the tag | Two feature sets compared (no_card primary, with_card); never presented as a causal driver |
| 5 | Units and currency of balance and income | Used only through ranks, tiers and relative changes | Absolute comparisons would be unreliable | No absolute-value claims; "income measure" used instead of "income" |
| 6 | Definition of ActiveMember | A binary activity flag | Unknown | Used descriptively; weak association noted |
| 7 | Q5 shift (all balance changes Q4->Q5 are increases; active rate falls) | May be real behaviour or data construction | Drift conclusions may be artefacts | Reported as a shift to monitor, not explained |
| 8 | Zero income (251) and zero balances | Valid values, not missing data | Imputation would distort | Retained; flagged with indicator features |

## Limitations
- Same customers in both files: the validation is not on unseen customers.
- No ground truth for what the tag means, so results describe statistical associations only.
- The data may be synthetic or constructed for teaching; patterns may not reflect real banking behaviour.
- Group sizes for 4+ products and for single branches are small; wide uncertainty is shown with intervals.

## What would reduce the uncertainty
A data dictionary, the tag definition and assignment rule, the calendar meaning of quarters, and an explanation of the
card-status and Q5 patterns.
