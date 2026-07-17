# Temaje Zakaria — Data Analyst Portfolio

![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Excel](https://img.shields.io/badge/Microsoft_Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)

Hi, I'm Temaje — a Humber College grad (Business Management, 2022) with a 2025
Business Analytics Certificate, looking to break into a Data Analyst role.

---

# NorthStar Retail Group — Retail Analytics Project

**Business problem:** Leadership had no single source of truth on whether the
business was growing sustainably — revenue could be rising while margin quietly
erodes, or growth could be masking a retention problem. This project builds the
analysis to answer that with evidence.

<img width="931" height="877" alt="dashboard_preview" src="https://github.com/user-attachments/assets/eed105d0-b6a9-4355-9ffa-8aea6bed7ba3" />

## KPIs

| Revenue | Gross Margin | YoY Growth | Active Customers |
|---|---|---|---|
| **$31.1M** | **42.7%** | **+11.5%** | **5,911** |

## Key Business Insights

1. **Geographic concentration risk** — the top 2 of 5 regions (West, Southwest) drive 41.8% of total revenue.
2. **Category concentration risk** — Electronics alone accounts for 51.4% of revenue.
3. **Retention cliff** — ~90% of new customers don't return after their first purchase, but the ~10% who do stabilize through month 6.
4. **Customer value is skewed** — the top customer decile is worth 3.4x the median customer ($14,696 vs. $4,341).
5. **Growth is durable** — consistent ~12% YoY revenue growth for 3 consecutive years, not a one-time spike.

## Strategic Recommendations

1. Launch a second-purchase incentive targeting the month-1 retention cliff.
2. Build category-specific contingency planning for Electronics given its 51.4% revenue share.
3. Shift fulfillment staffing to match the Friday/Saturday demand peak (+30% vs. midweek).

## Financial Impact Summary

A conservative, data-grounded scenario for Recommendation #1:

| Assumption | Value |
|---|---|
| New customers per month (avg.) | 164 |
| Target month-1 retention lift | +5 percentage points |
| Additional repeat customers (3 years) | 296 |
| Average order value | $1,231 |
| **Estimated incremental revenue** | **$363,700** |
| **Estimated incremental profit (42.7% margin)** | **$155,300** |

*Estimate based on this project's actual transaction data; a real implementation would validate the retention lift with an A/B test before scaling.*

---

## Dataset

- Synthetically generated using Python (pandas, NumPy) to simulate 3 years of realistic retail transactions, complete with seasonality and intentional data-quality issues to clean
- Stored and queried via a SQLite database using a star-schema design (3 dimension tables + 2 fact tables)
- No real company or customer data involved — PII-free by design

## Features

- **Full analytics pipeline** — SQL star-schema database, Python cleaning/EDA, Excel KPI workbook, and Power BI dashboard design in one cohesive project
- **Advanced SQL** — RFM customer segmentation, cohort retention analysis, Pareto analysis, YoY trend comparisons using window functions
- **Data cleaning & validation** — documented handling of duplicates, missing values, and outliers on realistic messy transaction data
- **Interactive-style Excel workbook** — pivot-style summaries, conditional formatting, VLOOKUP/INDEX-MATCH lookups
- **Executive-ready dashboards** — 4-page Power BI design covering executive, sales, customer, and operations views

✉️ [temajezakaria@gmail.com](mailto:temajezakaria@gmail.com)

---

© 2026 Temaje Zakaria. All rights reserved.
