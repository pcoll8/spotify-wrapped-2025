# Spotify Wrapped 2025 (V2)

A local Spotify Wrapped web app with:
- A cached summary API (`/api/v2/wrapped`) for fast frontend loading.
- Batched loader ingestion for better data import performance.
- A redesigned editorial frontend using one API request, Chart.js, and GSAP.

## Prerequisites

- Python 3.8+
- PostgreSQL
- Spotify export JSON files (request from [Spotify Privacy](https://www.spotify.com/us/account/privacy/))

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure database:
   - Ensure PostgreSQL is running.
   - Create a database (example: `spotify_wrapped`).
   - Create `backend/.env`:
     ```env
     DATABASE_URL=postgresql://user:password@localhost:5432/spotify_wrapped
     ```

3. Apply schema:
   ```bash
   psql -d spotify_wrapped -f schema.sql
   ```
   This creates:
   - `RAW.SPOTIFY_EVENTS`
   - `PRS.SPOTIFY_EVENTS_2025`
   - `PRS.SPOTIFY_WRAPPED_2025_SUMMARY`
   - Indexes and SQL refresh function: `PRS.refresh_spotify_wrapped_2025_summary(...)`

4. Load data and build summary cache:
   - Place Spotify JSON files in `data/`.
   - Run:
     ```bash
     cd backend
     python loader.py
     ```
   The loader will:
   - Batch insert into `RAW.SPOTIFY_EVENTS`
   - Rebuild `PRS.SPOTIFY_EVENTS_2025`
   - Refresh `PRS.SPOTIFY_WRAPPED_2025_SUMMARY` for year 2025

5. Start API + frontend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   Open: [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

## API

### V2 endpoint (primary)

`GET /api/v2/wrapped`

Response shape:
- `year`
- `generated_at`
- `total_time`
- `top_artist`
- `active_hour`
- `top_tracks`
- `top_podcasts`
- `listening_periods`
- `top_days`
- `most_played`
- `skips`

### Legacy compatibility endpoints

The existing `/api/stats/*` routes are still available and now read from the cached summary payload:
- `/api/stats/total-time`
- `/api/stats/top-artist`
- `/api/stats/top-tracks`
- `/api/stats/top-podcasts`
- `/api/stats/active-hour`
- `/api/stats/listening-periods`
- `/api/stats/top-days`
- `/api/stats/most-played`
- `/api/stats/skips`

## Manual summary refresh (optional)

If needed, refresh summary cache directly in SQL:
```sql
SELECT PRS.refresh_spotify_wrapped_2025_summary(2025);
```

## Frontend notes

- The UI is still static HTML/CSS/JS (no framework migration).
- Chart rendering uses CDN Chart.js.
- Motion uses CDN GSAP.
- The page fetches only one endpoint on load: `/api/v2/wrapped`.

## Tests

- Run unit tests:
  ```bash
  python -m pytest -q
  ```
- Integration summary test requires `TEST_DATABASE_URL`:
  ```bash
  set TEST_DATABASE_URL=postgresql://user:password@localhost:5432/spotify_wrapped_test
  python -m pytest -m integration -q
  ```
