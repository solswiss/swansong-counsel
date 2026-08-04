import json
import os
import random
import requests

from typing import Optional, Any
from supabase import create_client, Client
from helper import generate_track_lore, search_youtube, build_audio_vector
from models import TrackRecord, TrackTile

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY", "")


class TrackDatabase:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_track(self, isrc: str):
        """Return a track by ISRC from the database."""
        response = self.supabase.table("tracks").select("*").eq("isrc", isrc).execute()
        if response.count != 0:
            return response.data[0]
        return None

    def get_track_tile(self, isrc: str):
        track = self.get_track(isrc)
        if track is None:
            return None
        return TrackTile.model_validate(track)

    def get_track_record(self, isrc: str):
        track = self.get_track(isrc)
        if track is None:
            return None
        return TrackRecord.model_validate(track)

    def get_audio_vector(self, isrc: str):
        track = self.get_track(isrc)
        if track is None:
            return None
        return track["audio_vector"]
    
    def track_exists(self, isrc: str) -> bool:
        response = self.supabase.table("tracks").select("isrc").eq("isrc", isrc).execute()
        return response.count > 0 if response.count is not None else len(response.data) > 0    

    def inc_times_offered(self, isrc: str):
        self.supabase.rpc("increment_times_offered", {"target_isrc": isrc}).execute()

    def inc_times_chosen(self, isrc: str):
        self.supabase.rpc("increment_times_chosen", {"target_isrc": isrc}).execute()

    def insert_track(self, track: TrackRecord) -> Optional[list[dict[str, Any]]]:
        """Insert a single track using Pydantic model dict export."""
        if self.track_exists(track.isrc):
            print(f"Track '{track.title}' ({track.isrc}) already exists. Skipping.")
            return None
        
        data = track.model_dump()
        response = self.supabase.table("tracks").insert(data).execute()
        return response.data #type: ignore

    def fetch_tracks(self, isrc_list: list[str]) -> list[TrackRecord]:
        """Retrieve all tracks with matching ISRC from the catalog."""
        response = self.supabase.table("tracks").select("*").in_("isrc", isrc_list)
        return [TrackRecord(**row) for row in response.data] # type: ignore
    
    def fetch_catalog(self) -> list[TrackRecord]:
        """Retrieve all tracks from the catalog."""
        response = self.supabase.table("tracks").select("*").execute()
        return [TrackRecord(**row) for row in response.data] # type: ignore
    
    def create_track(self, isrc: str):
        """Add new track by ISRC to catalog."""
        if self.track_exists(isrc):
            raise Exception("Track already exists.")

        try:
            track_req = f"https://api.reccobeats.com/v1/track?ids={isrc}"
            headers = {
                'Accept':'application/json'
            }
            try:
                track_res = json.loads(requests.request("GET", track_req, headers=headers).text)["content"][0] #type: ignore
                recco_id = track_res["id"]
            except:
                raise Exception("Track not found by Reccobeats")
            
            try:
                detail_req = f"https://api.reccobeats.com/v1/track/{recco_id}/audio-features"
                detail_res = json.loads(requests.request("GET", detail_req, headers=headers).text) #type: ignore
            except:
               raise Exception("Track detail not found by Reccobeats")

            try:
                req = f"https://musicbrainz.org/ws/2/isrc/{isrc}?fmt=json"
                data = json.loads(requests.request("GET", req).text)["recordings"][0]
                mbid = data["id"]
                year = int(data["first-release-date"].split("-",1)[0])
            except:
                raise Exception("Track (ISRC) not found by MusicBrainz")
            
            try:
                req = f"https://musicbrainz.org/ws/2/recording/{mbid}?inc=genres&fmt=json"
                data = json.loads(requests.request("GET", req).text)
                genres = [i["name"] for i in data["genres"]] or []
            except:
                raise Exception("Track (MBID) not found by MusicBrainz")

            data = track_res | detail_res
            
            try:
                youtube = search_youtube(isrc, data["trackTitle"], data["artists"][0]["name"], YOUTUBE_KEY)
            except:
                raise Exception("Track not found by YouTube")

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
                youtube_id=youtube
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

            print("Adding track ",track.isrc)
            if self.insert_track(track) is None:
                return None
            return TrackTile.model_validate(track.model_dump())
        finally:pass
        
    def query_twin(self, vector: list[float], exclude_ids: list[str] = [], limit: int = 5) -> list[str]:
        res = self.supabase.rpc("match_twin", {"query_embedding": vector, "exclude_ids": exclude_ids, "match_count": limit}).execute()
        if res.data is None:
            return []
        candidates = [row["isrc"] for row in res.data]
        return random.sample(candidates, min(len(candidates), limit))

    def query_cross(self, energy: float, exclude_ids: list[str] = [], limit: int = 5) -> list[str]:
        res = self.supabase.rpc("match_cross", {"target_energy": energy, "exclude_ids": exclude_ids, "match_count": limit}).execute()
        if res.data is None:
            return []
        candidates = [row["isrc"] for row in res.data]
        return random.sample(candidates, min(len(candidates), limit))

    def query_farmer(self, acousticness: float, instrumentalness: float, exclude_ids: list[str] = [], limit: int = 5) -> list[str]:
        res = self.supabase.rpc("match_farmer", {"target_acousticness": acousticness, "target_instrumentalness": instrumentalness, "exclude_ids": exclude_ids, "match_count": limit}).execute()
        if res.data is None:
            return []
        candidates = [row["isrc"] for row in res.data]
        return random.sample(candidates, min(len(candidates), limit))

    def query_sail(self, exclude_genres: list[str], tempo: float, valence: float, exclude_ids: list[str] = [], limit: int = 5) -> list[str]:
        res = self.supabase.rpc("match_sail", {"exclude_genres": exclude_genres, "target_tempo": tempo, "target_valence": valence, "exclude_ids": exclude_ids, "match_count": limit}).execute()
        if res.data is None:
            return []
        candidates = [row["isrc"] for row in res.data]
        return random.sample(candidates, min(len(candidates), limit))

    def query_diamondus(self, vector: list[float], exclude_ids: list[str] = [], limit: int = 5) -> list[str]:
        res = self.supabase.rpc("match_diamondus", {"query_embedding": vector, "exclude_ids": exclude_ids, "match_count": limit}).execute()
        if res.data is None:
            return []
        candidates = [row["isrc"] for row in res.data]
        return random.sample(candidates, min(len(candidates), limit))