-- =====================================================================
-- 02_import_data.sql : load CSVs into staging, verify overlap, populate dims/facts
-- Run from the PROJECT ROOT (the \copy paths are relative to where psql is started):
--   psql -h localhost -U postgres -d finanku -f sql/02_import_data.sql
-- Expected files:
--   data/raw/finanku_data_all.csv       (22 columns, Q1-Q4)
--   data/raw/finanku_data_validasi.csv  (22 columns, Q2-Q5)
-- The CSV header names are ignored (HEADER true skips the row); columns are matched BY POSITION.
-- =====================================================================
\set ON_ERROR_STOP on
BEGIN;

TRUNCATE fact_unpaid_tagging, fact_customer_quarterly, dim_customer, dim_branch,
         dim_observation_window, stg_data_all, stg_data_validasi;

-- 1) Load raw files into staging ------------------------------------------------
\copy stg_data_all      FROM 'data/raw/finanku_data_all.csv'      WITH (FORMAT csv, HEADER true)
\copy stg_data_validasi FROM 'data/raw/finanku_data_validasi.csv' WITH (FORMAT csv, HEADER true)

-- 2) Guard: both files must describe the same customers with identical profile and identical Q2-Q4.
--    If anything differs, the script stops and NOTHING is committed.
DO $$
DECLARE
    n_all INT; n_val INT; n_only_one INT; n_profile_diff INT; n_q_diff INT; n_dup INT;
BEGIN
    SELECT COUNT(*) INTO n_all FROM stg_data_all;
    SELECT COUNT(*) INTO n_val FROM stg_data_validasi;
    SELECT COUNT(*) - COUNT(DISTINCT customer_id) INTO n_dup FROM stg_data_all;

    SELECT COUNT(*) INTO n_only_one FROM (
        (SELECT customer_id FROM stg_data_all EXCEPT SELECT customer_id FROM stg_data_validasi)
        UNION ALL
        (SELECT customer_id FROM stg_data_validasi EXCEPT SELECT customer_id FROM stg_data_all)
    ) x;

    SELECT COUNT(*) INTO n_profile_diff
    FROM stg_data_all a JOIN stg_data_validasi v USING (customer_id)
    WHERE (a.branch_code, a.city, a.age, a.income_measure)
          IS DISTINCT FROM (v.branch_code, v.city, v.age, v.income_measure);

    SELECT COUNT(*) INTO n_q_diff
    FROM stg_data_all a JOIN stg_data_validasi v USING (customer_id)
    WHERE (a.balance_q2, a.num_products_q2, a.has_credit_card_q2, a.active_member_q2,
           a.balance_q3, a.num_products_q3, a.has_credit_card_q3, a.active_member_q3,
           a.balance_q4, a.num_products_q4, a.has_credit_card_q4, a.active_member_q4)
          IS DISTINCT FROM
          (v.balance_q2, v.num_products_q2, v.has_credit_card_q2, v.active_member_q2,
           v.balance_q3, v.num_products_q3, v.has_credit_card_q3, v.active_member_q3,
           v.balance_q4, v.num_products_q4, v.has_credit_card_q4, v.active_member_q4);

    RAISE NOTICE 'rows: all=%, validasi=%, duplicate ids=%, ids in only one file=%, profile differences=%, Q2-Q4 differences=%',
                 n_all, n_val, n_dup, n_only_one, n_profile_diff, n_q_diff;

    IF n_all <> n_val OR n_dup > 0 OR n_only_one > 0 OR n_profile_diff > 0 OR n_q_diff > 0 THEN
        RAISE EXCEPTION 'Overlap validation failed: files cannot be merged into a canonical customer-quarter table';
    END IF;
END $$;

-- 3) Observation windows --------------------------------------------------------
INSERT INTO dim_observation_window (window_id, window_name, starting_quarter, ending_quarter, source_dataset) VALUES
    (1, 'Data All (Q1-Q4)',      'Q1', 'Q4', 'FinanKu Data All'),
    (2, 'Data Validasi (Q2-Q5)', 'Q2', 'Q5', 'FinanKu Data Validasi');

-- 4) Branches and customers (profile is identical in both files; take it from Data All)
INSERT INTO dim_branch (branch_code, city)
SELECT DISTINCT branch_code::TEXT, TRIM(city) FROM stg_data_all;      -- fails if a branch maps to 2 cities

INSERT INTO dim_customer (customer_id, branch_code, age, income_measure)
SELECT customer_id, branch_code::TEXT, age, income_measure FROM stg_data_all;

-- 5) Canonical quarterly snapshots: Q1-Q4 from Data All, Q5 from Data Validasi (Q2-Q4 verified identical above)
INSERT INTO fact_customer_quarterly (customer_id, quarter_label, balance, num_products, has_credit_card, active_member)
SELECT a.customer_id, q.quarter_label, q.balance, q.num_products, q.has_credit_card, q.active_member
FROM stg_data_all a
CROSS JOIN LATERAL (VALUES
    ('Q1', a.balance_q1, a.num_products_q1, a.has_credit_card_q1, a.active_member_q1),
    ('Q2', a.balance_q2, a.num_products_q2, a.has_credit_card_q2, a.active_member_q2),
    ('Q3', a.balance_q3, a.num_products_q3, a.has_credit_card_q3, a.active_member_q3),
    ('Q4', a.balance_q4, a.num_products_q4, a.has_credit_card_q4, a.active_member_q4)
) AS q (quarter_label, balance, num_products, has_credit_card, active_member);

INSERT INTO fact_customer_quarterly (customer_id, quarter_label, balance, num_products, has_credit_card, active_member)
SELECT customer_id, 'Q5', balance_q5, num_products_q5, has_credit_card_q5, active_member_q5
FROM stg_data_validasi;

-- 6) Target labels: one per window (they differ between the files, so both are kept)
INSERT INTO fact_unpaid_tagging (customer_id, window_id, unpaid_tagging)
SELECT customer_id, 1, unpaid_tagging FROM stg_data_all
UNION ALL
SELECT customer_id, 2, unpaid_tagging FROM stg_data_validasi;

COMMIT;

ANALYZE;
SELECT 'dim_customer' AS table_name, COUNT(*) AS rows FROM dim_customer
UNION ALL SELECT 'dim_branch', COUNT(*) FROM dim_branch
UNION ALL SELECT 'dim_observation_window', COUNT(*) FROM dim_observation_window
UNION ALL SELECT 'fact_customer_quarterly', COUNT(*) FROM fact_customer_quarterly
UNION ALL SELECT 'fact_unpaid_tagging', COUNT(*) FROM fact_unpaid_tagging;
