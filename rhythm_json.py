import curses
import time
import json
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k')]

# Game Tuning
NOTE_SPEED = 6.0        # Smooth, slow fall speed
HIT_WINDOW = 0.350      # Generous hit timing window
HIT_LINE_OFFSET = 2     # Hit bar offset from bottom

def load_beatmap(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Beatmap file '{file_path}' not found.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    notes = sorted(data.get("notes", []), key=lambda x: x["time"])
    return data.get("song_file"), notes

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    try:
        audio_file, beatmap = load_beatmap("song.json")
    except Exception as e:
        stdscr.addstr(0, 0, f"Error loading beatmap: {e}")
        stdscr.refresh()
        time.sleep(2)
        return

    note_states = ['pending'] * len(beatmap)

    audio_loaded = False
    try:
        pygame.mixer.init()
        if audio_file and os.path.exists(audio_file):
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            audio_loaded = True
    except Exception:
        audio_loaded = False

    start_time = time.perf_counter()
    score = 0
    combo = 0
    feedback_text = ""
    feedback_timer = 0

    running = True
    while running:
        if audio_loaded and pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000.0
        else:
            current_time = time.perf_counter() - start_time

        max_y, max_x = stdscr.getmaxyx()
        target_y = max_y - HIT_LINE_OFFSET

        key = stdscr.getch()
        if key == 27:  # ESC key
            break

        if key in LANE_KEYS:
            pressed_lane = LANE_KEYS.index(key)
            
            closest_idx = None
            closest_diff = float('inf')

            for i, note in enumerate(beatmap):
                if note["lane"] == pressed_lane and note_states[i] == 'pending':
                    diff = abs(current_time - note["time"])
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_idx = i

            if closest_idx is not None and closest_diff <= HIT_WINDOW:
                note_states[closest_idx] = 'hit'
                score += 100
                combo += 1
                feedback_text = "PERFECT!"
                feedback_timer = current_time
            else:
                combo = 0
                feedback_text = "MISS!"
                feedback_timer = current_time

        for i, note in enumerate(beatmap):
            if note_states[i] == 'pending' and (current_time - note["time"]) > HIT_WINDOW:
                note_states[i] = 'miss'
                combo = 0
                feedback_text = "MISS!"
                feedback_timer = current_time

        if all(s != 'pending' for s in note_states) and (current_time > beatmap[-1]["time"] + 2.0):
            running = False

        stdscr.erase()
        stdscr.addstr(0, 2, f"Score: {score} | Combo: {combo} | Time: {current_time:.1f}s")
        if current_time - feedback_timer < 0.4:
            stdscr.addstr(1, 2, f"[{feedback_text}]")

        lane_width = 8
        start_x = (max_x - (4 * lane_width)) // 2

        # Draw Lanes
        for l_idx in range(4):
            x = start_x + (l_idx * lane_width)
            for y in range(2, target_y + 1):
                stdscr.addch(y, x, '|')
                stdscr.addch(y, x + lane_width - 1, '|')

            stdscr.addstr(target_y, x + 1, f"[{LANES[l_idx]}]".center(lane_width - 2), curses.A_BOLD)

        # Draw Falling Notes
        for i, note in enumerate(beatmap):
            if note_states[i] != 'pending':
                continue

            time_until_hit = note["time"] - current_time
            y_pos = int(target_y - (time_until_hit * NOTE_SPEED))

            # Only display notes when they enter the top of the terminal screen
            if 2 <= y_pos <= target_y:
                note_x = start_x + (note["lane"] * lane_width) + 1
                stdscr.addstr(y_pos, note_x, "  ==  ", curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(0.008)

if __name__ == "__main__":
    curses.wrapper(main)
