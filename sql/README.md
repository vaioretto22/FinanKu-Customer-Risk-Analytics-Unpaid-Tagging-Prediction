# SQL: PostgreSQL Database

> **Status: executed locally on 2026-11-28.** The scripts were written for PostgreSQL 16 and run locally on
> PostgreSQL 19 (`psql` 19.0, Windows). The validation script reported all checks as `PASS`, and the Python
> check (`check_db.py`) confirmed that database totals match the source CSV files. See the execution log below.

## What this folder contains
| File | Purpose |
|---|---|
| `01_create_tables.sql` | Creates staging tables, dimension and fact tables, constraints, indexes and helper functions |
| `02_import_data.sql` | Loads the two CSV files, checks that the overlapping quarters (Q2-Q4) are identical, then fills dimensions and facts in one transaction |
| `03_data_validation.sql` | 18 PASS/FAIL checks plus informational checks |
| `04_analysis_queries.sql` | 13 analytical queries (CTEs, window functions, conditional aggregation) |
| `05_create_views.sql` | Aggregated views for Power BI (no customer identifiers) |
| `schema_documentation.md` | ER diagram, table grain and design decisions |

## Data model (summary)
`dim_branch` -> `dim_customer` -> `fact_customer_quarterly` (customer x quarter, Q1-Q5)
and `fact_unpaid_tagging` (customer x observation window) with `dim_observation_window`.
Both target labels are stored, because they differ between the two observation windows.
Full details: `schema_documentation.md`.

## Requirements
- PostgreSQL (written for 16, run locally on 19) and the `psql` command-line client
- The two CSV files placed locally in `data/raw/` as `finanku_data_all.csv` and `finanku_data_validasi.csv`
  (the data is not included in this repository)

## How to run
1. Create the database:
   ```sql
   CREATE DATABASE finanku;
   ```
2. From the **project root** (the `\copy` paths are relative to where `psql` is started), run in order:
   ```bat
   psql -U postgres -d finanku -f sql/01_create_tables.sql
   psql -U postgres -d finanku -f sql/02_import_data.sql
   psql -U postgres -d finanku -f sql/03_data_validation.sql
   psql -U postgres -d finanku -f sql/05_create_views.sql
   psql -U postgres -d finanku -f sql/04_analysis_queries.sql
   ```
   `\copy` is a `psql` command and does not work in the pgAdmin Query Tool. To avoid the pager in
   `04_analysis_queries.sql`, add `-P pager=off`.
3. Optional end-to-end check from Python (credentials come from a local `.env` file, see `.env.example`):
   ```bat
   python check_db.py
   ```

## Expected validation results
| Check | Expected |
|---|---|
| Customers / branches / windows | 7,561 / 18 / 2 |
| Customer-quarter rows | 37,805 (7,561 x 5 quarters) |
| Tagging rows | 15,122 (7,561 x 2 windows) |
| Tagged customers, Data All | 2,019 (26.70%) |
| Tagged customers, Data Validasi | 2,709 (35.83%) |
| Customers whose label differs between windows | 2,042 |
| Zero-income customers | 251 |
| Result of `03_data_validation.sql` | 18 rows with status `PASS`, none `FAIL` |
| Customer identifiers exposed by `vw_*` views | 0 |

## Local execution log
- [x] PostgreSQL installed and database `finanku` created
- [x] `01_create_tables.sql` ran without errors
- [x] `02_import_data.sql` ran without errors (overlap check passed)
- [x] `03_data_validation.sql`: all checks `PASS`
- [x] `05_create_views.sql`: safety query returned 0 rows
- [x] `04_analysis_queries.sql` ran without errors
- [x] `python check_db.py`: both windows `MATCH` (SQL totals equal the CSV totals: 7,561 customers; 2,019 and 2,709 tagged)

Date of local run: 2026-11-28
Environment: Windows, PostgreSQL 19 (`psql` 19.0), Python virtual environment (`.venv`)

## Troubleshooting
- **`could not open file ... data/raw/...`**: run `psql` from the project root, or use `\cd` to move there first.
  Also check that the CSV files are named exactly `finanku_data_all.csv` and `finanku_data_validasi.csv`
  (Windows can hide extensions and produce `.csv.csv`).
- **`psql` not recognised (Windows)**: use "SQL Shell (psql)", or add the PostgreSQL `bin` folder to PATH, or call `psql.exe` by its full path.
- **`password authentication failed`**: use the password set for the `postgres` user during installation.
  For `check_db.py`, make sure `.env` contains your real `DB_USER` and `DB_PASSWORD` (not the placeholders from `.env.example`).
- **Overlap validation failed**: the two CSV files no longer have identical Q2-Q4 data; the load stops and
  nothing is committed. Re-check the files.

## Data confidentiality
No customer-level data or credentials are stored in this repository. Database credentials are read from a
local `.env` file that is excluded by `.gitignore`.
