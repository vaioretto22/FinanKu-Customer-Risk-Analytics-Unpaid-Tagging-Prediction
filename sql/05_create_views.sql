-- =====================================================================
-- 05_create_views.sql : reusable views for Power BI
-- Privacy by design: NO customer_id (or any row-level customer record) is exposed.
-- Views are pre-aggregated; measures in Power BI should SUM the count columns and divide
-- (tagging rate = SUM(tagged) / SUM(customers)); never average a column of rates.
--   psql -h localhost -U postgres -d finanku -f sql/05_create_views.sql
-- =====================================================================
\set ON_ERROR_STOP on

-- Tagging counts across window x city x branch x age group x income group
CREATE OR REPLACE VIEW vw_tagging_cube AS
SELECT w.window_name, w.window_id, b.city, b.branch_code,
       fn_age_group(c.age) AS age_group,
       fn_income_group(c.income_measure) AS income_group,
       COUNT(*)::INT AS customers,
       SUM(t.unpaid_tagging)::INT AS tagged
FROM fact_unpaid_tagging t
JOIN dim_observation_window w USING (window_id)
JOIN dim_customer c USING (customer_id)
JOIN dim_branch   b USING (branch_code)
GROUP BY w.window_name, w.window_id, b.city, b.branch_code, fn_age_group(c.age), fn_income_group(c.income_measure);

-- Quarterly behaviour by quarter x city x age group x income group (additive columns)
CREATE OR REPLACE VIEW vw_quarterly_behavior AS
SELECT f.quarter_label, b.city, fn_age_group(c.age) AS age_group, fn_income_group(c.income_measure) AS income_group,
       COUNT(*)::INT                                   AS customers,
       SUM(f.balance)                                  AS total_balance,
       SUM((f.balance = 0)::INT)::INT                  AS zero_balance_customers,
       SUM(f.num_products)::INT                        AS total_products,
       SUM(f.active_member)::INT                       AS active_customers,
       SUM(f.has_credit_card)::INT                     AS card_customers
FROM fact_customer_quarterly f
JOIN dim_customer c USING (customer_id)
JOIN dim_branch   b USING (branch_code)
GROUP BY f.quarter_label, b.city, fn_age_group(c.age), fn_income_group(c.income_measure);

-- Start vs end of each observation window (additive sums; divide by customers in DAX)
CREATE OR REPLACE VIEW vw_window_comparison AS
SELECT w.window_id, w.window_name, w.starting_quarter, w.ending_quarter,
       COUNT(*)::INT AS customers,
       SUM(s.balance) AS balance_start_total,       SUM(e.balance) AS balance_end_total,
       SUM(s.num_products)::INT AS products_start_total, SUM(e.num_products)::INT AS products_end_total,
       SUM(s.active_member)::INT AS active_start_customers, SUM(e.active_member)::INT AS active_end_customers,
       SUM((s.balance = 0)::INT)::INT AS zero_balance_start_customers, SUM((e.balance = 0)::INT)::INT AS zero_balance_end_customers,
       SUM((e.balance < s.balance)::INT)::INT AS balance_decreased_customers
FROM dim_observation_window w
JOIN fact_customer_quarterly s ON s.quarter_label = w.starting_quarter
JOIN fact_customer_quarterly e ON e.customer_id = s.customer_id AND e.quarter_label = w.ending_quarter
GROUP BY w.window_id, w.window_name, w.starting_quarter, w.ending_quarter;

-- Label transitions between windows
CREATE OR REPLACE VIEW vw_label_transitions AS
SELECT a.unpaid_tagging AS tag_in_all, v.unpaid_tagging AS tag_in_validasi,
       CASE WHEN a.unpaid_tagging = v.unpaid_tagging THEN 'Unchanged' ELSE 'Changed' END AS change_status,
       COUNT(*)::INT AS customers
FROM fact_unpaid_tagging a
JOIN fact_unpaid_tagging v ON v.customer_id = a.customer_id AND v.window_id = 2
WHERE a.window_id = 1
GROUP BY a.unpaid_tagging, v.unpaid_tagging;

-- Branch summary with rank within each window
CREATE OR REPLACE VIEW vw_branch_summary AS
SELECT window_id, window_name, city, branch_code,
       SUM(customers)::INT AS customers, SUM(tagged)::INT AS tagged,
       ROUND(100.0 * SUM(tagged) / SUM(customers), 2) AS tagging_rate_pct,
       RANK() OVER (PARTITION BY window_id ORDER BY SUM(tagged)::NUMERIC / SUM(customers) DESC) AS rate_rank
FROM vw_tagging_cube
GROUP BY window_id, window_name, city, branch_code;

-- Safety check: no view may contain a customer_id column (expect 0 rows)
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema = 'public' AND table_name LIKE 'vw\_%' AND column_name ILIKE '%customer\_id%';
