import pytest

from pydantic_ai.models.test import TestModel
from pydantic import BaseModel, Field, field_validator
from unittest.mock import AsyncMock

from gallery import Gallery
from db import TrackDatabase

@pytest.fixture
def mock_db():
    """Creates a mock instance of TrackDatabase with predefined return values."""
    mock_db = AsyncMock(spec=TrackDatabase)
    mock_db.query_twin.return_value = ["demo1"]
    mock_db.query_cross.return_value = ["demo10"]
    mock_db.query_farmer.return_value = ["demo16"]
    mock_db.query_sail.return_value = ["demo28"]
    mock_db.query_diamondus.return_value = ["demo23"]
    return mock_db

##### TOOLS
@pytest.fixture
def test_gallery(mock_db: AsyncMock):
    gallery = Gallery(db=mock_db)
    gallery.agent.model = TestModel()
    return gallery

@pytest.mark.asyncio
async def test_agent_selects_twin_tool(test_gallery: Gallery, mock_db: AsyncMock):
    prompt = (
        "Seeking similar track."
        "Use appropriate strategy for track 'demo0'."
        "Return just the chosen track's ISRC."
    )

    await test_gallery.agent.run(prompt, deps=mock_db)
    mock_db.query_twin.assert_called_once()

@pytest.mark.asyncio
async def test_agent_selects_cross_tool(test_gallery: Gallery, mock_db: AsyncMock):
    prompt = (
        "Seeking change in energy."
        "Use appropriate strategy for track 'demo0'."
        "Return just the chosen track's ISRC."
    )

    await test_gallery.agent.run(prompt, deps=mock_db)
    mock_db.query_cross.assert_called_once()

@pytest.mark.asyncio
async def test_agent_selects_farmer_tool(test_gallery: Gallery, mock_db: AsyncMock):   
    prompt = (
        "Seeking different production style."
        "Use appropriate strategy for track 'demo0'."
        "Return just the chosen track's ISRC."
    )

    await test_gallery.agent.run(prompt, deps=mock_db)
    mock_db.query_farmer.assert_called_once()

@pytest.mark.asyncio
async def test_agent_selects_sail_tool(test_gallery: Gallery, mock_db: AsyncMock):
    prompt = (
        "Seeking different genre but same tempo and mood."
        "Use appropriate strategy for track 'demo0'."
        "Return just the chosen track's ISRC."
    )

    await test_gallery.agent.run(prompt, deps=mock_db)
    mock_db.query_sail.assert_called_once()

@pytest.mark.asyncio
async def test_agent_selects_diamondus_tool(test_gallery: Gallery, mock_db: AsyncMock):
    prompt = (
        "Seeking something completely different."
        "Use appropriate strategy for track 'demo0'."
        "Return just the chosen track's ISRC."
    )

    await test_gallery.agent.run(prompt, deps=mock_db)
    mock_db.query_diamondus.assert_called_once()

##### HARD RULES
def test_sail_strategy_enforces_exclusions():
    """Integration test against DB/RPC to enforce hard filtering constraints."""
    db = TrackDatabase()
    
    exclude_ids = ["demo0", "demo1", "demo2"]
    exclude_genres = ["synthwave", "electronic","darkwave"]
    
    # Run the query_sail DB method
    results = db.query_sail(
        exclude_genres=exclude_genres,
        tempo=120.0,
        valence=0.5,
        exclude_ids=exclude_ids,
        limit=5
    )
    
    # 1. Assert excluded IDs are NOT returned
    for track_id in results:
        assert track_id not in exclude_ids, f"Excluded ID {track_id} was returned!"

    # 2. Assert excluded genres are NOT present in returned tracks
    # (Fetches returned track details to inspect)
    for track_id in results:
        track = db.get_track_record(track_id)
        assert track is not None
        for genre in track.genre:
            assert genre not in exclude_genres, f"Excluded genre '{genre}' found in results!"


##### LORE
class LoreSnippetGuard(BaseModel):
    lore: str = Field(description="Single-sentence room lore clue.")

    @field_validator("lore")
    @classmethod
    def validate_word_count_and_punctuation(cls, v: str) -> str:
        words = v.strip().split()
        if len(words) > 16:
            raise ValueError(f"Lore is too long ({len(words)} words). Max allowed is 16 words.")
        if not v.endswith((".", "!", "?")):
            raise ValueError("Lore must end with proper terminal punctuation.")
        
        banned_words = ["tempo", "bpm", "synthesizer", "audio", "track", "db"]
        for word in banned_words:
            if word in v.lower():
                raise ValueError(f"Lore contains banned technical jargon: '{word}'")
        return v

def test_lore_structure():
    valid = LoreSnippetGuard(lore="Cold obsidian pillars hum with a distant, subterranean resonance.")
    assert valid.lore is not None

    with pytest.raises(ValueError):
        LoreSnippetGuard(lore="This high bpm track has a fast tempo that fills the huge mechanical room with noisy synthesizer music.")