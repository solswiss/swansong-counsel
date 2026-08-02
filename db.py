import json
import os
import requests

from typing import List, Optional, Union
from supabase import create_client, Client
from pydantic import BaseModel, field_validator
from gallery import generate_track_lore

# Ensure credentials are set in environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


class TrackRecord(BaseModel):
    isrc: str
    mbid: str = ""
    recco_id: str = ""
    spotify_id: str = ""
    title: str
    artist: List[str]
    genre: List[str]
    year: int
    duration: int
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: float
    loudness: float
    mode: int
    speechiness: float
    tempo: float
    valence: float
    audio_vector: List[float] = []
    lore: str = ""
    times_offered: int = 0
    times_chosen: int = 0

    @field_validator("audio_vector", mode="before")
    @classmethod
    def parse_vector_string(cls, v: Union[str, List[float]]) -> List[float]:
        if isinstance(v, str):
            return json.loads(v)
        return v

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

class TrackDatabase:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def track_exists(self, isrc: str) -> bool:
        """Check if a track is already in the database."""
        response = self.supabase.table("tracks").select("isrc").eq("isrc", isrc).execute()
        return len(response.data) > 0

    def insert_track(self, track: TrackRecord) -> Optional[list[dict]]:
        """Insert a single track using Pydantic model dict export."""
        if self.track_exists(track.isrc):
            print(f"Track '{track.title}' ({track.isrc}) already exists. Skipping.")
            return None
        
        data = track.model_dump()
        response = self.supabase.table("tracks").insert(data).execute()
        return response.data

    def fetch_catalog(self) -> List[TrackRecord]:
        """Retrieve all tracks from the catalog."""
        response = self.supabase.table("tracks").select("*").execute()
        return [TrackRecord(**row) for row in response.data] # type: ignore
    
    def add_track(self, isrc: str):
        """Add new track by ISRC to catalog"""
        track_req = f"https://api.reccobeats.com/v1/track?ids={isrc}"
        headers = {
            'Accept':'application/json'
        }
        track_res = json.loads(requests.request("GET", track_req, headers=headers).text)["content"][0] #type: ignore
        recco_id = track_res["id"]

        detail_req = f"https://api.reccobeats.com/v1/track/{recco_id}/audio-features"
        detail_res = json.loads(requests.request("GET", detail_req, headers=headers).text) #type: ignore

        req = f"https://musicbrainz.org/ws/2/isrc/{isrc}?fmt=json"
        data = json.loads(requests.request("GET", req).text)["recordings"][0]
        mbid = data["id"]
        year = int(data["first-release-date"].split("-",1)[0])

        req = f"https://musicbrainz.org/ws/2/recording/{mbid}?inc=genres&fmt=json"
        data = json.loads(requests.request("GET", req).text)
        genres = []
        if data["genres"]:
            genres = [i.name for i in data["genres"]]

        data = track_res | detail_res
        track = TrackRecord(
            isrc=isrc,
            mbid=mbid,
            recco_id=recco_id,
            spotify_id=data["href"].rsplit("/",1)[1],
            title=data["trackTitle"],
            artist=[a["name"] for a in data["artists"]],
            genre=genres,
            year=year,
            duration=data["durationMs"],
            acousticness=data["acousticness"],
            danceability=data["danceability"],
            energy=data["energy"],
            instrumentalness=data["instrumentalness"],
            loudness=data["loudness"],
            mode=data["mode"],
            speechiness=data["speechiness"],
            tempo=data["tempo"],
            valence=data["valence"],
        )
        track.audio_vector = build_audio_vector(track)
        track.lore = generate_track_lore(
            track.title, 
            track.artist, 
            track.genre, 
            track.valence, 
            track.energy,
            track.acousticness,
            track.instrumentalness
        )
        
        print(track)

        if input("add to db? ") == "y":
            self.insert_track(track)