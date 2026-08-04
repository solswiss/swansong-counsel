import requests
import statistics
import datetime

from typing import Any
from google import genai

from models import TrackRecord


client = genai.Client()

def generate_track_lore(title: str, artist: list[str], genre: list[str], valence: float, energy: float, acousticness: float, instrumentalness: float) -> str | None:
    """Generate the lore clue for a track."""
    prompt = f"""
    You are the narrative architect for an estate. 
    Your task is to write a single-sentence description of a room inspired by a track's audio profile.
    In this estate, a room is any distinct space; this includes interiors, exteriors, underground, etc.
    Focus on 2 or 3 prominent, distinct, and/or contrasting sensory anchors, including architecture, furnishings, sound, smell, etc..
    Capture the room's unique essence through a combination of story, emotion, or grounding descriptors you judge most suitable.

    Track Attributes:
    - Title: "{title}" by {", ".join(artist)}
    - Genres: {", ".join(genre)}
    - Mood/Valence: {valence} (Scale: 0.0 = dark/somber/grief, 1.0 = bright/serene/triumphant)
    - Energy: Energy={energy} (0.0=still/empty, 1.0=crowded/aesthetically loud)
    - Texture: Acousticness={acousticness} (0-1 scale; high=organic/natural, low=synthetic/glass/metal), Instrumentalness={instrumentalness} (0-1 scale; high=wordless/ambient, low=vocal/echoing)

    Constraints:
    1. TENSE: Present tense only.
    2. LENGTH: Maximum 16 words. Make deliberate wording choices.
    3. VOICE: Third-person declarative. No fluff, double adjectives, or purple prose.
    4. ZERO MUSIC TERMS: Translate audio profile purely into physical architecture, light, materials, and atmosphere.
    
    Generate the single-sentence lore snippet:
    """
    return client.interactions.create(
        model="gemini-2.5-flash",
        input=prompt
    ).output_text


def search_youtube(isrc: str, title: str, artist: str, api_key: str) -> str | None:
    """Search for a Youtube video corresponding to a track first by 
    ISRC then by title and artist"""
    res = search_youtube_by_isrc(isrc, api_key)
    if res:
        return res
    return search_youtube_by_query(title, artist, api_key)

def search_youtube_by_isrc(isrc: str, api_key: str) -> str | None:
    """Finds YouTube Video ID using the track's ISRC code."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params: dict[str, Any] = {
        "part": "snippet",
        "q": isrc,  # Searching directly by ISRC code
        "type": "video",
        "videoCategoryId": "10",  # Category 10 = Music
        "maxResults": 1,
        "key": api_key
    }
    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if items:
        return items[0]["id"]["videoId"]

    #TODO: remove comment
    print("X search_youtube_by_isrc")
    return None

def search_youtube_by_query(title: str, artist: str, api_key: str) -> str | None:
    """Finds official YouTube Music topic track for a song."""
    # Appending 'Topic' targets official YouTube Music uploads
    query = f"{artist} {title} Topic"
    url = "https://www.googleapis.com/youtube/v3/search"
    params: dict[str, Any] = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",
        "maxResults": 1,
        "key": api_key
    }
    response = requests.get(url, params=params).json()
    items = response.get("items", [])
    if items:
        return items[0]["id"]["videoId"]

    #TODO: remove comment
    print("X search_youtube_by_query")
    return None

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

def build_estate_title(tracks: list[TrackRecord]):
    """Final title for a floorplan based on its attributes"""
    acousticness = statistics.mean(t.acousticness for t in tracks)

    danceability = statistics.mean(t.danceability for t in tracks)

    energy_list = [t.energy for t in tracks]
    energy = statistics.mean(energy_list)
    energy_variance = statistics.variance(energy_list)

    instrumentalness = statistics.mean(t.instrumentalness for t in tracks)

    loudness = statistics.mean(t.loudness for t in tracks)

    speechiness = statistics.mean(t.speechiness for t in tracks)

    tempo_list = [t.tempo for t in tracks]
    tempo = statistics.mean(tempo_list)
    tempo_variance = statistics.variance(tempo_list)
    
    valence = statistics.mean(t.valence for t in tracks)

    duration = statistics.mean(t.duration for t in tracks)

    year_list = [t.year for t in tracks]
    year = statistics.mean(year_list)
    year_variance = statistics.variance(year_list)

    prefix = ""
    if duration > 8*60000:
        prefix = "Endless"
    elif duration < 2*60000:
        prefix = "Endless"
    elif tempo_variance > 2000:
        prefix = "Marching"
    elif year_variance < 15:
        prefix = "Temporal"
    elif year_variance > 150:
        prefix = "Generational"
    elif year < datetime.date.today().year - 80:
        prefix = "Venerable"
    elif year > datetime.date.today().year - 1:
        prefix = "Young"
    elif energy_variance > .1:
        prefix = "Mercurial"
    

    #TODO: map genre to titles etc
    title = "Bungalow"
    size = len(tracks)
    if size > 10:
        title = "Chateau"
    elif size > 6:
        title = "Manor"
    elif size > 3:
        title = "Villa"
    elif size > 1:
        title = "Cottage"
    elif energy < .5 and loudness < .3 and acousticness > .6:
        title = "Inn"
    elif energy < .55 and loudness < .3:
        title = "Hotel"
    elif instrumentalness > .6 or energy > .6:
        title = "Concert Hall"
    
    
    suffix = ""
    if danceability > .4 and valence > .6:
        suffix = "of Celebration"
    elif tempo < 65:
        suffix = "of Leisure"
    elif speechiness > .15:
        suffix = "of Speech"

    if prefix != "":
        title = prefix + " " + title
    if suffix != "":
        title += " " + suffix
    return title