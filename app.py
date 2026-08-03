from models import FloorplanState
from gallery import generate_turn_options
from db import TrackDatabase

def run_mvp_draft_loop():
    state = FloorplanState(max_rooms=5)
    
    print("--- STARTING FLOORPLAN DRAFT ---")

    db = TrackDatabase()

    seeded = -1
    while seeded == -1:
        isrc = input("Choose a song to start. Pass its ISRC: ")
        seeded = db.add_track(isrc)
    
    while state.current_turn < state.max_rooms:
        print(f"\n--- TURN {state.current_turn}/{state.max_rooms} ---")
        
        # Agent calculates options
        draft_turn = generate_turn_options(db, state)
        print(f"Architect's Strategy: {draft_turn.reasoning}\n")
        
        # Display 3 Choices
        for idx, option in enumerate(draft_turn.options, 1):
            print(f"[{idx}] {option.title} - {", ".join(option.artist)}")
            print(f"    Genre: {option.genre} | ")
            print(f"    Room Clue: \"{option.lore}\"")
        
        choice = input("\nSelect a room (1-3) or type 'end' to finish early: ").strip().lower()
        
        if choice == 'end':
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

if __name__ == "__main__":
    run_mvp_draft_loop()

run_mvp_draft_loop()