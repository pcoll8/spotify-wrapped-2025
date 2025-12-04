import os
import json
import glob
from datetime import datetime
from database import get_db_connection

DATA_DIR = "../data"

def load_json_files():
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    if not json_files:
        print("No JSON files found in data directory.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    print(f"Found {len(json_files)} JSON files. Starting load...")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Some exports are a list of objects, some might be different. Assuming list of objects.
                if not isinstance(data, list):
                    print(f"Skipping {file_path}: Expected a list of records.")
                    continue
                
                print(f"Loading {file_path} with {len(data)} records...")
                
                for record in data:
                    # Handle potential missing keys safely
                    cur.execute("""
                        INSERT INTO RAW.SPOTIFY_EVENTS (
                            end_time, artist_name, track_name, ms_played, album_name, 
                            context, platform, user_id, conn_country, ip_addr, 
                            spotify_track_uri, episode_name, episode_show_name, spotify_episode_uri,
                            audiobook_title, audiobook_uri, audiobook_chapter_uri, audiobook_chapter_title,
                            reason_start, reason_end, shuffle, skipped, offline, offline_timestamp, incognito_mode
                        ) VALUES (
                            %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        record.get("ts") or record.get("end_time"), # end_time
                        record.get("master_metadata_album_artist_name") or record.get("artist_name"), # artist_name
                        record.get("master_metadata_track_name") or record.get("track_name"), # track_name
                        record.get("ms_played", 0),
                        record.get("master_metadata_album_album_name") or record.get("album_name"),
                        record.get("conn_country"), # context (mapping might be loose, using country as placeholder or NULL if not exact match in JSON) -> Wait, 'context' usually refers to 'spotify_track_uri' context or similar. Let's map strictly what we have.
                        # Actually, let's look at standard Spotify export keys.
                        # 'ts', 'username', 'platform', 'ms_played', 'conn_country', 'ip_addr_decrypted', 'user_agent_decrypted', 
                        # 'master_metadata_track_name', 'master_metadata_album_artist_name', 'master_metadata_album_album_name', 
                        # 'spotify_track_uri', 'episode_name', 'episode_show_name', 'spotify_episode_uri', 'reason_start', 'reason_end', 'shuffle', 'skipped', 'offline', 'offline_timestamp', 'incognito_mode'
                        
                        # Re-mapping based on standard export structure:
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
                        str(record.get("offline_timestamp")),
                        record.get("incognito_mode")
                    ))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                conn.rollback()
                continue
            
            conn.commit()
    
    print("Raw data loaded successfully.")
    process_data(conn)
    conn.close()

def process_data(conn):
    print("Processing data for 2025...")
    cur = conn.cursor()
    
    # Clear existing 2025 data to avoid duplicates if re-run
    cur.execute("TRUNCATE TABLE PRS.SPOTIFY_EVENTS_2025")
    
    # Insert filtered data
    # Note: 'ts' in JSON is usually ISO 8601 string. Postgres can cast it to timestamp.
    # We filter for year 2025.
    cur.execute("""
        INSERT INTO PRS.SPOTIFY_EVENTS_2025 (end_time, artist_name, track_name, ms_played, episode_name, episode_show_name)
        SELECT 
            end_time, 
            artist_name, 
            track_name, 
            ms_played,
            episode_name,
            episode_show_name
        FROM RAW.SPOTIFY_EVENTS
        WHERE EXTRACT(YEAR FROM end_time) = 2025
          AND ms_played > 0
          AND (track_name IS NOT NULL OR episode_name IS NOT NULL)
    """)
    
    conn.commit()
    print("Data processed and populated into PRS.SPOTIFY_EVENTS_2025.")

if __name__ == "__main__":
    load_json_files()
