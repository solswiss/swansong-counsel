import requests
from typing import Any
from typing import List
from google import genai

from models import TrackRecord


client = genai.Client()

def generate_track_lore(title: str, artist: List[str], genre: List[str], valence: float, energy: float, acousticness: float, instrumentalness: float) -> str | None:
    """Generate the lore clue for a track."""
    prompt = f"""
    You are the narrative architect for an estate. Your task is to write a single-sentence description of a room inspired by a track's audio profile.

    Track Attributes:
    - Title: "{title}" by {", ".join(artist)}
    - Genres: {", ".join(genre)}
    - Mood/Valence: {valence} (Scale: 0.0 = dark/somber/grief, 1.0 = bright/serene/triumphant)
    - Energy: Energy={energy} (0.0=still/empty, 1.0=crowded/aesthetically loud)
    - Texture: Acousticness={acousticness} (0-1 scale; high=organic/natural, low=synthetic/glass/metal), Instrumentalness={instrumentalness} (0-1 scale; high=wordless/ambient, low=vocal/echoing)

    Spatial Concept:
    In this estate, a "room" is any distinct space. This includes indoor chambers and passages, subterranean vaults, open-air grounds, etc..

    Grammar & Tone Constraints:
    1. TENSE: Present tense only.
    2. LENGTH: Maximum 16 words. Make deliberate wording choices.
    3. VOICE: Third-person declarative. No fluff, double adjectives, or purple prose.
    4. ZERO MUSIC TERMS: Translate audio profile purely into physical architecture, light, materials, and atmosphere.
    
    Focus on 2 or 3 prominent, distinct, and/or contrasting sensory anchors to distill an image and find the room's essence through story or grounding descriptors.

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