# FinanKu Customer Risk Analytics & Unpaid Tagging Prediction

End-to-end banking analytics portfolio project: data audit, feature engineering, exploratory analysis,
SQL (PostgreSQL), statistical analysis, machine learning classification, shifted-window validation,
Power BI dashboard and business report.

> **Status: Phase 4 complete, Phase 5 (statistical analysis) next.**
> SQL scripts were executed locally and validated on 2026-11-28 (see [`sql/README.md`](sql/README.md)).

## Project status
| Phase | Topic | Status |
|---|---|---|
| 0 | Planning and environment | Done |
| 1 | Data audit and quality assessment | Done |
| 2 | Cleaning and feature engineering | Done |
| 3 | Exploratory data analysis | Done |
| 4 | SQL database (PostgreSQL) | Done, executed locally |
| 5 | Statistical analysis | Next |
| 6 | Machine learning | Pending |
| 7 | Validation and robustness | Pending |
| 8 | Power BI dashboard | Pending |
| 9 | Business report | Pending |
| 10 | Final repository audit | Pending |

## Business problem
Financial institutions need to understand customer behavior, monitor customer segments and identify patterns
associated with unpaid-related tagging. This project studies customer demographics and quarterly banking behavior,
and evaluates whether machine learning can classify the **Unpaid Tagging** indicator on a shifted observation window.

**Important:** the definition of Unpaid Tagging has not been provided. The project uses the neutral terms
*tagged* (= 1) and *non-tagged* (= 0) and does not interpret the indicator as loan default or delinquency.
Results describe statistical associations, not causal relationships.

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

Both files describe the **same customers**. Q2-Q4 observations are identical across files; the Unpaid Tagging labels
differ. The validation is therefore a *shifted-window evaluation of the same population*, not validation on unseen customers.

**Data provenance.** The data were provided through a course assignment, with permission to use them in a public
portfolio. No data dictionary is available, so all variable definitions are working assumptions documented in
[`reports/assumptions_and_limitations.md`](reports/assumptions_and_limitations.md). Calendar meaning of Q1-Q5 is unknown.

## Tools
Python (pandas, NumPy, scikit-learn, statsmodels, SciPy, matplotlib, seaborn), PostgreSQL, SQLAlchemy, Power BI, Git/GitHub.

## Workflow
Audit -> Cleaning and feature engineering -> EDA -> SQL -> Statistics -> ML -> Shifted-window validation -> Power BI -> Report.

## Data quality findings (aggregate only)
- No missing values, no duplicated Customer IDs; identical customer population and ordering in both files.
- Tagging rate: 26.70% (Data All) vs 35.83% (Data Validasi). **2,042 customers have a different label between files**
  (1,366 non-tagged to tagged, 676 tagged to non-tagged).
- Credit-card indicator is identical for Q1-Q3 and equals 1 for every customer from Q4 (constant in Q4 and Q5).
- 251 customers have zero income; zero balances decline from Q1 to Q4.
- Number of products never decreases between consecutive quarters; Q5 reaches up to 7 products.
- Q5 differs from Q1-Q4: mean balance rises by 9.66% from Q4 to Q5 (previously about 0.1% per quarter), every balance
  change from Q4 to Q5 is an increase, and the active-member rate falls from 58.1% to 45.9%.

## Key analytical findings so far
All findings are descriptive associations; variable definitions are unconfirmed.
- **Customers without a credit card until the final quarter (611, 8.1% of customers) are 100% tagged in Data All**
  (66.0% in Data Validasi) and make up 30.3% of tagged customers. This may indicate a definitional link or leakage and is
  handled explicitly: models will be compared with and without card information.
- Tagging rate by number of products is non-linear (Data All: 34.9% for 1 product, 16.9% for 2, 27.8% for 3, 58.5% for 4).
- Customers with no or low balance have lower tagging rates (about 19-21%) than those with mid or high balances (about 31-32%).
- Age, income band and city show almost no association with tagging; branch differences are weak (1 of 18 branches has an
  interval excluding the overall rate in each window).
- Associations are clearly weaker in Data Validasi than in Data All.
- Customers whose label changed between windows look similar, on the observed features, to those whose label did not change.

## Model performance
Pending (Phase 6-7).

## Dashboard preview
Pending (Phase 8).

## Repository structure
```
README.md
requirements.txt
.gitignore
.env.example          template only; real credentials stay in a local .env
check_env.py          verifies the Python environment
check_db.py           verifies PostgreSQL connection and SQL vs CSV totals
data/                 raw / processed / sample (real data is git-ignored)
notebooks/            01 audit, 02 cleaning and features, 03 EDA (04-06 to come)
src/                  preprocessing, feature_engineering, eda, db
sql/                  PostgreSQL scripts, schema documentation, sql/README.md
figures/              EDA charts (aggregate only)
reports/              data quality report, data dictionary, EDA findings, assumptions and limitations
dashboard/            Power BI screenshots (to come)
models/               saved models (git-ignored)
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
1. Place the confidential CSV files locally as `data/raw/finanku_data_all.csv` and
   `data/raw/finanku_data_validasi.csv` (they are never committed).
2. Run the notebooks in `notebooks/` in numeric order (VS Code or Jupyter, kernel: `.venv`).

## SQL database setup
1. Install PostgreSQL and create a database: `CREATE DATABASE finanku;`
2. Copy `.env.example` to `.env` and fill in your credentials (this file is git-ignored).
3. From the project root run, in order: `sql/01_create_tables.sql`, `02_import_data.sql`, `03_data_validation.sql`,
   `05_create_views.sql` (e.g. `psql -U postgres -d finanku -f sql/01_create_tables.sql`).
4. Verify with `python check_db.py`.

Details, expected results and the local execution log: [`sql/README.md`](sql/README.md).

## Limitations
- Unpaid Tagging, ActiveMember, income and balance units are not formally defined.
- Q1-Q5 are not linked to calendar dates.
- Same-customer shifted-window validation is not independent unseen-customer validation.
- The tag is not stable across windows (2,042 labels differ), and the data may be constructed for teaching.
- Findings are associations, not causal claims, and do not support claims about future credit default.

See [`reports/assumptions_and_limitations.md`](reports/assumptions_and_limitations.md).

## Data confidentiality statement
The original files are treated as confidential customer-level financial data. No raw data, customer identifiers,
customer-level predictions, credentials or embedded-data Power BI files are committed. Any public demo data will be
clearly labeled synthetic.
