import json
from datetime import datetime

from database import execute_query

SUMMARY_YEAR = 2025

REFRESH_WRAPPED_SUMMARY_SQL = """
WITH base AS (
    SELECT *
    FROM PRS.SPOTIFY_EVENTS_2025
    WHERE EXTRACT(YEAR FROM end_time) = %s
),
total_time AS (
    SELECT COALESCE(ROUND(SUM(ms_played) / 3600000.0, 2), 0)::double precision AS hours
    FROM base
),
top_artist AS (
    SELECT
        artist_name,
        ROUND(SUM(ms_played) / 3600000.0, 2)::double precision AS total_hours_played
    FROM base
    WHERE artist_name IS NOT NULL
    GROUP BY artist_name
    ORDER BY total_hours_played DESC
    LIMIT 1
),
active_hour AS (
    SELECT
        EXTRACT(HOUR FROM end_time)::int AS hour,
        ROUND(SUM(ms_played) / 60000.0, 2)::double precision AS total_minutes_played
    FROM base
    GROUP BY EXTRACT(HOUR FROM end_time)
    ORDER BY total_minutes_played DESC
    LIMIT 1
),
top_tracks AS (
    SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.total_minutes_played DESC), '[]'::jsonb) AS items
    FROM (
        SELECT
            artist_name,
            track_name,
            ROUND(SUM(ms_played) / 60000.0, 2)::double precision AS total_minutes_played,
            ROUND(SUM(ms_played) / 3600000.0, 2)::double precision AS total_hours_played
        FROM base
        WHERE track_name IS NOT NULL
        GROUP BY artist_name, track_name
        ORDER BY total_minutes_played DESC
        LIMIT 5
    ) t
),
top_podcasts AS (
    SELECT COALESCE(jsonb_agg(to_jsonb(p) ORDER BY p.total_minutes_played DESC), '[]'::jsonb) AS items
    FROM (
        SELECT
            episode_show_name,
            episode_name,
            ROUND(SUM(ms_played) / 60000.0, 2)::double precision AS total_minutes_played,
            ROUND(SUM(ms_played) / 3600000.0, 2)::double precision AS total_hours_played
        FROM base
        WHERE episode_name IS NOT NULL
        GROUP BY episode_show_name, episode_name
        ORDER BY total_minutes_played DESC
        LIMIT 5
    ) p
),
listening_periods AS (
    SELECT COALESCE(jsonb_agg(to_jsonb(lp) ORDER BY lp.total_minutes_played DESC), '[]'::jsonb) AS items
    FROM (
        SELECT
            CASE
                WHEN EXTRACT(HOUR FROM end_time) BETWEEN 5 AND 11 THEN 'Morning'
                WHEN EXTRACT(HOUR FROM end_time) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN EXTRACT(HOUR FROM end_time) BETWEEN 18 AND 22 THEN 'Evening'
                ELSE 'Night'
            END AS period,
            ROUND(SUM(ms_played) / 60000.0, 2)::double precision AS total_minutes_played
        FROM base
        GROUP BY 1
        ORDER BY 2 DESC
    ) lp
),
top_days AS (
    SELECT COALESCE(jsonb_agg(to_jsonb(d) ORDER BY d.total_minutes_played DESC), '[]'::jsonb) AS items
    FROM (
        SELECT
            TO_CHAR(DATE(end_time), 'YYYY-MM-DD') AS day,
            TRIM(TO_CHAR(end_time, 'Day')) AS day_of_week,
            TRIM(TO_CHAR(end_time, 'Month')) AS month,
            ROUND(SUM(ms_played) / 60000.0, 2)::double precision AS total_minutes_played
        FROM base
        GROUP BY DATE(end_time), TRIM(TO_CHAR(end_time, 'Day')), TRIM(TO_CHAR(end_time, 'Month'))
        ORDER BY total_minutes_played DESC
        LIMIT 5
    ) d
),
most_played AS (
    SELECT
        track_name,
        COUNT(*)::int AS play_count
    FROM base
    WHERE track_name IS NOT NULL
    GROUP BY track_name
    ORDER BY play_count DESC
    LIMIT 1
),
skips AS (
    SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.skips DESC), '[]'::jsonb) AS items
    FROM (
        SELECT
            track_name,
            COUNT(*)::int AS skips
        FROM base
        WHERE ms_played < 5000 AND track_name IS NOT NULL
        GROUP BY track_name
        ORDER BY skips DESC
        LIMIT 10
    ) s
)
INSERT INTO PRS.SPOTIFY_WRAPPED_2025_SUMMARY (year, generated_at, payload)
VALUES (
    %s,
    NOW(),
    jsonb_build_object(
        'total_time', jsonb_build_object('hours', (SELECT hours FROM total_time)),
        'top_artist', COALESCE((SELECT to_jsonb(a) FROM top_artist a), '{}'::jsonb),
        'active_hour', COALESCE((SELECT to_jsonb(h) FROM active_hour h), '{}'::jsonb),
        'top_tracks', (SELECT items FROM top_tracks),
        'top_podcasts', (SELECT items FROM top_podcasts),
        'listening_periods', (SELECT items FROM listening_periods),
        'top_days', (SELECT items FROM top_days),
        'most_played', COALESCE((SELECT to_jsonb(m) FROM most_played m), '{}'::jsonb),
        'skips', (SELECT items FROM skips)
    )
)
ON CONFLICT (year)
DO UPDATE
SET generated_at = EXCLUDED.generated_at,
    payload = EXCLUDED.payload
RETURNING year, generated_at, payload;
"""

GET_WRAPPED_SUMMARY_SQL = """
SELECT year, generated_at, payload
FROM PRS.SPOTIFY_WRAPPED_2025_SUMMARY
WHERE year = %s
LIMIT 1;
"""


def _normalize_payload(payload):
    if payload is None:
        return {}
    if isinstance(payload, str):
        return json.loads(payload)
    return payload


def _to_iso(ts):
    if isinstance(ts, datetime):
        return ts.isoformat()
    if ts is None:
        return None
    return str(ts)


def refresh_wrapped_summary(year=SUMMARY_YEAR):
    row = execute_query(REFRESH_WRAPPED_SUMMARY_SQL, (year, year), fetch="one")
    if not row:
        return None

    payload = _normalize_payload(row.get("payload"))
    return {
        "year": int(row["year"]),
        "generated_at": _to_iso(row.get("generated_at")),
        **payload,
    }


def get_wrapped_summary(year=SUMMARY_YEAR):
    row = execute_query(GET_WRAPPED_SUMMARY_SQL, (year,), fetch="one")
    if not row:
        return None

    payload = _normalize_payload(row.get("payload"))
    return {
        "year": int(row["year"]),
        "generated_at": _to_iso(row.get("generated_at")),
        **payload,
    }
