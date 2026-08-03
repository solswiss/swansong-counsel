from models import FloorplanState
from db import TrackDatabase
from gallery import Gallery

def run_mvp_draft_loop(db: TrackDatabase):
    state = FloorplanState(max_rooms=3)
    
    print("--- STARTING FLOORPLAN DRAFT ---")

    gallery = Gallery(db)

    seeded = None
    while seeded is None:
        isrc = input("Choose a song to start. Pass its ISRC: ")
        if db.track_exists(isrc):
            seeded = db.get_track_tile(isrc)
            continue
        seeded = db.create_track(isrc)
    state.drafted_rooms.append(seeded)
    gallery.insert_draft(seeded.isrc)
    
    while state.current_turn <= state.max_rooms:
        print(f"\n--- TURN {state.current_turn-1}/{state.max_rooms} ---")

        # Display current sequence
        print("[DEBUG] CURRENT FLOORPLAN")
        for idx, room in enumerate(state.drafted_rooms, 1):
            print(f"Room {idx}: {room.title} - {room.artist} [{room.genre}]")

        # Agent calculates options
        draft_turn = gallery.generate_turn_options(state)
        if draft_turn is None:
            print("Ending turn early...")
            continue
        print(f"Architect's Strategy\n{draft_turn.reasoning}\n")
        
        # Display 3 Choices
        for idx, option in enumerate(draft_turn.options, 1):
            print(f"[{idx}:{option.isrc}] {option.title} - {", ".join(option.artist)} ({option.observation})")
            print(f"    Genre: {', '.join(option.genre)} | {"https://youtube.com/watch?v="+option.youtube_id if option.youtube_id else ""}")
            print(f"    Room Clue: \"{option.lore}\"")
        
        choice = input("\nSelect a room (1-3) or type 'end' to finish early: ").strip().lower()
        
        if choice.lower() == 'end':
            print("Ending.")
            break
        
        if choice in ['1', '2', '3']:
            selected_tile = draft_turn.options[int(choice) - 1]
            state.drafted_rooms.append(selected_tile)
            print(f"Drafted: {selected_tile.title}")
            try:
                db.inc_times_chosen(selected_tile.isrc)
            except:
                print("X Error inc_times_chosen")
        else:
            print("Invalid input, skipping turn selection.")


    print("\n=== FINAL FLOORPLAN SEQUENCE ===")
    for idx, room in enumerate(state.drafted_rooms, 1):
        print(f"[{room.isrc}] Room {idx}: {room.title} - {room.artist} | {', '.join(room.genre)}")

uc = "0"
print("Starting system, please wait!")
db = TrackDatabase()

while uc != "9":
    print("=== MENU ===")
    print("0 | Draft Floorplan")
    print("1 | Add Floorplan to Draft Pool")
    print("2 | Open (non-demo) Draft Pool")
    print("9 | Quit")
    uc = input("Type your choice: ")

    if uc == "0":
        run_mvp_draft_loop(db)
    elif uc == "1":
        isrc = input("Track ISRC: ")
        try:
            if db.create_track(isrc) is None:
                print("Failed to register new Floorplan.")
            else:
                print("Added new Floorplan.")
        except Exception as e:
            print("Failed to register new Floorplan:",e)
    elif uc == "2":
        cat = db.fetch_catalog()
        for room in cat:
            if "demo" not in room.isrc:
                print(f"[{room.isrc}] {room.title} - {room.artist} | {', '.join(room.genre)}")
