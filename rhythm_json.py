import curses
import json
import os
import time

# Suppress Pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# -------------------------------------------------------------------
# AUDIO INITIALIZATION
# -------------------------------------------------------------------
pygame.mixer.init()

# -------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# -------------------------------------------------------------------
LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k'), ord('D'), ord('F'), ord('J'), ord('K')]
KEY_MAP = {
    ord('d'): 0, ord('D'): 0,
    ord('f'): 1, ord('F'): 1,
    ord('j'): 2, ord('J'): 2,
    ord('k'): 3, ord('K'): 3
}

# -------------------------------------------------------------------
# LEVEL 1: PIANO TRACK (WITH MP3 AUDIO SYNC)
# -------------------------------------------------------------------
def play_piano_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    song_file = level_data.get("song_file", "song.mp3")
    notes = level_data.get("notes", [])
    speed = level_data.get("speed", 6.0)
    hit_window = level_data.get("hit_window", 0.350)

    # Load and start audio playback
    audio_active = False
    if os.path.exists(song_file):
        try:
            pygame.mixer.music.load(song_file)
            pygame.mixer.music.set_volume(0.8)
            audio_active = True
        except Exception:
            audio_active = False

    score = 0
    combo = 0
    feedback = ""
    feedback_time = 0

    # Notes status tracking
    active_notes = [{"lane": n["lane"], "time": n["time"], "hit": False, "missed": False} for n in notes]

    # Countdown sequence
    for c in range(3, 0, -1):
        stdscr.erase()
        stdscr.addstr(5, 10, f"READY? Starting in {c}...", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1)

    start_time = time.perf_counter()
    if audio_active:
        pygame.mixer.music.play()

    while True:
        # Sync clock: Use Pygame audio position if available, else system timer fallback
        if audio_active and pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000.0
            if current_time < 0:
                current_time = time.perf_counter() - start_time
        else:
            current_time = time.perf_counter() - start_time

        # Input Handling
        key = stdscr.getch()
        if key == 27:  # ESC to exit level
            break

        if key in LANE_KEYS:
            target_lane = KEY_MAP[key]
            # Find closest un-hit note in this lane
            closest_note = None
            min_diff = float('inf')

            for note in active_notes:
                if note["lane"] == target_lane and not note["hit"] and not note["missed"]:
                    diff = abs(note["time"] - current_time)
                    if diff < min_diff:
                        min_diff = diff
                        closest_note = note

            if closest_note and min_diff <= hit_window:
                closest_note["hit"] = True
                score += 100
                combo += 1
                feedback = "PERFECT!"
                feedback_time = current_time
            else:
                combo = 0
                feedback = "MISS!"
                feedback_time = current_time

        # Update Missed Notes
        for note in active_notes:
            if not note["hit"] and not note["missed"] and (current_time - note["time"]) > hit_window:
                note["missed"] = True
                combo = 0
                feedback = "MISS!"
                feedback_time = current_time

        # Draw UI
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        # Track Lines
        lane_width = 8
        start_x = 4
        hit_line_y = height - 4

        stdscr.addstr(0, 2, f"Song: {song_file} | Time: {current_time:.2f}s | Score: {score} | Combo: {combo}")
        
        # Lanes Header
        for i, lane in enumerate(LANES):
            x = start_x + (i * lane_width)
            stdscr.addstr(2, x + 2, f"[{lane}]", curses.A_BOLD)
            for y in range(3, hit_line_y):
                stdscr.addstr(y, x + 3, "|")

        # Hit Line Indicator
        hit_str = "=" * (len(LANES) * lane_width + 4)
        stdscr.addstr(hit_line_y, start_x - 1, hit_str, curses.A_REVERSE)

        # Draw Falling Notes
        for note in active_notes:
            if note["hit"] or note["missed"]:
                continue

            time_diff = note["time"] - current_time
            # Falling calculation
            y_pos = int(hit_line_y - (time_diff * speed))

            if 3 <= y_pos < hit_line_y:
                x_pos = start_x + (note["lane"] * lane_width) + 2
                stdscr.addstr(y_pos, x_pos, "O", curses.A_BOLD)

        # Draw Feedback
        if current_time - feedback_time < 0.5:
            stdscr.addstr(hit_line_y + 2, start_x + 6, feedback, curses.A_BOLD)

        stdscr.addstr(height - 1, 2, "Press ESC to return to Menu")
        stdscr.refresh()
        time.sleep(0.005)

        # End of level check
        all_done = all(n["hit"] or n["missed"] for n in active_notes)
        if all_done and (current_time > (notes[-1]["time"] + 1.0 if notes else 5.0)):
            break

    if audio_active:
        pygame.mixer.music.stop()

# -------------------------------------------------------------------
# LEVEL 2: FROG JUMP RHYTHM
# -------------------------------------------------------------------
def play_frog_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    obstacles = level_data.get("obstacles", [])
    hit_window = level_data.get("hit_window", 0.300)

    score = 0
    start_time = time.perf_counter()
    is_jumping = False
    jump_start = 0

    while True:
        current_time = time.perf_counter() - start_time

        key = stdscr.getch()
        if key == 27:
            break
        elif key == ord(' ') and not is_jumping:
            is_jumping = True
            jump_start = current_time
            score += 50

        if is_jumping and (current_time - jump_start > 0.4):
            is_jumping = False

        stdscr.erase()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(1, 2, "LEVEL 2: FROG JUMP | Press SPACE to Jump over obstacles!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s")

        ground_y = 10
        stdscr.addstr(ground_y, 0, "_" * (width - 1))

        # Draw Frog
        frog_y = ground_y - 2 if is_jumping else ground_y - 1
        stdscr.addstr(frog_y, 10, "(🐸)", curses.A_BOLD)

        # Draw Moving Obstacles
        for obs in obstacles:
            t_diff = obs["time"] - current_time
            if -1.0 <= t_diff <= 4.0:
                obs_x = int(10 + (t_diff * 15))
                if 0 < obs_x < width - 2:
                    stdscr.addstr(ground_y - 1, obs_x, "🌵")

        stdscr.addstr(ground_y + 3, 2, "Press ESC to return to Menu")
        stdscr.refresh()
        time.sleep(0.01)

        if obstacles and current_time > (obstacles[-1]["time"] + 2.0):
            break

# -------------------------------------------------------------------
# LEVEL 3: ECHO BEAT CHALLENGE
# -------------------------------------------------------------------
def play_echo_level(stdscr, level_data):
    sequence = level_data.get("sequence", ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"])
    key_dict = {
        curses.KEY_UP: "KEY_UP",
        curses.KEY_DOWN: "KEY_DOWN",
        curses.KEY_LEFT: "KEY_LEFT",
        curses.KEY_RIGHT: "KEY_RIGHT"
    }

    stdscr.nodelay(False)
    
    # Phase 1: Demonstration
    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: ECHO BEAT CHALLENGE")
    stdscr.addstr(3, 2, "Watch the sequence carefully:")
    stdscr.refresh()
    time.sleep(1)

    for arrow in sequence:
        stdscr.addstr(5, 5, f"--> {arrow} <--   ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.6)
        stdscr.addstr(5, 5, " " * 30)
        stdscr.refresh()
        time.sleep(0.2)

    # Phase 2: User Input
    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: ECHO BEAT CHALLENGE")
    stdscr.addstr(3, 2, "Your turn! Repeat the pattern using your Arrow Keys:")
    stdscr.refresh()

    user_seq = []
    while len(user_seq) < len(sequence):
        key = stdscr.getch()
        if key == 27:
            return
        if key in key_dict:
            user_seq.append(key_dict[key])
            stdscr.addstr(6, 2 + (len(user_seq) * 12), f"[{key_dict[key]}]")
            stdscr.refresh()

    # Evaluation
    time.sleep(0.5)
    stdscr.erase()
    if user_seq == sequence:
        stdscr.addstr(4, 5, "SUCCESS! Sequence Matched Perfectly!", curses.A_BOLD)
    else:
        stdscr.addstr(4, 5, "FAILED! Sequence mismatch.", curses.A_BOLD)

    stdscr.addstr(6, 5, "Press any key to return to Menu...")
    stdscr.refresh()
    stdscr.getch()

# -------------------------------------------------------------------
# MAIN MENU & ENTRY POINT
# -------------------------------------------------------------------
def main(stdscr):
    curses.curs_set(0)

    # Load levels from song.json
    if os.path.exists("song.json"):
        with open("song.json", "r") as f:
            data = json.load(f)
            levels = data.get("levels", [])
    else:
        levels = []

    while True:
        stdscr.nodelay(False)
        stdscr.erase()
        stdscr.addstr(1, 2, "==========================================", curses.A_BOLD)
        stdscr.addstr(2, 2, "         RHYTHM GAME ENGINE MENU          ", curses.A_BOLD)
        stdscr.addstr(3, 2, "==========================================", curses.A_BOLD)

        if not levels:
            stdscr.addstr(5, 2, "No levels found in song.json!")
        else:
            for i, lvl in enumerate(levels):
                stdscr.addstr(5 + i, 4, f"{i + 1}. {lvl.get('title', 'Untitled Level')}")

        stdscr.addstr(10, 2, "Press 1, 2, or 3 to play a level. Press 'Q' to quit.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]:
            break
        elif key in [ord('1'), ord('2'), ord('3')]:
            idx = int(chr(key)) - 1
            if idx < len(levels):
                lvl = levels[idx]
                lvl_type = lvl.get("type", "piano")

                if lvl_type == "piano":
                    play_piano_level(stdscr, lvl)
                elif lvl_type == "frog":
                    play_frog_level(stdscr, lvl)
                elif lvl_type == "echo":
                    play_echo_level(stdscr, lvl)

if __name__ == "__main__":
    curses.wrapper(main)
