import curses
import time
import json
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k')]

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    audio_file = "song.mp3"
    if not os.path.exists(audio_file):
        stdscr.addstr(0, 0, f"Error: '{audio_file}' not found in ~/rhythm_game/")
        stdscr.refresh()
        time.sleep(2)
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
    except Exception as e:
        stdscr.addstr(0, 0, f"Audio Error: {e}")
        stdscr.refresh()
        time.sleep(2)
        return

    notes = []

    for count in range(3, 0, -1):
        stdscr.erase()
        stdscr.addstr(2, 4, f"Get Ready! Starting in {count}...", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1)

    pygame.mixer.music.play()
    start_time = time.perf_counter()

    while pygame.mixer.music.get_busy():
        current_time = pygame.mixer.music.get_pos() / 1000.0
        if current_time < 0:
            current_time = time.perf_counter() - start_time

        key = stdscr.getch()
        if key == 27:
            break

        if key in LANE_KEYS:
            lane_idx = LANE_KEYS.index(key)
            notes.append({"lane": lane_idx, "time": round(current_time, 3)})

        stdscr.erase()
        stdscr.addstr(1, 2, f"RECORDING BEATMAP FOR: {audio_file}")
        stdscr.addstr(2, 2, f"Current Time: {current_time:.2f}s | Notes Tapped: {len(notes)}")
        stdscr.addstr(4, 2, "Tap D, F, J, or K along with the beat!")
        stdscr.addstr(5, 2, "Press ESC to finish early.")
        stdscr.refresh()
        time.sleep(0.005)

    pygame.mixer.music.stop()

    # Load existing levels or create fallback
    if os.path.exists("song.json"):
        with open("song.json", "r") as f:
            data = json.load(f)
    else:
        data = {"levels": []}

    # Update Level 1 notes without deleting Level 2 or Level 3
    if "levels" in data and len(data["levels"]) > 0:
        data["levels"][0]["notes"] = notes
        data["levels"][0]["song_file"] = audio_file
    else:
        data["levels"] = [
            {
                "level_id": 1,
                "title": "Level 1: Piano Track",
                "type": "piano",
                "speed": 6.0,
                "hit_window": 0.350,
                "song_file": audio_file,
                "notes": notes
            }
        ]

    with open("song.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    curses.wrapper(main)
    print("\nRecorded notes updated for Level 1 while keeping Level 2 & 3 intact!")
