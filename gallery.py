from pydantic_ai import Agent
from models import DraftOptions, FloorplanState
from db import TrackRecord

PROMPT = """
You are the Sound Architect for a music recommendation and discovery algorithm. Your role is to analyze the floorplan history and generate 3 strategic track choices based on a list of songs.

Recommendation Strategy Bank:
- Twin: High audio feature similarity (genres, valence, tempo, energy, mode, instrumentalness, speechiness, danceability, loudness). Acts as a direct progression.
- Cross: Drastically shifts the dynamic energy or loudness (e.g., drops into a ambient lull or surges into high intensity)
- Farmer: Flips the production style (e.g., switches high acousticness/organic instruments for high instrumentalness/synthesizers)
- Sail: Shifts genre while preserving underlying attributes like tempo or mood
- Diamondus: Low direct correlation in many attributes

Rules:
1. Every turn MUST present exactly 3 options
2. Option 1 MUST ALWAYS be a "Twin"
3. Options 2 and 3 MUST be selected from the Recommendation Strategy Bank. Choose strategies that create meaningful choices based on the trajectory of the drafted floorplan; e.g. if the current songs lack variety in a direction, choose the strategy to increase variety in some direction.

Output Format:
For each track, assign realistic numeric audio features matching the target track you are describing and assign `observation` with the Strategy from the Recommendation Strategy Bank used for it.
"""

# Initialize lightweight agent (e.g., using Ollama locally or free OpenAI/Groq tier)
agent = Agent(
    'openai:gpt-4o-mini',
    output_type=DraftOptions,
    system_prompt=(PROMPT)
)

def generate_turn_options(state: FloorplanState) -> DraftOptions:
    # 1. Format the current state context
    if not state.drafted_rooms:
        prompt = "The floorplan is currently empty. Provide 3 initial seed rooms across different genres."
    else:
        last_room = state.drafted_rooms[-1]
        history = [f"{r.title} ({r.genre}, Energy: {r.energy})" for r in state.drafted_rooms]
        
        prompt = f"""
        Current Turn: {state.current_turn} of {state.max_rooms}
        Draft History: { ' -> '.join(history) }
        Last Placed Room: {last_room.title} by {last_room.artist} 
        (Tempo: {last_room.tempo}, Energy: {last_room.energy}, Valence: {last_room.valence})

        Generate 3 strategic next room choices.
        """

    # 2. Run agent execution
    result = agent.run_sync(prompt)
    return result.output

def generate_track_lore(title: str, artist: str, genre: str, valence: float, energy: float) -> str:
    prompt = f"""
    Write a 1-sentence atmospheric description for a room based on a song.
    Track: '{title}' by {artist} ({genre}).
    Mood profile: Valence={valence} (0=Dark, 1=Bright), Energy={energy} (0=Calm, 1=Aggressive).
    Output Style: Cryptic, evocative, e.g., 'A corridor lit by humming neon where time seems to slow down'.
    """
    # Call your local LLM / lightweight agent
    return llm.generate(prompt)

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