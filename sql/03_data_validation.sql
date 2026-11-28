-- =====================================================================
-- 03_data_validation.sql : post-load checks. Every row should say PASS.
--   psql -h localhost -U postgres -d finanku -f sql/03_data_validation.sql
-- Expected values come from the Phase 1 audit of the supplied files.
-- =====================================================================
\set ON_ERROR_STOP on

WITH checks AS (
    SELECT 1 AS ord, 'customers loaded' AS check_name, 7561::BIGINT AS expected,
           (SELECT COUNT(*) FROM dim_customer) AS actual
    UNION ALL SELECT 2, 'branches', 18, (SELECT COUNT(*) FROM dim_branch)
    UNION ALL SELECT 3, 'observation windows', 2, (SELECT COUNT(*) FROM dim_observation_window)
    UNION ALL SELECT 4, 'customer-quarter rows (7,561 x 5 quarters)', 37805, (SELECT COUNT(*) FROM fact_customer_quarterly)
    UNION ALL SELECT 5, 'tagging rows (7,561 x 2 windows)', 15122, (SELECT COUNT(*) FROM fact_unpaid_tagging)
    UNION ALL SELECT 6, 'customers with exactly 5 quarters', 7561,
           (SELECT COUNT(*) FROM (SELECT customer_id FROM fact_customer_quarterly GROUP BY customer_id HAVING COUNT(*) = 5) x)
    UNION ALL SELECT 7, 'customers with exactly 2 tagging rows', 7561,
           (SELECT COUNT(*) FROM (SELECT customer_id FROM fact_unpaid_tagging GROUP BY customer_id HAVING COUNT(*) = 2) x)
    UNION ALL SELECT 8, 'tagged, Data All', 2019,
           (SELECT SUM(unpaid_tagging) FROM fact_unpaid_tagging WHERE window_id = 1)
    UNION ALL SELECT 9, 'tagged, Data Validasi', 2709,
           (SELECT SUM(unpaid_tagging) FROM fact_unpaid_tagging WHERE window_id = 2)
    UNION ALL SELECT 10, 'customers whose label differs between windows', 2042,
           (SELECT COUNT(*) FROM fact_unpaid_tagging a JOIN fact_unpaid_tagging v
              ON a.customer_id = v.customer_id AND a.window_id = 1 AND v.window_id = 2
             WHERE a.unpaid_tagging <> v.unpaid_tagging)
    UNION ALL SELECT 11, 'zero-income customers', 251,
           (SELECT COUNT(*) FROM dim_customer WHERE income_measure = 0)
    UNION ALL SELECT 12, 'customers without card in Q3 (all have card in Q4)', 611,
           (SELECT COUNT(*) FROM fact_customer_quarterly WHERE quarter_label = 'Q3' AND has_credit_card = 0)
    UNION ALL SELECT 13, 'distinct has_credit_card values in Q4 and Q5 (constant = 1)', 1,
           (SELECT COUNT(DISTINCT has_credit_card) FROM fact_customer_quarterly WHERE quarter_label IN ('Q4','Q5'))
    UNION ALL SELECT 14, 'orphan quarterly rows (no customer)', 0,
           (SELECT COUNT(*) FROM fact_customer_quarterly f LEFT JOIN dim_customer c USING (customer_id) WHERE c.customer_id IS NULL)
    UNION ALL SELECT 15, 'orphan tagging rows (no customer or window)', 0,
           (SELECT COUNT(*) FROM fact_unpaid_tagging t
              LEFT JOIN dim_customer c USING (customer_id)
              LEFT JOIN dim_observation_window w USING (window_id)
             WHERE c.customer_id IS NULL OR w.window_id IS NULL)
    UNION ALL SELECT 16, 'Q4 balance total equals staging (Data All)', 1,
           ((SELECT SUM(balance) FROM fact_customer_quarterly WHERE quarter_label = 'Q4')
             = (SELECT SUM(balance_q4) FROM stg_data_all))::INT
    UNION ALL SELECT 17, 'Q5 balance total equals staging (Data Validasi)', 1,
           ((SELECT SUM(balance) FROM fact_customer_quarterly WHERE quarter_label = 'Q5')
             = (SELECT SUM(balance_q5) FROM stg_data_validasi))::INT
    UNION ALL SELECT 18, 'branches mapped to more than one city', 0,
           (SELECT COUNT(*) FROM (SELECT branch_code FROM stg_data_all GROUP BY branch_code HAVING COUNT(DISTINCT city) > 1) x)
)
SELECT ord, check_name, expected, actual,
       CASE WHEN expected = actual THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks ORDER BY ord;

-- Informational: product counts never decrease between consecutive quarters
SELECT 'product decreases between consecutive quarters' AS info, COUNT(*) AS cases
FROM (
    SELECT customer_id, quarter_label,
           num_products - LAG(num_products) OVER (PARTITION BY customer_id ORDER BY quarter_label) AS d
    FROM fact_customer_quarterly
) x WHERE d < 0;

-- Informational: value ranges
SELECT quarter_label, MIN(num_products) AS min_products, MAX(num_products) AS max_products,
       MIN(balance) AS min_balance, MAX(balance) AS max_balance
FROM fact_customer_quarterly GROUP BY quarter_label ORDER BY quarter_label;
