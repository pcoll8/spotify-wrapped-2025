import glob
import json
import os

from psycopg2.extras import execute_values

from database import get_db_connection
from wrapped_summary import SUMMARY_YEAR, refresh_wrapped_summary

DATA_DIR = "../data"
BATCH_SIZE = 1000
RAW_INSERT_SQL = """
    INSERT INTO RAW.SPOTIFY_EVENTS (
        end_time, artist_name, track_name, ms_played, album_name,
        context, platform, user_id, conn_country, ip_addr,
        spotify_track_uri, episode_name, episode_show_name, spotify_episode_uri,
        audiobook_title, audiobook_uri, audiobook_chapter_uri, audiobook_chapter_title,
        reason_start, reason_end, shuffle, skipped, offline, offline_timestamp, incognito_mode
    ) VALUES %s
"""


def _chunked(values, chunk_size):
    for start in range(0, len(values), chunk_size):
        yield values[start:start + chunk_size]


def _map_record(record):
    offline_timestamp = record.get("offline_timestamp")

    return (
        record.get("ts") or record.get("end_time"),
        record.get("master_metadata_album_artist_name") or record.get("artist_name"),
        record.get("master_metadata_track_name") or record.get("track_name"),
        record.get("ms_played", 0),
        record.get("master_metadata_album_album_name") or record.get("album_name"),
        record.get("context"),
        record.get("platform"),
        record.get("username") or record.get("user_id"),
        record.get("conn_country"),
        record.get("ip_addr_decrypted") or record.get("ip_addr"),
        record.get("spotify_track_uri"),
        record.get("episode_name"),
        record.get("episode_show_name"),
        record.get("spotify_episode_uri"),
        record.get("audiobook_title"),
        record.get("audiobook_uri"),
        record.get("audiobook_chapter_uri"),
        record.get("audiobook_chapter_title"),
        record.get("reason_start"),
        record.get("reason_end"),
        record.get("shuffle"),
        record.get("skipped"),
        record.get("offline"),
        str(offline_timestamp) if offline_timestamp is not None else None,
        record.get("incognito_mode"),
    )


def _load_file_records(file_path):
    with open(file_path, "r", encoding="utf-8") as file_obj:
        data = json.load(file_obj)
        if not isinstance(data, list):
            raise ValueError("Expected file content to be a JSON list of records.")
        return [_map_record(record) for record in data]


def load_json_files():
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    if not json_files:
        print("No JSON files found in data directory.")
        return

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            print(f"Found {len(json_files)} JSON files. Starting load...")
            cur.execute("TRUNCATE TABLE RAW.SPOTIFY_EVENTS")

            for file_path in json_files:
                try:
                    records = _load_file_records(file_path)
                except Exception as exc:
                    print(f"Skipping {file_path}: {exc}")
                    continue

                if not records:
                    print(f"Skipping {file_path}: no records found.")
                    continue

                print(f"Loading {file_path} with {len(records)} records...")
                for batch in _chunked(records, BATCH_SIZE):
                    execute_values(cur, RAW_INSERT_SQL, batch, page_size=BATCH_SIZE)
                conn.commit()

        print("Raw data loaded successfully.")
        process_data(conn)
    finally:
        conn.close()

    summary = refresh_wrapped_summary(SUMMARY_YEAR)
    if summary:
        print(f"Summary cache refreshed for {summary['year']} at {summary['generated_at']}.")


def process_data(conn):
    print(f"Processing data for {SUMMARY_YEAR}...")

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE PRS.SPOTIFY_EVENTS_2025")

        cur.execute(
            """
            INSERT INTO PRS.SPOTIFY_EVENTS_2025 (end_time, artist_name, track_name, ms_played, episode_name, episode_show_name)
            SELECT
                end_time,
                artist_name,
                track_name,
                ms_played,
                episode_name,
                episode_show_name
            FROM RAW.SPOTIFY_EVENTS
            WHERE EXTRACT(YEAR FROM end_time) = %s
              AND ms_played > 0
              AND (track_name IS NOT NULL OR episode_name IS NOT NULL)
            """,
            (SUMMARY_YEAR,),
        )

    conn.commit()
    print("Data processed and populated into PRS.SPOTIFY_EVENTS_2025.")


if __name__ == "__main__":
    load_json_files()
