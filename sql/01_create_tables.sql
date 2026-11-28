-- =====================================================================
-- 01_create_tables.sql : schema for FinanKu Customer Risk Analytics
-- Run from the project root:
--   psql -h localhost -U postgres -d finanku -f sql/01_create_tables.sql
-- (the database "finanku" must exist: CREATE DATABASE finanku;)
-- WARNING: drops and recreates all project tables.
-- =====================================================================
\set ON_ERROR_STOP on

DROP VIEW  IF EXISTS vw_tagging_cube, vw_quarterly_behavior, vw_window_comparison,
                     vw_label_transitions, vw_branch_summary CASCADE;
DROP TABLE IF EXISTS fact_unpaid_tagging, fact_customer_quarterly, dim_customer,
                     dim_branch, dim_observation_window, stg_data_all, stg_data_validasi CASCADE;

-- ---------------------------------------------------------------------
-- Staging tables: raw wide files, loaded as-is (22 columns each)
-- ---------------------------------------------------------------------
CREATE TABLE stg_data_all (
    customer_id        BIGINT,
    branch_code        INTEGER,
    city               TEXT,
    age                INTEGER,
    income_measure     NUMERIC(18,2),
    balance_q1 NUMERIC(18,2), num_products_q1 INTEGER, has_credit_card_q1 SMALLINT, active_member_q1 SMALLINT,
    balance_q2 NUMERIC(18,2), num_products_q2 INTEGER, has_credit_card_q2 SMALLINT, active_member_q2 SMALLINT,
    balance_q3 NUMERIC(18,2), num_products_q3 INTEGER, has_credit_card_q3 SMALLINT, active_member_q3 SMALLINT,
    balance_q4 NUMERIC(18,2), num_products_q4 INTEGER, has_credit_card_q4 SMALLINT, active_member_q4 SMALLINT,
    unpaid_tagging     SMALLINT
);

CREATE TABLE stg_data_validasi (
    customer_id        BIGINT,
    branch_code        INTEGER,
    city               TEXT,
    age                INTEGER,
    income_measure     NUMERIC(18,2),
    balance_q2 NUMERIC(18,2), num_products_q2 INTEGER, has_credit_card_q2 SMALLINT, active_member_q2 SMALLINT,
    balance_q3 NUMERIC(18,2), num_products_q3 INTEGER, has_credit_card_q3 SMALLINT, active_member_q3 SMALLINT,
    balance_q4 NUMERIC(18,2), num_products_q4 INTEGER, has_credit_card_q4 SMALLINT, active_member_q4 SMALLINT,
    balance_q5 NUMERIC(18,2), num_products_q5 INTEGER, has_credit_card_q5 SMALLINT, active_member_q5 SMALLINT,
    unpaid_tagging     SMALLINT
);

-- ---------------------------------------------------------------------
-- Dimensions
-- ---------------------------------------------------------------------
-- Each branch belongs to exactly one city (verified in Phase 1), so city is stored once per branch (3NF).
CREATE TABLE dim_branch (
    branch_code  VARCHAR(10) PRIMARY KEY,          -- categorical identifier, not a number
    city         VARCHAR(50) NOT NULL
);

CREATE TABLE dim_customer (
    customer_id     BIGINT PRIMARY KEY,
    branch_code     VARCHAR(10) NOT NULL REFERENCES dim_branch (branch_code),
    age             SMALLINT NOT NULL CHECK (age > 0),
    income_measure  NUMERIC(18,2) NOT NULL CHECK (income_measure >= 0)   -- unit/currency unconfirmed
);

CREATE TABLE dim_observation_window (
    window_id         SMALLINT PRIMARY KEY,
    window_name       VARCHAR(40) NOT NULL UNIQUE,
    starting_quarter  VARCHAR(2) NOT NULL CHECK (starting_quarter ~ '^Q[1-5]$'),
    ending_quarter    VARCHAR(2) NOT NULL CHECK (ending_quarter   ~ '^Q[1-5]$'),
    source_dataset    VARCHAR(60) NOT NULL
);

-- ---------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------
-- Canonical customer-quarter snapshots (Q1-Q5). Q2-Q4 appear in both files and are verified identical
-- before being stored once.
CREATE TABLE fact_customer_quarterly (
    customer_id      BIGINT      NOT NULL REFERENCES dim_customer (customer_id),
    quarter_label    VARCHAR(2)  NOT NULL CHECK (quarter_label ~ '^Q[1-5]$'),
    balance          NUMERIC(18,2) NOT NULL CHECK (balance >= 0),
    num_products     SMALLINT    NOT NULL CHECK (num_products >= 0),
    has_credit_card  SMALLINT    NOT NULL CHECK (has_credit_card IN (0, 1)),
    active_member    SMALLINT    NOT NULL CHECK (active_member IN (0, 1)),
    PRIMARY KEY (customer_id, quarter_label)
);

-- One label per customer per observation window (labels differ between windows, so both are kept).
CREATE TABLE fact_unpaid_tagging (
    customer_id     BIGINT   NOT NULL REFERENCES dim_customer (customer_id),
    window_id       SMALLINT NOT NULL REFERENCES dim_observation_window (window_id),
    unpaid_tagging  SMALLINT NOT NULL CHECK (unpaid_tagging IN (0, 1)),   -- 1 = tagged, 0 = non-tagged
    PRIMARY KEY (customer_id, window_id)
);

-- ---------------------------------------------------------------------
-- Indexes (primary keys are indexed automatically)
-- ---------------------------------------------------------------------
CREATE INDEX idx_dim_customer_branch  ON dim_customer (branch_code);
CREATE INDEX idx_dim_customer_age     ON dim_customer (age);
CREATE INDEX idx_fcq_quarter          ON fact_customer_quarterly (quarter_label);
CREATE INDEX idx_fut_window_tag       ON fact_unpaid_tagging (window_id, unpaid_tagging);

-- ---------------------------------------------------------------------
-- Reusable grouping rules (same bands as the EDA notebook)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_age_group(p_age INTEGER) RETURNS TEXT
LANGUAGE SQL IMMUTABLE AS $$
    SELECT CASE WHEN p_age <= 30 THEN '1) <=30'
                WHEN p_age <= 40 THEN '2) 31-40'
                WHEN p_age <= 50 THEN '3) 41-50'
                WHEN p_age <= 60 THEN '4) 51-60'
                ELSE '5) >60' END
$$;

CREATE OR REPLACE FUNCTION fn_income_group(p_income NUMERIC) RETURNS TEXT
LANGUAGE SQL IMMUTABLE AS $$
    SELECT CASE WHEN p_income = 0        THEN '1) Zero'
                WHEN p_income <= 18000000 THEN '2) <=18M'
                WHEN p_income <= 23000000 THEN '3) 18-23M'
                WHEN p_income <= 30000000 THEN '4) 23-30M'
                ELSE '5) >30M' END
$$;
