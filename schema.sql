-- Create schemas
CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS PRS;

-- =========================
-- RAW DATA TABLE
-- =========================
DROP TABLE IF EXISTS RAW.SPOTIFY_EVENTS;
CREATE TABLE RAW.SPOTIFY_EVENTS (
    id SERIAL PRIMARY KEY,
    end_time TIMESTAMP NOT NULL,
    artist_name TEXT,
    track_name TEXT,
    ms_played INTEGER NOT NULL,
    album_name TEXT,
    context TEXT,
    platform TEXT,
    user_id TEXT,
    conn_country TEXT,
    ip_addr TEXT,
    spotify_track_uri TEXT,
    episode_name TEXT,
    episode_show_name TEXT,
    spotify_episode_uri TEXT,
    audiobook_title TEXT,
    audiobook_uri TEXT,
    audiobook_chapter_uri TEXT,
    audiobook_chapter_title TEXT,
    reason_start TEXT,
    reason_end TEXT,
    shuffle BOOLEAN,
    skipped BOOLEAN,
    offline BOOLEAN,
    offline_timestamp TEXT,
    incognito_mode BOOLEAN
);

-- =========================
-- PROCESSED 2025 DATA TABLE
-- =========================
DROP TABLE IF EXISTS PRS.SPOTIFY_EVENTS_2025;
CREATE TABLE PRS.SPOTIFY_EVENTS_2025 (
    id SERIAL PRIMARY KEY,
    end_time TIMESTAMP NOT NULL,
    artist_name TEXT,
    track_name TEXT,
    ms_played INTEGER,
    episode_name TEXT,
    episode_show_name TEXT
);

CREATE INDEX IF NOT EXISTS idx_prs_events_2025_end_time
    ON PRS.SPOTIFY_EVENTS_2025 (end_time);

CREATE INDEX IF NOT EXISTS idx_prs_events_2025_artist_name
    ON PRS.SPOTIFY_EVENTS_2025 (artist_name)
    WHERE artist_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_prs_events_2025_track_name
    ON PRS.SPOTIFY_EVENTS_2025 (track_name)
    WHERE track_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_prs_events_2025_episode_name
    ON PRS.SPOTIFY_EVENTS_2025 (episode_name)
    WHERE episode_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_prs_events_2025_ms_played_skips
    ON PRS.SPOTIFY_EVENTS_2025 (ms_played)
    WHERE ms_played < 5000;

-- =========================
-- CACHED WRAPPED SUMMARY
-- =========================
DROP TABLE IF EXISTS PRS.SPOTIFY_WRAPPED_2025_SUMMARY;
CREATE TABLE PRS.SPOTIFY_WRAPPED_2025_SUMMARY (
    year SMALLINT PRIMARY KEY,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE OR REPLACE FUNCTION PRS.refresh_spotify_wrapped_2025_summary(target_year SMALLINT DEFAULT 2025)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    WITH base AS (
        SELECT *
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE EXTRACT(YEAR FROM end_time) = target_year
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
        target_year,
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
        payload = EXCLUDED.payload;
END;
$$;
