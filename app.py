from models import FloorplanState
from db import TrackDatabase
from gallery import Gallery

def run_mvp_draft_loop():
    state = FloorplanState(max_rooms=5)
    
    print("--- STARTING FLOORPLAN DRAFT ---")

    db = TrackDatabase()
    gallery = Gallery(db)

    seeded = None
    while seeded is None:
        isrc = input("Choose a song to start. Pass its ISRC: ")
        if db.track_exists(isrc):
            seeded = db.get_track_tile(isrc)
            continue
        seeded = db.create_track(isrc)
    state.drafted_rooms.append(seeded)
    
    while state.current_turn <= state.max_rooms:
        print(f"\n--- TURN {state.current_turn-1}/{state.max_rooms} ---")
        
        # Agent calculates options
        draft_turn = gallery.generate_turn_options(state)
        if draft_turn is None:
            print("Ending turn early...")
            continue
        print(f"Architect's Strategy: {draft_turn.reasoning}\n")
        
        # Display 3 Choices
        for idx, option in enumerate(draft_turn.options, 1):
            print(f"[{idx}] {option.title} - {", ".join(option.artist)}")
            print(f"    Genre: {', '.join(option.genre)} | ")
            print(f"    Room Clue: \"{option.lore}\"")
        
        choice = input("\nSelect a room (1-3) or type 'end' to finish early: ").strip().lower()
        
        if choice.lower() == 'end':
            print("Ending.")
            break
        
        if choice in ['1', '2', '3']:
            selected_tile = draft_turn.options[int(choice) - 1]
            state.drafted_rooms.append(selected_tile)
            print(f"Drafted: {selected_tile.title}")
        else:
            print("Invalid input, skipping turn selection.")


    print("\n=== FINAL FLOORPLAN SEQUENCE ===")
    for idx, room in enumerate(state.drafted_rooms, 1):
        print(f"Room {idx}: {room.title} - {room.artist} [{room.genre}]")

    if input("\nType 'quit' to quit\n").lower() == "quit":
        print("Farewell.")
        exit(0)


if __name__ == "__main__":
    run_mvp_draft_loop()

run_mvp_draft_loop()