import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def sample_summary():
    return {
        "year": 2025,
        "generated_at": "2026-02-12T12:00:00",
        "total_time": {"hours": 321.5},
        "top_artist": {"artist_name": "Rosalia", "total_hours_played": 48.2},
        "active_hour": {"hour": 22, "total_minutes_played": 780.0},
        "top_tracks": [
            {
                "artist_name": "Rosalia",
                "track_name": "SAOKO",
                "total_minutes_played": 190.0,
                "total_hours_played": 3.17,
            }
        ],
        "top_podcasts": [
            {
                "episode_show_name": "Daily Mix",
                "episode_name": "Episode 10",
                "total_minutes_played": 120.0,
                "total_hours_played": 2.0,
            }
        ],
        "listening_periods": [
            {"period": "Night", "total_minutes_played": 200.0},
            {"period": "Evening", "total_minutes_played": 150.0},
        ],
        "top_days": [
            {
                "day": "2025-07-14",
                "day_of_week": "Monday",
                "month": "July",
                "total_minutes_played": 260.0,
            }
        ],
        "most_played": {"track_name": "SAOKO", "play_count": 42},
        "skips": [{"track_name": "Track X", "skips": 5}],
    }
