# NorthStar Retail Group — Power BI Executive Dashboard Design

This document specifies four dashboard pages built on top of `cleaned_transactions.csv`,
`customer_rfm_features.csv`, and the star-schema tables. It is written as a real BI design
spec would be — visual by visual, with the business decision each one supports — so it can
be handed to a BI developer (or rebuilt directly in Power BI Desktop) without ambiguity.

**Data model in Power BI:** Import `dim_customers`, `dim_products`, `dim_stores`,
`fact_orders`, `fact_order_items` as a star schema; add a standalone `dim_date` table
marked as a Date Table for time-intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`,
`DATEADD`). Relationships: one-to-many from each dimension to its fact table, single
direction filtering, `fact_orders` (1) → `fact_order_items` (many).

**Core DAX measures used across pages:**
```dax
Total Revenue         = SUM(fact_order_items[line_total])
Total Profit          = SUMX(fact_order_items, fact_order_items[line_total] - fact_order_items[line_cost])
Gross Margin %        = DIVIDE([Total Profit], [Total Revenue])
Revenue YoY %         = DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])
Revenue LY            = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[Date]))
Active Customers      = DISTINCTCOUNT(fact_orders[customer_id])
Avg Order Value       = DIVIDE([Total Revenue], DISTINCTCOUNT(fact_orders[order_id]))
Repeat Purchase Rate  = DIVIDE([Customers with 2+ Orders], [Active Customers])
```

---

## Page 1 — Executive Summary

**Purpose:** The single page a CEO/CFO looks at before any 1:1 meeting. Must answer
"how is the business doing" in under 15 seconds.

| Visual | Type | Why This Visual | Business Decision Supported |
|---|---|---|---|
| Revenue, Profit, Growth Rate, Customer Count | 4 KPI Cards with YoY sparkline | Cards are scannable in under a second; sparkline gives trend context without a full chart | Go/no-go signal for whether deeper investigation is needed this week |
| Monthly Revenue & Profit Trend | Combo chart (bar = revenue, line = margin %) | Combining an absolute measure with a ratio on one chart avoids misleading "revenue is up" when margin is quietly eroding | Whether growth is healthy or margin-diluting |
| YoY Growth by Month | Line chart, 3 series (2023/2024/2025 overlaid by month) | Overlaying years on a shared month-axis is the fastest way to see if growth is seasonal or structural | Whether current growth is likely to persist into next quarter |
| Revenue by Region | Filled map or bar chart | Map view builds executive intuition about geographic concentration instantly | Where to prioritize regional marketing/ops investment |
| Top 5 Products This Month | Table with conditional-formatting data bars | Executives want the "so what" specifics, not just aggregate trend | Immediate merchandising/promotion follow-up |
| **Slicers** | Date range, Region, Store Type | Every exec asks "what about just this region/quarter" live in the meeting | Enables real-time drill-down without rebuilding the page |

---

## Page 2 — Sales Dashboard

**Purpose:** Working page for Sales/Merchandising leadership to manage category and
regional performance week to week.

| Visual | Type | Why This Visual | Business Decision Supported |
|---|---|---|---|
| Sales Trend (Daily/Weekly toggle) | Line chart with 7-day moving average overlay | Raw daily sales are noisy; showing both raw and smoothed line lets the analyst distinguish real trend shifts from daily noise | Whether a dip is a blip or the start of a real decline |
| Product Performance | Matrix/table: Category → Product, with Revenue, Units, Margin %, RANKX-based rank column | A drillable matrix mirrors how merchandising actually reviews performance (category first, then SKU) | SKU rationalization, reorder, and discontinue decisions |
| Category Revenue Share | 100% stacked bar by month | Shows whether category mix is shifting over time, not just totals | Category-level marketing budget reallocation |
| Regional Performance | Bar chart ranked descending + cumulative % line (Pareto) | Directly mirrors SQL Query 5 — shows revenue concentration risk at a glance | Store investment / expansion / closure prioritization |
| Discount Impact | Scatter plot: discount tier (x) vs. margin % (y), bubble size = revenue | Visualizes the margin-erosion tradeoff from SQL Query 6 far more intuitively than a table | Setting promotional discount guardrails by category |
| **Slicers** | Category, Brand, Store, Payment Method | Lets category managers self-serve without ad hoc analyst requests | Reduces analyst request backlog |

---

## Page 3 — Customer Dashboard

**Purpose:** CRM/Retention leadership's page for understanding who the customers
are, how loyal they are, and how much they're worth.

| Visual | Type | Why This Visual | Business Decision Supported |
|---|---|---|---|
| Customer Segmentation (RFM) | Treemap: segment size = customer count, color = avg monetary value | Treemap communicates both "how many" and "how valuable" in one glance — better than a pie chart for 5+ categories | Which segment to target with which campaign (win-back vs. VIP) |
| Customer Retention (Cohort Grid) | Matrix heat-map: cohort month (rows) × months-since-first-purchase (columns), color-scaled % retained | This is the direct visual translation of SQL Query 4 — heat-map color makes the retention cliff instantly visible | Whether onboarding/retention initiatives are working, cohort over cohort |
| Customer Lifetime Value by Acquisition Channel | Bar chart, sorted descending, with a secondary line for customer count | Directly operationalizes SQL Query 10 for marketing spend decisions | Reallocating acquisition budget toward higher-LTV channels |
| New vs. Returning Revenue Split | Stacked area chart over time | Immediately shows if growth is acquisition-driven or retention-driven, per SQL Query 7 | Budget balance between acquisition and retention marketing |
| Top 20 Customers | Table with drill-through to customer order history | Account-level visibility for B2B/VIP account management | Personalized retention outreach for highest-value accounts |
| **Slicers** | Region, Acquisition Channel, Loyalty Member (Y/N) | Segments the entire page instantly for different stakeholder questions | Self-service segment-specific reporting |

---

## Page 4 — Operations Dashboard

**Purpose:** Ops/Fulfillment leadership's page for monitoring process health,
not just sales outcomes.

| Visual | Type | Why This Visual | Business Decision Supported |
|---|---|---|---|
| Order Volume by Day of Week | Column chart | Directly powers staffing schedule decisions (SQL Query 11) | Weekly labor/staffing allocation across stores and fulfillment centers |
| Cancellation / Refund Rate by Payment Method | Bar chart with a target reference line | Makes it obvious which payment rail needs fraud/ops review, per SQL Query 8 | Renegotiating payment provider terms or adding checkout friction/fraud checks |
| Fulfillment Cost (Shipping Cost) Trend | Line chart by month, split Online vs Physical | Rising shipping cost as % of revenue is an early warning for margin compression | Carrier renegotiation or shipping-fee policy changes |
| Store-Level Efficiency (Revenue per Sq Ft) | Bar chart ranked, physical stores only | Standard retail-industry efficiency metric normalizing for store size | Real estate decisions: which stores to renovate, downsize, or close |
| Order Status Breakdown | Donut chart (Completed / Cancelled / Refunded) with KPI card for total problem rate | Quick health check; donut is acceptable here since only 3 categories | Overall operational health flag for the ops leadership standup |
| **Slicers** | Store, Region, Month | Lets regional ops managers filter to their own footprint | Localized accountability and performance reviews |

---

## Design Principles Applied Throughout

- **Consistent color encoding:** Navy = revenue, Teal = profit/margin, Orange = risk/attention
  metrics — reused identically across all 4 pages so users build pattern recognition.
- **Every page answers one core stakeholder question** rather than cramming every possible
  metric onto one page — a very common mistake that makes dashboards unusable in practice.
- **Cards + trend + drill-down, in that order,** on every page: executives scan top-down,
  so the highest-level number is always top-left.
- **No 3D charts, no unnecessary pie charts with 6+ slices** — both are known to distort
  perception of magnitude and would be flagged in any professional design review.
