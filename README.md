# Spotify Wrapped 2025 Web App

A local web application to analyze your Spotify streaming history for 2025.

## Prerequisites

- Python 3.8+
- PostgreSQL
- Your Spotify Data (Request from [Spotify Privacy](https://www.spotify.com/us/account/privacy/))

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Database Setup**:
    - Ensure PostgreSQL is running.
    - Create a database (e.g., `spotify_wrapped`).
    - Create a `.env` file in the `backend/` directory with your connection string:
        ```
        DATABASE_URL=postgresql://user:password@localhost:5432/spotify_wrapped
        ```
    - Run the schema script to create tables:
        ```bash
        psql -d spotify_wrapped -f schema.sql
        ```
        *(Or use any SQL client to execute the contents of `schema.sql`)*

3.  **Load Data**:
    - Place your Spotify JSON export files (e.g., `StreamingHistory0.json`, `endsong_0.json`) into the `data/` folder.
    - Run the loader script:
        ```bash
        cd backend
        python loader.py
        ```
    - This will load raw data and populate the `PRS.SPOTIFY_EVENTS_2025` table.

4.  **Run the App**:
    - Start the backend server:
        ```bash
        cd backend
        uvicorn main:app --reload
        ```
    - Open your browser and go to: [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

## Features

- **Total Time**: See total hours listened in 2025.
- **Top Artist**: Your #1 artist by listening time.
- **Top Tracks**: Top 5 tracks by duration.
- **Active Hour**: The hour of the day you listen the most.
- **Listening Periods**: Breakdown by Morning, Afternoon, Evening, Night.
- **Top Days**: Days with the most listening time.
- **Most Played**: Track with the highest play count.
- **Skips**: Tracks you skipped the most (played < 5s).

## Tech Stack

- **Backend**: FastAPI, Python, PostgreSQL
- **Frontend**: Vanilla HTML/CSS/JS
- **Design**: Custom Dark Mode
