import json
import random
from datetime import datetime, timedelta
import uuid

# Configuración
NUM_RECORDS = 500
OUTPUT_FILE = "../data/spotify_events.json"

# Datos de muestra para aleatoriedad
ARTISTS = [
    ("Bad Bunny", "Un Verano Sin Ti"),
    ("Taylor Swift", "Midnights"),
    ("The Weeknd", "Starboy"),
    ("Rosalía", "MOTOMAMI"),
    ("Arctic Monkeys", "AM"),
    ("Quevedo", "Donde quiero estar"),
    ("Dua Lipa", "Future Nostalgia"),
    ("Harry Styles", "Harry's House")
]

TRACKS = {
    "Bad Bunny": ["Moscow Mule", "Tití Me Preguntó", "Ojitos Lindos", "Efecto"],
    "Taylor Swift": ["Anti-Hero", "Lavender Haze", "Karma", "Midnight Rain"],
    "The Weeknd": ["Starboy", "I Feel It Coming", "Die For You", "Reminder"],
    "Rosalía": ["SAOKO", "CANDY", "BIZCOCHITO", "DESPECHÁ"],
    "Arctic Monkeys": ["Do I Wanna Know?", "R U Mine?", "Arabella", "505"],
    "Quevedo": ["Ahora qué", "Yankee", "Vista al mar", "Punto G"],
    "Dua Lipa": ["Levitating", "Don't Start Now", "Physical", "Break My Heart"],
    "Harry Styles": ["As It Was", "Late Night Talking", "Matilda", "Cinema"]
}

PODCASTS = [
    ("The Joe Rogan Experience", "Joe Rogan"),
    ("TED Talks Daily", "TED"),
    ("The Daily", "The New York Times"),
    ("Wild Project", "Jordi Wild")
]

PLATFORMS = ["iOS 16.0 (iPhone)", "Android OS 12", "Windows 10 (10.0.19041)", "OS X 13.0.0"]
COUNTRIES = ["ES", "MX", "US", "AR", "CO", "GB"]
REASONS_START = ["trackdone", "clickrow", "appload", "playbtn", "remote"]
REASONS_END = ["trackdone", "fwdbtn", "backbtn", "endplay", "logout", "unexpected-exit"]

def generate_record(index):
    # Decidir si es canción (85%), podcast (10%) o audiobook (5%)
    content_type = random.choices(["music", "podcast", "audiobook"], weights=[85, 10, 5])[0]
    
    end_time = datetime.now() - timedelta(minutes=random.randint(0, 10000))
    ms_played = random.randint(1000, 300000)
    user_id = "user_" + str(random.randint(100, 105)) # Simular pocos usuarios
    platform = random.choice(PLATFORMS)
    country = random.choice(COUNTRIES)
    shuffle = random.choice([True, False])
    skipped = ms_played < 30000 and random.choice([True, False])
    offline = random.choice([True, False])
    
    record = {
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ms_played": ms_played,
        "user_id": user_id,
        "platform": platform,
        "conn_country": country,
        "ip_addr": f"192.168.1.{random.randint(1, 255)}",
        "reason_start": random.choice(REASONS_START),
        "reason_end": random.choice(REASONS_END),
        "shuffle": shuffle,
        "skipped": skipped,
        "offline": offline,
        "offline_timestamp": str(int(end_time.timestamp() * 1000)) if offline else None,
        "incognito_mode": random.choice([True, False]),
        
        # Inicializar campos nulos
        "artist_name": None, "track_name": None, "album_name": None, 
        "spotify_track_uri": None, "episode_name": None, "episode_show_name": None,
        "spotify_episode_uri": None, "audiobook_title": None, "audiobook_uri": None,
        "audiobook_chapter_uri": None, "audiobook_chapter_title": None,
        "context": None
    }

    if content_type == "music":
        artist, album = random.choice(ARTISTS)
        track = random.choice(TRACKS[artist])
        record["artist_name"] = artist
        record["track_name"] = track
        record["album_name"] = album
        record["spotify_track_uri"] = f"spotify:track:{uuid.uuid4().hex[:22]}"
        record["context"] = f"spotify:album:{uuid.uuid4().hex[:22]}"
        
    elif content_type == "podcast":
        show, publisher = random.choice(PODCASTS)
        record["episode_show_name"] = show
        record["episode_name"] = f"Episode #{random.randint(1, 500)}: Guest {random.choice(['A', 'B', 'C'])}"
        record["spotify_episode_uri"] = f"spotify:episode:{uuid.uuid4().hex[:22]}"
        record["context"] = f"spotify:show:{uuid.uuid4().hex[:22]}"

    elif content_type == "audiobook":
        record["audiobook_title"] = "Harry Potter and the Sorcerer's Stone"
        record["audiobook_uri"] = f"spotify:audiobook:{uuid.uuid4().hex[:22]}"
        record["audiobook_chapter_title"] = f"Chapter {random.randint(1, 10)}"
        record["audiobook_chapter_uri"] = f"spotify:chapter:{uuid.uuid4().hex[:22]}"

    return record

# Generar lista
data = [generate_record(i) for i in range(NUM_RECORDS)]

# Escribir archivo
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=None, separators=(',', ':')) # Formato compacto pero válido

print(f"Archivo '{OUTPUT_FILE}' generado exitosamente con {NUM_RECORDS} registros.")