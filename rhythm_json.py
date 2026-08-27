import curses
import json
import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

pygame.mixer.init()

LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k'), ord('D'), ord('F'), ord('J'), ord('K')]
KEY_MAP = {
    ord('d'): 0, ord('D'): 0,
    ord('f'): 1, ord('F'): 1,
    ord('j'): 2, ord('J'): 2,
    ord('k'): 3, ord('K'): 3
}

# --- LEVEL 1: PIANO TRACK ---
def play_piano_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    song_file = level_data.get("song_file", "song.mp3")
    notes = level_data.get("notes", [])
    speed = level_data.get("speed", 6.0)
    hit_window = level_data.get("hit_window", 0.350)

    audio_active = False
    if os.path.exists(song_file):
        try:
            pygame.mixer.music.load(song_file)
            pygame.mixer.music.set_volume(0.8)
            audio_active = True
        except Exception:
            audio_active = False

    score, combo, feedback, feedback_time = 0, 0, "", 0
    active_notes = [{"lane": n["lane"], "time": n["time"], "hit": False, "missed": False} for n in notes]

    for c in range(3, 0, -1):
        stdscr.erase()
        stdscr.addstr(5, 10, f"READY? Starting in {c}...", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1)

    start_time = time.perf_counter()
    if audio_active:
        pygame.mixer.music.play()

    while True:
        if audio_active and pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000.0
            if current_time < 0:
                current_time = time.perf_counter() - start_time
        else:
            current_time = time.perf_counter() - start_time

        key = stdscr.getch()
        if key == 27: break

        if key in LANE_KEYS:
            target_lane = KEY_MAP[key]
            closest_note, min_diff = None, float('inf')
            for note in active_notes:
                if note["lane"] == target_lane and not note["hit"] and not note["missed"]:
                    diff = abs(note["time"] - current_time)
                    if diff < min_diff:
                        min_diff, closest_note = diff, note

            if closest_note and min_diff <= hit_window:
                closest_note["hit"] = True
                score += 100
                combo += 1
                feedback, feedback_time = "PERFECT!", current_time
            else:
                combo = 0
                feedback, feedback_time = "MISS!", current_time

        for note in active_notes:
            if not note["hit"] and not note["missed"] and (current_time - note["time"]) > hit_window:
                note["missed"] = True
                combo = 0
                feedback, feedback_time = "MISS!", current_time

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        lane_width, start_x, hit_line_y = 8, 4, height - 4

        stdscr.addstr(0, 2, f"Song: {song_file} | Time: {current_time:.2f}s | Score: {score} | Combo: {combo}")
        for i, lane in enumerate(LANES):
            x = start_x + (i * lane_width)
            stdscr.addstr(2, x + 2, f"[{lane}]", curses.A_BOLD)
            for y in range(3, hit_line_y): stdscr.addstr(y, x + 3, "|")

        stdscr.addstr(hit_line_y, start_x - 1, "=" * (len(LANES) * lane_width + 4), curses.A_REVERSE)

        for note in active_notes:
            if note["hit"] or note["missed"]: continue
            y_pos = int(hit_line_y - ((note["time"] - current_time) * speed))
            if 3 <= y_pos < hit_line_y:
                stdscr.addstr(y_pos, start_x + (note["lane"] * lane_width) + 2, "O", curses.A_BOLD)

        if current_time - feedback_time < 0.5:
            stdscr.addstr(hit_line_y + 2, start_x + 6, feedback, curses.A_BOLD)

        stdscr.refresh()
        time.sleep(0.005)

        if all(n["hit"] or n["missed"] for n in active_notes) and (current_time > (notes[-1]["time"] + 1.0 if notes else 5.0)):
            break

    if audio_active: pygame.mixer.music.stop()

# --- LEVEL 2: FROG JUMP ---
def play_frog_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    obstacles = level_data.get("obstacles", [])
    score, start_time, is_jumping, jump_start = 0, time.perf_counter(), False, 0

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27: break
        elif key == ord(' ') and not is_jumping:
            is_jumping = True
            jump_start = current_time
            score += 50

        if is_jumping and (current_time - jump_start > 0.4): is_jumping = False

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, "LEVEL 2: FROG JUMP | Press SPACE to Jump!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s")

        ground_y = 10
        stdscr.addstr(ground_y, 0, "_" * (width - 1))
        frog_y = ground_y - 2 if is_jumping else ground_y - 1
        stdscr.addstr(frog_y, 10, "(🐸)", curses.A_BOLD)

        for obs in obstacles:
            t_diff = obs["time"] - current_time
            if -1.0 <= t_diff <= 4.0:
                obs_x = int(10 + (t_diff * 15))
                if 0 < obs_x < width - 2: stdscr.addstr(ground_y - 1, obs_x, "🌵")

        stdscr.refresh()
        time.sleep(0.01)
        if obstacles and current_time > (obstacles[-1]["time"] + 2.0): break

# --- LEVEL 3: ECHO BEAT ---
def play_echo_level(stdscr, level_data):
    sequence = level_data.get("sequence", ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"])
    key_dict = {curses.KEY_UP: "KEY_UP", curses.KEY_DOWN: "KEY_DOWN", curses.KEY_LEFT: "KEY_LEFT", curses.KEY_RIGHT: "KEY_RIGHT"}
    stdscr.nodelay(False)

    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: ECHO BEAT CHALLENGE - Watch sequence:")
    stdscr.refresh()
    time.sleep(1)

    for arrow in sequence:
        stdscr.addstr(5, 5, f"--> {arrow} <--   ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.6)
        stdscr.addstr(5, 5, " " * 30)
        stdscr.refresh()
        time.sleep(0.2)

    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: Repeat using Arrow Keys:")
    stdscr.refresh()

    user_seq = []
    while len(user_seq) < len(sequence):
        key = stdscr.getch()
        if key == 27: return
        if key in key_dict:
            user_seq.append(key_dict[key])
            stdscr.addstr(6, 2 + (len(user_seq) * 12), f"[{key_dict[key]}]")
            stdscr.refresh()

    time.sleep(0.5)
    stdscr.erase()
    if user_seq == sequence: stdscr.addstr(4, 5, "SUCCESS! Sequence Matched!", curses.A_BOLD)
    else: stdscr.addstr(4, 5, "FAILED! Mismatch.", curses.A_BOLD)
    stdscr.refresh()
    time.sleep(1.5)

# --- LEVEL 4: NOODLE SLURP (HOLD KEY GAME) ---
def play_noodle_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    noodles = level_data.get("noodles", [])

    score, combo = 0, 0
    feedback = ""
    start_time = time.perf_counter()

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27: break

        is_holding_space = (key == ord(' '))

        stdscr.erase()
        stdscr.addstr(1, 2, "LEVEL 4: NOODLE SLURP | Hold SPACEBAR while noodles pass through mouth!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s | Feedback: {feedback}")

        mouth_x = 15
        mouth_y = 6
        stdscr.addstr(mouth_y - 1, mouth_x - 4, "┌──────┐")
        mouth_str = "│ ( >◡< ) │" if is_holding_space else "│ ( >o< ) │"
        stdscr.addstr(mouth_y, mouth_x - 4, mouth_str, curses.A_BOLD)
        stdscr.addstr(mouth_y + 1, mouth_x - 4, "└──────┘")

        # Track active slurp
        actively_slurping = False
        for ndl in noodles:
            start_t = ndl["time"]
            end_t = start_t + ndl["duration"]

            # Draw approaching/passing noodle segment
            t_diff = start_t - current_time
            head_x = int(mouth_x + (t_diff * 10))
            tail_x = int(head_x + (ndl["duration"] * 10))

            if start_t <= current_time <= end_t:
                actively_slurping = True
                if is_holding_space:
                    score += 5
                    feedback = "SLURPING! (+5)"
                else:
                    feedback = "PRESS & HOLD SPACE!"

            if head_x < 60 and tail_x > 2:
                for x in range(max(2, head_x), min(60, tail_x)):
                    if x != mouth_x: stdscr.addch(mouth_y, x, '~')

        if not actively_slurping and is_holding_space:
            feedback = "DONT CHEW AIR!"

        stdscr.refresh()
        time.sleep(0.015)
        if noodles and current_time > (noodles[-1]["time"] + noodles[-1]["duration"] + 1.5): break

# --- LEVEL 5: SPACE BEAT BLAST (SECTOR SHOOTER) ---
def play_space_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    enemies = level_data.get("enemies", [])
    speed = level_data.get("speed", 5.0)
    hit_window = level_data.get("hit_window", 0.350)
    active_enemies = [{"sector": e["sector"], "time": e["time"], "destroyed": False} for e in enemies]

    score = 0
    lasers = []
    start_time = time.perf_counter()

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27: break

        pressed_sector = -1
        if key == ord('1'): pressed_sector = 0
        elif key == ord('2'): pressed_sector = 1
        elif key == ord('3'): pressed_sector = 2

        if pressed_sector != -1:
            lasers.append({"sector": pressed_sector, "start_time": current_time})
            # Check hit against enemy
            for enemy in active_enemies:
                if enemy["sector"] == pressed_sector and not enemy["destroyed"]:
                    diff = abs(enemy["time"] - current_time)
                    if diff <= hit_window:
                        enemy["destroyed"] = True
                        score += 200

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, "LEVEL 5: SPACE BEAT BLAST | Press 1, 2, or 3 to shoot beat lasers!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s")

        sector_xs = [10, 25, 40]
        ship_y = height - 4

        # Draw Sectors & Player Cannons
        for s_idx, x in enumerate(sector_xs):
            stdscr.addstr(ship_y, x - 1, f"[{s_idx + 1}]^", curses.A_BOLD)

        # Draw Lasers
        for laser in lasers:
            elapsed = current_time - laser["start_time"]
            if elapsed < 0.2:
                lx = sector_xs[laser["sector"]] + 1
                for ly in range(4, ship_y): stdscr.addch(ly, lx, '|', curses.A_BOLD)

        # Draw Enemies
        for enemy in active_enemies:
            if enemy["destroyed"]: continue
            t_diff = enemy["time"] - current_time
            y_pos = int(ship_y - (t_diff * speed))
            if 4 <= y_pos <= ship_y:
                ex = sector_xs[enemy["sector"]]
                stdscr.addstr(y_pos, ex, "<V>", curses.A_REVERSE)

        stdscr.refresh()
        time.sleep(0.01)
        if active_enemies and current_time > (enemies[-1]["time"] + 2.0): break

# --- MENU ROUTER ---
def main(stdscr):
    curses.curs_set(0)

    if os.path.exists("song.json"):
        with open("song.json", "r") as f:
            levels = json.load(f).get("levels", [])
    else: levels = []

    while True:
        stdscr.nodelay(False)
        stdscr.erase()
        stdscr.addstr(1, 2, "==========================================", curses.A_BOLD)
        stdscr.addstr(2, 2, "     5-LEVEL RHYTHM MINI-GAME ENGINE      ", curses.A_BOLD)
        stdscr.addstr(3, 2, "==========================================", curses.A_BOLD)

        for i, lvl in enumerate(levels):
            stdscr.addstr(5 + i, 4, f"{i + 1}. {lvl.get('title', 'Untitled')}")

        stdscr.addstr(12, 2, "Press 1-5 to play. Press 'Q' to quit.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]: break
        elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
            idx = int(chr(key)) - 1
            if idx < len(levels):
                lvl = levels[idx]
                g_type = lvl.get("type", "piano")

                if g_type == "piano": play_piano_level(stdscr, lvl)
                elif g_type == "frog": play_frog_level(stdscr, lvl)
                elif g_type == "echo": play_echo_level(stdscr, lvl)
                elif g_type == "noodle": play_noodle_level(stdscr, lvl)
                elif g_type == "space": play_space_level(stdscr, lvl)

if __name__ == "__main__":
    curses.wrapper(main)
