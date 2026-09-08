--- "What did users do over time?"

CREATE OR REPLACE TABLE product_analytics.analytics.fct_user_activity AS

WITH user_day AS (
    SELECT
        CUSTOMER_ID,
        SESSION_DATE AS ACTIVITY_DATE,

        -- Session metrics
        COUNT(DISTINCT SESSION_ID) AS SESSION_COUNT,

        -- Event metrics
        SUM(EVENT_COUNT) AS EVENT_COUNT,
        SUM(PAGE_VIEW_COUNT) AS PAGE_VIEW_COUNT,
        SUM(ADD_TO_CART_COUNT) AS ADD_TO_CART_COUNT,
        SUM(CHECKOUT_COUNT) AS CHECKOUT_COUNT,
        SUM(PURCHASE_COUNT) AS PURCHASE_COUNT,

        -- Revenue
        SUM(SESSION_REVENUE) AS PURCHASE_EVENT_REVENUE,

        -- Activity flags
        MAX(
            CASE
                WHEN HAS_PURCHASE THEN 1
                ELSE 0
            END
        ) = 1 AS PURCHASER_FLAG

    FROM product_analytics.analytics.FCT_SESSIONS

    GROUP BY
        CUSTOMER_ID,
        SESSION_DATE
)

SELECT
    u.CUSTOMER_ID,

    -- Customer attributes
    c.SIGNUP_DATE,
    c.COUNTRY AS CUSTOMER_COUNTRY,
    c.MARKETING_OPT_IN,

    -- Activity
    u.ACTIVITY_DATE,

    -- Metrics
    u.SESSION_COUNT,
    u.EVENT_COUNT,
    u.PAGE_VIEW_COUNT,
    u.ADD_TO_CART_COUNT,
    u.CHECKOUT_COUNT,
    u.PURCHASE_COUNT,
    u.PURCHASE_EVENT_REVENUE,

    -- Flags
    TRUE AS ACTIVE_FLAG,
    u.PURCHASER_FLAG,

    -- Cohort information
    DATEDIFF(
        'day',
        c.SIGNUP_DATE,
        u.ACTIVITY_DATE
    ) AS DAYS_SINCE_SIGNUP,

    DATE_TRUNC(
        'month',
        c.SIGNUP_DATE
    ) AS SIGNUP_COHORT_MONTH

FROM user_day u

LEFT JOIN product_analytics.raw_events.CUSTOMERS_CLEAN c
    ON u.CUSTOMER_ID = c.CUSTOMER_ID;


--- Result head
select * from product_analytics.analytics.fct_user_activity
LIMIT 10;