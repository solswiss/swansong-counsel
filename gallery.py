from pydantic_ai import Agent, RunContext

from models import AgentDraftOptions, DraftOptions, TrackTile, FloorplanState, TrackRecord
from db import TrackDatabase

class Gallery:
    def __init__(self, db: TrackDatabase, model_name: str = "google:gemini-3.6-flash"):
        self.db = db
        self.history: list[str] = []
        self.history_prompt: str = ""
        
        self.agent = Agent(
            model_name,
            deps_type=TrackDatabase,
            output_type=AgentDraftOptions,
            instructions=self._build_system_prompt,
        )

        @self.agent.tool
        async def query_twin(
            ctx: RunContext[TrackDatabase],
            isrc: str,
            exclude_ids: list[str] = self.history,
            limit: int = 3
        ) -> list[str]:
            """
            Twin Strategy: Finds tracks with high audio feature similarity across all 9 dimensions.
            Use this for safe transitions that preserve the current room's sonic identity.
            Always include the ISRC of the track of interest.
            Returns a list of matching track IDs.
            """
            return ctx.deps.query_twin(
                vector=self.db.get_audio_vector(isrc),
                exclude_ids=exclude_ids,
                limit=limit
            )

        @self.agent.tool
        async def query_cross(
            ctx: RunContext[TrackDatabase],
            target_energy: float,
            exclude_ids: list[str] = self.history,
            limit: int = 3
        ) -> list[str]:
            """
            Cross Strategy: Shifts dynamic energy drastically (e.g., drops into a calm lull or surges into high intensity).
            Pass the target or current track's energy level to find contrast candidates.
            Returns a list of matching track IDs.
            """
            return ctx.deps.query_cross(
                energy=target_energy,
                exclude_ids=exclude_ids,
                limit=limit
            )

        @self.agent.tool
        async def query_farmer(
            ctx: RunContext[TrackDatabase],
            acousticness: float,
            instrumentalness: float,
            exclude_ids: list[str] = self.history,
            limit: int = 3
        ) -> list[str]:
            """
            Farmer Strategy: Flips the production style (e.g., switches organic/acoustic instruments for synthetic/electronic textures).
            Pass the current track's acousticness and instrumentalness to search for production inversions.
            Returns a list of matching track IDs.
            """
            return ctx.deps.query_farmer(
                acousticness=acousticness,
                instrumentalness=instrumentalness,
                exclude_ids=exclude_ids,
                limit=limit
            )

        @self.agent.tool
        async def query_sail(
            ctx: RunContext[TrackDatabase],
            exclude_genres: list[str],
            target_tempo: float,
            target_valence: float,
            exclude_ids: list[str] = self.history,
            limit: int = 3
        ) -> list[str]:
            """
            Sail Strategy: Shifts genre while preserving underlying tempo and valence/mood.
            Always pass the current track's genre list into exclude_genres to ensure a genre pivot.
            Returns a list of matching track IDs.
            """
            return ctx.deps.query_sail(
                exclude_genres=exclude_genres,
                tempo=target_tempo,
                valence=target_valence,
                exclude_ids=exclude_ids,
                limit=limit
            )

        @self.agent.tool
        async def query_diamondus(
            ctx: RunContext[TrackDatabase],
            isrc: str,
            exclude_ids: list[str] = self.history,
            limit: int = 3
        ) -> list[str]:
            """
            Diamondus Strategy: Wildcard selector with low direct correlation across features.
            Finds mathematical outliers to inject unexpected novelty or high contrast into choices.
            Always include the ISRC of the track of interest.
            Returns a list of matching track IDs.
            """
            return ctx.deps.query_diamondus(
                self.db.get_audio_vector(isrc),
                exclude_ids=exclude_ids,
                limit=limit
            )

    def _build_system_prompt(self, ctx: RunContext[TrackDatabase]) -> str:
        """Dynamic system prompt injected automatically on agent run."""
        return f"""
You are the architect for a music recommendation and discovery algorithm. 
Your role is to analyze a song sequence and generate 3 strategic track choices based on it.

You have access to 5 recommendation strategy tools which will give you a list of matching tracks by their ISRC. 
After using a tool, recommend one of the tracks based on the sequence.
1. `query_twin`: Safe continuation (similar 9D vector).
2. `query_cross`: Dynamic energy shift (intensity contrast).
3. `query_farmer`: Production flip (organic vs synthetic shift).
4. `query_sail`: Genre shift with preserved tempo and mood.
5. `query_diamondus`: Wildcard outlier.

## Rules
1. Present exactly 3 unique track options, all from the music catalog
2. Option 1 must be a "Twin"

### Output
Format each track as a `DraftOption` with the corresponding isrc in `isrc` and strategy used in `observation`
#### Reasoning
Write your recommendation reasoning in `reasoning` in the format:
- 1 sentence about your sequence analysis and strategy choice.
- 1 bulleted sentence for each track about the strategy used and why you chose that track out of the tracks given to you.
"""

    def insert_draft(self, isrc: str) -> bool:
        if isrc not in self.history:
            self.history.append(isrc)
            return True
        print("X ISRC already in Agent's history")
        return False

    def transform_drafts(self, agent_drafts: AgentDraftOptions) -> DraftOptions:
        opts: list[TrackTile] = []
        for tile in agent_drafts.options:
            track = self.db.get_track_tile(tile.isrc)
            if track is None:
                print("X",tile.isrc,"not found in db")
                continue
            opts.append(TrackTile(
                isrc=tile.isrc,
                title=track.title,
                artist=track.artist,
                genre=track.genre,
                lore=track.lore,
                youtube_id=track.youtube_id,
                observation=tile.observation
            ))
        return DraftOptions(
            reasoning=agent_drafts.reasoning, 
            options=opts
        )

    def generate_turn_options(self, state: FloorplanState):
        if not state.drafted_rooms:
            print("X State history is empty - Agent cannot start drafting")
            return None #prompt = "The song sequence is empty. Use strategies to provide 3 initial songs across different genres."
        else:
            t = self.db.get_track_record(self.history[-1])
            if t is None:
                print("X last room is not found")
                return None
            self.history_prompt += f"- ID: {t.isrc} | '{t.title}' by {', '.join(t.artist)} | Genre: {', '.join(t.genre)} | Valence: {t.valence}, Energy: {t.energy}, Acousticness: {t.acousticness}, Danceability: {t.danceability}, Instrumentalness: {t.instrumentalness}, Temp: {t.tempo}\n"
            prompt = self.history_prompt + "\nGenerate 3 strategic next room choices."
            #print("[DEBUG] AGENT'S HISTORY PROMPT")
            #print(prompt)
        try:
            result = self.agent.run_sync(prompt, deps=self.db)
            for tile in result.output.options:
                self.history.append(tile.isrc)
                try: 
                    self.db.inc_times_offered(tile.isrc)
                except:
                    print("X Error inc_times_offered")
            #print("[DEBUG] AGENT'S HISTORY:",self.history)
            return self.transform_drafts(result.output)
        except Exception as e:
            print("Error generating turn options:",e)
            return None
