from pydantic_ai import Agent
from google import genai

from models import DraftOptions, FloorplanState

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
    'google:gemini-2.5-flash',
    output_type=DraftOptions,
    system_prompt=(PROMPT)
)
client = genai.Client()


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

def generate_track_lore(title: str, artist: str, genre: str, valence: float, energy: float, acousticness: float, instrumentalness: float) -> str:
    prompt = f"""
    You are the narrative architect for an estate. Your task is to write a single-sentence description of a room inspired by a track's audio profile.

    Track Attributes:
    - Title: "{title}" by {artist}
    - Genres: {genre}
    - Mood/Valence: {valence} (Scale: 0.0 = dark/somber/grief, 1.0 = bright/serene/triumphant)
    - Energy: Energy={energy} (0.0=still/empty, 1.0=crowded/aesthetically loud)
    - Texture: Acousticness={acousticness} (0-1 scale; high=organic/natural, low=synthetic/glass/metal), Instrumentalness={instrumentalness} (0-1 scale; high=wordless/ambient, low=vocal/echoing)

    Spatial Concept:
    In this estate, a "room" is any distinct space. This includes indoor chambers and passages, subterranean vaults, open-air grounds, etc..

    ### Writing Guidelines:
    1. Output EXACTLY one evocative sentence describing a location, chamber, or outdoor zone in the estate layout.
    2. DO NOT mention musical terms. Translate audio parameters directly into physical architecture, flora, light, acoustics, and atmosphere.
    3. Align the space type with Genre & Texture. Example rooms:
    - High Acousticness + High Energy / Bright Valence -> Sunlit courtyard, stone fountain plaza, rustling birch grove, hedge maze.
    - High Acousticness + Low Energy / Dark Valence -> Overgrown ivy garden, mossy stone well, rain-drenched terrace, ancient gazebo.
    - Synthetic/Electronic + Low Energy -> Neon-lit server passage, damp cellar, glass observation deck, flickering terminal bay.
    - Synthetic/Electronic + High Energy -> Industrial gear room, hum of subterranean generators, illuminated catwalk above a dark floor.

    Generate the single-sentence lore snippet:
    """
    return client.interactions.create(model="gemini-2.5-flash",input=prompt).output_text
    