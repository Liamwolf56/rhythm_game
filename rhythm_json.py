import curses
import time
import json
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

def load_levels(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Beatmap file '{file_path}' not found.")
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get("levels", [])

def select_level_menu(stdscr, levels):
    """Displays an interactive main menu to select a game level."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    selected_idx = 0

    while True:
        stdscr.erase()
        stdscr.addstr(1, 2, "=== TERMINAL RHYTHM GAME: SELECT LEVEL ===", curses.A_BOLD)
        stdscr.addstr(2, 2, "Use UP/DOWN arrows to select, ENTER to play, ESC to exit.\n")

        for idx, lvl in enumerate(levels):
            title = lvl.get("title", f"Level {idx+1}")
            mode = lvl.get("mode", "standard").upper()
            label = f"  [{idx+1}] {title} (Mode: {mode})  "
            if idx == selected_idx:
                stdscr.addstr(4 + idx, 4, label, curses.A_REVERSE)
            else:
                stdscr.addstr(4 + idx, 4, label)

        key = stdscr.getch()
        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(levels) - 1:
            selected_idx += 1
        elif key in [10, 13]:  # ENTER key
            return levels[selected_idx]
        elif key == 27:        # ESC key
            return None

def play_level(stdscr, level_data):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    mode = level_data.get("mode", "standard")
    note_speed = level_data.get("speed", 6.0)
    hit_window = level_data.get("hit_window", 0.300)
    beatmap = sorted(level_data.get("notes", []), key=lambda x: x["time"])

    # Configure key bindings based on mode
    if mode == "dual":
        lanes = ['F', 'J']
        lane_keys = [ord('f'), ord('j')]
        lane_width = 12
    else:
        lanes = ['D', 'F', 'J', 'K']
        lane_keys = [ord('d'), ord('f'), ord('j'), ord('k')]
        lane_width = 8

    note_states = ['pending'] * len(beatmap)
    start_time = time.perf_counter()
    score = 0
    combo = 0
    feedback_text = ""
    feedback_timer = 0
    hit_line_offset = 2

    running = True
    while running:
        current_time = time.perf_counter() - start_time
        max_y, max_x = stdscr.getmaxyx()
        target_y = max_y - hit_line_offset

        key = stdscr.getch()
        if key == 27:  # ESC to exit level back to menu
            break

        # Process Key Press
        if key in lane_keys:
            pressed_lane = lane_keys.index(key)
            closest_idx = None
            closest_diff = float('inf')

            for i, note in enumerate(beatmap):
                if note["lane"] == pressed_lane and note_states[i] == 'pending':
                    diff = abs(current_time - note["time"])
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_idx = i

            if closest_idx is not None and closest_diff <= hit_window:
                note_states[closest_idx] = 'hit'
                score += 100
                combo += 1
                feedback_text = "PERFECT!"
                feedback_timer = current_time
            else:
                combo = 0
                feedback_text = "MISS!"
                feedback_timer = current_time

        # Check Missed Notes
        for i, note in enumerate(beatmap):
            if note_states[i] == 'pending' and (current_time - note["time"]) > hit_window:
                note_states[i] = 'miss'
                combo = 0
                feedback_text = "MISS!"
                feedback_timer = current_time

        # End Level
        if len(beatmap) > 0 and all(s != 'pending' for s in note_states) and (current_time > beatmap[-1]["time"] + 1.5):
            running = False

        # Render Terminal Graphics
        stdscr.erase()
        stdscr.addstr(0, 2, f"Level: {level_data.get('title')} | Score: {score} | Combo: {combo}")
        if current_time - feedback_timer < 0.4:
            stdscr.addstr(1, 2, f"[{feedback_text}]")

        start_x = (max_x - (len(lanes) * lane_width)) // 2

        # Draw Lanes
        for l_idx in range(len(lanes)):
            x = start_x + (l_idx * lane_width)
            for y in range(2, target_y + 1):
                stdscr.addch(y, x, '|')
                stdscr.addch(y, x + lane_width - 1, '|')

            stdscr.addstr(target_y, x + 1, f"[{lanes[l_idx]}]".center(lane_width - 2), curses.A_BOLD)

        # Draw Notes
        for i, note in enumerate(beatmap):
            if note_states[i] != 'pending':
                continue

            # In dual-lane mode, clamp lane index to 0 or 1
            lane_idx = note["lane"] if note["lane"] < len(lanes) else len(lanes) - 1
            time_until_hit = note["time"] - current_time
            y_pos = int(target_y - (time_until_hit * note_speed))

            if 2 <= y_pos <= target_y:
                note_x = start_x + (lane_idx * lane_width) + 1
                note_str = "  ====  " if mode == "dual" else "  ==  "
                stdscr.addstr(y_pos, note_x, note_str, curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(0.008)

def main(stdscr):
    try:
        levels = load_levels("song.json")
    except Exception as e:
        stdscr.erase()
        stdscr.addstr(0, 0, f"Error loading levels: {e}")
        stdscr.refresh()
        time.sleep(2)
        return

    while True:
        selected = select_level_menu(stdscr, levels)
        if selected is None:
            break  # Exit program from menu
        play_level(stdscr, selected)

if __name__ == "__main__":
    curses.wrapper(main)
