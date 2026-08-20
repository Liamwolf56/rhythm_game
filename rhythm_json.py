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
    curses.curs_set(0)
    stdscr.nodelay(False)
    selected_idx = 0

    while True:
        stdscr.erase()
        stdscr.addstr(1, 2, "=== TERMINAL RHYTHM MULTI-GAME ===", curses.A_BOLD)
        stdscr.addstr(2, 2, "Use UP/DOWN arrows to select, ENTER to play, ESC to exit.\n")

        for idx, lvl in enumerate(levels):
            title = lvl.get("title", f"Level {idx+1}")
            g_type = lvl.get("type", "piano").upper()
            label = f"  [{idx+1}] {title} (Type: {g_type})  "
            if idx == selected_idx:
                stdscr.addstr(4 + idx, 4, label, curses.A_REVERSE)
            else:
                stdscr.addstr(4 + idx, 4, label)

        key = stdscr.getch()
        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(levels) - 1:
            selected_idx += 1
        elif key in [10, 13]:
            return levels[selected_idx]
        elif key == 27:
            return None

# --- GAME TYPE 1: CLASSIC PIANO FALLING NOTES ---
def play_piano_level(stdscr, level_data):
    lanes = ['D', 'F', 'J', 'K']
    lane_keys = [ord('d'), ord('f'), ord('j'), ord('k')]
    beatmap = sorted(level_data.get("notes", []), key=lambda x: x["time"])
    note_states = ['pending'] * len(beatmap)
    
    speed = level_data.get("speed", 6.0)
    hit_window = level_data.get("hit_window", 0.350)
    start_time = time.perf_counter()
    score, combo = 0, 0
    feedback, feedback_timer = "", 0

    while True:
        current_time = time.perf_counter() - start_time
        max_y, max_x = stdscr.getmaxyx()
        target_y = max_y - 2

        key = stdscr.getch()
        if key == 27: break

        if key in lane_keys:
            pressed = lane_keys.index(key)
            closest_idx, closest_diff = None, float('inf')
            for i, note in enumerate(beatmap):
                if note["lane"] == pressed and note_states[i] == 'pending':
                    diff = abs(current_time - note["time"])
                    if diff < closest_diff:
                        closest_diff, closest_idx = diff, i

            if closest_idx is not None and closest_diff <= hit_window:
                note_states[closest_idx] = 'hit'
                score += 100
                combo += 1
                feedback, feedback_timer = "PERFECT!", current_time
            else:
                combo = 0
                feedback, feedback_timer = "MISS!", current_time

        for i, note in enumerate(beatmap):
            if note_states[i] == 'pending' and (current_time - note["time"]) > hit_window:
                note_states[i] = 'miss'
                combo = 0
                feedback, feedback_timer = "MISS!", current_time

        if len(beatmap) > 0 and all(s != 'pending' for s in note_states) and (current_time > beatmap[-1]["time"] + 1.5):
            break

        stdscr.erase()
        stdscr.addstr(0, 2, f"Piano Mode | Score: {score} | Combo: {combo}")
        if current_time - feedback_timer < 0.4:
            stdscr.addstr(1, 2, f"[{feedback}]")

        lane_w = 8
        start_x = (max_x - (4 * lane_w)) // 2
        for l_idx in range(4):
            x = start_x + (l_idx * lane_w)
            for y in range(2, target_y + 1):
                stdscr.addch(y, x, '|')
                stdscr.addch(y, x + lane_w - 1, '|')
            stdscr.addstr(target_y, x + 1, f"[{lanes[l_idx]}]".center(lane_w - 2), curses.A_BOLD)

        for i, note in enumerate(beatmap):
            if note_states[i] != 'pending': continue
            y_pos = int(target_y - ((note["time"] - current_time) * speed))
            if 2 <= y_pos <= target_y:
                stdscr.addstr(y_pos, start_x + (note["lane"] * lane_w) + 1, "  ==  ", curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(0.008)

# --- GAME TYPE 2: FROG JUMP RHYTHM ---
def play_frog_level(stdscr, level_data):
    obstacles = sorted(level_data.get("obstacles", []), key=lambda x: x["time"])
    obs_states = ['pending'] * len(obstacles)
    hit_window = level_data.get("hit_window", 0.300)

    start_time = time.perf_counter()
    score, combo = 0, 0
    feedback, feedback_timer = "", 0
    is_jumping, jump_timer = False, 0

    while True:
        current_time = time.perf_counter() - start_time
        max_y, max_x = stdscr.getmaxyx()
        ground_y = max_y - 4
        frog_x = max_x // 2

        key = stdscr.getch()
        if key == 27: break

        # Spacebar to jump
        if key == ord(' ') and not is_jumping:
            is_jumping = True
            jump_timer = current_time

            # Check timing against closest approaching obstacle
            closest_idx, closest_diff = None, float('inf')
            for i, obs in enumerate(obstacles):
                if obs_states[i] == 'pending':
                    diff = abs(current_time - obs["time"])
                    if diff < closest_diff:
                        closest_diff, closest_idx = diff, i

            if closest_idx is not None and closest_diff <= hit_window:
                obs_states[closest_idx] = 'cleared'
                score += 150
                combo += 1
                feedback, feedback_timer = "CLEARED JUMP!", current_time
            else:
                combo = 0
                feedback, feedback_timer = "BAD TIMING!", current_time

        # Frog jump animation reset after 0.4s
        if is_jumping and (current_time - jump_timer > 0.4):
            is_jumping = False

        # Check missed jumps
        for i, obs in enumerate(obstacles):
            if obs_states[i] == 'pending' and (current_time - obs["time"]) > hit_window:
                obs_states[i] = 'hit_player'
                combo = 0
                feedback, feedback_timer = "TRIPPED!", current_time

        if len(obstacles) > 0 and all(s != 'pending' for s in obs_states) and (current_time > obstacles[-1]["time"] + 1.5):
            break

        stdscr.erase()
        stdscr.addstr(0, 2, f"Frog Jump Mode | Score: {score} | Combo: {combo} | Press SPACE to Jump!")
        if current_time - feedback_timer < 0.4:
            stdscr.addstr(1, 2, f"[{feedback}]")

        # Draw Ground Line
        stdscr.addstr(ground_y, 2, "=" * (max_x - 4))

        # Draw Frog
        frog_y = ground_y - 2 if is_jumping else ground_y - 1
        stdscr.addstr(frog_y, frog_x - 3, " (o_o) ", curses.A_BOLD)

        # Draw Moving Obstacles (Log / Wave moving right to left)
        for i, obs in enumerate(obstacles):
            if obs_states[i] != 'pending': continue
            time_diff = obs["time"] - current_time
            obs_x = int(frog_x + (time_diff * 15))

            if 2 <= obs_x < max_x - 2:
                stdscr.addstr(ground_y - 1, obs_x, "###", curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(0.008)

# --- GAME TYPE 3: ECHO / REPEAT BEAT ---
def play_echo_level(stdscr, level_data):
    sequence = level_data.get("sequence", ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"])
    key_map = {
        curses.KEY_UP: "KEY_UP",
        curses.KEY_DOWN: "KEY_DOWN",
        curses.KEY_LEFT: "KEY_LEFT",
        curses.KEY_RIGHT: "KEY_RIGHT"
    }

    step = 0
    score = 0
    feedback = "Watch & Remember..."
    stdscr.nodelay(False)

    # Phase 1: Demo Sequence
    stdscr.erase()
    stdscr.addstr(1, 2, "Echo Challenge: Memorize the arrow beat pattern!")
    stdscr.refresh()
    time.sleep(1.0)

    for arrow in sequence:
        stdscr.erase()
        stdscr.addstr(3, 10, f"LISTEN: {arrow}", curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.6)
        stdscr.erase()
        stdscr.refresh()
        time.sleep(0.2)

    # Phase 2: Player Input Response
    feedback = "Your turn! Repeat the pattern!"
    while step < len(sequence):
        stdscr.erase()
        stdscr.addstr(1, 2, f"Echo Mode | Progress: {step}/{len(sequence)} | Score: {score}")
        stdscr.addstr(3, 2, feedback)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27: break

        pressed = key_map.get(key, "")
        if pressed == sequence[step]:
            score += 200
            step += 1
            feedback = f"Correct! Hit next arrow..."
        else:
            feedback = "WRONG ARROW! Game Over!"
            stdscr.erase()
            stdscr.addstr(3, 2, feedback)
            stdscr.refresh()
            time.sleep(1.5)
            return

    stdscr.erase()
    stdscr.addstr(3, 2, f"LEVEL COMPLETE! Total Score: {score}")
    stdscr.refresh()
    time.sleep(2.0)

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
            break

        g_type = selected.get("type", "piano")
        stdscr.nodelay(True)
        stdscr.timeout(0)

        if g_type == "piano":
            play_piano_level(stdscr, selected)
        elif g_type == "frog":
            play_frog_level(stdscr, selected)
        elif g_type == "echo":
            play_echo_level(stdscr, selected)

if __name__ == "__main__":
    curses.wrapper(main)
