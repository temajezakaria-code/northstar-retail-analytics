"""
NorthStar Retail Group - Synthetic Dataset Generator
======================================================
Generates a realistic, messy, multi-year retail transactions dataset
(dimension + fact tables) for a portfolio Data Analytics project.

Why messy on purpose?
Real company data is never clean. This generator deliberately injects:
- Missing values (nulls in emails, discount codes, shipping cost)
- Duplicate order rows (system double-submits)
- Outlier transactions (fat-finger quantities, testing/refund transactions)
- Inconsistent text casing / whitespace (e.g., "toronto" vs "Toronto ")
- A few impossible values (negative quantity, future birth dates)
so that the Python cleaning/EDA notebook has real work to do.

Output: CSV files in /data (also loaded into a SQLite DB for SQL practice)
    dim_customers.csv   (~6,000 rows)
    dim_products.csv    (~220 rows)
    dim_stores.csv      (~28 rows)
    fact_orders.csv      (~28,000 rows)
    fact_order_items.csv (~68,000 rows)   <-- primary analysis table, 50k+ rows
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

OUT_DIR = "/home/claude/northstar-retail-analytics/data"

# ---------------------------------------------------------------------------
# 1. DIMENSION: STORES (25 physical + 3 online "virtual" stores)
# ---------------------------------------------------------------------------
regions = {
    "West": ["Los Angeles, CA", "San Francisco, CA", "Seattle, WA", "Portland, OR", "San Diego, CA"],
    "Midwest": ["Chicago, IL", "Detroit, MI", "Columbus, OH", "Minneapolis, MN", "St. Louis, MO"],
    "Northeast": ["New York, NY", "Boston, MA", "Philadelphia, PA", "Pittsburgh, PA", "Newark, NJ"],
    "South": ["Houston, TX", "Dallas, TX", "Atlanta, GA", "Miami, FL", "Charlotte, NC"],
    "Southwest": ["Phoenix, AZ", "Austin, TX", "Denver, CO", "Las Vegas, NV", "Albuquerque, NM"],
}

store_rows = []
store_id = 1000
for region, cities in regions.items():
    for city_state in cities:
        city, state = city_state.split(", ")
        open_date = datetime(2015, 1, 1) + timedelta(days=random.randint(0, 3000))
        store_rows.append({
            "store_id": store_id,
            "store_name": f"NorthStar {city}",
            "store_type": "Physical",
            "city": city,
            "state": state,
            "region": region,
            "open_date": open_date.date().isoformat(),
            "square_footage": random.choice([8000, 10000, 12000, 15000, 18000]),
        })
        store_id += 1

for i, region in enumerate(["West", "Midwest", "Northeast"]):
    store_rows.append({
        "store_id": store_id,
        "store_name": f"NorthStar Online - {region} DC",
        "store_type": "Online",
        "city": None,
        "state": None,
        "region": region,
        "open_date": datetime(2016, 6, 1).date().isoformat(),
        "square_footage": None,
    })
    store_id += 1

dim_stores = pd.DataFrame(store_rows)

# ---------------------------------------------------------------------------
# 2. DIMENSION: PRODUCTS (220 SKUs across 6 categories)
# ---------------------------------------------------------------------------
categories = {
    "Home Appliances": (["Blender", "Air Fryer", "Coffee Maker", "Toaster", "Microwave", "Vacuum Cleaner"], 40, 350),
    "Electronics": (["Bluetooth Speaker", "Wireless Earbuds", "Smart Watch", "4K TV", "Laptop", "Tablet"], 60, 1400),
    "Furniture": (["Office Chair", "Bookshelf", "Coffee Table", "Bed Frame", "Sofa", "Desk"], 90, 900),
    "Kitchenware": (["Cookware Set", "Knife Set", "Cutting Board", "Mixing Bowls", "Dinnerware Set"], 25, 220),
    "Home Decor": (["Wall Art", "Area Rug", "Throw Pillow", "Table Lamp", "Curtains", "Mirror"], 15, 260),
    "Outdoor & Garden": (["Patio Set", "Grill", "Garden Tools Kit", "Outdoor Heater", "Hammock"], 50, 700),
}
brands = ["Aurora", "Vantek", "HomeCraft", "Nexa", "PrimeLiving", "Urbanox", "CoreHome", "Lumeo"]

product_rows = []
pid = 1
for category, (items, low, high) in categories.items():
    n_products = 220 // len(categories)
    for _ in range(n_products):
        base_name = random.choice(items)
        brand = random.choice(brands)
        unit_cost = round(random.uniform(low, high) * 0.55, 2)
        unit_price = round(unit_cost / 0.55, 2)  # ~45% gross margin target
        launch_date = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2700))
        product_rows.append({
            "product_id": pid,
            "product_name": f"{brand} {base_name} {random.choice(['Pro','Classic','X','Lite','Max',''])}".strip(),
            "category": category,
            "subcategory": base_name,
            "brand": brand,
            "unit_cost": unit_cost,
            "unit_price": unit_price,
            "launch_date": launch_date.date().isoformat(),
        })
        pid += 1

dim_products = pd.DataFrame(product_rows)

# ---------------------------------------------------------------------------
# 3. DIMENSION: CUSTOMERS (6,000 customers, 2022-2025 signups)
# ---------------------------------------------------------------------------
first_names = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","David","Elizabeth",
               "Sarah","Daniel","Jessica","Matthew","Ashley","Chris","Amanda","Andrew","Emily","Joshua",
               "Priya","Wei","Sofia","Omar","Fatima","Liam","Noah","Emma","Olivia","Ava"]
last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
              "Wilson","Anderson","Taylor","Thomas","Moore","Jackson","Martin","Lee","Perez","Thompson"]
acquisition_channels = ["Organic Search", "Paid Social", "Email Campaign", "Referral", "Direct", "Affiliate", "In-Store Signup"]
all_cities = [c for cities in regions.values() for c in cities]

def messy_city(city_state):
    """Intentionally inconsistent formatting for the cleaning exercise."""
    city, state = city_state.split(", ")
    roll = random.random()
    if roll < 0.08:
        return city.lower() + "  ", state  # extra whitespace + lowercase
    elif roll < 0.14:
        return city.upper(), state
    return city, state

cust_rows = []
for cid in range(1, 6001):
    fn, ln = random.choice(first_names), random.choice(last_names)
    signup_date = datetime(2022, 1, 1) + timedelta(days=random.randint(0, 1290))
    birth_date = datetime(1955, 1, 1) + timedelta(days=random.randint(0, 18250))
    city_state = random.choice(all_cities)
    city, state = messy_city(city_state)
    region = [r for r, cities in regions.items() if city_state in cities][0]

    # ~4% missing emails, ~2% malformed emails (data quality issue)
    email_roll = random.random()
    if email_roll < 0.04:
        email = None
    elif email_roll < 0.06:
        email = f"{fn.lower()}.{ln.lower()}at example.com"  # malformed
    else:
        email = f"{fn.lower()}.{ln.lower()}{cid}@example.com"

    cust_rows.append({
        "customer_id": cid,
        "first_name": fn,
        "last_name": ln,
        "email": email,
        "gender": random.choice(["F", "M", "Non-binary", None]) if random.random() > 0.97 else random.choice(["F", "M"]),
        "birth_date": birth_date.date().isoformat(),
        "signup_date": signup_date.date().isoformat(),
        "city": city,
        "state": state,
        "region": region,
        "acquisition_channel": random.choice(acquisition_channels),
        "loyalty_member": random.choice([True, False, False]),  # ~33% loyalty members
    })

dim_customers = pd.DataFrame(cust_rows)
# Inject a few duplicate customer records (common real-world CRM issue)
dupes = dim_customers.sample(15, random_state=1).copy()
dim_customers = pd.concat([dim_customers, dupes], ignore_index=True)

# ---------------------------------------------------------------------------
# 4. FACT: ORDERS (~28,000 orders, Jan 2023 - Dec 2025, with seasonality)
# ---------------------------------------------------------------------------
start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_days = (end_date - start_date).days

payment_methods = ["Credit Card", "Debit Card", "PayPal", "Gift Card", "Buy Now Pay Later"]
order_statuses = ["Completed", "Completed", "Completed", "Completed", "Cancelled", "Refunded"]

def seasonal_weight(date):
    """November-December holiday lift, July summer dip."""
    month = date.month
    if month in (11, 12):
        return 2.4
    if month == 7:
        return 0.7
    if month in (1,):
        return 0.8
    return 1.0

# Build a day-by-day order count schedule reflecting seasonality + YoY growth
order_rows = []
order_id = 500000
store_ids = dim_stores["store_id"].tolist()
customer_ids = dim_customers["customer_id"].unique().tolist()

for d in range(date_range_days + 1):
    date = start_date + timedelta(days=d)
    year_growth = 1.0 + (date.year - 2023) * 0.12  # ~12% YoY growth
    weekday_factor = 1.3 if date.weekday() in (4, 5) else 1.0  # Fri/Sat lift
    base_orders = 24 * seasonal_weight(date) * year_growth * weekday_factor
    n_orders_today = np.random.poisson(base_orders)

    for _ in range(n_orders_today):
        cust = random.choice(customer_ids)
        store = random.choice(store_ids)
        payment = random.choice(payment_methods)
        status = random.choice(order_statuses)
        # ~5% missing shipping cost, occasional negative discount error
        shipping_cost = round(random.uniform(0, 15), 2) if random.random() > 0.05 else None
        discount_amount = round(random.choice([0, 0, 0, 5, 10, 15, 20]) * random.uniform(0.8, 1.2), 2)
        if random.random() < 0.005:
            discount_amount = -discount_amount  # data entry error, negative discount

        order_rows.append({
            "order_id": order_id,
            "customer_id": cust,
            "store_id": store,
            "order_date": date.date().isoformat(),
            "order_status": status,
            "payment_method": payment,
            "shipping_cost": shipping_cost,
            "discount_amount": discount_amount,
        })
        order_id += 1

fact_orders = pd.DataFrame(order_rows)
# Inject ~25 duplicate order records (system double-submit bug)
dupe_orders = fact_orders.sample(25, random_state=2).copy()
fact_orders = pd.concat([fact_orders, dupe_orders], ignore_index=True)

# ---------------------------------------------------------------------------
# 5. FACT: ORDER ITEMS (~68,000 line items -> satisfies 50,000+ row requirement)
# ---------------------------------------------------------------------------
product_lookup = dim_products.set_index("product_id")[["unit_cost", "unit_price", "category"]]
product_ids = dim_products["product_id"].tolist()
# Weight popular categories (Electronics & Home Appliances sell more units)
category_weights = dim_products["category"].map({
    "Electronics": 3.0, "Home Appliances": 2.5, "Kitchenware": 1.8,
    "Furniture": 1.2, "Home Decor": 1.5, "Outdoor & Garden": 1.0
}).values
category_weights = category_weights / category_weights.sum()

item_rows = []
item_id = 1
order_ids = fact_orders["order_id"].tolist()

for oid in order_ids:
    n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.45, 0.28, 0.15, 0.08, 0.04])
    chosen_products = np.random.choice(product_ids, size=n_items, replace=True, p=category_weights)
    for pid in chosen_products:
        cost, price, category = product_lookup.loc[pid]
        qty = np.random.choice([1, 2, 3, 4], p=[0.65, 0.20, 0.10, 0.05])
        # Inject rare outliers: bulk B2B-style orders and fat-finger entries
        if random.random() < 0.003:
            qty = random.choice([25, 40, 60])  # legit bulk order outlier
        if random.random() < 0.001:
            qty = -qty  # data entry error: negative quantity (return mis-key)

        unit_price_actual = round(price * random.uniform(0.92, 1.0), 2)  # minor promo variance
        line_total = round(unit_price_actual * qty, 2)
        line_cost = round(cost * qty, 2)

        item_rows.append({
            "order_item_id": item_id,
            "order_id": oid,
            "product_id": pid,
            "quantity": qty,
            "unit_price": unit_price_actual,
            "unit_cost": cost,
            "line_total": line_total,
            "line_cost": line_cost,
        })
        item_id += 1

fact_order_items = pd.DataFrame(item_rows)

# ---------------------------------------------------------------------------
# SAVE ALL FILES
# ---------------------------------------------------------------------------
dim_customers.to_csv(f"{OUT_DIR}/dim_customers.csv", index=False)
dim_products.to_csv(f"{OUT_DIR}/dim_products.csv", index=False)
dim_stores.to_csv(f"{OUT_DIR}/dim_stores.csv", index=False)
fact_orders.to_csv(f"{OUT_DIR}/fact_orders.csv", index=False)
fact_order_items.to_csv(f"{OUT_DIR}/fact_order_items.csv", index=False)

print("Dataset generated:")
print(f"  dim_customers:    {len(dim_customers):,} rows")
print(f"  dim_products:     {len(dim_products):,} rows")
print(f"  dim_stores:       {len(dim_stores):,} rows")
print(f"  fact_orders:      {len(fact_orders):,} rows")
print(f"  fact_order_items: {len(fact_order_items):,} rows  <-- primary fact table")
print(f"  TOTAL ROWS ACROSS ALL FILES: {len(dim_customers)+len(dim_products)+len(dim_stores)+len(fact_orders)+len(fact_order_items):,}")
