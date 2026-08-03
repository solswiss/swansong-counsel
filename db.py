import json
import os
import requests

from typing import List, Optional, Any
from supabase import create_client, Client
from helper import generate_track_lore, search_youtube, build_audio_vector
from models import TrackRecord

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY", "")


class TrackDatabase:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_track(self, isrc: str) -> TrackRecord | None:
        """Return a track by ISRC from the database."""
        response = self.supabase.table("tracks").select("*").eq("isrc", isrc).execute()
        if response.count != 0:
            print(response.data)
            return None #return TrackRecord.model_validate_json(response.model_dump_json())
        return None

    def track_exists(self, isrc: str) -> bool:
        response = self.supabase.table("tracks").select("isrc").eq("isrc", isrc).execute()
        return response.count > 0 if response.count is not None else len(response.data) > 0    

    def insert_track(self, track: TrackRecord) -> Optional[list[dict[str, Any]]]:
        """Insert a single track using Pydantic model dict export."""
        if self.track_exists(track.isrc):
            print(f"Track '{track.title}' ({track.isrc}) already exists. Skipping.")
            return None
        
        data = track.model_dump()
        response = self.supabase.table("tracks").insert(data).execute()
        return response.data #type: ignore

    def fetch_catalog(self) -> List[TrackRecord]:
        """Retrieve all tracks from the catalog."""
        response = self.supabase.table("tracks").select("*").execute()
        return [TrackRecord(**row) for row in response.data] # type: ignore
    
    def add_track(self, isrc: str):
        """Add new track by ISRC to catalog."""
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
            youtube_id=search_youtube(isrc, data["trackTitle"], data["artist"][0], YOUTUBE_KEY)
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
        ) or "Mystery"

        print("Adding track\n",track)
        if self.insert_track(track) is None:
            return -1
