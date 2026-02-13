# Spotify Wrapped 2025 V2 Roadmap

## What Changed

1. Backend performance architecture was upgraded.
   - Added PostgreSQL connection pooling in `backend/database.py`.
   - Added cached summary service in `backend/wrapped_summary.py`.
   - Added new aggregated endpoint `GET /api/v2/wrapped` in `backend/main.py`.
   - Kept all legacy `GET /api/stats/*` endpoints, now served from cached payload projections.
   - Added clearer 503 error handling for database and missing-summary states.

2. Data loading pipeline was optimized.
   - Refactored `backend/loader.py` to batch insert with `execute_values`.
   - Preserved processing flow for `PRS.SPOTIFY_EVENTS_2025`.
   - Added automatic wrapped-summary refresh after load.

3. Database schema was extended for analytics speed and cache support.
   - Added indexes on `PRS.SPOTIFY_EVENTS_2025` in `schema.sql`.
   - Added `PRS.SPOTIFY_WRAPPED_2025_SUMMARY` table.
   - Added SQL routine `PRS.refresh_spotify_wrapped_2025_summary(target_year)` for cache refresh.

4. Frontend was redesigned with a new visual system.
   - Rebuilt layout and narrative sections in `frontend/index.html`.
   - Replaced styling with bold editorial direction in `frontend/style.css`.
   - Refactored `frontend/script.js` to make one request to `/api/v2/wrapped`.
   - Added Chart.js visualizations, GSAP entry animations, and robust loading/error/retry states.

5. Test and docs coverage were expanded.
   - Added API and summary tests in `tests/`.
   - Added `pytest.ini` marker configuration for integration tests.
   - Updated setup and API docs in `README.md`.

## How To Validate

1. Install dependencies.
   ```bash
   python -m pip install -r requirements.txt
   ```

2. Apply schema changes.
   ```bash
   psql -d <your_db_name> -f schema.sql
   ```

3. Load source data and refresh cache.
   ```bash
   cd backend
   python loader.py
   ```

4. Start the application.
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

5. Validate API endpoints manually.
   - Open `http://localhost:8000/api/v2/wrapped` and confirm payload contains:
     `year`, `generated_at`, `total_time`, `top_artist`, `active_hour`, `top_tracks`, `top_podcasts`, `listening_periods`, `top_days`, `most_played`, `skips`.
   - Open one or more legacy endpoints (for compatibility), for example:
     - `http://localhost:8000/api/stats/total-time`
     - `http://localhost:8000/api/stats/top-tracks`
     - `http://localhost:8000/api/stats/skips`

6. Validate automated tests.
   ```bash
   python -m pytest -q
   ```
   Expected: all unit tests pass; integration summary test is skipped unless `TEST_DATABASE_URL` is configured.

7. Validate integration test (optional, DB required).
   ```bash
   set TEST_DATABASE_URL=postgresql://user:password@localhost:5432/spotify_wrapped_test
   python -m pytest -m integration -q
   ```

8. Validate frontend behavior.
   - Open `http://localhost:8000/static/index.html`.
   - Confirm dashboard loads using one primary API call to `/api/v2/wrapped`.
   - Confirm charts render, lists populate, and retry button appears on errors.
   - Confirm responsive layout works on desktop and mobile widths.

## Next Steps

1. Run schema + loader in each target environment to initialize summary cache before first use.
2. Add CI pipeline step to run `python -m pytest -q` on every push/PR.
3. Add a scheduled refresh strategy for summary cache after new Spotify exports are added.
4. Add an operational smoke test that verifies `/api/v2/wrapped` returns a complete payload.
5. Add performance baseline tracking for:
   - loader runtime,
   - `/api/v2/wrapped` response time,
   - frontend first meaningful render time.
6. Plan a follow-up iteration to support year parameterization when multi-year Wrapped is needed.
