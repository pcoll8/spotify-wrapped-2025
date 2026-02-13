import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import close_db_pool, init_db_pool
from wrapped_summary import SUMMARY_YEAR, get_wrapped_summary


@asynccontextmanager
async def lifespan(app_instance):
    try:
        init_db_pool()
        app_instance.state.db_pool_error = None
    except Exception as exc:
        app_instance.state.db_pool_error = str(exc)

    yield

    close_db_pool()


app = FastAPI(title="Spotify Wrapped 2025", lifespan=lifespan)
app.state.db_pool_error = None

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def _get_cached_summary():
    startup_error = getattr(app.state, "db_pool_error", None)
    if startup_error:
        try:
            init_db_pool()
            app.state.db_pool_error = None
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Database unavailable. {exc}",
            )

    try:
        summary = get_wrapped_summary(SUMMARY_YEAR)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Verify DATABASE_URL and that PostgreSQL is running.",
        )

    if not summary:
        raise HTTPException(
            status_code=503,
            detail="Wrapped summary for 2025 is missing. Run `python backend/loader.py` to load data and refresh the summary cache.",
        )

    return summary


@app.get("/")
async def read_root():
    return {
        "message": "Spotify Wrapped 2025 API is running. Visit /api/v2/wrapped or /static/index.html."
    }


@app.get("/api/v2/wrapped")
def get_wrapped_v2():
    return _get_cached_summary()


@app.get("/api/stats/top-tracks")
def get_top_tracks():
    summary = _get_cached_summary()
    return summary.get("top_tracks", [])


@app.get("/api/stats/top-podcasts")
def get_top_podcasts():
    summary = _get_cached_summary()
    return summary.get("top_podcasts", [])


@app.get("/api/stats/total-time")
def get_total_time():
    summary = _get_cached_summary()
    hours = summary.get("total_time", {}).get("hours", 0)
    return {"total_hours_played_2025": hours}


@app.get("/api/stats/top-artist")
def get_top_artist():
    summary = _get_cached_summary()
    return summary.get("top_artist", {})


@app.get("/api/stats/active-hour")
def get_active_hour():
    summary = _get_cached_summary()
    return summary.get("active_hour", {})


@app.get("/api/stats/top-days")
def get_top_days():
    summary = _get_cached_summary()
    return summary.get("top_days", [])


@app.get("/api/stats/listening-periods")
def get_listening_periods():
    summary = _get_cached_summary()
    return summary.get("listening_periods", [])


@app.get("/api/stats/most-played")
def get_most_played():
    summary = _get_cached_summary()
    return summary.get("most_played", {})


@app.get("/api/stats/skips")
def get_skips():
    summary = _get_cached_summary()
    return summary.get("skips", [])
