from fastapi.testclient import TestClient

import main


def test_v2_wrapped_contract(monkeypatch, sample_summary):
    monkeypatch.setattr(main, "get_wrapped_summary", lambda year: sample_summary)

    with TestClient(main.app) as client:
        main.app.state.db_pool_error = None
        response = client.get("/api/v2/wrapped")

    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 2025
    assert payload["generated_at"]
    assert "total_time" in payload
    assert "top_artist" in payload
    assert "active_hour" in payload
    assert "top_tracks" in payload
    assert "top_podcasts" in payload
    assert "listening_periods" in payload
    assert "top_days" in payload
    assert "most_played" in payload
    assert "skips" in payload


def test_legacy_endpoints_project_from_v2(monkeypatch, sample_summary):
    monkeypatch.setattr(main, "get_wrapped_summary", lambda year: sample_summary)

    with TestClient(main.app) as client:
        main.app.state.db_pool_error = None
        v2_payload = client.get("/api/v2/wrapped").json()

        assert client.get("/api/stats/top-tracks").json() == v2_payload["top_tracks"]
        assert client.get("/api/stats/top-podcasts").json() == v2_payload["top_podcasts"]
        assert client.get("/api/stats/top-artist").json() == v2_payload["top_artist"]
        assert client.get("/api/stats/active-hour").json() == v2_payload["active_hour"]
        assert client.get("/api/stats/listening-periods").json() == v2_payload["listening_periods"]
        assert client.get("/api/stats/top-days").json() == v2_payload["top_days"]
        assert client.get("/api/stats/most-played").json() == v2_payload["most_played"]
        assert client.get("/api/stats/skips").json() == v2_payload["skips"]
        assert client.get("/api/stats/total-time").json() == {
            "total_hours_played_2025": v2_payload["total_time"]["hours"]
        }


def test_missing_summary_returns_503(monkeypatch):
    monkeypatch.setattr(main, "get_wrapped_summary", lambda year: None)

    with TestClient(main.app) as client:
        main.app.state.db_pool_error = None
        response = client.get("/api/v2/wrapped")

    assert response.status_code == 503
    assert "summary for 2025 is missing" in response.json()["detail"]


def test_database_error_returns_503(monkeypatch):
    def raise_db_error(_year):
        raise RuntimeError("Database down")

    monkeypatch.setattr(main, "get_wrapped_summary", raise_db_error)

    with TestClient(main.app) as client:
        main.app.state.db_pool_error = None
        response = client.get("/api/v2/wrapped")

    assert response.status_code == 503
    assert "Database unavailable" in response.json()["detail"]
