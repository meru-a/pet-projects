---Creating a complete view of the events 
CREATE OR REPLACE VIEW product_analytics.analytics.fct_events AS
SELECT
    e.event_id,
    s.customer_id,
    e.session_id,
    e.timestamp,
    DATE(e.timestamp) as event_date,
    e.event_type,
    e.product_id,
    s.start_time as session_start_date,
    s.device,
    s.source,
    s.country
FROM product_analytics.raw_events.events as e
JOIN product_analytics.raw_events.sessions as s
ON e.session_id = s.session_id;

--- Result head
select * from product_analytics.analytics.fct_events
LIMIT 10;

---Manual quick check to see if correct customers were joined
-- select session_id, customer_id 
-- from product_analytics.raw_events.sessions 
-- where session_id in (62174, 62175, 62176);
