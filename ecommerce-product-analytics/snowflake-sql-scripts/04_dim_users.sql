-- Cleaned/enriched representation of the existing customer dimension, and most 
-- of the additional attributes are derived from activity.
-- Grain: one row per customer.

CREATE OR REPLACE VIEW product_analytics.analytics.dim_user AS

WITH first_activity AS (
    SELECT
        CUSTOMER_ID,
        MIN(ACTIVITY_DATE) AS FIRST_ACTIVITY_DATE
    FROM product_analytics.analytics.FCT_USER_ACTIVITY
    GROUP BY CUSTOMER_ID
),

first_purchase AS (
    SELECT
        CUSTOMER_ID,
        MIN(SESSION_DATE) AS FIRST_PURCHASE_DATE
    FROM product_analytics.analytics.FCT_SESSIONS
    WHERE HAS_PURCHASE = TRUE
    GROUP BY CUSTOMER_ID
)

SELECT
    c.CUSTOMER_ID,
    c.NAME,
    c.EMAIL,
    c.COUNTRY,
    c.AGE,
    c.SIGNUP_DATE,
    c.MARKETING_OPT_IN,

    -- Cohort
    DATE_TRUNC('month', c.SIGNUP_DATE) AS SIGNUP_COHORT_MONTH,

    -- First product activity
    fa.FIRST_ACTIVITY_DATE,

    -- First purchase
    fp.FIRST_PURCHASE_DATE,

    -- Acquisition / activation timing
    DATEDIFF(
        'day',
        c.SIGNUP_DATE,
        fa.FIRST_ACTIVITY_DATE
    ) AS DAYS_TO_FIRST_ACTIVITY,

    DATEDIFF(
        'day',
        c.SIGNUP_DATE,
        fp.FIRST_PURCHASE_DATE
    ) AS DAYS_TO_FIRST_PURCHASE

FROM product_analytics.raw_events.CUSTOMERS_CLEAN c
LEFT JOIN first_activity fa
    ON c.CUSTOMER_ID = fa.CUSTOMER_ID
LEFT JOIN first_purchase fp
    ON c.CUSTOMER_ID = fp.CUSTOMER_ID;


--- Result head
select * from product_analytics.analytics.dim_user
LIMIT 10;
