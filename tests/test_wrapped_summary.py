import os
from datetime import datetime

import psycopg2
import pytest
from psycopg2.extras import RealDictCursor

import wrapped_summary


def test_get_wrapped_summary_normalizes_payload(monkeypatch):
    row = {
        "year": 2025,
        "generated_at": datetime(2026, 2, 12, 8, 45, 0),
        "payload": '{"top_artist":{"artist_name":"Artist A"},"total_time":{"hours":12}}',
    }

    monkeypatch.setattr(wrapped_summary, "execute_query", lambda *_args, **_kwargs: row)
    result = wrapped_summary.get_wrapped_summary(2025)

    assert result["year"] == 2025
    assert result["generated_at"] == "2026-02-12T08:45:00"
    assert result["top_artist"]["artist_name"] == "Artist A"
    assert result["total_time"]["hours"] == 12


def test_refresh_wrapped_summary_returns_none_when_query_returns_none(monkeypatch):
    monkeypatch.setattr(wrapped_summary, "execute_query", lambda *_args, **_kwargs: None)
    result = wrapped_summary.refresh_wrapped_summary(2025)
    assert result is None


@pytest.mark.integration
def test_refresh_wrapped_summary_generates_expected_payload(monkeypatch):
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run integration summary test.")

    conn = psycopg2.connect(test_database_url)

    try:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS PRS")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS PRS.SPOTIFY_EVENTS_2025 (
                    id SERIAL PRIMARY KEY,
                    end_time TIMESTAMP NOT NULL,
                    artist_name TEXT,
                    track_name TEXT,
                    ms_played INTEGER,
                    episode_name TEXT,
                    episode_show_name TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS PRS.SPOTIFY_WRAPPED_2025_SUMMARY (
                    year SMALLINT PRIMARY KEY,
                    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    payload JSONB NOT NULL
                )
                """
            )
            cur.execute("TRUNCATE TABLE PRS.SPOTIFY_EVENTS_2025")
            cur.execute("TRUNCATE TABLE PRS.SPOTIFY_WRAPPED_2025_SUMMARY")
            cur.execute(
                """
                INSERT INTO PRS.SPOTIFY_EVENTS_2025 (end_time, artist_name, track_name, ms_played, episode_name, episode_show_name)
                VALUES
                    ('2025-01-01 08:10:00', 'Artist A', 'Song 1', 180000, NULL, NULL),
                    ('2025-01-01 08:40:00', 'Artist A', 'Song 1', 120000, NULL, NULL),
                    ('2025-01-01 09:00:00', 'Artist C', 'Song Skip', 3000, NULL, NULL),
                    ('2025-01-01 14:20:00', NULL, NULL, 240000, 'Podcast Episode', 'Podcast Show'),
                    ('2025-01-01 20:00:00', 'Artist B', 'Song 2', 60000, NULL, NULL)
                """
            )
        conn.commit()

        def run_query(query, params=None, fetch=False):
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = None
                if fetch == "one":
                    result = cur.fetchone()
                elif fetch:
                    result = cur.fetchall()
                conn.commit()
                return result

        monkeypatch.setattr(wrapped_summary, "execute_query", run_query)
        summary = wrapped_summary.refresh_wrapped_summary(2025)

        assert summary["year"] == 2025
        assert summary["total_time"]["hours"] == pytest.approx(0.17, abs=0.01)
        assert summary["top_artist"]["artist_name"] == "Artist A"
        assert summary["most_played"]["track_name"] == "Song 1"
        assert summary["most_played"]["play_count"] == 2
        assert summary["active_hour"]["hour"] == 8
        assert summary["skips"][0]["track_name"] == "Song Skip"
    finally:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE PRS.SPOTIFY_EVENTS_2025")
            cur.execute("TRUNCATE TABLE PRS.SPOTIFY_WRAPPED_2025_SUMMARY")
        conn.commit()
        conn.close()
