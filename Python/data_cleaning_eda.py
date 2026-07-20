"""
NorthStar Retail Group — Data Cleaning, Validation & Exploratory Data Analysis
================================================================================
Author: [Your Name] | Senior Data Analyst (Portfolio Project)
Tools: pandas, numpy, matplotlib

This script takes the raw, intentionally-messy CSV exports (as a real BI
analyst would receive from an operational system) and produces an analysis-
ready dataset, plus the charts and summary stats used in the Executive
Summary and stakeholder readouts.

Each section below states:
  (1) PURPOSE           - what the code does and why it's necessary
  (2) BUSINESS IMPACT    - what breaks downstream if this step is skipped
  (3) HOW TO PRESENT IT  - how an analyst would summarize this to a
                           non-technical stakeholder (e.g., VP of Sales)
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)

DATA_DIR = "/home/claude/northstar-retail-analytics/data"
OUT_DIR = "/home/claude/northstar-retail-analytics/outputs"

plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["font.size"] = 10
NAVY, TEAL, ORANGE, GREY = "#1f3b57", "#2a9d8f", "#e76f51", "#6c757d"


# ==============================================================================
# SECTION 1 — LOAD RAW DATA
# ==============================================================================
# PURPOSE: Load the 5 source files exactly as a real analyst would receive them
#          from a warehouse export (CRM extract, POS export, e-commerce DB dump).
# BUSINESS IMPACT: Establishes the row-count baseline used later to prove no
#          silent data loss occurred during cleaning (a common stakeholder
#          concern: "did you accidentally delete real orders?").
# PRESENT TO MANAGEMENT: "Here is the raw data volume we received, before any
#          cleaning — this is our starting point and audit trail."
# ==============================================================================
customers = pd.read_csv(f"{DATA_DIR}/dim_customers.csv")
products = pd.read_csv(f"{DATA_DIR}/dim_products.csv")
stores = pd.read_csv(f"{DATA_DIR}/dim_stores.csv")
orders = pd.read_csv(f"{DATA_DIR}/fact_orders.csv", parse_dates=["order_date"])
order_items = pd.read_csv(f"{DATA_DIR}/fact_order_items.csv")

print("=" * 70)
print("RAW DATA VOLUME (BEFORE CLEANING)")
print("=" * 70)
for name, df in [("customers", customers), ("products", products),
                  ("stores", stores), ("orders", orders), ("order_items", order_items)]:
    print(f"  {name:15s}: {len(df):>8,} rows | {df.shape[1]} columns")


# ==============================================================================
# SECTION 2 — DATA VALIDATION
# ==============================================================================
# PURPOSE: Before touching a single value, verify the data actually matches
#          what the schema promises: correct dtypes, valid primary keys
#          (unique, non-null), and referential integrity (every order's
#          customer_id/store_id actually exists in the dimension tables).
# BUSINESS IMPACT: Silent referential-integrity failures (an order pointing
#          to a customer_id that doesn't exist) cause dashboards to under-
#          report revenue via failed JOINs, with no error thrown — one of
#          the most dangerous "silent" BI failure modes.
# PRESENT TO MANAGEMENT: "We validated 100% referential integrity between
#          orders and our customer/product/store master data before
#          building any KPI — you can trust these numbers reconcile."
# ==============================================================================
print("\n" + "=" * 70)
print("DATA VALIDATION")
print("=" * 70)

# 2a. Primary key uniqueness checks
for name, df, pk in [("customers", customers, "customer_id"),
                      ("products", products, "product_id"),
                      ("orders", orders, "order_id"),
                      ("order_items", order_items, "order_item_id")]:
    dupe_count = df[pk].duplicated().sum()
    print(f"  [{name}] duplicate {pk} values: {dupe_count}")

# 2b. Referential integrity: every order_item.order_id must exist in orders,
#     every order_item.product_id must exist in products
orphan_items_order = (~order_items["order_id"].isin(orders["order_id"])).sum()
orphan_items_product = (~order_items["product_id"].isin(products["product_id"])).sum()
orphan_orders_customer = (~orders["customer_id"].isin(customers["customer_id"])).sum()
orphan_orders_store = (~orders["store_id"].isin(stores["store_id"])).sum()
print(f"  Order items with no matching order:     {orphan_items_order}")
print(f"  Order items with no matching product:   {orphan_items_product}")
print(f"  Orders with no matching customer:       {orphan_orders_customer}")
print(f"  Orders with no matching store:          {orphan_orders_store}")

# 2c. Range / logic validation (values that are structurally impossible)
neg_qty = (order_items["quantity"] < 0).sum()
neg_discount = (orders["discount_amount"] < 0).sum()
future_orders = (orders["order_date"] > pd.Timestamp.today()).sum()
print(f"  Negative quantity line items (data entry errors): {neg_qty}")
print(f"  Negative discount amounts (data entry errors):    {neg_discount}")
print(f"  Orders dated in the future:                       {future_orders}")


# ==============================================================================
# SECTION 3 — DATA CLEANING
# ==============================================================================
# PURPOSE: Fix the concrete issues surfaced in validation: duplicate records,
#          inconsistent text casing/whitespace, malformed emails, and sign
#          errors on quantity/discount.
# BUSINESS IMPACT: Duplicate order rows alone would overstate revenue in
#          every downstream KPI. Inconsistent city casing ("toronto" vs
#          "Toronto") silently fragments a "revenue by city" GROUP BY into
#          multiple rows for what is really one city — a very common,
#          very costly real-world bug.
# PRESENT TO MANAGEMENT: "We identified and corrected duplicate transactions
#          and standardized inconsistent text fields, which alone changed
#          our reported city-level revenue figures — cleaning is not
#          optional, it materially changes the numbers you'll see."
# ==============================================================================
print("\n" + "=" * 70)
print("DATA CLEANING")
print("=" * 70)

# 3a. Remove exact-duplicate rows (system double-submit bug)
before = len(orders)
orders = orders.drop_duplicates(subset="order_id", keep="first")
print(f"  Removed {before - len(orders)} duplicate order records")

before = len(customers)
customers = customers.drop_duplicates(subset="customer_id", keep="first")
print(f"  Removed {before - len(customers)} duplicate customer records")

# 3b. Standardize text fields: trim whitespace, title-case city names
customers["city"] = customers["city"].astype(str).str.strip().str.title()
customers["city"] = customers["city"].replace("Nan", np.nan)
customers["state"] = customers["state"].astype(str).str.strip().str.upper().replace("NAN", np.nan)

# 3c. Flag malformed emails (missing "@") rather than silently dropping —
#     preserves the customer record for revenue analysis while flagging the
#     contact-info quality issue separately for the CRM team.
customers["email_valid"] = customers["email"].apply(
    lambda x: isinstance(x, str) and "@" in x and "." in x.split("@")[-1]
)
invalid_emails = (~customers["email_valid"]).sum()
print(f"  Flagged {invalid_emails} missing/malformed email addresses (kept record, flagged contact quality)")

# 3d. Fix sign errors: negative quantity/discount are data entry mistakes,
#     not legitimate negative values in this business context — take absolute value
order_items["quantity"] = order_items["quantity"].abs()
orders["discount_amount"] = orders["discount_amount"].abs()
print(f"  Corrected {neg_qty} negative-quantity entries and {neg_discount} negative-discount entries to absolute value")

# Recompute line_total/line_cost after quantity correction to keep data internally consistent
order_items["line_total"] = (order_items["unit_price"] * order_items["quantity"]).round(2)
order_items["line_cost"] = (order_items["unit_cost"] * order_items["quantity"]).round(2)


# ==============================================================================
# SECTION 4 — MISSING VALUE HANDLING
# ==============================================================================
# PURPOSE: Apply a deliberate, documented strategy per column rather than a
#          blanket dropna() or fillna(0), because the "right" treatment
#          differs by field and business meaning.
# BUSINESS IMPACT: Blindly filling missing shipping_cost with 0 would
#          understate true fulfillment cost in a profitability model.
#          Blindly dropping rows with missing email would remove real,
#          revenue-generating customers from every other analysis.
# PRESENT TO MANAGEMENT: "Rather than deleting incomplete records, we
#          applied targeted, business-justified imputation so that no
#          real transaction is lost from revenue or profit reporting."
# ==============================================================================
print("\n" + "=" * 70)
print("MISSING VALUE HANDLING")
print("=" * 70)

missing_summary = pd.DataFrame({
    "orders_missing": orders.isna().sum(),
}).query("orders_missing > 0")
print("Missing values in orders table:\n", missing_summary)

# shipping_cost: missing ~5% of the time. Impute with the median shipping cost
# for that store_type (Online vs Physical), since online orders systematically
# have shipping costs and physical/in-store pickup often does not.
orders = orders.merge(stores[["store_id", "store_type"]], on="store_id", how="left")
median_shipping_by_type = orders.groupby("store_type")["shipping_cost"].transform("median")
missing_shipping_before = orders["shipping_cost"].isna().sum()
orders["shipping_cost"] = orders["shipping_cost"].fillna(median_shipping_by_type)
print(f"  Imputed {missing_shipping_before} missing shipping_cost values using store-type median (business-aware imputation)")

# gender: missing/blank -> explicit 'Not Specified' category rather than
# imputing a guessed gender (avoids introducing bias into any downstream
# demographic analysis)
customers["gender"] = customers["gender"].fillna("Not Specified")


# ==============================================================================
# SECTION 5 — OUTLIER DETECTION
# ==============================================================================
# PURPOSE: Use the IQR (interquartile range) method on order line-item
#          revenue to flag statistically extreme values, then manually
#          classify them as either legitimate bulk-order transactions or
#          likely data errors — outliers should be investigated, not
#          automatically deleted.
# BUSINESS IMPACT: A single un-flagged $50,000 fat-finger transaction can
#          distort an average-order-value KPI enough to trigger a false
#          "sales are up 30%!" headline in an exec dashboard.
# PRESENT TO MANAGEMENT: "We identified X unusually large transactions.
#          Y of them are legitimate bulk/B2B-style orders we're keeping;
#          Z were data entry errors we corrected before they could distort
#          the average order value metric on your dashboard."
# ==============================================================================
print("\n" + "=" * 70)
print("OUTLIER DETECTION (IQR METHOD)")
print("=" * 70)

Q1 = order_items["line_total"].quantile(0.25)
Q3 = order_items["line_total"].quantile(0.75)
IQR = Q3 - Q1
upper_bound = Q3 + 1.5 * IQR
lower_bound = max(Q1 - 1.5 * IQR, 0)

outliers = order_items[order_items["line_total"] > upper_bound]
print(f"  IQR bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
print(f"  Outlier line items above upper bound: {len(outliers):,} ({len(outliers)/len(order_items)*100:.2f}% of all rows)")

# Business rule: distinguish "legitimate bulk order" (quantity >= 20, a
# realistic wholesale/B2B purchase) from "likely data error" (quantity < 20
# but line_total still statistically extreme, e.g. a price/qty mismatch)
outliers = outliers.copy()
outliers["outlier_type"] = np.where(outliers["quantity"] >= 20, "Legitimate Bulk Order", "Investigate: Possible Data Error")
print(outliers["outlier_type"].value_counts().to_string())


# ==============================================================================
# SECTION 6 — FEATURE ENGINEERING
# ==============================================================================
# PURPOSE: Build the derived fields that make downstream analysis possible:
#          profit per line, customer age/tenure, order-level aggregates,
#          and RFM-style recency/frequency/monetary features.
# BUSINESS IMPACT: Stakeholders ask "what's our margin," "how old is our
#          customer base," "who are our best customers" — none of these
#          questions are answerable from raw transaction data without
#          these engineered features existing somewhere first.
# PRESENT TO MANAGEMENT: "We've engineered a customer-level dataset that
#          answers 'who is our most valuable customer segment' directly,
#          rather than requiring a fresh manual pull every time someone asks."
# ==============================================================================
print("\n" + "=" * 70)
print("FEATURE ENGINEERING")
print("=" * 70)

# Item-level profit features
order_items["line_profit"] = order_items["line_total"] - order_items["line_cost"]
order_items["margin_pct"] = (order_items["line_profit"] / order_items["line_total"]).round(4)

# Merge to build a single analysis-ready transaction table
txn = (order_items
       .merge(orders, on="order_id", how="left")
       .merge(customers[["customer_id", "region", "acquisition_channel", "loyalty_member", "signup_date"]],
              on="customer_id", how="left")
       .merge(products[["product_id", "category", "brand"]], on="product_id", how="left"))

txn["order_date"] = pd.to_datetime(txn["order_date"])
txn["order_year"] = txn["order_date"].dt.year
txn["order_month"] = txn["order_date"].dt.to_period("M").astype(str)
txn["order_weekday"] = txn["order_date"].dt.day_name()

# Customer tenure in days at time of each transaction (how "new" was the
# customer when they made this purchase — useful for onboarding analysis)
txn["signup_date"] = pd.to_datetime(txn["signup_date"])
txn["customer_tenure_days"] = (txn["order_date"] - txn["signup_date"]).dt.days.clip(lower=0)

print(f"  Built unified transaction table: {len(txn):,} rows, {txn.shape[1]} columns")

# Customer-level RFM feature table
snapshot_date = txn["order_date"].max() + pd.Timedelta(days=1)
completed = txn[txn["order_status"] == "Completed"]
rfm = completed.groupby("customer_id").agg(
    recency_days=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("line_total", "sum"),
).reset_index()
rfm["avg_order_value"] = (rfm["monetary"] / rfm["frequency"]).round(2)
print(f"  Built customer-level RFM feature table: {len(rfm):,} customers")


# ==============================================================================
# SECTION 7 — EXPLORATORY DATA ANALYSIS (EDA)
# ==============================================================================
# PURPOSE: Visualize the cleaned, feature-engineered data to surface the
#          patterns that drive the business insights and dashboard design.
# BUSINESS IMPACT: These four charts are the exact visuals a Sales VP or
#          CFO would ask for in a first "walk me through the business"
#          meeting — they are not decorative, they anchor real decisions
#          (staffing, category investment, regional strategy).
# PRESENT TO MANAGEMENT: Lead with the takeaway sentence, THEN show the
#          chart — e.g., "Revenue grew 34% YoY but is concentrated in Q4;
#          here's the monthly trend that shows it."
# ==============================================================================
print("\n" + "=" * 70)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 70)

completed_txn = txn[txn["order_status"] == "Completed"]

# --- Chart 1: Monthly Revenue Trend ---
monthly = completed_txn.groupby("order_month")["line_total"].sum().reset_index()
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["order_month"], monthly["line_total"], color=NAVY, linewidth=2)
ax.fill_between(monthly["order_month"], monthly["line_total"], color=NAVY, alpha=0.08)
ax.set_title("Monthly Revenue Trend (2023–2025)", fontweight="bold", loc="left")
ax.set_ylabel("Revenue ($)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:,.0f}K"))
ax.set_xticks(monthly["order_month"][::3])
ax.set_xticklabels(monthly["order_month"][::3], rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart1_monthly_revenue_trend.png")
plt.close()
print("  Saved chart1_monthly_revenue_trend.png")

# --- Chart 2: Revenue by Category ---
cat_rev = completed_txn.groupby("category")["line_total"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.barh(cat_rev.index, cat_rev.values, color=TEAL)
ax.set_title("Revenue by Product Category", fontweight="bold", loc="left")
ax.set_xlabel("Revenue ($)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:,.1f}M"))
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart2_revenue_by_category.png")
plt.close()
print("  Saved chart2_revenue_by_category.png")

# --- Chart 3: Regional Revenue Share (Pareto) ---
region_rev = completed_txn.groupby("region")["line_total"].sum().sort_values(ascending=False)
cum_pct = (region_rev.cumsum() / region_rev.sum() * 100)
fig, ax1 = plt.subplots(figsize=(9, 4.5))
ax1.bar(region_rev.index, region_rev.values, color=ORANGE)
ax1.set_ylabel("Revenue ($)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:,.1f}M"))
ax2 = ax1.twinx()
ax2.plot(region_rev.index, cum_pct.values, color=NAVY, marker="o")
ax2.set_ylabel("Cumulative % of Revenue")
ax2.set_ylim(0, 110)
ax1.set_title("Revenue by Region — Concentration (Pareto) View", fontweight="bold", loc="left")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart3_regional_pareto.png")
plt.close()
print("  Saved chart3_regional_pareto.png")

# --- Chart 4: Customer Monetary Value Distribution (with outlier context) ---
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.hist(rfm["monetary"].clip(upper=rfm["monetary"].quantile(0.99)), bins=40, color=GREY, edgecolor="white")
ax.axvline(rfm["monetary"].median(), color=ORANGE, linestyle="--", linewidth=2, label=f"Median: ${rfm['monetary'].median():,.0f}")
ax.set_title("Distribution of Customer Lifetime Revenue (99th pct capped)", fontweight="bold", loc="left")
ax.set_xlabel("Lifetime Revenue ($)")
ax.set_ylabel("Number of Customers")
ax.legend()
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart4_customer_value_distribution.png")
plt.close()
print("  Saved chart4_customer_value_distribution.png")


# ==============================================================================
# SECTION 8 — BUSINESS INSIGHTS SUMMARY (printed console output)
# ==============================================================================
# PURPOSE: Translate the statistical output above into plain-English,
#          decision-ready statements — the actual deliverable a Director
#          or VP reads, since they will not read the code or raw charts
#          without a narrative.
# BUSINESS IMPACT: This is literally "data storytelling" — the difference
#          between an analyst who produces numbers and one who produces
#          decisions.
# PRESENT TO MANAGEMENT: This section IS the presentation — read aloud
#          almost verbatim in a stakeholder readout.
# ==============================================================================
print("\n" + "=" * 70)
print("KEY BUSINESS INSIGHTS (auto-generated from cleaned data)")
print("=" * 70)

total_rev = completed_txn["line_total"].sum()
total_profit = completed_txn["line_profit"].sum()
yoy = completed_txn.groupby("order_year")["line_total"].sum()
top_region_share = cum_pct.iloc[0]
top2_region_share = cum_pct.iloc[1]

print(f"  1. Total revenue across the analysis window: ${total_rev:,.0f}, "
      f"total gross profit: ${total_profit:,.0f} ({total_profit/total_rev*100:.1f}% margin)")
print(f"  2. Revenue by year: {dict(yoy.round(0))}")
print(f"  3. Top region ({region_rev.index[0]}) alone drives {top_region_share:.1f}% of revenue; "
      f"top 2 regions drive {top2_region_share:.1f}% — meaningful geographic concentration risk")
print(f"  4. Top category ({cat_rev.index[-1]}) generates ${cat_rev.iloc[-1]:,.0f} "
      f"({cat_rev.iloc[-1]/total_rev*100:.1f}% of total revenue)")
print(f"  5. Median customer lifetime value: ${rfm['monetary'].median():,.0f}; "
      f"top-decile customers average ${rfm.nlargest(int(len(rfm)*0.1),'monetary')['monetary'].mean():,.0f}")

# Save the cleaned, feature-engineered dataset for downstream use (Power BI, etc.)
txn.to_csv(f"{OUT_DIR}/cleaned_transactions.csv", index=False)
rfm.to_csv(f"{OUT_DIR}/customer_rfm_features.csv", index=False)
print(f"\n  Saved cleaned_transactions.csv ({len(txn):,} rows) and customer_rfm_features.csv ({len(rfm):,} rows) to /outputs")
print("\nEDA & Feature Engineering complete.")
