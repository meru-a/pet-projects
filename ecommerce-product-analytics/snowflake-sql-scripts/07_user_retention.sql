
CREATE OR REPLACE VIEW product_analytics.analytics.user_retention AS

WITH cohort_users AS (
    SELECT
        CUSTOMER_ID,
        SIGNUP_DATE,
        SIGNUP_COHORT_MONTH
    FROM product_analytics.analytics.DIM_USER
),

activity AS (
    SELECT
        CUSTOMER_ID,
        ACTIVITY_DATE,
        DAYS_SINCE_SIGNUP
    FROM product_analytics.analytics.FCT_USER_ACTIVITY
    WHERE DAYS_SINCE_SIGNUP >= 0
),

cohort_sizes AS (
    SELECT
        SIGNUP_COHORT_MONTH,
        COUNT(DISTINCT CUSTOMER_ID) AS COHORT_USERS
    FROM cohort_users
    GROUP BY SIGNUP_COHORT_MONTH
),

retentions AS (
    SELECT
        cu.SIGNUP_COHORT_MONTH,
        a.DAYS_SINCE_SIGNUP,
        COUNT(DISTINCT a.CUSTOMER_ID) AS RETAINED_USERS
    FROM cohort_users cu
    INNER JOIN activity a
        ON cu.CUSTOMER_ID = a.CUSTOMER_ID
    GROUP BY
        cu.SIGNUP_COHORT_MONTH,
        a.DAYS_SINCE_SIGNUP
)

SELECT
    r.SIGNUP_COHORT_MONTH,
    r.DAYS_SINCE_SIGNUP,
    cs.COHORT_USERS,
    r.RETAINED_USERS,
    ROUND(
        r.RETAINED_USERS / NULLIF(cs.COHORT_USERS, 0),
        4
    ) AS RETENTION_RATE
FROM retentions r
INNER JOIN cohort_sizes cs
    ON r.SIGNUP_COHORT_MONTH = cs.SIGNUP_COHORT_MONTH;


--- Result head
select * from product_analytics.analytics.user_retention
limit 10;