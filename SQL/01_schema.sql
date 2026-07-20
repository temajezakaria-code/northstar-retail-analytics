-- =============================================================================
-- NorthStar Retail Group — Data Warehouse Schema (Star Schema)
-- =============================================================================
-- Design notes:
-- This follows a classic Kimball-style star schema: one large fact table
-- (fact_order_items) at the grain of "one row per product per order", a
-- supporting fact table (fact_orders) at the grain of "one row per order",
-- and three dimension tables (customers, products, stores).
--
-- Why two fact tables instead of one flattened table?
-- Order-level attributes (payment method, shipping cost, discount, status)
-- do not repeat per line item. Splitting avoids data redundancy and lets us
-- analyze order-level metrics (AOV, cancellation rate) and item-level
-- metrics (units sold, product margin) independently without double-counting.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_customers
-- -----------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id         INTEGER PRIMARY KEY,
    first_name           VARCHAR(50),
    last_name            VARCHAR(50),
    email                VARCHAR(100),
    gender               VARCHAR(15),
    birth_date           DATE,
    signup_date          DATE          NOT NULL,   -- date customer created an account
    city                 VARCHAR(50),
    state                VARCHAR(20),
    region               VARCHAR(20)   NOT NULL,   -- West / Midwest / Northeast / South / Southwest
    acquisition_channel  VARCHAR(30),               -- how the customer was acquired (marketing attribution)
    loyalty_member       BOOLEAN       DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_products
-- -----------------------------------------------------------------------------
CREATE TABLE dim_products (
    product_id    INTEGER PRIMARY KEY,
    product_name  VARCHAR(100)   NOT NULL,
    category      VARCHAR(50)    NOT NULL,
    subcategory   VARCHAR(50),
    brand         VARCHAR(50),
    unit_cost     DECIMAL(10,2)  NOT NULL,   -- wholesale/COGS cost per unit
    unit_price    DECIMAL(10,2)  NOT NULL,   -- standard list price per unit
    launch_date   DATE
);

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_stores
-- -----------------------------------------------------------------------------
CREATE TABLE dim_stores (
    store_id        INTEGER PRIMARY KEY,
    store_name      VARCHAR(100) NOT NULL,
    store_type      VARCHAR(20)  NOT NULL,   -- 'Physical' or 'Online'
    city            VARCHAR(50),
    state           VARCHAR(20),
    region          VARCHAR(20)  NOT NULL,
    open_date       DATE,
    square_footage  INTEGER
);

-- -----------------------------------------------------------------------------
-- FACT: fact_orders  (grain: one row per order)
-- -----------------------------------------------------------------------------
CREATE TABLE fact_orders (
    order_id         INTEGER PRIMARY KEY,
    customer_id      INTEGER       NOT NULL REFERENCES dim_customers(customer_id),
    store_id         INTEGER       NOT NULL REFERENCES dim_stores(store_id),
    order_date       DATE          NOT NULL,
    order_status     VARCHAR(20)   NOT NULL,   -- Completed / Cancelled / Refunded
    payment_method   VARCHAR(30),
    shipping_cost    DECIMAL(8,2),
    discount_amount  DECIMAL(8,2)
);

-- -----------------------------------------------------------------------------
-- FACT: fact_order_items  (grain: one row per product line within an order)
-- This is the PRIMARY analytical table — 75,000+ rows
-- -----------------------------------------------------------------------------
CREATE TABLE fact_order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER       NOT NULL REFERENCES fact_orders(order_id),
    product_id     INTEGER       NOT NULL REFERENCES dim_products(product_id),
    quantity       INTEGER       NOT NULL,
    unit_price     DECIMAL(10,2) NOT NULL,   -- actual transacted price (may differ from list price via promos)
    unit_cost      DECIMAL(10,2) NOT NULL,
    line_total     DECIMAL(12,2) NOT NULL,   -- quantity * unit_price
    line_cost      DECIMAL(12,2) NOT NULL    -- quantity * unit_cost
);

-- -----------------------------------------------------------------------------
-- INDEXES — added to support the join patterns and date filters used
-- throughout the analysis queries (foreign keys are not auto-indexed in SQLite)
-- -----------------------------------------------------------------------------
CREATE INDEX idx_orders_customer   ON fact_orders(customer_id);
CREATE INDEX idx_orders_store      ON fact_orders(store_id);
CREATE INDEX idx_orders_date       ON fact_orders(order_date);
CREATE INDEX idx_items_order       ON fact_order_items(order_id);
CREATE INDEX idx_items_product     ON fact_order_items(product_id);
CREATE INDEX idx_customers_region  ON dim_customers(region);
CREATE INDEX idx_products_category ON dim_products(category);

-- =============================================================================
-- ENTITY RELATIONSHIP SUMMARY
-- =============================================================================
-- dim_customers (1) ----< fact_orders (many)
-- dim_stores    (1) ----< fact_orders (many)
-- fact_orders   (1) ----< fact_order_items (many)
-- dim_products  (1) ----< fact_order_items (many)
--
-- This star schema supports slicing revenue/profit/units by any combination
-- of customer attribute, product attribute, store/region, and calendar date —
-- exactly the flexibility a real BI team needs for ad-hoc stakeholder requests.
-- =============================================================================
