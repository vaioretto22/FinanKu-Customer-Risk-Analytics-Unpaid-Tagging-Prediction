-- =====================================================================
-- 04_analysis_queries.sql : analytical queries (run them one at a time in pgAdmin/psql, or all with -f)
-- Terms: tagged = unpaid_tagging 1 (definition not provided; NOT assumed to be default).
-- Window 1 = Data All (Q1-Q4), window 2 = Data Validasi (Q2-Q5).
-- =====================================================================

-- 1. Total customers -------------------------------------------------------------
SELECT COUNT(*) AS total_customers FROM dim_customer;

-- 2. Number of tagged customers (per window) -------------------------------------
SELECT w.window_name, SUM(t.unpaid_tagging) AS tagged_customers,
       COUNT(*) - SUM(t.unpaid_tagging)      AS non_tagged_customers
FROM fact_unpaid_tagging t
JOIN dim_observation_window w USING (window_id)
GROUP BY w.window_id, w.window_name ORDER BY w.window_id;

-- 3. Unpaid Tagging rate (per window) --------------------------------------------
SELECT w.window_name, COUNT(*) AS customers, SUM(t.unpaid_tagging) AS tagged,
       ROUND(100.0 * AVG(t.unpaid_tagging), 2) AS tagging_rate_pct
FROM fact_unpaid_tagging t
JOIN dim_observation_window w USING (window_id)
GROUP BY w.window_id, w.window_name ORDER BY w.window_id;

-- 4. Tagging rate by city (group size always shown) ------------------------------
SELECT w.window_name, b.city, COUNT(*) AS customers, SUM(t.unpaid_tagging) AS tagged,
       ROUND(100.0 * AVG(t.unpaid_tagging), 2) AS tagging_rate_pct
FROM fact_unpaid_tagging t
JOIN dim_observation_window w USING (window_id)
JOIN dim_customer c USING (customer_id)
JOIN dim_branch   b USING (branch_code)
GROUP BY w.window_id, w.window_name, b.city
ORDER BY w.window_id, tagging_rate_pct DESC;

-- 5. Tagging rate by branch, with rank and gap to the overall rate (CTE + window functions)
WITH branch_rates AS (
    SELECT t.window_id, b.branch_code, b.city, COUNT(*) AS customers,
           SUM(t.unpaid_tagging) AS tagged, AVG(t.unpaid_tagging) AS rate
    FROM fact_unpaid_tagging t
    JOIN dim_customer c USING (customer_id)
    JOIN dim_branch   b USING (branch_code)
    GROUP BY t.window_id, b.branch_code, b.city
)
SELECT w.window_name, br.branch_code, br.city, br.customers, br.tagged,
       ROUND(100.0 * br.rate, 2) AS tagging_rate_pct,
       RANK() OVER (PARTITION BY br.window_id ORDER BY br.rate DESC) AS rank_in_window,
       ROUND(100.0 * (br.rate - SUM(br.tagged) OVER (PARTITION BY br.window_id)::NUMERIC
                                / SUM(br.customers) OVER (PARTITION BY br.window_id)), 2) AS gap_to_overall_pp
FROM branch_rates br
JOIN dim_observation_window w USING (window_id)
ORDER BY br.window_id, rank_in_window;

-- 6. Average balance by quarter, with change vs previous quarter (LAG) -----------
WITH q AS (
    SELECT quarter_label, ROUND(AVG(balance), 0) AS avg_balance FROM fact_customer_quarterly GROUP BY quarter_label
)
SELECT quarter_label, avg_balance,
       ROUND(100.0 * (avg_balance - LAG(avg_balance) OVER (ORDER BY quarter_label))
             / NULLIF(LAG(avg_balance) OVER (ORDER BY quarter_label), 0), 2) AS pct_change_vs_previous
FROM q ORDER BY quarter_label;

-- 7. Average number of products by quarter ---------------------------------------
WITH q AS (
    SELECT quarter_label, ROUND(AVG(num_products), 3) AS avg_products FROM fact_customer_quarterly GROUP BY quarter_label
)
SELECT quarter_label, avg_products,
       ROUND(avg_products - LAG(avg_products) OVER (ORDER BY quarter_label), 3) AS change_vs_previous
FROM q ORDER BY quarter_label;

-- 8. Active-member rate and credit-card ownership by quarter ---------------------
SELECT quarter_label,
       ROUND(100.0 * AVG(active_member), 2)   AS active_member_rate_pct,
       ROUND(100.0 * AVG(has_credit_card), 2) AS credit_card_rate_pct,
       ROUND(100.0 * AVG((balance = 0)::INT), 2) AS zero_balance_pct
FROM fact_customer_quarterly GROUP BY quarter_label ORDER BY quarter_label;

-- 9. Customer segmentation by income band (customers and tagging rate per window)
SELECT fn_income_group(c.income_measure) AS income_group,
       COUNT(DISTINCT c.customer_id) AS customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.window_id = 1 AND t.unpaid_tagging = 1)
             / NULLIF(COUNT(*) FILTER (WHERE t.window_id = 1), 0), 2) AS tagging_rate_all_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.window_id = 2 AND t.unpaid_tagging = 1)
             / NULLIF(COUNT(*) FILTER (WHERE t.window_id = 2), 0), 2) AS tagging_rate_validasi_pct
FROM dim_customer c JOIN fact_unpaid_tagging t USING (customer_id)
GROUP BY 1 ORDER BY 1;

-- 10. Customer segmentation by age group -----------------------------------------
SELECT fn_age_group(c.age) AS age_group,
       COUNT(DISTINCT c.customer_id) AS customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.window_id = 1 AND t.unpaid_tagging = 1)
             / NULLIF(COUNT(*) FILTER (WHERE t.window_id = 1), 0), 2) AS tagging_rate_all_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.window_id = 2 AND t.unpaid_tagging = 1)
             / NULLIF(COUNT(*) FILTER (WHERE t.window_id = 2), 0), 2) AS tagging_rate_validasi_pct
FROM dim_customer c JOIN fact_unpaid_tagging t USING (customer_id)
GROUP BY 1 ORDER BY 1;

-- 11. Tagging distribution across demographic segments (age x income) ------------
WITH base AS (
    SELECT t.window_id, fn_age_group(c.age) AS age_group, fn_income_group(c.income_measure) AS income_group,
           t.unpaid_tagging
    FROM fact_unpaid_tagging t JOIN dim_customer c USING (customer_id)
), seg AS (
    SELECT window_id, age_group, income_group, COUNT(*) AS customers, SUM(unpaid_tagging) AS tagged
    FROM base GROUP BY window_id, age_group, income_group
)
SELECT w.window_name, s.age_group, s.income_group, s.customers, s.tagged,
       ROUND(100.0 * s.tagged / s.customers, 2) AS tagging_rate_pct,
       ROUND(100.0 * s.customers / SUM(s.customers) OVER (PARTITION BY s.window_id), 2) AS share_of_customers_pct,
       ROUND(100.0 * s.tagged    / SUM(s.tagged)    OVER (PARTITION BY s.window_id), 2) AS share_of_tagged_pct
FROM seg s JOIN dim_observation_window w USING (window_id)
ORDER BY s.window_id, s.age_group, s.income_group;

-- 12. Customer behaviour comparison between observation windows ------------------
-- Start/end quarter of each window are read from dim_observation_window, so the same logic serves both windows.
SELECT w.window_name,
       ROUND(AVG(s.balance), 0)                       AS avg_balance_start,
       ROUND(AVG(e.balance), 0)                       AS avg_balance_end,
       ROUND(AVG(e.balance - s.balance), 0)           AS avg_balance_change,
       ROUND(AVG(s.num_products), 3)                  AS avg_products_start,
       ROUND(AVG(e.num_products), 3)                  AS avg_products_end,
       ROUND(100.0 * AVG(s.active_member), 2)         AS active_rate_start_pct,
       ROUND(100.0 * AVG(e.active_member), 2)         AS active_rate_end_pct,
       ROUND(100.0 * AVG((s.balance = 0)::INT), 2)    AS zero_balance_start_pct,
       ROUND(100.0 * AVG((e.balance = 0)::INT), 2)    AS zero_balance_end_pct,
       ROUND(100.0 * AVG((e.balance < s.balance)::INT), 2) AS pct_customers_balance_decreased
FROM dim_observation_window w
JOIN fact_customer_quarterly s ON s.quarter_label = w.starting_quarter
JOIN fact_customer_quarterly e ON e.customer_id = s.customer_id AND e.quarter_label = w.ending_quarter
GROUP BY w.window_id, w.window_name ORDER BY w.window_id;

-- 12b. Label transitions between windows (how many customers changed tag?)
SELECT a.unpaid_tagging AS tag_in_all, v.unpaid_tagging AS tag_in_validasi, COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM fact_unpaid_tagging a
JOIN fact_unpaid_tagging v ON v.customer_id = a.customer_id AND v.window_id = 2
WHERE a.window_id = 1
GROUP BY 1, 2 ORDER BY 1, 2;

-- 13. Extra: tagging by credit-card status at the start of each window -----------
-- Customers without a card at the window start are a special group (see EDA findings); meaning unconfirmed.
SELECT w.window_name,
       CASE WHEN s.has_credit_card = 1 THEN 'Card at window start' ELSE 'No card at window start' END AS card_status,
       COUNT(*) AS customers, SUM(t.unpaid_tagging) AS tagged,
       ROUND(100.0 * AVG(t.unpaid_tagging), 2) AS tagging_rate_pct
FROM dim_observation_window w
JOIN fact_customer_quarterly s ON s.quarter_label = w.starting_quarter
JOIN fact_unpaid_tagging t ON t.customer_id = s.customer_id AND t.window_id = w.window_id
GROUP BY w.window_id, w.window_name, s.has_credit_card
ORDER BY w.window_id, s.has_credit_card;
