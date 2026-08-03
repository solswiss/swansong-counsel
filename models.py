import json

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Union


class TrackRecord(BaseModel):
    isrc: str = "demo"
    mbid: str = "demo"
    recco_id: str = "demo"
    spotify_id: str = "demo"
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
    youtube_id: str | None = None
    times_offered: int = 0
    times_chosen: int = 0

    @field_validator("audio_vector", mode="before")
    @classmethod
    def parse_vector_string(cls, v: Union[str, List[float]]) -> List[float]:
        if isinstance(v, str):
            return json.loads(v)
        return v


Strategy = Literal[
    "Twin",
    "Cross",
    "Farmer",
    "Sail",
    "Diamondus"
]

class TrackTile(BaseModel):
    isrc: str
    title: str
    artist: List[str]
    genre: List[str]
    lore: str
    youtube_id: str | None
    observation: Strategy = Field(..., description="The Recommendation Strategy for this song.")

# class T(BaseModel):
#     isrc: str
#     title: str
#     artist: List[str]
#     genre: List[str]
#     year: datetime
#     acousticness: float
#     danceability: float
#     energy: float
#     instrumentalness: float
#     loudness: float = Field(..., description="The overall loudness of a track in decibels (dB). Values typical range between -60 and 0 db.")
#     mode: int = Field(..., description="Mode indicates the modality (major or minor) of a track. Major is represented by 1 and minor is 0.")
#     speechiness: float = Field(..., ge=0.0, le=1.0, description="0=No speech, 1=Exclusively speech")
#     tempo: float
#     valence: float = Field(..., ge=0.0, le=1.0, description="0=Dark/Sad, 1=Bright/Happy")
#     observation: Strategy = Field(..., description="The Recommendation Strategy for this song.")
#     lore: str = Field(..., description="Write a 1-sentence atmospheric description for a room based on this song in a cryptic and evocative style, e.g., 'A corridor lit by humming neon where time seems to slow down'.")

class DraftOptions(BaseModel):
    reasoning: str = Field(..., description="Agent's evaluation of the board and strategy selection")
    options: List[TrackTile] = Field(..., min_length=3, max_length=3)

class FloorplanState(BaseModel):
    max_rooms: int = 5
    drafted_rooms: List[TrackTile] = []
    
    @property
    def current_turn(self) -> int:
        return len(self.drafted_rooms) + 1