-- =============================================================================
-- NorthStar Retail Group — Advanced SQL Analysis Suite
-- 12 production-style queries covering: joins, CTEs, window functions,
-- CASE logic, aggregates, ranking, subqueries, date analysis, segmentation,
-- and trend analysis. Tested and verified against northstar_retail.db (SQLite).
-- =============================================================================


-- =============================================================================
-- QUERY 1: MONTHLY REVENUE, PROFIT & YEAR-OVER-YEAR GROWTH
-- Techniques: CTE, JOIN, aggregate functions, window function (LAG), date analysis
-- =============================================================================
-- WHY THIS QUERY:
--   Every executive dashboard starts with "how is revenue trending?" This query
--   builds the monthly time series once (in the CTE) then reuses LAG() to compare
--   each month to the same month one year prior — the standard way finance teams
--   measure growth without seasonal noise distorting month-over-month comparisons.
-- BUSINESS VALUE:
--   Finance/Exec teams use this exact output to build the board deck revenue
--   slide and to flag whether the business is decelerating before it shows up
--   in quarterly results.
-- HOW A HIRING MANAGER READS THIS:
--   Seeing LAG() used correctly (partitioned/ordered, self-referencing 12 months
--   back) signals the candidate understands YoY vs. MoM analysis — a very common
--   interview trap where junior analysts confuse the two.
-- =============================================================================
WITH monthly_revenue AS (
    SELECT
        strftime('%Y', o.order_date)              AS order_year,
        strftime('%m', o.order_date)               AS order_month,
        strftime('%Y-%m', o.order_date)             AS year_month,
        SUM(oi.line_total)                          AS revenue,
        SUM(oi.line_total - oi.line_cost)            AS gross_profit,
        COUNT(DISTINCT o.order_id)                   AS order_count
    FROM fact_orders o
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY 1, 2, 3
)
SELECT
    year_month,
    revenue,
    gross_profit,
    ROUND(gross_profit / revenue * 100, 1)                       AS gross_margin_pct,
    order_count,
    LAG(revenue, 12) OVER (ORDER BY year_month)                   AS revenue_same_month_last_year,
    ROUND(
        (revenue - LAG(revenue, 12) OVER (ORDER BY year_month))
        / NULLIF(LAG(revenue, 12) OVER (ORDER BY year_month), 0) * 100, 1
    )                                                              AS yoy_growth_pct
FROM monthly_revenue
ORDER BY year_month;


-- =============================================================================
-- QUERY 2: RFM CUSTOMER SEGMENTATION (Recency, Frequency, Monetary)
-- Techniques: CTE, window functions (NTILE), CASE, aggregate, subquery
-- =============================================================================
-- WHY THIS QUERY:
--   RFM is the industry-standard framework for turning raw transactions into
--   actionable customer segments without needing a machine-learning model.
--   NTILE(4) splits customers into quartiles for each dimension independently,
--   which is more robust to skew than fixed dollar-amount thresholds.
-- BUSINESS VALUE:
--   Marketing uses "Champions" for VIP loyalty offers, "At Risk" for win-back
--   email campaigns, and "Lost" to stop spending acquisition budget on churned
--   customers. This single query can drive a targeted CRM campaign.
-- HOW A HIRING MANAGER READS THIS:
--   RFM segmentation is one of the most frequently requested case-study asks
--   in Analyst interviews. Producing it cleanly with NTILE (vs. manual bucket
--   CASE statements on raw values) shows SQL fluency beyond basic aggregation.
-- =============================================================================
WITH customer_orders AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)                    AS last_order_date,
        COUNT(DISTINCT o.order_id)            AS frequency,
        SUM(oi.line_total)                    AS monetary
    FROM fact_orders o
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER) AS recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY julianday(last_order_date) DESC) AS recency_score,   -- 4 = most recent
        NTILE(4) OVER (ORDER BY frequency ASC)                    AS frequency_score,
        NTILE(4) OVER (ORDER BY monetary ASC)                     AS monetary_score
    FROM customer_orders
)
SELECT
    customer_id,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary,
    recency_score, frequency_score, monetary_score,
    CASE
        WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score <= 2                        THEN 'New / Promising'
        WHEN recency_score <= 2 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'At Risk (High Value)'
        WHEN recency_score <= 2 AND frequency_score <= 2                        THEN 'Lost / Dormant'
        ELSE 'Needs Attention'
    END AS customer_segment
FROM rfm_scores
ORDER BY monetary DESC
LIMIT 25;


-- =============================================================================
-- QUERY 3: TOP 3 PRODUCTS BY REVENUE WITHIN EACH CATEGORY
-- Techniques: window function (RANK/DENSE_RANK), subquery, JOIN, aggregate
-- =============================================================================
-- WHY THIS QUERY:
--   A flat "top 10 products" list is dominated by one or two mega-categories.
--   Ranking WITHIN category (PARTITION BY category) gives every category
--   manager visibility into their own top performers — a much more common
--   real-world ask from category/merchandising teams.
-- BUSINESS VALUE:
--   Merchandising uses this to decide which SKUs get featured placement and
--   marketing spend, and which underperforming products in each category
--   should be discontinued or discounted.
-- HOW A HIRING MANAGER READS THIS:
--   Filtering ranked window function output requires wrapping it in a subquery
--   (you can't filter on a window function in the same-level WHERE clause).
--   Getting this right without a wasted extra JOIN demonstrates real SQL
--   experience, not just memorized syntax.
-- =============================================================================
SELECT * FROM (
    SELECT
        p.category,
        p.product_name,
        SUM(oi.line_total)                                                       AS total_revenue,
        SUM(oi.quantity)                                                          AS units_sold,
        RANK() OVER (PARTITION BY p.category ORDER BY SUM(oi.line_total) DESC)    AS revenue_rank_in_category
    FROM fact_order_items oi
    JOIN dim_products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_name
) ranked
WHERE revenue_rank_in_category <= 3
ORDER BY category, revenue_rank_in_category;


-- =============================================================================
-- QUERY 4: MONTHLY CUSTOMER COHORT RETENTION
-- Techniques: CTE, self-join logic via date math, aggregate, date analysis
-- =============================================================================
-- WHY THIS QUERY:
--   Cohort analysis (grouping customers by their signup/first-purchase month
--   and tracking what % are still buying N months later) is the gold-standard
--   way to measure whether retention is structurally improving or declining,
--   independent of new-customer acquisition growth masking a churn problem.
-- BUSINESS VALUE:
--   Retention/CRM leadership uses this to evaluate whether loyalty program
--   changes or onboarding email sequences actually improved repeat purchase
--   behavior for customers who joined after the change.
-- HOW A HIRING MANAGER READS THIS:
--   Cohort tables are notoriously easy to get wrong (off-by-one month errors,
--   double counting). A clean, correct implementation signals strong date-math
--   skills, which is one of the most common SQL interview failure points.
-- =============================================================================
WITH first_purchase AS (
    SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM fact_orders
    WHERE order_status = 'Completed'
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        o.customer_id,
        fp.cohort_month,
        strftime('%Y-%m', o.order_date) AS order_month,
        (CAST(strftime('%Y', o.order_date) AS INTEGER) - CAST(SUBSTR(fp.cohort_month,1,4) AS INTEGER)) * 12
          + (CAST(strftime('%m', o.order_date) AS INTEGER) - CAST(SUBSTR(fp.cohort_month,6,2) AS INTEGER)) AS months_since_first_purchase
    FROM fact_orders o
    JOIN first_purchase fp ON fp.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
)
SELECT
    cohort_month,
    months_since_first_purchase,
    COUNT(DISTINCT customer_id) AS active_customers
FROM orders_with_cohort
WHERE months_since_first_purchase BETWEEN 0 AND 6
GROUP BY cohort_month, months_since_first_purchase
ORDER BY cohort_month, months_since_first_purchase;


-- =============================================================================
-- QUERY 5: REGIONAL PERFORMANCE RANKING WITH RUNNING TOTAL SHARE OF REVENUE
-- Techniques: window functions (SUM OVER, RANK), JOIN, aggregate
-- =============================================================================
-- WHY THIS QUERY:
--   Ranking regions AND showing what cumulative % of total revenue they
--   represent (Pareto-style) tells leadership in one glance whether the
--   business is dangerously concentrated in 1-2 regions.
-- BUSINESS VALUE:
--   Used directly in regional expansion / store-closure decisions — if the
--   bottom 3 regions represent <8% of revenue, that's a real estate
--   rationalization conversation.
-- HOW A HIRING MANAGER READS THIS:
--   Combining RANK() with a running SUM() OVER (ORDER BY ... ROWS UNBOUNDED
--   PRECEDING) in a single pass (no self-join) is a noticeably more advanced,
--   efficient pattern than what most candidates default to.
-- =============================================================================
WITH region_revenue AS (
    SELECT
        c.region,
        SUM(oi.line_total) AS revenue
    FROM fact_orders o
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    JOIN dim_customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.region
)
SELECT
    region,
    revenue,
    RANK() OVER (ORDER BY revenue DESC) AS region_rank,
    ROUND(SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
          / SUM(revenue) OVER () * 100, 1) AS cumulative_pct_of_total_revenue
FROM region_revenue
ORDER BY revenue DESC;


-- =============================================================================
-- QUERY 6: DISCOUNT DEPTH VS. MARGIN IMPACT BY CATEGORY
-- Techniques: CASE statement, aggregate, JOIN, subquery
-- =============================================================================
-- WHY THIS QUERY:
--   Buckets orders into discount tiers using CASE, then measures gross margin
--   for each tier. This directly answers "are our promotions eroding margin
--   faster than they're driving incremental volume?"
-- BUSINESS VALUE:
--   Pricing/Promotions team uses this to set discount guardrails (e.g., cap
--   promo depth at 15% for categories where margin falls off a cliff beyond
--   that threshold).
-- HOW A HIRING MANAGER READS THIS:
--   Business-aware CASE bucketing (not arbitrary bins, but bins tied to actual
--   promo tiers the business runs) shows the candidate thinks about the
--   business problem first, SQL syntax second.
-- =============================================================================
SELECT
    p.category,
    CASE
        WHEN o.discount_amount = 0                          THEN 'No Discount'
        WHEN o.discount_amount BETWEEN 0.01 AND 9.99         THEN 'Low (< $10)'
        WHEN o.discount_amount BETWEEN 10 AND 19.99          THEN 'Medium ($10-$20)'
        ELSE 'High (>$20)'
    END AS discount_tier,
    COUNT(DISTINCT o.order_id)                                        AS orders,
    ROUND(SUM(oi.line_total), 2)                                      AS revenue,
    ROUND(SUM(oi.line_total - oi.line_cost) / NULLIF(SUM(oi.line_total),0) * 100, 1) AS gross_margin_pct
FROM fact_orders o
JOIN fact_order_items oi ON oi.order_id = o.order_id
JOIN dim_products p ON p.product_id = oi.product_id
WHERE o.order_status = 'Completed' AND o.discount_amount >= 0
GROUP BY p.category, discount_tier
ORDER BY p.category,
    CASE discount_tier WHEN 'No Discount' THEN 1 WHEN 'Low (< $10)' THEN 2 WHEN 'Medium ($10-$20)' THEN 3 ELSE 4 END;


-- =============================================================================
-- QUERY 7: NEW VS. RETURNING CUSTOMER REVENUE SPLIT BY MONTH
-- Techniques: CASE, subquery (correlated), CTE, date analysis
-- =============================================================================
-- WHY THIS QUERY:
--   Total revenue growth can hide a serious problem: if 100% of growth comes
--   from new customers while returning-customer revenue shrinks, the business
--   has a leaky-bucket retention problem masked by acquisition spend.
-- BUSINESS VALUE:
--   CFO/CMO use this split to decide budget allocation between acquisition
--   marketing and retention/loyalty investment.
-- HOW A HIRING MANAGER READS THIS:
--   Using a correlated subquery to determine "is this the customer's first
--   order month" without a full self-join shows comfort with subquery
--   performance tradeoffs.
-- =============================================================================
WITH order_customer_month AS (
    SELECT
        o.order_id,
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month,
        (SELECT MIN(strftime('%Y-%m', o2.order_date))
         FROM fact_orders o2
         WHERE o2.customer_id = o.customer_id AND o2.order_status = 'Completed') AS first_order_month
    FROM fact_orders o
    WHERE o.order_status = 'Completed'
)
SELECT
    ocm.order_month,
    CASE WHEN ocm.order_month = ocm.first_order_month THEN 'New Customer' ELSE 'Returning Customer' END AS customer_type,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    COUNT(DISTINCT ocm.customer_id) AS customers
FROM order_customer_month ocm
JOIN fact_order_items oi ON oi.order_id = ocm.order_id
GROUP BY ocm.order_month, customer_type
ORDER BY ocm.order_month, customer_type;


-- =============================================================================
-- QUERY 8: ORDER CANCELLATION / REFUND RATE BY PAYMENT METHOD
-- Techniques: aggregate, CASE, JOIN
-- =============================================================================
-- WHY THIS QUERY:
--   Simple but high-value: measures operational failure rate segmented by
--   a controllable business lever (payment method offered at checkout).
-- BUSINESS VALUE:
--   If "Buy Now Pay Later" shows a materially higher cancellation rate,
--   Operations/Finance may renegotiate terms with that BNPL provider or
--   add fraud screening specifically on that payment rail.
-- HOW A HIRING MANAGER READS THIS:
--   Simple aggregate + CASE queries like this are exactly what gets asked
--   in take-home SQL screens — clean, readable, correct GROUP BY logic
--   matters more here than cleverness.
-- =============================================================================
SELECT
    payment_method,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN order_status = 'Refunded' THEN 1 ELSE 0 END)  AS refunded_orders,
    ROUND(SUM(CASE WHEN order_status IN ('Cancelled','Refunded') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS problem_rate_pct
FROM fact_orders
GROUP BY payment_method
ORDER BY problem_rate_pct DESC;


-- =============================================================================
-- QUERY 9: PRODUCT PARETO ANALYSIS (80/20 RULE)
-- Techniques: window function (cumulative SUM), CTE, ranking
-- =============================================================================
-- WHY THIS QUERY:
--   Tests whether ~20% of SKUs generate ~80% of revenue — the classic Pareto
--   check every retail merchandising team runs before an inventory rationalization
--   project.
-- BUSINESS VALUE:
--   Directly informs SKU-reduction and warehouse-space allocation decisions:
--   if the tail 60% of products contribute <5% of revenue, that's a strong
--   case to discontinue slow movers and free up capital.
-- HOW A HIRING MANAGER READS THIS:
--   A cumulative-percentage window function computed correctly (ordered
--   descending, dividing by the grand total via a second window) is a
--   frequently-flubbed technique — nailing it stands out.
-- =============================================================================
WITH product_revenue AS (
    SELECT p.product_id, p.product_name, SUM(oi.line_total) AS revenue
    FROM fact_order_items oi
    JOIN dim_products p ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name
)
SELECT
    product_name,
    revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC) AS product_rank,
    ROUND(SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING) / SUM(revenue) OVER () * 100, 1) AS cumulative_pct
FROM product_revenue
ORDER BY revenue DESC
LIMIT 50;


-- =============================================================================
-- QUERY 10: CUSTOMER LIFETIME VALUE (CLV) ESTIMATE BY ACQUISITION CHANNEL
-- Techniques: CTE, JOIN, aggregate, ranking
-- =============================================================================
-- WHY THIS QUERY:
--   A simple historical CLV proxy (avg revenue per customer, by channel) tells
--   marketing which acquisition channels bring in higher-value customers, not
--   just cheaper ones.
-- BUSINESS VALUE:
--   If Paid Social has the lowest cost-per-acquisition but also the lowest
--   CLV, that channel may actually be destroying value once blended with
--   ad spend — a classic marketing-attribution correction.
-- HOW A HIRING MANAGER READS THIS:
--   Connecting a marketing dimension (acquisition_channel) to a financial
--   outcome (CLV) demonstrates the candidate thinks cross-functionally,
--   not just "run the aggregation."
-- =============================================================================
WITH customer_value AS (
    SELECT
        c.customer_id,
        c.acquisition_channel,
        SUM(oi.line_total) AS lifetime_revenue,
        COUNT(DISTINCT o.order_id) AS lifetime_orders
    FROM dim_customers c
    JOIN fact_orders o ON o.customer_id = c.customer_id AND o.order_status = 'Completed'
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.acquisition_channel
)
SELECT
    acquisition_channel,
    COUNT(customer_id)                       AS customers,
    ROUND(AVG(lifetime_revenue), 2)          AS avg_customer_lifetime_value,
    ROUND(AVG(lifetime_orders), 2)           AS avg_orders_per_customer,
    RANK() OVER (ORDER BY AVG(lifetime_revenue) DESC) AS clv_rank
FROM customer_value
GROUP BY acquisition_channel
ORDER BY avg_customer_lifetime_value DESC;


-- =============================================================================
-- QUERY 11: DAY-OF-WEEK SEASONALITY / DEMAND PATTERN
-- Techniques: date analysis, aggregate, CASE, window function (AVG)
-- =============================================================================
-- WHY THIS QUERY:
--   Retail demand is highly cyclical by day of week. This surfaces which
--   days need heavier staffing (physical stores) and server/fulfillment
--   capacity (online).
-- BUSINESS VALUE:
--   Operations uses this to build weekly staffing schedules and warehouse
--   labor plans that match actual demand instead of flat staffing.
-- HOW A HIRING MANAGER READS THIS:
--   Translating a raw date into a business-meaningful CASE label (day name)
--   and immediately connecting it to a staffing/ops decision (not just
--   "here's a chart") shows business acumen expected of an Ops Analyst.
-- =============================================================================
SELECT
    CASE CAST(strftime('%w', order_date) AS INTEGER)
        WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        ELSE 'Saturday'
    END AS day_of_week,
    COUNT(*) AS total_orders,
    ROUND(AVG(COUNT(*)) OVER (), 0) AS avg_orders_per_day_overall,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_weekly_volume
FROM fact_orders
WHERE order_status = 'Completed'
GROUP BY strftime('%w', order_date)
ORDER BY total_orders DESC;


-- =============================================================================
-- QUERY 12: 7-DAY MOVING AVERAGE REVENUE TREND (SMOOTHING NOISE FOR TREND DETECTION)
-- Techniques: window function (AVG OVER ROWS BETWEEN), date analysis, CTE
-- =============================================================================
-- WHY THIS QUERY:
--   Daily revenue is noisy: a 7-day trailing moving average is the standard
--   technique to reveal the underlying trend line an executive dashboard
--   should chart, without needing an external BI tool to compute it.
-- BUSINESS VALUE:
--   Powers the "Revenue Trend" line chart on the Executive Summary dashboard
--   page — smoothed trend lines are what leadership actually watches week
--   to week, not jagged daily totals.
-- HOW A HIRING MANAGER READS THIS:
--   ROWS BETWEEN 6 PRECEDING AND CURRENT ROW is precise, correct trailing-
--   window syntax — a detail that separates candidates who've truly used
--   window functions in production from those who've only seen tutorials.
-- =============================================================================
WITH daily_revenue AS (
    SELECT o.order_date, SUM(oi.line_total) AS revenue
    FROM fact_orders o
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY o.order_date
)
SELECT
    order_date,
    revenue,
    ROUND(AVG(revenue) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS moving_avg_7day
FROM daily_revenue
ORDER BY order_date;
