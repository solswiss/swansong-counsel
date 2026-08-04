# swansong-counsel
## Context
Swansong Counsel is a CLI music recommendation and exploration app drawing heavily from the mechanics and style of a popular game, and potentially the MVP of a larger project.  

It is extended from AI110 Module 3 Project ["Music Recommender Simulation"](github.com/solswiss/ai110-musrec) whose [original capabilities](https://github.com/solswiss/ai110-musrec/blob/15d452b7514d20838f8377d23cf77b0901334b06/model_card.md) are grounded in tuning song recommendations to user "taste profiles" based on explicit and implicit information, e.g. likes/dislikes in songs and genres and artist diversity score. The algorithm scores songs based on hard rules and sends the top *n* highest scoring songs to the user, subscores attached.  
  
This project is important to me for two reasons.  
**I.** Personally, I think music discovery should never, ever, stagnate. I find engaging with recommendations from friends and algorithms alike very rewarding and this project became an opportunity to explore music from another side. Swansong Counsel promotes venturing into unfamiliar territory and adapts to user tastes for a balanced curation experience.  
**II.** The system examines an unlikely intersection and presents a novel concept. As it stands, this project is but a prototype which establishes ground in a particular method of music discovery.    
  

## [MVP Architecture](https://github.com/solswiss/swansong-counsel/blob/e739ce821c2bf6cd1fdabefd8e89fee18a514783/diagrams/architecture.md) Overview
**Input layer:** The user provides a starting track ISRC to start the recommendation loop.  

**Data layer:** The TrackDatabase holds your music catalog with precomputed audio vectors and metadata. The system retrieves both the track details and high-dimensional embeddings needed for similarity matching.  

**Retrieval strategies:** Five specialized query functions in the database run in parallel, each encoding a different musical relationship. These return candidate ISRCs based on features like audio similarity, energy contrast, or genre shifts.  

**Reasoning layer:** The AI Agent, Gallery, receives the sequence history plus the candidate lists from each strategy. It evaluates which tracks fit best and generates a reasoning explanation plus 3 options with their strategy labels.  

**Presentation:** The app formats those options for the user with metadata: title, artist, genre, clue (atmospheric description), YouTube link, and which strategy was used.  

**Human evaluation:** The user selects one of the three options. This choice is logged and the loop continues until the user hits max_rooms or chooses to end.  

**Feedback closure:** Each chosen track feeds back as input to the next turn, building the sequence incrementally. The agent's history accumulates, making later recommendations context-aware.  

## Setup
1. Create a virtual environment (optional but recommended)
```
python -m venv .venv
source .venv/bin/activate      # Mac or Linux
.venv\Scripts\activate         # Windows
```
2. Install dependencies
```
pip install -r requirements.txt
```
3. Run the app
```
python app.py
```

## Sample Interactions
The AI Agent is also known as Architect. `[DEBUG]` messages can be safely ignored but may be of interest to inquisitive users. Note that the number of turns is very limited due to API rate limits and less so on catalog size. Also note that the catalog contains 30 demo tracks and at least 2 real/non-demo tracks.   
  
The program connects to the database and User sees menu display and will input a choice
```
Starting system, please wait!
=== MENU ===
0 | Draft Floorplan
1 | Add Floorplan to Draft Pool
2 | Open (non-demo) Draft Pool
9 | Quit
Type your choice: 
```
### Draft Floorplan
User types 0 to begin recommendation loop
```
Type your choice: 0
```
User chooses to pass `demo0` (see the [demo catalog](https://supabase.com/dashboard/project/mwlkbnwihhhowrghywqo/editor/18609))
```
--- STARTING FLOORPLAN DRAFT ---
Choose a song to start. Pass its ISRC: demo0 
```
AI Agent explains its reasoning and strategies used based on the singular initial song, ISRC `demo0`, for the 3 options and User selects option 3
```
--- TURN 1/3 ---
[DEBUG] CURRENT FLOORPLAN
Room 1: Corridor of Cyan - ['The Draftmaster'] [['synthwave', 'electronic']]
Architect's Strategy
To build a compelling progression from 'Corridor of Cyan', I analyzed its high energy, electronic production, and driving tempo to select a blend of seamless continuation, genre pivoting, and production contrast.
- For demo2, I chose this Twin recommendation to smoothly maintain the track's driving synthwave atmosphere and consistent 9D audio profile.
- For demo28, I selected this Sail option to pivot into a new genre space while preserving the 120 BPM tempo and balanced emotional valence.
- For demo22, I picked this Farmer track to introduce a stark organic production flip that inverts the heavy synthetic instrumentation of the initial track.

[1:demo2] 46th Room Sequence - Vector Syndicate (Twin)
    Genre: synthwave, electronic | 
    Room Clue: "Cold glass monitors reflect glowing grid lines across a silent terminal."
[2:demo28] Lament for the West Wing - The Highland Draft (Sail)
    Genre: celtic folk, world | 
    Room Clue: "A wooden flute hums across a mist-covered outdoor terrace at dawn."
[3:demo22] Cantata for the Grand Hall - The Estate Choir (Farmer)
    Genre: baroque, choral | 
    Room Clue: "Wordless vocal harmonies reverberate off high stone vaulted ceilings."

Select a room (1-3) or type 'end' to finish early: 2
Drafted: Lament for the West Wing
```
AI Agent explains its choices with logic drawing from metadata of the full sequence (both the latest and initial song) and User selects option 2
```
--- TURN 2/3 ---
[DEBUG] CURRENT FLOORPLAN
Room 1: Corridor of Cyan - ['The Draftmaster'] [['synthwave', 'electronic']]
Room 2: Lament for the West Wing - ['The Highland Draft'] [['celtic folk', 'world']]
Architect's Strategy
After transitioning from energetic synthwave to serene choral baroque, the sequence calls for options that either maintain the current contemplative mood, surge back into high-energy electronic textures, or explore new genres at the same pace.
• Option 1 uses the Twin strategy with track demo17 to seamlessly preserve the intimate acoustic warmth and reflective, low-energy choral landscape of the current room.
• Option 2 uses the Cross strategy with track demo9 to abruptly inject high dynamic energy, steering the sequence back toward peak intensity.
• Option 3 uses the Sail strategy with track demo18 to pivot to a fresh genre while holding the relaxed 72 BPM tempo and somber valence steady.

[1:demo17] Pebbles in the Cloister Pool - The Orchard Draft (Twin)
    Genre: indie folk | 
    Room Clue: "Ripples spread across a quiet stone basin surrounded by white lilies."
[2:demo9] Static in the Conservatory - Echoes of Holly (Cross)
    Genre: ambient | 
    Room Clue: "Overgrown ivy clings to iron beams in a fog-choked glasshouse."
[3:demo18] Courtyard in Autumn - Cora & The Architecture (Sail)
    Genre: indie folk, acoustic | 
    Room Clue: "Crisp fallen leaves scrape across cobblestones in a chill breeze."

Select a room (1-3) or type 'end' to finish early: 2
Drafted: Static in the Conservatory
```
The last turn ends and User is presented with the final sequence of songs and a title of the sequence as an estate, as it were
```
=== FINAL FLOORPLAN SEQUENCE ===
Mercurial Cottage
[demo0] Room 1: Corridor of Cyan - ['The Draftmaster'] | synthwave, electronic
[demo28] Room 2: Lament for the West Wing - ['The Highland Draft'] | celtic folk, world
[demo9] Room 3: Static in the Conservatory - ['Echoes of Holly'] | ambient
```
### Add Floorplan to Draft Pool
User adds a song ([GBDUW2300080] Touch - Daft Punk) and the database successfully receives it
```
Type your choice: 1
Track ISRC: GBDUW2300080
Adding track  GBDUW2300080
Added new Floorplan.
```
### Open (non-demo) Draft Pool
User sees display of the real/non-demo songs in the catalog (2/32)
```
Type your choice: 2
[USAT21602338] Sweet Talk - ['Saint Motel'] | 
[GBDUW2300080] Touch (2021 Epilogue) [feat. Paul Williams] - ['Daft Punk', 'Paul Williams'] | disco, electro, funk, synth-pop
```

## Design Decisions
### Architecture
I realized the architecture would involve models, agents, and API calls while drafting the project, in addition to a synced app with unified frontend in the future. In anticipation of that, I designed a modular system and relegated data storage elsewhere. 
### Input 
Designed around a loop and menu for a seamless input process.  
### Data
To facilitate the needs of an agentic workflow and as a progression from the original project, I opted to search and store individual tracks with certain metadata—for details, check the [public table](https://supabase.com/dashboard/project/mwlkbnwihhhowrghywqo/editor/18609). The musical metadata itself is limited intentionally and works well for the MVP.  
However, data like album or popularity which are useful to deepen recommendation logic is lost. I decided not to search for albums and popularity yet due to the jungle of API calls that could require. Further, I chose to leave out important fields such as explicit user data for the sake of a more lightweight MVP.  
### Agentic Workflow
Since the agent will drive the track recommendation logic, it must have access to some part of the catalog to compare the existing user choices against. Passing the entire music catalog is not advisable so I opted to give it tools to select a recommendation direction, which return candidate options with relevant information. This middle-man operation was acceptable, maybe even good.
#### Tools
Designed five retrieval strategies to encompass five distinct musical relationships. To offer a variety of candidates across the catalog, one strategy searches for most similar, one for wildcards, and the rest for a middle ground based on genres and/or audio vectors.
### Presentation
A CLI is sufficient to demonstrate the app's capacities. For debugging and communication's sake, the app displays tracks to the user with metadata.

## Testing Summary
Implmentation of AI felt like the easy part of this project, though I'm sure that will not be the case as progress continues. There were some hiccups: the agent's reasoning varied drastically in formatting, and the LLM took many tweaks before outputting acceptable lore/clues. Most of the issues lay in prompting.  
The ability to add songs by ISRC was one of the hardest parts, due largely to my design decisions, which called for entangling multiple API services. By the end I learned to code with exceptions in mind.
One thing that proved especially helpful is the Pydantic package, which ensured all objects made are valid for any given class.  

## Reflection
This project put into perspective how important a grounding development cycles are. The efficiency of this project would greatly benefit from test-driven development (by a better programmer), but I'm glad to have found the Agile model suitable for this case.  
The AI aspect was fun to implement and use, although too easy. Although it would be at the expense of this project's development, I'm curious to enlist AI in more projects. 
