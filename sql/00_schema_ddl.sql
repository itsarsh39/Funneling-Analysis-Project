-- ==============================================================================
-- Schema DDL: E-Commerce Funnel Experimentation Star Schema
-- Database Engine: SQLite / ANSI SQL Compatible
-- Description: Creates dimensional entities (users, stages, calendar) and 
--              fact tables (funnel events, orders/revenue) with indexes.
-- ==============================================================================

-- 1. Dimension: Users (Entity Grain: One record per unique user)
CREATE TABLE IF NOT EXISTS dim_users (
    user_id          TEXT PRIMARY KEY,
    variant          TEXT NOT NULL CHECK(variant IN ('control', 'treatment')),
    device_type      TEXT NOT NULL CHECK(device_type IN ('Desktop', 'Mobile', 'Tablet')),
    browser          TEXT NOT NULL,
    traffic_source   TEXT NOT NULL,
    country          TEXT NOT NULL,
    first_seen_at    DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_users_variant ON dim_users(variant);
CREATE INDEX IF NOT EXISTS idx_dim_users_device ON dim_users(device_type);
CREATE INDEX IF NOT EXISTS idx_dim_users_browser ON dim_users(browser);
CREATE INDEX IF NOT EXISTS idx_dim_users_source ON dim_users(traffic_source);

-- 2. Dimension: Funnel Stages (Entity Grain: One record per funnel step)
CREATE TABLE IF NOT EXISTS dim_funnel_stages (
    stage_order         INTEGER PRIMARY KEY,
    stage_name          TEXT NOT NULL UNIQUE,
    stage_category      TEXT NOT NULL,
    is_conversion_step  INTEGER NOT NULL CHECK(is_conversion_step IN (0, 1))
);

-- 3. Dimension: Date Calendar (Entity Grain: One record per experiment day)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER PRIMARY KEY, -- YYYYMMDD
    date            DATE NOT NULL UNIQUE,
    experiment_day  INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,    -- 0 = Monday, 6 = Sunday
    day_name        TEXT NOT NULL,
    is_weekend      INTEGER NOT NULL CHECK(is_weekend IN (0, 1)),
    window_period   TEXT NOT NULL CHECK(window_period IN ('Days 1-3 (Novelty)', 'Days 4-14 (Stabilized)'))
);

-- 4. Fact: Funnel Events (Entity Grain: One record per user-stage interaction)
CREATE TABLE IF NOT EXISTS fct_events (
    event_id         INTEGER PRIMARY KEY,
    session_id       TEXT NOT NULL,
    user_id          TEXT NOT NULL,
    stage_order      INTEGER NOT NULL,
    funnel_stage     TEXT NOT NULL,
    date_id          INTEGER NOT NULL,
    event_timestamp  DATETIME NOT NULL,
    latency_ms       INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id),
    FOREIGN KEY (stage_order) REFERENCES dim_funnel_stages(stage_order),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE INDEX IF NOT EXISTS idx_fct_events_user ON fct_events(user_id);
CREATE INDEX IF NOT EXISTS idx_fct_events_session ON fct_events(session_id);
CREATE INDEX IF NOT EXISTS idx_fct_events_stage ON fct_events(stage_order);
CREATE INDEX IF NOT EXISTS idx_fct_events_date ON fct_events(date_id);

-- 5. Fact: Orders & Gross Merchandise Value (Entity Grain: One record per completed purchase)
CREATE TABLE IF NOT EXISTS fct_orders (
    order_id         TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    date_id          INTEGER NOT NULL,
    order_timestamp  DATETIME NOT NULL,
    revenue_usd      REAL NOT NULL CHECK(revenue_usd > 0),
    items_count      INTEGER NOT NULL CHECK(items_count >= 1),
    payment_method   TEXT NOT NULL,
    payment_status   TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE INDEX IF NOT EXISTS idx_fct_orders_user ON fct_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_fct_orders_date ON fct_orders(date_id);
CREATE INDEX IF NOT EXISTS idx_fct_orders_method ON fct_orders(payment_method);

-- 6. Analytical View: Unified Event Log (Joins Dimensions for Direct BI Querying)
DROP VIEW IF EXISTS vw_unified_events;
CREATE VIEW vw_unified_events AS
SELECT 
    fe.event_id,
    fe.session_id,
    fe.user_id,
    u.variant,
    u.device_type,
    u.browser,
    u.traffic_source,
    u.country,
    fe.stage_order,
    fe.funnel_stage,
    s.stage_category,
    s.is_conversion_step,
    fe.date_id,
    d.date,
    d.experiment_day,
    d.day_name,
    d.window_period,
    fe.event_timestamp,
    fe.latency_ms
FROM fct_events fe
JOIN dim_users u ON fe.user_id = u.user_id
JOIN dim_funnel_stages s ON fe.stage_order = s.stage_order
JOIN dim_date d ON fe.date_id = d.date_id;
