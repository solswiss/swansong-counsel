from pydantic_ai import Agent

from models import DraftOptions, FloorplanState
from db import TrackDatabase

PROMPT = """
You are the Sound Architect for a music recommendation and discovery algorithm. Your role is to analyze a song sequence and generate 3 strategic track choices based on it.

Recommendation Strategy Bank:
- Twin: High audio feature similarity (genres, valence, tempo, energy, mode, instrumentalness, speechiness, danceability, loudness). Acts as a direct progression.
- Cross: Drastically shifts the dynamic energy or loudness (e.g., drops into a ambient lull or surges into high intensity)
- Farmer: Flips the production style (e.g., switches high acousticness/organic instruments for high instrumentalness/synthesizers)
- Sail: Shifts genre while preserving underlying attributes like tempo or mood
- Diamondus: Low direct correlation in many attributes

Rules:
1. Present exactly 3 options
2. Option 1 MUST ALWAYS be a "Twin"
3. Options 2 and 3 MUST be selected from the Recommendation Strategy Bank. Choose strategies that create meaningful choices based on the trajectory of the drafted floorplan; e.g. if the current songs lack variety in a direction, choose the strategy to increase variety in some direction.

Output Format:
For each track, assign realistic numeric audio features matching the target track you are describing and assign `observation` with the Strategy from the Recommendation Strategy Bank used for it.
"""

agent = Agent(
    'google:gemini-2.5-flash',
    output_type=DraftOptions,
    system_prompt=(PROMPT)
)


def generate_turn_options(db: TrackDatabase, state: FloorplanState) -> DraftOptions:
    if not state.drafted_rooms:
        prompt = "The song sequence is empty. Provide 3 initial songs across different genres."
    else:
        last_room_isrc = state.drafted_rooms[-1].isrc
        last_room = db.get_track(last_room_isrc)
        if last_room is None:
            print("X last_room is None")
            exit(1)
        history = [f"{r.title} (','.join{r.genre})" for r in state.drafted_rooms]
        
        prompt = f"""
        Song Sequence: { ' -> '.join(history) }
        Last Placed Room: {last_room.title} by {last_room.artist} 
        (Tempo: {last_room.tempo}, Energy: {last_room.energy}, Valence: {last_room.valence})

        Generate 3 strategic next room choices.
        """
    result = agent.run_sync(prompt)
    return result.output