from pydantic_ai import Agent, RunContext

from models import AgentDraftOptions, DraftOptions, TrackTile, FloorplanState, TrackRecord
from db import TrackDatabase

class Gallery:
    def __init__(self, db: TrackDatabase, model_name: str = "google:gemini-2.5-flash"):
        self.db = db
        self.history: list[str] = []
        
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
        catalog: list[TrackRecord] = ctx.deps.fetch_catalog()
        #TODO: use indexes
        catalog_summary = "\n".join([
            f"- ID: {t.isrc} | '{t.title}' by {', '.join(t.artist)} | Genre: {', '.join(t.genre)} | "
            f"Valence: {t.valence}, Energy: {t.energy}, Acousticness: {t.acousticness}, Danceability: {t.danceability}, Instrumentalness: {t.instrumentalness}, Temp: {t.tempo}"
            for t in catalog
        ])

        #TODO: write reasoning formatting
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

Rules:
1. Present exactly 3 unique track options, all from the music catalog
2. Option 1 must be a "Twin"

Output:
- Format each track as a `DraftOption` with the corresponding isrc in `isrc` and strategy used in `observation`
- Write your recommendation reasoning in `reasoning`. 

Music Catalog:
{catalog_summary}
"""

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
            prompt = "The song sequence is empty. Provide 3 initial songs across different genres."
        else:
            last_room_isrc = state.drafted_rooms[-1].isrc
            last_room = self.db.get_track_record(last_room_isrc)
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
        result = self.agent.run_sync(prompt, deps=self.db)
        for tile in result.output.options:
            self.history.append(tile.isrc)
        return self.transform_drafts(result.output)
        # try:
        #     result = self.agent.run_sync(prompt, deps=self.db)
        #     for tile in result.output.options:
        #         self.history.append(tile.isrc)
        #     return self.transform_drafts(result.output)
        # except Exception as e:
        #     print("Error generating turn options:",e)
        #     return None
