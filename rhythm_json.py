import curses
import json
import os
import random
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import numpy as np

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k'), ord('D'), ord('F'), ord('J'), ord('K')]
KEY_MAP = {
    ord('d'): 0, ord('D'): 0,
    ord('f'): 1, ord('F'): 1,
    ord('j'): 2, ord('J'): 2,
    ord('k'): 3, ord('K'): 3
}

HIGH_SCORE_FILE = "high_scores.json"

# --- AUDIO SYNTHESIZER FOR HIT SOUNDS ---
def generate_hit_sound(frequency=520, duration=0.06):
    """Generates a quick synthetic hit pop sound in memory."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-t * 35)
    audio_data = (wave * envelope * 32767).astype(np.int16)
    stereo_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
    return pygame.sndarray.make_sound(stereo_data)

def generate_noise_sound(duration=0.08):
    """Generates a noise burst for drum snares/knife chops."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, n_samples)
    envelope = np.exp(-np.linspace(0, duration, n_samples) * 30)
    audio_data = (noise * envelope * 20000).astype(np.int16)
    stereo_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
    return pygame.sndarray.make_sound(stereo_data)

try:
    LANE_SOUNDS = [
        generate_hit_sound(440, 0.06),  # D - A4
        generate_hit_sound(554, 0.06),  # F - C#5
        generate_hit_sound(659, 0.06),  # J - E5
        generate_hit_sound(880, 0.06)   # K - A5
    ]
    CHOP_SOUND = generate_noise_sound(0.05)
    DRUM_SOUND = generate_noise_sound(0.12)
except Exception:
    LANE_SOUNDS = [None, None, None, None]
    CHOP_SOUND = None
    DRUM_SOUND = None

# --- HIGH SCORE PERSISTENCE ---
def load_high_scores():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_high_score(level_id, score):
    scores = load_high_scores()
    current_high = scores.get(str(level_id), 0)
    if score > current_high:
        scores[str(level_id)] = score
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump(scores, f, indent=2)
        return True, score
    return False, current_high

# --- LEVEL TRANSITION OVERLAY ---
def show_transition(stdscr, level_data, score):
    is_new_high, best_score = save_high_score(level_data.get("level_id", 1), score)
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(3, 5, "==================================================", curses.A_BOLD)
    stdscr.addstr(4, 5, f" FINISHED: {level_data.get('title', 'Level')} ", curses.A_REVERSE)
    stdscr.addstr(5, 5, f" Score Achieved: {score}", curses.A_BOLD)
    if is_new_high:
        stdscr.addstr(7, 5, " ★ NEW HIGH SCORE! ★", curses.A_BOLD | curses.A_REVERSE)
    else:
        stdscr.addstr(7, 5, f" Personal Best: {best_score}")

    stdscr.addstr(10, 5, "Next randomized level loading in 2 seconds...", curses.A_DIM)
    stdscr.addstr(11, 5, "Press 'Q' or ESC to exit to Menu.")
    stdscr.refresh()

    stdscr.timeout(2000)
    key = stdscr.getch()
    stdscr.timeout(-1)
    if key in [27, ord('q'), ord('Q')]:
        return False
    return True

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

    for c in range(2, 0, -1):
        stdscr.erase()
        stdscr.addstr(5, 10, f"NEXT UP: {level_data.get('title')} - Starting in {c}...", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(0.8)

    start_time = time.perf_counter()
    if audio_active:
        pygame.mixer.music.play()

    user_quit = False
    while True:
        if audio_active and pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000.0
            if current_time < 0:
                current_time = time.perf_counter() - start_time
        else:
            current_time = time.perf_counter() - start_time

        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        if key in LANE_KEYS:
            target_lane = KEY_MAP[key]
            if LANE_SOUNDS[target_lane]:
                LANE_SOUNDS[target_lane].play()

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
    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 2: FROG JUMP ---
def play_frog_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    obstacles = level_data.get("obstacles", [])
    score, start_time, is_jumping, jump_start = 0, time.perf_counter(), False, 0
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break
        elif key == ord(' ') and not is_jumping:
            is_jumping = True
            jump_start = current_time
            score += 50
            if LANE_SOUNDS[0]: LANE_SOUNDS[0].play()

        if is_jumping and (current_time - jump_start > 0.4): is_jumping = False

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, f"LEVEL 2: {level_data.get('title')} | Press SPACE to Jump!")
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

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 3: ECHO BEAT ---
def play_echo_level(stdscr, level_data):
    sequence = level_data.get("sequence", ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"])
    key_dict = {curses.KEY_UP: "KEY_UP", curses.KEY_DOWN: "KEY_DOWN", curses.KEY_LEFT: "KEY_LEFT", curses.KEY_RIGHT: "KEY_RIGHT"}
    stdscr.nodelay(False)

    stdscr.erase()
    stdscr.addstr(1, 2, f"LEVEL 3: {level_data.get('title')} - Watch sequence:")
    stdscr.refresh()
    time.sleep(0.8)

    for arrow in sequence:
        stdscr.addstr(5, 5, f"--> {arrow} <--   ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.5)
        stdscr.addstr(5, 5, " " * 30)
        stdscr.refresh()
        time.sleep(0.15)

    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: Repeat using Arrow Keys:")
    stdscr.refresh()

    user_seq = []
    user_quit = False
    while len(user_seq) < len(sequence):
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break
        if key in key_dict:
            user_seq.append(key_dict[key])
            if LANE_SOUNDS[len(user_seq) % 4]: LANE_SOUNDS[len(user_seq) % 4].play()
            stdscr.addstr(6, 2 + (len(user_seq) * 12), f"[{key_dict[key]}]")
            stdscr.refresh()

    if user_quit: return False
    score = 500 if user_seq == sequence else 0
    return show_transition(stdscr, level_data, score)

# --- LEVEL 4: NOODLE SLURP ---
def play_noodle_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    noodles = level_data.get("noodles", [])

    score = 0
    feedback = ""
    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        is_holding_space = (key == ord(' '))

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 4: {level_data.get('title')} | Hold SPACEBAR while noodles pass through mouth!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s | Feedback: {feedback}")

        mouth_x, mouth_y = 15, 6
        stdscr.addstr(mouth_y - 1, mouth_x - 4, "┌──────┐")
        mouth_str = "│ ( >◡< ) │" if is_holding_space else "│ ( >o< ) │"
        stdscr.addstr(mouth_y, mouth_x - 4, mouth_str, curses.A_BOLD)
        stdscr.addstr(mouth_y + 1, mouth_x - 4, "└──────┘")

        actively_slurping = False
        for ndl in noodles:
            start_t = ndl["time"]
            end_t = start_t + ndl["duration"]
            head_x = int(mouth_x + ((start_t - current_time) * 10))
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

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 5: SPACE BEAT BLAST ---
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
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        pressed_sector = -1
        if key == ord('1'): pressed_sector = 0
        elif key == ord('2'): pressed_sector = 1
        elif key == ord('3'): pressed_sector = 2

        if pressed_sector != -1:
            lasers.append({"sector": pressed_sector, "start_time": current_time})
            if LANE_SOUNDS[pressed_sector]: LANE_SOUNDS[pressed_sector].play()

            for enemy in active_enemies:
                if enemy["sector"] == pressed_sector and not enemy["destroyed"]:
                    diff = abs(enemy["time"] - current_time)
                    if diff <= hit_window:
                        enemy["destroyed"] = True
                        score += 200

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, f"LEVEL 5: {level_data.get('title')} | Press 1, 2, or 3 to shoot beat lasers!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.1f}s")

        sector_xs = [10, 25, 40]
        ship_y = height - 4

        for s_idx, x in enumerate(sector_xs):
            stdscr.addstr(ship_y, x - 1, f"[{s_idx + 1}]^", curses.A_BOLD)

        for laser in lasers:
            elapsed = current_time - laser["start_time"]
            if elapsed < 0.2:
                lx = sector_xs[laser["sector"]] + 1
                for ly in range(4, ship_y): stdscr.addch(ly, lx, '|', curses.A_BOLD)

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

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 6: DRUM ROLL ---
def play_drum_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    bpm = level_data.get("bpm", 120)
    beats = level_data.get("beats", [])
    hit_window = level_data.get("hit_window", 0.250)

    active_beats = [{"type": b["type"], "time": b["time"], "hit": False} for b in beats]
    score = 0
    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        if key in [ord(' '), 10, 13]:
            if DRUM_SOUND: DRUM_SOUND.play()
            for b in active_beats:
                if not b["hit"] and abs(b["time"] - current_time) <= hit_window:
                    b["hit"] = True
                    score += 150

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 6: {level_data.get('title')} (BPM: {bpm}) | Strike [SPACE/ENTER] on Beat!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.2f}s")

        ring_state = int(current_time * 8) % 4
        frames = ["(  O  )", "( -O- )", "( |O| )", "( /O/ )"]
        stdscr.addstr(5, 10, f"DRUM KIT: {frames[ring_state]}", curses.A_BOLD)

        track_y = 8
        stdscr.addstr(track_y, 2, "[" + "=" * 50 + "]")
        marker_x = int(2 + ((current_time % 4.0) / 4.0) * 50)
        stdscr.addch(track_y, min(51, max(2, marker_x)), 'I', curses.A_REVERSE)

        for b in active_beats:
            if not b["hit"]:
                bx = int(2 + ((b["time"] % 4.0) / 4.0) * 50)
                if 2 <= bx <= 51:
                    stdscr.addch(track_y - 1, bx, 'v')

        stdscr.refresh()
        time.sleep(0.01)
        if active_beats and current_time > (beats[-1]["time"] + 1.5): break

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 7: RHYTHM CHEF ---
def play_chef_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    chops = level_data.get("chops", [])
    hit_window = level_data.get("hit_window", 0.300)
    active_chops = [{"time": c["time"], "hit": False} for c in chops]

    score = 0
    last_chop_vis = 0
    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        if key in [ord('c'), ord('C'), ord(' ')]:
            last_chop_vis = current_time
            if CHOP_SOUND: CHOP_SOUND.play()

            for c in active_chops:
                if not c["hit"] and abs(c["time"] - current_time) <= hit_window:
                    c["hit"] = True
                    score += 120

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 7: {level_data.get('title')} | Press 'C' or SPACE to Slice Veggies!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.2f}s")

        knife_char = " | " if (current_time - last_chop_vis) > 0.1 else "\\|/"
        stdscr.addstr(5, 12, f" Knife: {knife_char}")
        stdscr.addstr(6, 4, "[BOARD] === (🥕) === (🧅) === (🍄) ===")

        for c in active_chops:
            if not c["hit"]:
                dx = int(35 - ((c["time"] - current_time) * 12))
                if 4 <= dx <= 50:
                    stdscr.addstr(7, dx, "^")

        stdscr.refresh()
        time.sleep(0.01)
        if active_chops and current_time > (chops[-1]["time"] + 1.5): break

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL 8: MATRIX BULLET TIME ---
def play_matrix_level(stdscr, level_data):
    stdscr.nodelay(True)
    stdscr.timeout(0)

    bullets = level_data.get("bullets", [])
    hit_window = level_data.get("hit_window", 0.350)
    active_bullets = [{"lane": b["lane"], "time": b["time"], "dodged": False} for b in bullets]

    score = 0
    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        if key in LANE_KEYS:
            lane = KEY_MAP[key]
            if LANE_SOUNDS[lane]: LANE_SOUNDS[lane].play()

            for b in active_bullets:
                if b["lane"] == lane and not b["dodged"]:
                    if abs(b["time"] - current_time) <= hit_window:
                        b["dodged"] = True
                        score += 250

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 8: {level_data.get('title')} | Press D, F, J, K to Dodge!")
        stdscr.addstr(2, 2, f"Score: {score} | Time: {current_time:.2f}s")

        for i, l in enumerate(LANES):
            stdscr.addstr(4, 6 + (i * 10), f"[{l}]")

        for b in active_bullets:
            if not b["dodged"]:
                y_pos = int(18 - ((b["time"] - current_time) * 8))
                if 5 <= y_pos <= 18:
                    stdscr.addstr(y_pos, 6 + (b["lane"] * 10), "║|║", curses.A_BOLD)

        stdscr.addstr(18, 2, "DODGE ZONE =========================================")

        stdscr.refresh()
        time.sleep(0.01)
        if active_bullets and current_time > (bullets[-1]["time"] + 1.5): break

    if user_quit: return False
    return show_transition(stdscr, level_data, score)

# --- LEVEL DISPATCHER ---
def run_level(stdscr, level_data):
    g_type = level_data.get("type", "piano")
    if g_type == "piano": return play_piano_level(stdscr, level_data)
    elif g_type == "frog": return play_frog_level(stdscr, level_data)
    elif g_type == "echo": return play_echo_level(stdscr, level_data)
    elif g_type == "noodle": return play_noodle_level(stdscr, level_data)
    elif g_type == "space": return play_space_level(stdscr, level_data)
    elif g_type == "drum": return play_drum_level(stdscr, level_data)
    elif g_type == "chef": return play_chef_level(stdscr, level_data)
    elif g_type == "matrix": return play_matrix_level(stdscr, level_data)
    return True

# --- RANDOMIZED SHUFFLE RUNNER ---
def start_random_endless_mode(stdscr, levels):
    if not levels: return
    
    # Shuffle level order continuously
    while True:
        playlist = list(levels)
        random.shuffle(playlist)

        for lvl in playlist:
            continue_game = run_level(stdscr, lvl)
            if not continue_game:
                return

# --- MENU ROUTER ---
def main(stdscr):
    curses.curs_set(0)

    if os.path.exists("song.json"):
        with open("song.json", "r") as f:
            levels = json.load(f).get("levels", [])
    else: levels = []

    while True:
        high_scores = load_high_scores()
        stdscr.nodelay(False)
        stdscr.erase()
        stdscr.addstr(1, 2, "==========================================================", curses.A_BOLD)
        stdscr.addstr(2, 2, "        8-LEVEL SHUFFLED CONTINUOUS RHYTHM ENGINE         ", curses.A_BOLD)
        stdscr.addstr(3, 2, "==========================================================", curses.A_BOLD)

        stdscr.addstr(5, 4, "[R] PLAY RANDOM SHUFFLED MODE (Continuous Progression)", curses.A_BOLD | curses.A_REVERSE)

        stdscr.addstr(7, 2, "--- Or Practice Individual Levels ---", curses.A_DIM)
        for i, lvl in enumerate(levels):
            lvl_id = str(lvl.get("level_id", i + 1))
            best = high_scores.get(lvl_id, 0)
            title = lvl.get('title', 'Untitled')
            stdscr.addstr(9 + i, 4, f"{i + 1}. {title:<36} | High Score: {best}")

        stdscr.addstr(18, 2, "Press 'R' for Random Arcade Mode, 1-8 for Practice, or 'Q' to Quit.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]: break
        elif key in [ord('r'), ord('R')]:
            start_random_endless_mode(stdscr, levels)
        elif key in [ord(str(n)) for n in range(1, 9)]:
            idx = int(chr(key)) - 1
            if idx < len(levels):
                run_level(stdscr, levels[idx])

if __name__ == "__main__":
    curses.wrapper(main)
