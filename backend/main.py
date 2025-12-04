from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import execute_query
import os

app = FastAPI(title="Spotify Wrapped 2025")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
# Assuming frontend files are in ../frontend relative to this file
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def read_root():
    return {"message": "Spotify Wrapped 2025 API is running. Go to /static/index.html to view the app."}

@app.get("/api/stats/top-tracks")
def get_top_tracks():
    query = """
        SELECT
            artist_name,
            track_name,
            SUM(ms_played)/60000 AS total_minutes_played,
            SUM(ms_played)/3600000 AS total_hours_played
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE track_name IS NOT NULL
        GROUP BY artist_name, track_name
        ORDER BY total_minutes_played DESC
        LIMIT 5;
    """
    return execute_query(query, fetch=True)

@app.get("/api/stats/top-podcasts")
def get_top_podcasts():
    query = """
        SELECT
            episode_show_name,
            episode_name,
            SUM(ms_played)/60000 AS total_minutes_played,
            SUM(ms_played)/3600000 AS total_hours_played
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE episode_name IS NOT NULL
        GROUP BY episode_show_name, episode_name
        ORDER BY total_minutes_played DESC
        LIMIT 5;
    """
    return execute_query(query, fetch=True)

@app.get("/api/stats/total-time")
def get_total_time():
    query = """
        SELECT
            SUM(ms_played)/3600000 AS total_hours_played_2025
        FROM PRS.SPOTIFY_EVENTS_2025;
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {"total_hours_played_2025": 0}

@app.get("/api/stats/top-artist")
def get_top_artist():
    query = """
        SELECT
            artist_name,
            SUM(ms_played)/3600000 AS total_hours_played
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE artist_name IS NOT NULL
        GROUP BY artist_name
        ORDER BY total_hours_played DESC
        LIMIT 1;
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {}

@app.get("/api/stats/active-hour")
def get_active_hour():
    query = """
        SELECT
            EXTRACT(HOUR FROM end_time) AS hour,
            SUM(ms_played)/60000 AS total_minutes_played
        FROM PRS.SPOTIFY_EVENTS_2025
        GROUP BY hour
        ORDER BY total_minutes_played DESC
        LIMIT 1;
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {}

@app.get("/api/stats/top-days")
def get_top_days():
    query = """
        SELECT
            DATE(end_time) AS day,
            TO_CHAR(end_time, 'Day') AS day_of_week,
            TO_CHAR(end_time, 'Month') AS month,
            SUM(ms_played) / 60000 AS total_minutes_played
        FROM PRS.SPOTIFY_EVENTS_2025
        GROUP BY DATE(end_time), TO_CHAR(end_time, 'Day'), TO_CHAR(end_time, 'Month') 
        ORDER BY total_minutes_played DESC
        LIMIT 5;
    """
    return execute_query(query, fetch=True)

@app.get("/api/stats/listening-periods")
def get_listening_periods():
    query = """
        SELECT CASE 
             WHEN EXTRACT(HOUR FROM end_time) BETWEEN 5 AND 11 THEN 'Morning'
             WHEN EXTRACT(HOUR FROM end_time) BETWEEN 12 AND 17 THEN 'Afternoon'
             WHEN EXTRACT(HOUR FROM end_time) BETWEEN 18 AND 22 THEN 'Evening'
             ELSE 'Night'
           END AS period,
           SUM(ms_played)/60000 AS total_minutes_played
        FROM PRS.SPOTIFY_EVENTS_2025
        GROUP BY period
        ORDER BY total_minutes_played DESC;
    """
    return execute_query(query, fetch=True)

@app.get("/api/stats/most-played")
def get_most_played():
    query = """
        SELECT
            track_name,
            COUNT(*) AS play_count
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE track_name IS NOT NULL
        GROUP BY track_name
        ORDER BY play_count DESC
        LIMIT 1;
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else {}

@app.get("/api/stats/skips")
def get_skips():
    query = """
        SELECT
            track_name,
            COUNT(*) AS skips
        FROM PRS.SPOTIFY_EVENTS_2025
        WHERE ms_played < 5000 AND track_name IS NOT NULL
        GROUP BY track_name
        ORDER BY skips DESC
        LIMIT 10;
    """
    return execute_query(query, fetch=True)
