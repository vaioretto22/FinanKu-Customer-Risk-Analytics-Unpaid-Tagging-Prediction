# FinanKu Customer Risk Analytics & Unpaid Tagging Prediction

End-to-end banking analytics portfolio project: data audit, feature engineering, EDA,
SQL (PostgreSQL), statistical analysis, machine learning classification, shifted-window
validation, Power BI dashboard, and business report.

> **Status: in progress.** Currently at Phase 2 ((cleaning & feature engineering).).

## Business problem
Financial institutions need to understand customer behavior, monitor customer segments and
identify patterns associated with unpaid-related tagging. This project studies customer
demographics and quarterly banking behavior, and evaluates whether machine learning can
classify the **Unpaid Tagging** indicator on a shifted observation window.

**Important:** the definition of Unpaid Tagging has not been provided. This project uses the
neutral terms *tagged* (= 1) and *non-tagged* (= 0), and does not interpret the indicator as loan
default or delinquency. Results describe statistical associations, not causal relationships.

## Business questions
1. Which customer segments (city, branch, age, income) show higher tagging rates?
2. How do balances, product ownership and activity evolve across quarters?
3. How are these behaviors associated with tagging?
4. Can a model classify the tag reliably, and at what operational trade-off?
5. How does the model behave on the shifted window (Q2-Q5)?

## Dataset (not included in this repository)
| Dataset | Window | Rows | Columns |
|---|---|---|---|
| Data All (development) | Q1-Q4 | 7,561 | 22 |
| Data Validasi (shifted window) | Q2-Q5 | 7,561 | 22 |

Both files describe the **same customers**. Q2-Q4 observations are identical across files; the
Unpaid Tagging labels differ. The validation is therefore a *shifted-window evaluation of the same
population*, not validation on unseen customers. No calendar dates or data dictionary were provided,
so the meaning of Q1-Q5 depends on confirmation by the data owner.

## Data audit highlights (aggregate only)
- No missing values, no duplicated Customer IDs, identical customer population and ordering.
- Tagging rate: 26.70% (Data All) vs 35.83% (Data Validasi); 2,042 customers have a different label
  between files (1,366 non-tagged to tagged, 676 tagged to non-tagged).
- `HasCrCard` is identical for Q1-Q3, and equals 1 for every customer from Q4 (constant in Q4 and Q5).
- 251 customers have zero income; zero balances decline from Q1 to Q4.
- Number of products never decreases between consecutive quarters; Q5 reaches up to 7 products.
- Q5 shows a visible shift in balance level and activity rate versus Q1-Q4 (to be examined as potential drift).

## Tools
Python (pandas, NumPy, scikit-learn, statsmodels, SciPy, matplotlib, seaborn), PostgreSQL, SQLAlchemy,
Power BI, Git/GitHub.

## Workflow
Audit -> Cleaning & feature engineering -> EDA -> SQL -> Statistics -> ML -> Shifted-window validation
-> Power BI -> Report.

## Repository structure
```
data/            raw / processed / sample (real data is git-ignored)
notebooks/       01_data_audit ... 06_validation_and_robustness
src/             preprocessing, feature_engineering, modeling, evaluation
sql/             PostgreSQL scripts
dashboard/       Power BI screenshots
reports/         data quality report, data dictionary, final report
models/          saved model artifacts (git-ignored)
```

## Installation
```bash
git clone https://github.com/vaioretto22/FinanKu-Customer-Risk-Analytics-Unpaid-Tagging-Prediction.git
cd FinanKu-Customer-Risk-Analytics-Unpaid-Tagging-Prediction
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python check_env.py
```

## Running the project
1. Place the confidential CSVs locally as `data/raw/finanku_data_all.csv` and
   `data/raw/finanku_data_validasi.csv` (never committed).
2. Run the notebooks in `notebooks/` in numeric order.

## Limitations
- Unpaid Tagging, ActiveMember, income and balance units are not formally defined.
- Q1-Q5 are not linked to calendar dates.
- Same-customer shifted-window validation is not independent unseen-customer validation.
- Findings are associations, not causal claims, and do not support claims about future credit default.

## Data confidentiality statement
The original files are treated as confidential customer-level financial data. No raw data, customer
identifiers, customer-level predictions, credentials or embedded-data Power BI files are committed.
Any public demo data will be clearly labeled synthetic.
