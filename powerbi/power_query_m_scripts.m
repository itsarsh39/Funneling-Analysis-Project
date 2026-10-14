// ==============================================================================
// POWER QUERY (M) INGESTION SCRIPTS
// Project: E-Commerce Funnel A/B Testing & Experimentation Case Study
// Description: Paste these scripts into the Advanced Editor of Power Query in Power BI Desktop
//              to load and cleanse the Star Schema tables directly from data/*.csv.
// ==============================================================================

// ------------------------------------------------------------------------------
// Query 1: dim_users
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\Users\WIN\Downloads\Funneling Analysis Project\data\dim_users.csv"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"user_id", type text},
        {"variant", type text},
        {"device_type", type text},
        {"browser", type text},
        {"traffic_source", type text},
        {"country", type text},
        {"first_seen_at", type datetime}
    })
in
    #"Changed Type"

// ------------------------------------------------------------------------------
// Query 2: dim_funnel_stages
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\Users\WIN\Downloads\Funneling Analysis Project\data\dim_funnel_stages.csv"), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"stage_order", Int64.Type},
        {"stage_name", type text},
        {"stage_category", type text},
        {"is_conversion_step", Int64.Type}
    })
in
    #"Changed Type"

// ------------------------------------------------------------------------------
// Query 3: dim_date
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\Users\WIN\Downloads\Funneling Analysis Project\data\dim_date.csv"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"date_id", Int64.Type},
        {"date", type date},
        {"experiment_day", Int64.Type},
        {"day_of_week", Int64.Type},
        {"day_name", type text},
        {"is_weekend", Int64.Type},
        {"window_period", type text}
    })
in
    #"Changed Type"

// ------------------------------------------------------------------------------
// Query 4: fct_events
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\Users\WIN\Downloads\Funneling Analysis Project\data\fct_events.csv"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"event_id", Int64.Type},
        {"session_id", type text},
        {"user_id", type text},
        {"stage_order", Int64.Type},
        {"funnel_stage", type text},
        {"date_id", Int64.Type},
        {"event_timestamp", type datetime},
        {"latency_ms", Int64.Type}
    })
in
    #"Changed Type"

// ------------------------------------------------------------------------------
// Query 5: fct_orders
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("C:\Users\WIN\Downloads\Funneling Analysis Project\data\fct_orders.csv"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", type text},
        {"user_id", type text},
        {"session_id", type text},
        {"date_id", Int64.Type},
        {"order_timestamp", type datetime},
        {"revenue_usd", Currency.Type},
        {"items_count", Int64.Type},
        {"payment_method", type text},
        {"payment_status", type text}
    })
in
    #"Changed Type"
