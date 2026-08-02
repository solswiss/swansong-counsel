from db import TrackDatabase, TrackRecord
#from gallery import build_audio_vector

def build_audio_vector(track: TrackRecord) -> list[float]:
    """Normalize tempo/loudness and construct 9-D vector array."""
    tempo_norm = min(max(track.tempo / 200.0, 0.0), 1.0)
    loudness_norm = min(max((track.loudness + 60.0) / 60.0, 0.0), 1.0)
    
    return [
        float(track.valence),
        float(track.energy),
        tempo_norm,
        float(track.danceability),
        float(track.acousticness),
        float(track.instrumentalness),
        float(track.speechiness),
        loudness_norm,
        float(track.mode)
    ]

SEED_TRACKS = [
    TrackRecord(
        id="4cOdK2wGLETKBW3PvgPWqT",
        title="Midnight City",
        composer=["Anthony Gonzalez", "Morgan Kibby", "Justin Meldal-Johnsen"],
        artist=["M83"],
        genre=["synthwave"],
        year=2011,
        acousticness=0.00008,
        danceability=0.52,
        energy=0.78,
        instrumentalness=0.00003,
        loudness=-5.3,
        mode=1,
        speechiness=0.035,
        tempo=105.0,
        valence=0.47,
        lore="A glass gallery suspended above a sleeping city, bathed in constant indigo neon."
    ),
    TrackRecord(
        id="0VjIjW4GlUZAMYd2vXMi3b",
        title="Blinding Lights",
        composer=["The Weeknd", "Max Martin", "Oscar Holter", "Belly", "DaHeala"],
        artist=["The Weeknd"],
        genre=["synthpop"],
        year=2019,
        acousticness=0.001,
        danceability=0.51,
        energy=0.73,
        instrumentalness=0.0,
        loudness=-5.9,
        mode=1,
        speechiness=0.06,
        tempo=171.0,
        valence=0.33,
        lore="A deserted arcade where static echoes off forgotten copper coins."
    ),
    TrackRecord(
        id="3y6I9p7UeInb7R8j4a3S3L",
        title="Clair de Lune",
        composer=["Claude Debussy"],
        artist=["Claude Debussy"],
        genre=["classical"],
        year=1890,
        acousticness=0.98,
        danceability=0.31,
        energy=0.05,
        instrumentalness=0.92,
        loudness=-23.1,
        mode=1,
        speechiness=0.04,
        tempo=65.0,
        valence=0.08,
        lore="An abandoned conservatory where moonlight filters through cracked stained glass onto damp velvet."
    ),
    TrackRecord(
        id="7A6L2xH3I4f3C0f135g3pM",
        title="Take Five",
        composer=["Paul Desmond"],
        artist=["The Dave Brubeck Quartet"],
        genre=["jazz"],
        year=1959,
        acousticness=0.53,
        danceability=0.45,
        energy=0.26,
        instrumentalness=0.61,
        loudness=-16.8,
        mode=0,
        speechiness=0.04,
        tempo=174.0,
        valence=0.60,
        lore="A dim lounge behind a hidden door, smelling of old leather, cedarwood, and quiet laughter."
    ),
    TrackRecord(
        id="0e8B38mXgVfE4s238F6k2P",
        title="Resonance",
        composer=["HOME"],
        artist=["HOME"],
        genre=["chillwave"],
        year=2014,
        acousticness=0.02,
        danceability=0.68,
        energy=0.59,
        instrumentalness=0.88,
        loudness=-8.2,
        mode=1,
        speechiness=0.03,
        tempo=85.0,
        valence=0.24,
        lore="A subterranean archive housing tape reels that endlessly spin without sound."
    )
]

def seed_database():
    db = TrackDatabase()
    print("Seeding Supabase catalog...")
    for track in SEED_TRACKS:
        track.audio_vector = build_audio_vector(track)
        print(track.audio_vector)
        db.insert_track(track)
    print("Seeded titles:")
    cat = db.fetch_catalog()
    for track in cat:
        print(track.title)

seed_database()
