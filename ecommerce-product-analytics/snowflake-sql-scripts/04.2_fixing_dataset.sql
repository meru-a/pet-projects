--- Upon the closer look on the results of dim_user, I notices negative #s in the last 2 columns.
--- It looks like 83.5% of users in this synthetic dataset had
--- signup dates later than the first activity dates. 
--- The code below demonstrates just that.

SELECT
    COUNT(*) AS TOTAL_USERS,
    COUNT_IF(
        FIRST_ACTIVITY_DATE < SIGNUP_DATE
    ) AS USERS_WITH_INVALID_SIGNUP,
    ROUND(
        100.0 * COUNT_IF(
            FIRST_ACTIVITY_DATE < SIGNUP_DATE
        ) / COUNT(*),
        2
    ) AS INVALID_PCT
FROM product_analytics.analytics.DIM_USER;

--- Other checks for orders/events ----------------
---------------------------------------------------

--- First purchase date before first activity date
SELECT
    COUNT(*) AS TOTAL_USERS,
    COUNT_IF(
        FIRST_PURCHASE_DATE < FIRST_ACTIVITY_DATE
    ) AS USERS_WITH_INVALID_SIGNUP,
    ROUND(
        100.0 * COUNT_IF(
            FIRST_PURCHASE_DATE < FIRST_ACTIVITY_DATE
        ) / COUNT(*),
        2
    ) AS INVALID_PCT
FROM product_analytics.analytics.DIM_USER;

---------------------------------------------------
--- Do all events belong to real sessions?
SELECT
    COUNT(*) AS TOTAL_EVENTS,
    COUNT_IF(s.SESSION_ID IS NULL) AS ORPHAN_EVENTS,
    ROUND(
        100.0 * COUNT_IF(s.SESSION_ID IS NULL) / COUNT(*),
        2
    ) AS ORPHAN_EVENT_PCT
FROM product_analytics.raw_events.EVENTS e
LEFT JOIN product_analytics.raw_events.SESSIONS s
    ON e.SESSION_ID = s.SESSION_ID;

---------------------------------------------------
--- Do all sessions belong to real customers?
SELECT
    COUNT(*) AS TOTAL_SESSIONS,
    COUNT_IF(c.CUSTOMER_ID IS NULL) AS ORPHAN_SESSIONS,
    ROUND(
        100.0 * COUNT_IF(c.CUSTOMER_ID IS NULL) / COUNT(*),
        2
    ) AS ORPHAN_SESSION_PCT
FROM product_analytics.raw_events.SESSIONS s
LEFT JOIN product_analytics.raw_events.CUSTOMERS c
    ON s.CUSTOMER_ID = c.CUSTOMER_ID;

---------------------------------------------------
--- Do all orders belong to real customers?
SELECT
    COUNT(*) AS TOTAL_ORDERS,
    COUNT_IF(c.CUSTOMER_ID IS NULL) AS ORPHAN_ORDERS,
    ROUND(
        100.0 * COUNT_IF(c.CUSTOMER_ID IS NULL) / COUNT(*),
        2
    ) AS ORPHAN_ORDER_PCT
FROM product_analytics.raw_events.ORDERS o
LEFT JOIN product_analytics.raw_events.CUSTOMERS c
    ON o.CUSTOMER_ID = c.CUSTOMER_ID;

---------------------------------------------------
--- Do all order items belong to real orders?
SELECT
    COUNT(*) AS TOTAL_ORDER_ITEMS,
    COUNT_IF(o.ORDER_ID IS NULL) AS ORPHAN_ORDER_ITEMS,
    ROUND(
        100.0 * COUNT_IF(o.ORDER_ID IS NULL) / COUNT(*),
        2
    ) AS ORPHAN_ORDER_ITEM_PCT
FROM product_analytics.raw_events.ORDER_ITEMS oi
LEFT JOIN product_analytics.raw_events.ORDERS o
    ON oi.ORDER_ID = o.ORDER_ID;

---------------------------------------------------
--- Do purchased events correspond to actual orders?
SELECT
    COUNT(*) AS PURCHASE_EVENTS,
    COUNT(DISTINCT SESSION_ID) AS PURCHASE_SESSIONS
FROM product_analytics.raw_events.EVENTS
WHERE EVENT_TYPE = 'purchase';

SELECT
    COUNT(*) AS ORDERS,
    COUNT(DISTINCT CUSTOMER_ID) AS ORDERING_CUSTOMERS
FROM product_analytics.raw_events.ORDERS;

---------------------------------------------------
--- Compare purchase-event revenue with order revenue
SELECT
    SUM(AMOUNT_USD) AS PURCHASE_EVENT_REVENUE,
    COUNT(*) AS PURCHASE_EVENTS
FROM product_analytics.raw_events.EVENTS
WHERE EVENT_TYPE = 'purchase';

SELECT
    SUM(TOTAL_USD) AS ORDER_REVENUE,
    COUNT(*) AS ORDERS
FROM product_analytics.raw_events.ORDERS;

---------------------------------------------------
--- Check whether order totals match their line items
--- (comparing with subtotals since that's the revenue after discount)
WITH item_totals AS (
    SELECT
        ORDER_ID,
        SUM(LINE_TOTAL_USD) AS ITEMS_TOTAL
    FROM product_analytics.raw_events.ORDER_ITEMS
    GROUP BY ORDER_ID
)

SELECT
    COUNT(*) AS ORDERS_CHECKED,
    COUNT_IF(
        ABS(o.SUBTOTAL_USD - i.ITEMS_TOTAL) > 0.01
    ) AS MISMATCHED_ORDERS,
    ROUND(
        100.0 *
        COUNT_IF(
            ABS(o.SUBTOTAL_USD - i.ITEMS_TOTAL) > 0.01
        ) / COUNT(*),
        2
    ) AS MISMATCH_PCT,
    MAX(
        ABS(o.SUBTOTAL_USD - i.ITEMS_TOTAL)
    ) AS MAX_DIFFERENCE
FROM product_analytics.raw_events.ORDERS o
INNER JOIN item_totals i
    ON o.ORDER_ID = i.ORDER_ID;

---------------------------------------------------
--- Check quantities and prices in order items
--- i.e CREATEheck if quantity × unit_price = line_total
SELECT
    COUNT(*) AS ITEMS_CHECKED,
    COUNT_IF(
        ABS(
            QUANTITY * UNIT_PRICE_USD - LINE_TOTAL_USD
        ) > 0.01
    ) AS PRICE_MISMATCHES
FROM product_analytics.raw_events.ORDER_ITEMS;

---------------------------------------------------
--- Check orders before signup

SELECT
    COUNT(*) AS ORDERS_BEFORE_SIGNUP
FROM product_analytics.raw_events.ORDERS o
INNER JOIN product_analytics.raw_events.CUSTOMERS c
    ON o.CUSTOMER_ID = c.CUSTOMER_ID
WHERE DATE(o.ORDER_TIME) < c.SIGNUP_DATE;


---------------------------------------------------
--- Orders before the customer's first session
WITH first_session AS (
    SELECT
        CUSTOMER_ID,
        MIN(START_TIME) AS FIRST_SESSION_TIME
    FROM product_analytics.raw_events.SESSIONS
    GROUP BY CUSTOMER_ID
)

SELECT
    COUNT(*) AS ORDERS_BEFORE_FIRST_SESSION
FROM product_analytics.raw_events.ORDERS o
INNER JOIN first_session fs
    ON o.CUSTOMER_ID = fs.CUSTOMER_ID
WHERE DATE(o.ORDER_TIME) < CAST(fs.FIRST_SESSION_TIME AS DATE);


---------------------------------------------------
--- Purchase events before signup 
SELECT
    COUNT(*) AS PURCHASES_BEFORE_SIGNUP
FROM product_analytics.raw_events.EVENTS e
INNER JOIN product_analytics.raw_events.SESSIONS s
    ON e.SESSION_ID = s.SESSION_ID
INNER JOIN product_analytics.raw_events.CUSTOMERS c
    ON s.CUSTOMER_ID = c.CUSTOMER_ID
WHERE e.EVENT_TYPE = 'purchase'
  AND CAST(e.TIMESTAMP AS DATE) < c.SIGNUP_DATE;


---------------------------------------------------
--- Customers whose first order predates their first recorded session.
SELECT
    o.CUSTOMER_ID,
    MIN(DATE(o.ORDER_TIME)) AS FIRST_ORDER_TIME,
    MIN(DATE(s.START_TIME)) AS FIRST_SESSION_DATE
FROM product_analytics.raw_events.ORDERS o
LEFT JOIN product_analytics.raw_events.SESSIONS s
    ON o.CUSTOMER_ID = s.CUSTOMER_ID
GROUP BY o.CUSTOMER_ID
HAVING MIN(DATE(o.ORDER_TIME)) < MIN(DATE(s.START_TIME))
ORDER BY FIRST_ORDER_TIME;

---------------------------------------------------
--- first order → first purchase event
WITH first_dates AS (
    SELECT
        c.CUSTOMER_ID,
        MIN(DATE(o.ORDER_TIME)) AS FIRST_ORDER_DATE,
        MIN(
            CASE
                WHEN e.EVENT_TYPE = 'purchase'
                THEN e.TIMESTAMP::DATE
            END
        ) AS FIRST_PURCHASE_EVENT_DATE
    FROM product_analytics.raw_events.CUSTOMERS_RAW c
    LEFT JOIN product_analytics.raw_events.ORDERS o
        ON c.CUSTOMER_ID = o.CUSTOMER_ID
    LEFT JOIN product_analytics.raw_events.SESSIONS s
        ON c.CUSTOMER_ID = s.CUSTOMER_ID
    LEFT JOIN product_analytics.raw_events.EVENTS e
        ON s.SESSION_ID = e.SESSION_ID
    GROUP BY c.CUSTOMER_ID
)

SELECT
    COUNT(*) AS CUSTOMERS_WITH_BOTH,
    COUNT_IF(
        FIRST_ORDER_DATE < FIRST_PURCHASE_EVENT_DATE
    ) AS ORDER_BEFORE_PURCHASE_EVENT,
    COUNT_IF(
        FIRST_PURCHASE_EVENT_DATE < FIRST_ORDER_DATE
    ) AS PURCHASE_EVENT_BEFORE_ORDER
FROM first_dates
WHERE FIRST_ORDER_DATE IS NOT NULL
  AND FIRST_PURCHASE_EVENT_DATE IS NOT NULL;

--- I remediated an integrity issue in the synthetic source data 
--- by creating the cleaned customers table as below.

--- First backup the customers ----------------
CREATE OR REPLACE TABLE product_analytics.raw_events.CUSTOMERS_RAW AS
SELECT *
FROM product_analytics.raw_events.CUSTOMERS;

--- Calculate each customer's first activity ----------------
CREATE OR REPLACE TEMPORARY TABLE product_analytics.analytics.CUSTOMER_FIRST_ACTIVITY AS

WITH customer_dates AS (
    SELECT
        c.CUSTOMER_ID,
        MIN(s.START_TIME)::DATE AS FIRST_SESSION_DATE,
        MIN(e.TIMESTAMP)::DATE AS FIRST_EVENT_DATE,
        MIN(o.ORDER_TIME)::DATE AS FIRST_ORDER_DATE
    FROM product_analytics.raw_events.CUSTOMERS_RAW c
    LEFT JOIN product_analytics.raw_events.SESSIONS s
        ON c.CUSTOMER_ID = s.CUSTOMER_ID
    LEFT JOIN product_analytics.raw_events.EVENTS e
        ON s.SESSION_ID = e.SESSION_ID
    LEFT JOIN product_analytics.raw_events.ORDERS o
        ON c.CUSTOMER_ID = o.CUSTOMER_ID
    GROUP BY c.CUSTOMER_ID
)

SELECT
    CUSTOMER_ID,
    LEAST(
        COALESCE(FIRST_SESSION_DATE, '9999-12-31'::DATE),
        COALESCE(FIRST_EVENT_DATE, '9999-12-31'::DATE),
        COALESCE(FIRST_ORDER_DATE, '9999-12-31'::DATE)
    ) AS FIRST_KNOWN_ACTIVITY
FROM customer_dates;

--- Create a signup date before their first known activity
CREATE OR REPLACE TEMPORARY TABLE product_analytics.analytics.CUSTOMER_SIGNUP_LAGS AS
SELECT
    CUSTOMER_ID,
    FIRST_KNOWN_ACTIVITY,
    CASE
        WHEN RANDOM_PERCENT <= 35
            THEN UNIFORM(0, 3, RANDOM())
        WHEN RANDOM_PERCENT <= 70
            THEN UNIFORM(4, 7, RANDOM())
        WHEN RANDOM_PERCENT <= 90
            THEN UNIFORM(8, 14, RANDOM())
        WHEN RANDOM_PERCENT <= 98
            THEN UNIFORM(15, 30, RANDOM())
        ELSE
            UNIFORM(31, 60, RANDOM())
    END AS SIGNUP_LAG_DAYS
FROM (
    SELECT
        CUSTOMER_ID,
        FIRST_KNOWN_ACTIVITY,
        UNIFORM(1, 100, RANDOM()) AS RANDOM_PERCENT
    FROM product_analytics.analytics.CUSTOMER_FIRST_ACTIVITY
    WHERE FIRST_KNOWN_ACTIVITY <> '9999-12-31'::DATE
);

--- Create corrected customers ----------------
CREATE OR REPLACE TABLE product_analytics.raw_events.CUSTOMERS_CLEAN AS

SELECT
    c.CUSTOMER_ID,
    c.NAME,
    c.EMAIL,
    c.COUNTRY,
    c.AGE,
    c.MARKETING_OPT_IN,
    CASE
        -- No activity at all:
        -- preserve original signup date
        WHEN sl.FIRST_KNOWN_ACTIVITY IS NULL
            THEN c.SIGNUP_DATE
        -- Existing signup date is valid:
        -- preserve it
        WHEN c.SIGNUP_DATE <= sl.FIRST_KNOWN_ACTIVITY
            THEN c.SIGNUP_DATE
        -- Invalid signup date:
        -- generate a realistic date before first activity
        ELSE DATEADD(
            'day',
            -sl.SIGNUP_LAG_DAYS,
            sl.FIRST_KNOWN_ACTIVITY
        )
    END AS SIGNUP_DATE
FROM product_analytics.raw_events.CUSTOMERS_RAW c
LEFT JOIN product_analytics.analytics.CUSTOMER_SIGNUP_LAGS sl
    ON c.CUSTOMER_ID = sl.CUSTOMER_ID;


--- QA the result
SELECT
    COUNT(*) AS CUSTOMERS_WITH_ACTIVITY,
    COUNT_IF(
        c.SIGNUP_DATE > a.FIRST_KNOWN_ACTIVITY
    ) AS INVALID_SIGNUPS
FROM product_analytics.raw_events.CUSTOMERS_CLEAN c
INNER JOIN product_analytics.analytics.CUSTOMER_FIRST_ACTIVITY a
    ON c.CUSTOMER_ID = a.CUSTOMER_ID
WHERE a.FIRST_KNOWN_ACTIVITY <> '9999-12-31'::DATE;


--- How many dates actually changed
SELECT
    COUNT(*) AS TOTAL_CUSTOMERS,
    COUNT_IF(
        c.SIGNUP_DATE <> r.SIGNUP_DATE
    ) AS CHANGED_SIGNUPS,
    ROUND(
        100.0 * COUNT_IF(
            c.SIGNUP_DATE <> r.SIGNUP_DATE
        ) / COUNT(*),
        2
    ) AS CHANGED_PCT
FROM product_analytics.raw_events.CUSTOMERS_CLEAN c
JOIN product_analytics.raw_events.CUSTOMERS_RAW r
    ON c.CUSTOMER_ID = r.CUSTOMER_ID;

