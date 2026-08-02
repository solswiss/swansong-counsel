import json
import os
from typing import List, Optional, Union
from supabase import create_client, Client
from pydantic import BaseModel, field_validator

# Ensure credentials are set in environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


class TrackRecord(BaseModel):
    id: str
    title: str
    composer: List[str]
    artist: List[str]
    genre: List[str]
    year: int
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
    lore: str
    times_offered: int = 0
    times_chosen: int = 0

    @field_validator("audio_vector", mode="before")
    @classmethod
    def parse_vector_string(cls, v: Union[str, List[float]]) -> List[float]:
        if isinstance(v, str):
            return json.loads(v)
        return v

class TrackDatabase:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def track_exists(self, spotify_id: str) -> bool:
        """Check if a Spotify track is already in the database."""
        response = self.supabase.from_("tracks").select("id").eq("id", spotify_id).execute()
        return len(response.data) > 0

    def insert_track(self, track: TrackRecord) -> Optional[list[dict]]:
        """Insert a single track using Pydantic model dict export."""
        if self.track_exists(track.id):
            print(f"Track '{track.title}' ({track.id}) already exists. Skipping.")
            return None
        
        data = track.model_dump()
        response = self.supabase.from_("tracks").insert(data).execute()
        return response.data

    def fetch_catalog(self) -> List[TrackRecord]:
        """Retrieve all tracks from the catalog."""
        response = self.supabase.table("tracks").select("*").execute()
        return [TrackRecord(**row) for row in response.data] # type: ignore