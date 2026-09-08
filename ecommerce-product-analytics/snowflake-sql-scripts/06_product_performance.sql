CREATE OR REPLACE VIEW product_analytics.analytics.PRODUCT_PERFORMANCE AS

WITH order_item_revenue AS (
    SELECT
        oi.ORDER_ID,
        oi.PRODUCT_ID,
        oi.QUANTITY,
        oi.UNIT_PRICE_USD,
        oi.LINE_TOTAL_USD,

        o.TOTAL_USD,
        o.SUBTOTAL_USD,

        -- Allocate order-level discount proportionally
        CASE
            WHEN o.TOTAL_USD > 0
            THEN oi.LINE_TOTAL_USD
                 * (o.SUBTOTAL_USD / o.TOTAL_USD)
            ELSE 0
        END AS NET_PRODUCT_REVENUE

    FROM product_analytics.raw_events.ORDER_ITEMS oi

    INNER JOIN product_analytics.raw_events.ORDERS o
        ON oi.ORDER_ID = o.ORDER_ID
),

sales_metrics AS (
    SELECT
        PRODUCT_ID,
        COUNT(DISTINCT ORDER_ID) AS ORDER_COUNT,
        SUM(QUANTITY) AS UNITS_SOLD,
        SUM(LINE_TOTAL_USD) AS GROSS_PRODUCT_REVENUE,
        SUM(NET_PRODUCT_REVENUE) AS NET_PRODUCT_REVENUE
    FROM order_item_revenue
    GROUP BY PRODUCT_ID
),

event_metrics AS (
    SELECT
        PRODUCT_ID,
        COUNT_IF(EVENT_TYPE = 'page_view') AS PRODUCT_VIEWS,
        COUNT_IF(EVENT_TYPE = 'add_to_cart') AS ADD_TO_CART_EVENTS,
        COUNT_IF(EVENT_TYPE = 'checkout') AS CHECKOUT_EVENTS,
        COUNT_IF(EVENT_TYPE = 'purchase') AS PURCHASE_EVENTS,
        COUNT(DISTINCT CASE
            WHEN EVENT_TYPE = 'page_view'
            THEN SESSION_ID
        END) AS VIEW_SESSIONS,

        COUNT(DISTINCT CASE
            WHEN EVENT_TYPE = 'add_to_cart'
            THEN SESSION_ID
        END) AS CART_SESSIONS,

        COUNT(DISTINCT CASE
            WHEN EVENT_TYPE = 'purchase'
            THEN SESSION_ID
        END) AS PURCHASE_SESSIONS

    FROM product_analytics.raw_events.EVENTS
    WHERE PRODUCT_ID IS NOT NULL
    GROUP BY PRODUCT_ID
)

SELECT
    p.PRODUCT_ID,
    p.NAME,
    p.CATEGORY,
    p.PRICE_USD,
    p.COST_USD,
    p.MARGIN_USD,

    -- Engagement
    COALESCE(e.PRODUCT_VIEWS, 0) AS PRODUCT_VIEWS,
    COALESCE(e.ADD_TO_CART_EVENTS, 0) AS ADD_TO_CART_EVENTS,
    COALESCE(e.CHECKOUT_EVENTS, 0) AS CHECKOUT_EVENTS,
    COALESCE(e.PURCHASE_EVENTS, 0) AS PURCHASE_EVENTS,

    -- Unique sessions
    COALESCE(e.VIEW_SESSIONS, 0) AS VIEW_SESSIONS,
    COALESCE(e.CART_SESSIONS, 0) AS CART_SESSIONS,
    COALESCE(e.PURCHASE_SESSIONS, 0) AS PURCHASE_SESSIONS,

    -- Sales
    COALESCE(s.ORDER_COUNT, 0) AS ORDER_COUNT,
    COALESCE(s.UNITS_SOLD, 0) AS UNITS_SOLD,

    COALESCE(
        s.GROSS_PRODUCT_REVENUE,
        0
    ) AS GROSS_PRODUCT_REVENUE,

    COALESCE(
        s.NET_PRODUCT_REVENUE,
        0
    ) AS NET_PRODUCT_REVENUE,

    -- Funnel conversion
    ROUND(
        e.CART_SESSIONS
        / NULLIF(e.VIEW_SESSIONS, 0),
        4
    ) AS VIEW_TO_CART_RATE,

    ROUND(
        e.PURCHASE_SESSIONS
        / NULLIF(e.CART_SESSIONS, 0),
        4
    ) AS CART_TO_PURCHASE_RATE,

    ROUND(
        e.PURCHASE_SESSIONS
        / NULLIF(e.VIEW_SESSIONS, 0),
        4
    ) AS VIEW_TO_PURCHASE_RATE

FROM product_analytics.raw_events.PRODUCTS p

LEFT JOIN event_metrics e
    ON p.PRODUCT_ID = e.PRODUCT_ID

LEFT JOIN sales_metrics s
    ON p.PRODUCT_ID = s.PRODUCT_ID;


--- Result head
select * from product_analytics.analytics.product_performance;
