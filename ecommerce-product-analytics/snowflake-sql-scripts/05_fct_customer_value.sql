
CREATE OR REPLACE VIEW product_analytics.analytics.fct_customer_value AS

WITH customer_orders AS (
    SELECT
        o.ORDER_ID,
        o.CUSTOMER_ID,
        DATE(o.ORDER_TIME) as ORDER_TIME,
        o.SUBTOTAL_USD,

        COALESCE(
            SUM(oi.QUANTITY),
            0
        ) AS TOTAL_ITEMS

    FROM product_analytics.raw_events.ORDERS o

    LEFT JOIN product_analytics.raw_events.ORDER_ITEMS oi
        ON o.ORDER_ID = oi.ORDER_ID

    GROUP BY
        o.ORDER_ID,
        o.CUSTOMER_ID,
        o.ORDER_TIME,
        o.SUBTOTAL_USD
),

customer_value AS (
    SELECT
        CUSTOMER_ID,
        COUNT(DISTINCT ORDER_ID) AS ORDER_COUNT,
        SUM(TOTAL_ITEMS) AS TOTAL_ITEMS,
        SUM(SUBTOTAL_USD) AS TOTAL_REVENUE,
        AVG(SUBTOTAL_USD) AS AVG_ORDER_VALUE,
        MIN(DATE(ORDER_TIME)) AS FIRST_PURCHASE_DATE,
        MAX(DATE(ORDER_TIME)) AS LAST_PURCHASE_DATE
    FROM customer_orders
    GROUP BY CUSTOMER_ID
)

SELECT
    d.CUSTOMER_ID,
    d.SIGNUP_DATE,
    d.SIGNUP_COHORT_MONTH,
    d.COUNTRY,

    -- Purchase metrics
    COALESCE(cv.ORDER_COUNT, 0) AS ORDER_COUNT,
    COALESCE(cv.TOTAL_ITEMS, 0) AS TOTAL_ITEMS,
    COALESCE(cv.TOTAL_REVENUE, 0) AS TOTAL_REVENUE,
    COALESCE(cv.AVG_ORDER_VALUE, 0) AS AVG_ORDER_VALUE,

    cv.FIRST_PURCHASE_DATE,
    cv.LAST_PURCHASE_DATE,

    -- Customer lifetime
    CASE
        WHEN cv.FIRST_PURCHASE_DATE IS NOT NULL
        THEN DATEDIFF(
            'day',
            cv.FIRST_PURCHASE_DATE,
            cv.LAST_PURCHASE_DATE
        )
        ELSE NULL
    END AS CUSTOMER_LIFETIME_DAYS,

    -- Recency as of end of 2025
    CASE
        WHEN cv.LAST_PURCHASE_DATE IS NOT NULL
        THEN DATEDIFF(
            'day',
            cv.LAST_PURCHASE_DATE,
            DATE('2025-12-31')
        )
        ELSE NULL
    END AS DAYS_SINCE_LAST_PURCHASE_END_2025,

    -- 30-day revenue after signup
    COALESCE(
        SUM(
            CASE
                WHEN co.ORDER_TIME >= d.SIGNUP_DATE
                 AND co.ORDER_TIME < DATEADD(
                     'day',
                     30,
                     d.SIGNUP_DATE
                 )
                THEN co.SUBTOTAL_USD
                ELSE 0
            END
        ),
        0
    ) AS REVENUE_30D,

    -- 90-day revenue after signup
    COALESCE(
        SUM(
            CASE
                WHEN co.ORDER_TIME >= d.SIGNUP_DATE
                 AND co.ORDER_TIME < DATEADD(
                     'day',
                     90,
                     d.SIGNUP_DATE
                 )
                THEN co.SUBTOTAL_USD
                ELSE 0
            END
        ),
        0
    ) AS REVENUE_90D

FROM product_analytics.analytics.DIM_USER d

LEFT JOIN customer_value cv
    ON d.CUSTOMER_ID = cv.CUSTOMER_ID

LEFT JOIN customer_orders co
    ON d.CUSTOMER_ID = co.CUSTOMER_ID

GROUP BY
    d.CUSTOMER_ID,
    d.SIGNUP_DATE,
    d.SIGNUP_COHORT_MONTH,
    d.COUNTRY,
    cv.ORDER_COUNT,
    cv.TOTAL_ITEMS,
    cv.TOTAL_REVENUE,
    cv.AVG_ORDER_VALUE,
    cv.FIRST_PURCHASE_DATE,
    cv.LAST_PURCHASE_DATE;


--- Result head
select * from product_analytics.analytics.fct_customer_value
LIMIT 10;
