---

CREATE OR REPLACE TABLE product_analytics.analytics.fct_sessions AS

WITH event_agg AS (
    SELECT
        SESSION_ID,

        -- Session timing
        MIN(TIMESTAMP) AS FIRST_EVENT_TIME,
        MAX(TIMESTAMP) AS LAST_EVENT_TIME,

        -- Overall event counts
        COUNT(*) AS EVENT_COUNT,

        -- Event-type counts
        COUNT_IF(EVENT_TYPE = 'page_view') AS PAGE_VIEW_COUNT,
        COUNT_IF(EVENT_TYPE = 'add_to_cart') AS ADD_TO_CART_COUNT,
        COUNT_IF(EVENT_TYPE = 'checkout') AS CHECKOUT_COUNT,
        COUNT_IF(EVENT_TYPE = 'purchase') AS PURCHASE_COUNT,

        -- Event-type flags
        COUNT_IF(EVENT_TYPE = 'page_view') > 0 AS HAS_PAGE_VIEW,
        COUNT_IF(EVENT_TYPE = 'add_to_cart') > 0 AS HAS_ADD_TO_CART,
        COUNT_IF(EVENT_TYPE = 'checkout') > 0 AS HAS_CHECKOUT,
        COUNT_IF(EVENT_TYPE = 'purchase') > 0 AS HAS_PURCHASE,

        -- Revenue
        SUM(
            CASE
                WHEN EVENT_TYPE = 'purchase'
                THEN COALESCE(AMOUNT_USD, 0)
                ELSE 0
            END
        ) AS PURCHASE_EVENT_REVENUE

    FROM product_analytics.raw_events.EVENTS
    GROUP BY SESSION_ID
)

SELECT
    s.SESSION_ID,
    s.CUSTOMER_ID,

    -- Session date/time
    CAST(s.START_TIME AS DATE) AS SESSION_DATE,
    s.START_TIME AS SESSION_START,

    -- Use the last event as session end.
    -- If a session has no events, fall back to START_TIME.
    COALESCE(
        e.LAST_EVENT_TIME,
        s.START_TIME
    ) AS SESSION_END,

    -- Duration in seconds
    DATEDIFF(
        'second',
        s.START_TIME,
        COALESCE(e.LAST_EVENT_TIME, s.START_TIME)
    ) AS SESSION_DURATION_SECONDS,

    -- Session attributes
    s.DEVICE,
    s.SOURCE,
    s.COUNTRY,

    -- Event metrics
    COALESCE(e.EVENT_COUNT, 0) AS EVENT_COUNT,
    COALESCE(e.PAGE_VIEW_COUNT, 0) AS PAGE_VIEW_COUNT,
    COALESCE(e.ADD_TO_CART_COUNT, 0) AS ADD_TO_CART_COUNT,
    COALESCE(e.CHECKOUT_COUNT, 0) AS CHECKOUT_COUNT,
    COALESCE(e.PURCHASE_COUNT, 0) AS PURCHASE_COUNT,

    -- Event flags
    COALESCE(e.HAS_PAGE_VIEW, FALSE) AS HAS_PAGE_VIEW,
    COALESCE(e.HAS_ADD_TO_CART, FALSE) AS HAS_ADD_TO_CART,
    COALESCE(e.HAS_CHECKOUT, FALSE) AS HAS_CHECKOUT,
    COALESCE(e.HAS_PURCHASE, FALSE) AS HAS_PURCHASE,

    -- Revenue
    COALESCE(e.PURCHASE_EVENT_REVENUE, 0) AS PURCHASE_EVENT_REVENUE 

FROM product_analytics.raw_events.SESSIONS s

LEFT JOIN event_agg e
    ON s.SESSION_ID = e.SESSION_ID;


--- Result head
select * from product_analytics.analytics.fct_sessions
LIMIT 10;