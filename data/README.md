# Data

The original data are **not included** in this repository.

## Source
- Provider: [MySkill](https://myskill.id)
- Program: *Data Analysis*, project *Prediction Model* (May 9, 2024)
- Use: provided as a course assignment, with permission to use it in a public portfolio. Redistribution of the files is not assumed.

## Files expected locally
| File | Window | Rows | Columns |
|---|---|---|---|
| `data/raw/finanku_data_all.csv` | Q1-Q4 (development) | 7,561 | 22 |
| `data/raw/finanku_data_validasi.csv` | Q2-Q5 (shifted window) | 7,561 | 22 |

Place the files in `data/raw/` with exactly these names (on Windows, check that the extension is not doubled as `.csv.csv`).
No official data dictionary was provided; see `reports/data_dictionary.md` and `reports/assumptions_and_limitations.md`.

## Confidentiality
- `data/raw/` and `data/processed/` are git-ignored. Do not commit the original files or any customer-level derived file
  (cleaned data, engineered features, predictions).
- Only aggregate results (tables, figures, summary metrics) are published.
