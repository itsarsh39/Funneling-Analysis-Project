-- ==============================================================================
-- Transformation: Window-Based Sessionization & Event Sequencing
-- Dialect: ANSI SQL / SQLite / PostgreSQL / BigQuery Compatible
-- Purpose:
--   1. Sequence events per user using ROW_NUMBER() and LAG().
--   2. Compute elapsed time (seconds) between consecutive funnel interactions.
--   3. Detect user bounces (sessions ending after a single step).
--   4. Attribute final drop-off stage for every user session.
-- ==============================================================================

WITH ordered_events AS (
    SELECT 
        event_id,
        session_id,
        user_id,
        stage_order,
        funnel_stage,
        event_timestamp,
        latency_ms,
        -- Sequence number of interaction within the session
        ROW_NUMBER() OVER (
            PARTITION BY user_id, session_id 
            ORDER BY stage_order ASC, event_timestamp ASC
        ) AS step_sequence_num,
        -- Total steps completed in this session
        COUNT(*) OVER (
            PARTITION BY user_id, session_id
        ) AS session_total_steps,
        -- Previous event timestamp to compute inter-event duration
        LAG(event_timestamp) OVER (
            PARTITION BY user_id, session_id 
            ORDER BY stage_order ASC, event_timestamp ASC
        ) AS prev_event_timestamp,
        -- Next stage name to identify step progression
        LEAD(funnel_stage) OVER (
            PARTITION BY user_id, session_id 
            ORDER BY stage_order ASC, event_timestamp ASC
        ) AS next_funnel_stage
    FROM fct_events
),
session_transitions AS (
    SELECT 
        oe.event_id,
        oe.session_id,
        oe.user_id,
        u.variant,
        u.device_type,
        oe.stage_order,
        oe.funnel_stage,
        oe.step_sequence_num,
        oe.session_total_steps,
        oe.event_timestamp,
        oe.prev_event_timestamp,
        -- Elapsed seconds since preceding event (handling SQLite datetime arithmetic)
        ROUND((JULIANDAY(oe.event_timestamp) - JULIANDAY(oe.prev_event_timestamp)) * 86400, 1) AS seconds_since_prev_step,
        oe.next_funnel_stage,
        -- Flag if this is the final interaction before drop-off
        CASE WHEN oe.next_funnel_stage IS NULL THEN 1 ELSE 0 END AS is_drop_off_point,
        -- Flag single-page bounce
        CASE WHEN oe.session_total_steps = 1 THEN 1 ELSE 0 END AS is_single_step_bounce,
        -- Flag successful terminal purchase
        CASE WHEN oe.funnel_stage = 'purchase' THEN 1 ELSE 0 END AS is_completed_purchase
    FROM ordered_events oe
    JOIN dim_users u ON oe.user_id = u.user_id
)
SELECT 
    session_id,
    user_id,
    variant,
    device_type,
    stage_order,
    funnel_stage,
    step_sequence_num,
    session_total_steps,
    event_timestamp,
    seconds_since_prev_step,
    is_drop_off_point,
    is_single_step_bounce,
    is_completed_purchase
FROM session_transitions
ORDER BY user_id ASC, stage_order ASC
LIMIT 100;
