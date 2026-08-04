# model_card

## Reflection
### Limitations and Biases
**Data bias**: The catalog reflects whatever tracks were added to it; if seeded with niche genres, recommendations will cluster there. No diversity guarantee.

**Vector-space bias**: The 9D audio vector (valence, energy, tempo, etc.) captures sonic properties but misses cultural context, artist intent, lyrical content, or social meaning. Two sonically similar tracks may differ drastically in context.

**Agent hallucination**: The AI could recommend tracks that don't exist in the database or misinterpret the strategy constraints. It's yet to happen since `transform_drafts` method catches this, though any agent-side error would be silently dropped.

**Cold-start problem**: New users with no history get random agent outputs. New tracks with no choice history have no signal of quality.

**Human fatigue**: A 3-turn limit (max_rooms=3) is arbitrary. Users can't explore deeply or curate long sequences.

### Misuse & Prevention
**Recommendation manipulation**: Someone could exploit the database to surface their own music by gaming the audio features. Injecting fake tracks is guardrailed by `create_track` which rejects invalid ISRCs, so long as the database key and `insert_track` remain inaccessible to general users.
- **Prevention**: Validate all incoming ISRCs against a trusted source before insertion in `create_track`.  
  
**Data exfiltration**: The agent sees full track history and could leak metadata if prompt-injected.  
- **Prevention**: Sanitize user prompts; never expose raw database queries to the agent. Limit agent context to only the current sequence, not the full catalog.
  
**Spam/low-quality recommendations**: The agent could recommend tracks with misleading clues or incorrect metadata.
- **Prevention**: Add a lightweight review step—human thumbs-up/down on each recommended option, feed that back to retrain or filter agent suggestions.
  
**Cost**: Calling an AI repeatedly (once per turn) adds up fast.
- **Prevention**: Cache agent reasoning for identical histories, or batch multiple users' turns into one call.

### Perceived Reliability 
In choosing to use Gemini (2.5 then 3.6) as the AI for the agent, I wanted to maximize the number of free calls; you don't know how shocked I was to be hit with `429` errors. Surprise surprise, the precious free RPD (requests per day) for one Gemini model capable of generating content is capped at 20. Due to this limitation, I had to switch from one model to another just to continue testing the app.  
  
The AI was quite reliable aside from rate limiting. Responses always complied with the prompt and I found no hallucinations.  

### Collaborative Development
Throughout implementation of my design, I relied heavily on Gemini to explain and generate code for full methods, demo seed data, and tests. I've realized Gemini likes to write a lot and requires explicit prompting to prevent similar unwanted behavior.  
  
Although its code generation is often flawed (perhaps due to a lack of context while building), I have to manually edit nearly everything half-usable it outputs. I found it particularly helpful to pass the job of generating seed data and tools for the agent.  
  
This project was my first time watching Gemini forget and hallucinate information, and its suggestions from thereon remained merely suggestions. It was still useful for clarifying implementation practices, however, and was a good assistant before its mental collapse.  
  
I only recalled that I could and should use Claude very last minute during MVP development, but I had the chance to have it generate the [system diagram](https://github.com/solswiss/swansong-counsel/blob/2c39e7a118ecd3f5f35dcc65b9597ba949ff10a9/diagrams/architecture.md). Despite the vague prompt (pulled directly from the course), it did pretty good.

## Tests
### Automated Testing
7 out of 7 tests passed. The agent successfully used tools as expected based on semantic queries that were almost obvious.
### Human Evaluation
| Test Subject | Test Input | Evaluation Criteria | Result
| --- | --- | --- | --- |
| lore/clue generation | Touch - Daft Punk, Paul Williams | descriptive, no banned words, under 16 words | pass
| agent reasoning | 2 tracks | 1 sentence strategy selection logic + 3 bullets per option with reason | pass
| agent options | 2 tracks | 3 total options, options exist in catalog | pass