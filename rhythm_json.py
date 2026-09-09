import curses
import json
import os
import random
import sys
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
import numpy as np

# --- AUDIO INITIALIZATION ---
AUDIO_AVAILABLE = False
for driver in ['alsa', 'pulse', 'dsp', 'dummy']:
    try:
        os.environ['SDL_AUDIODRIVER'] = driver
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        if driver != 'dummy':
            AUDIO_AVAILABLE = True
        break
    except Exception:
        continue

LANES = ['D', 'F', 'J', 'K']
LANE_KEYS = [ord('d'), ord('f'), ord('j'), ord('k'), ord('D'), ord('F'), ord('J'), ord('K')]
KEY_MAP = {
    ord('d'): 0, ord('D'): 0,
    ord('f'): 1, ord('F'): 1,
    ord('j'): 2, ord('J'): 2,
    ord('k'): 3, ord('K'): 3
}

HIGH_SCORE_FILE = "high_scores.json"
PLAYER_SCORES_FILE = "player_scores.json"

# --- SOUND GENERATORS ---
def generate_point_chime(pitch="deep", duration=0.05):
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        freq = 180 if pitch == "deep" else 360
        wave = np.sin(2 * np.pi * freq * t)
        envelope = np.exp(-t * 30)
        audio_data = (wave * envelope * 28000).astype(np.int16)
        stereo_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)
        return pygame.sndarray.make_sound(stereo_data)
    except Exception:
        return None

try:
    DEEP_SOUND = generate_point_chime("deep")
    DOOP_SOUND = generate_point_chime("doop")
except Exception:
    DEEP_SOUND, DOOP_SOUND = None, None

def play_point_rhythm(toggle_counter):
    sound_played = False
    if toggle_counter % 2 == 0:
        if DEEP_SOUND:
            try:
                DEEP_SOUND.play()
                sound_played = True
            except Exception: pass
    else:
        if DOOP_SOUND:
            try:
                DOOP_SOUND.play()
                sound_played = True
            except Exception: pass

    sys.stdout.write('\a')
    sys.stdout.flush()

# --- HIGH SCORE & PLAYER PERSISTENCE ---
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def save_player_game_run(player_name, total_score, levels_completed):
    data = load_json(PLAYER_SCORES_FILE)
    if player_name not in data:
        data[player_name] = {"high_score": 0, "runs": []}
    
    player = data[player_name]
    if total_score > player.get("high_score", 0):
        player["high_score"] = total_score
        
    player.setdefault("runs", []).append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "total_score": total_score,
        "levels_completed": levels_completed
    })
    save_json(PLAYER_SCORES_FILE, data)

def show_transition(stdscr, level_data, score, current_step=None, total_steps=None, cumulative_score=0):
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(3, 5, "==================================================", curses.A_BOLD)
    stdscr.addstr(4, 5, f" FINISHED: {level_data.get('title', 'Level')} ", curses.A_REVERSE)
    stdscr.addstr(5, 5, f" Level Score: {score}", curses.A_BOLD)
    if current_step is not None:
        stdscr.addstr(6, 5, f" Total Run Score So Far: {cumulative_score}", curses.A_BOLD)
        stdscr.addstr(8, 5, f" Progress: Level {current_step} of {total_steps} Complete", curses.A_DIM)

    stdscr.addstr(11, 5, "Next level loading...", curses.A_DIM)
    stdscr.addstr(12, 5, "Press 'Q' or ESC to return to Menu.")
    stdscr.refresh()

    stdscr.timeout(1500)
    key = stdscr.getch()
    stdscr.timeout(-1)
    if key in [27, ord('q'), ord('Q')]:
        return False
    return True

# --- MINIGAME LEVEL HANDLERS ---
def play_piano_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    song_file = level_data.get("song_file", "song.mp3")
    notes = level_data.get("notes", [])
    speed = level_data.get("speed", 6.0)
    hit_window = level_data.get("hit_window", 0.350)

    score, combo, feedback, feedback_time = 0, 0, "", 0
    hit_count = 0
    active_notes = [{"lane": n["lane"], "time": n["time"], "hit": False, "missed": False} for n in notes]

    for c in range(2, 0, -1):
        stdscr.erase()
        stdscr.addstr(5, 10, f"NEXT UP: {level_data.get('title')} - Starting in {c}...", curses.A_BOLD)
        stdscr.refresh()
        time.sleep(0.5)

    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

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
                hit_count += 1
                play_point_rhythm(hit_count)
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

        stdscr.addstr(0, 2, f"Song: {song_file} | Time: {current_time:.2f}s | Level Score: {score} | Run Total: {run_score + score}")
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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_frog_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    obstacles = level_data.get("obstacles", [])
    score, start_time, is_jumping, jump_start = 0, time.perf_counter(), False, 0
    hit_count = 0
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
            hit_count += 1
            play_point_rhythm(hit_count)

        if is_jumping and (current_time - jump_start > 0.4): is_jumping = False

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, f"LEVEL 2: {level_data.get('title')} | Press SPACE to Jump!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.1f}s")

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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_echo_level(stdscr, level_data, step=None, total=None, run_score=0):
    sequence = level_data.get("sequence", ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"])
    key_dict = {curses.KEY_UP: "KEY_UP", curses.KEY_DOWN: "KEY_DOWN", curses.KEY_LEFT: "KEY_LEFT", curses.KEY_RIGHT: "KEY_RIGHT"}
    stdscr.nodelay(False)

    stdscr.erase()
    stdscr.addstr(1, 2, f"LEVEL 3: {level_data.get('title')} - Watch sequence:")
    stdscr.refresh()
    time.sleep(0.5)

    for arrow in sequence:
        stdscr.addstr(5, 5, f"--> {arrow} <--   ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.35)
        stdscr.addstr(5, 5, " " * 30)
        stdscr.refresh()
        time.sleep(0.15)

    stdscr.erase()
    stdscr.addstr(1, 2, "LEVEL 3: Repeat using Arrow Keys:")
    stdscr.refresh()

    user_seq = []
    user_quit = False
    hit_count = 0
    while len(user_seq) < len(sequence):
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break
        if key in key_dict:
            user_seq.append(key_dict[key])
            hit_count += 1
            play_point_rhythm(hit_count)
            stdscr.addstr(6, 2 + (len(user_seq) * 12), f"[{key_dict[key]}]")
            stdscr.refresh()

    score = 500 if user_seq == sequence else 0
    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_noodle_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    noodles = level_data.get("noodles", [])
    score, hit_count, feedback = 0, 0, ""
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
        stdscr.addstr(1, 2, f"LEVEL 4: {level_data.get('title')} | Hold SPACEBAR while noodles pass!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.1f}s | Feedback: {feedback}")

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
                    hit_count += 1
                    play_point_rhythm(hit_count)
                    feedback = "SLURPING! (+5)"
                else:
                    feedback = "PRESS & HOLD SPACE!"

            if head_x < 60 and tail_x > 2:
                for x in range(max(2, head_x), min(60, tail_x)):
                    if x != mouth_x: stdscr.addch(mouth_y, x, '~')

        stdscr.refresh()
        time.sleep(0.015)
        if noodles and current_time > (noodles[-1]["time"] + noodles[-1]["duration"] + 1.5): break

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_space_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    enemies = level_data.get("enemies", [])
    speed = level_data.get("speed", 5.0)
    hit_window = level_data.get("hit_window", 0.350)
    active_enemies = [{"sector": e["sector"], "time": e["time"], "destroyed": False} for e in enemies]

    score, hit_count, lasers = 0, 0, []
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

            for enemy in active_enemies:
                if enemy["sector"] == pressed_sector and not enemy["destroyed"]:
                    diff = abs(enemy["time"] - current_time)
                    if diff <= hit_window:
                        enemy["destroyed"] = True
                        score += 200
                        hit_count += 1
                        play_point_rhythm(hit_count)

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(1, 2, f"LEVEL 5: {level_data.get('title')} | Press 1, 2, or 3 to shoot beat lasers!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.1f}s")

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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_drum_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    bpm = level_data.get("bpm", 120)
    beats = level_data.get("beats", [])
    hit_window = level_data.get("hit_window", 0.250)

    active_beats = [{"type": b["type"], "time": b["time"], "hit": False} for b in beats]
    score, hit_count = 0, 0
    start_time = time.perf_counter()
    user_quit = False

    while True:
        current_time = time.perf_counter() - start_time
        key = stdscr.getch()
        if key == 27:
            user_quit = True
            break

        if key in [ord(' '), 10, 13]:
            for b in active_beats:
                if not b["hit"] and abs(b["time"] - current_time) <= hit_window:
                    b["hit"] = True
                    score += 150
                    hit_count += 1
                    play_point_rhythm(hit_count)

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 6: {level_data.get('title')} (BPM: {bpm}) | Strike [SPACE/ENTER] on Beat!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.2f}s")

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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_chef_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    chops = level_data.get("chops", [])
    hit_window = level_data.get("hit_window", 0.300)
    active_chops = [{"time": c["time"], "hit": False} for c in chops]

    score, hit_count, last_chop_vis = 0, 0, 0
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
            for c in active_chops:
                if not c["hit"] and abs(c["time"] - current_time) <= hit_window:
                    c["hit"] = True
                    score += 120
                    hit_count += 1
                    play_point_rhythm(hit_count)

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 7: {level_data.get('title')} | Press 'C' or SPACE to Slice Veggies!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.2f}s")

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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

def play_matrix_level(stdscr, level_data, step=None, total=None, run_score=0):
    stdscr.nodelay(True)
    stdscr.timeout(0)
    bullets = level_data.get("bullets", [])
    hit_window = level_data.get("hit_window", 0.350)
    active_bullets = [{"lane": b["lane"], "time": b["time"], "dodged": False} for b in bullets]

    score, hit_count = 0, 0
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
            for b in active_bullets:
                if b["lane"] == lane and not b["dodged"]:
                    if abs(b["time"] - current_time) <= hit_window:
                        b["dodged"] = True
                        score += 250
                        hit_count += 1
                        play_point_rhythm(hit_count)

        stdscr.erase()
        stdscr.addstr(1, 2, f"LEVEL 8: {level_data.get('title')} | Press D, F, J, K to Dodge!")
        stdscr.addstr(2, 2, f"Level Score: {score} | Run Total: {run_score + score} | Time: {current_time:.2f}s")

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

    if user_quit: return False, score
    return show_transition(stdscr, level_data, score, step, total, run_score + score), score

# --- LEVEL DISPATCHER ---
def run_level(stdscr, level_data, step=None, total=None, run_score=0):
    g_type = level_data.get("type", "piano")
    if g_type == "piano": return play_piano_level(stdscr, level_data, step, total, run_score)
    elif g_type == "frog": return play_frog_level(stdscr, level_data, step, total, run_score)
    elif g_type == "echo": return play_echo_level(stdscr, level_data, step, total, run_score)
    elif g_type == "noodle": return play_noodle_level(stdscr, level_data, step, total, run_score)
    elif g_type == "space": return play_space_level(stdscr, level_data, step, total, run_score)
    elif g_type == "drum": return play_drum_level(stdscr, level_data, step, total, run_score)
    elif g_type == "chef": return play_chef_level(stdscr, level_data, step, total, run_score)
    elif g_type == "matrix": return play_matrix_level(stdscr, level_data, step, total, run_score)
    return True, 0

# --- NEW GAME: PLAYER NAME INPUT & 8-LEVEL RUN ---
def prompt_player_name(stdscr):
    curses.echo()
    curses.curs_set(1)
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(3, 4, "==================================================", curses.A_BOLD)
    stdscr.addstr(4, 4, "               NEW PLAYER PROFILE                 ", curses.A_REVERSE)
    stdscr.addstr(5, 4, "==================================================", curses.A_BOLD)
    stdscr.addstr(7, 4, "Enter Player Name: ")
    stdscr.refresh()
    
    player_name = stdscr.getstr(7, 23, 20).decode('utf-8').strip()
    curses.noecho()
    curses.curs_set(0)
    
    return player_name if player_name else "Player_1"

def start_new_player_game(stdscr, levels):
    if not levels: return
    player_name = prompt_player_name(stdscr)
    
    playlist = list(levels[:8])
    random.shuffle(playlist)
    total_levels = len(playlist)
    
    cumulative_score = 0
    completed_count = 0

    for idx, lvl in enumerate(playlist, start=1):
        continue_game, level_score = run_level(stdscr, lvl, step=idx, total=total_levels, run_score=cumulative_score)
        cumulative_score += level_score
        completed_count = idx
        if not continue_game:
            break

    # Save to Player Leaderboard File
    save_player_game_run(player_name, cumulative_score, completed_count)

    # Show Final Summary
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(3, 4, "==================================================", curses.A_BOLD)
    stdscr.addstr(4, 4, f" GAME OVER - {player_name.upper()}'S RUN SUMMARY ", curses.A_REVERSE)
    stdscr.addstr(5, 4, "==================================================", curses.A_BOLD)
    stdscr.addstr(7, 4, f" Total Run Score: {cumulative_score}", curses.A_BOLD)
    stdscr.addstr(8, 4, f" Levels Completed: {completed_count} / {total_levels}")
    stdscr.addstr(11, 4, "Score saved to Player Scoreboard!")
    stdscr.addstr(13, 4, "Press any key to return to Main Menu...")
    stdscr.refresh()
    stdscr.getch()

# --- OLD GAMES & PLAYER SCOREBOARD ---
def show_player_scoreboard(stdscr):
    data = load_json(PLAYER_SCORES_FILE)
    stdscr.nodelay(False)
    
    while True:
        stdscr.erase()
        stdscr.addstr(1, 2, "==========================================================", curses.A_BOLD)
        stdscr.addstr(2, 2, "            OLD GAMES & PLAYER SCOREBOARD                 ", curses.A_BOLD)
        stdscr.addstr(3, 2, "==========================================================", curses.A_BOLD)

        if not data:
            stdscr.addstr(6, 4, "No player history recorded yet. Start a New Game!")
        else:
            stdscr.addstr(5, 4, f"{'PLAYER NAME':<20} | {'BEST RUN SCORE':<15} | {'TOTAL RUNS':<10}", curses.A_REVERSE)
            sorted_players = sorted(data.items(), key=lambda x: x[1].get('high_score', 0), reverse=True)
            
            for idx, (p_name, p_data) in enumerate(sorted_players[:10]):
                runs_count = len(p_data.get("runs", []))
                best_s = p_data.get("high_score", 0)
                stdscr.addstr(7 + idx, 4, f"{p_name:<20} | {best_s:<15} | {runs_count:<10}")

        stdscr.addstr(19, 2, "Press [V] to View Specific Player Matches, or 'Q' / ESC for Menu.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), 27]:
            break
        elif key in [ord('v'), ord('V')] and data:
            view_individual_player_history(stdscr, data)

def view_individual_player_history(stdscr, data):
    p_name = prompt_player_name(stdscr)
    if p_name not in data:
        stdscr.erase()
        stdscr.addstr(5, 4, f"No records found for player: '{p_name}'", curses.A_BOLD)
        stdscr.addstr(7, 4, "Press any key to return...")
        stdscr.refresh()
        stdscr.getch()
        return

    player_data = data[p_name]
    runs = player_data.get("runs", [])

    stdscr.erase()
    stdscr.addstr(1, 2, f"=== MATCH HISTORY FOR: {p_name.upper()} ===", curses.A_BOLD)
    stdscr.addstr(3, 4, f"{'DATE/TIME':<20} | {'TOTAL SCORE':<12} | {'LEVELS COMPLETED':<15}", curses.A_REVERSE)

    for idx, run in enumerate(reversed(runs[-10:])):
        ts = run.get("timestamp", "N/A")
        score = run.get("total_score", 0)
        completed = run.get("levels_completed", 0)
        stdscr.addstr(5 + idx, 4, f"{ts:<20} | {score:<12} | {completed:<15}")

    stdscr.addstr(18, 2, "Press any key to back...")
    stdscr.refresh()
    stdscr.getch()

# --- MAIN MENU ---
def main(stdscr):
    curses.curs_set(0)

    if os.path.exists("song.json"):
        with open("song.json", "r") as f:
            levels = json.load(f).get("levels", [])
    else: levels = []

    while True:
        stdscr.nodelay(False)
        stdscr.erase()
        stdscr.addstr(1, 2, "==========================================================", curses.A_BOLD)
        stdscr.addstr(2, 2, "               RHYTHM GAME ENGINE MAIN MENU               ", curses.A_BOLD)
        stdscr.addstr(3, 2, "==========================================================", curses.A_BOLD)

        stdscr.addstr(6, 6, "[1] NEW GAME          (Enter Name & Run 8 Random Levels)", curses.A_BOLD)
        stdscr.addstr(8, 6, "[2] OLD GAMES / BOARD (View Player Profiles & Leaderboards)")
        stdscr.addstr(10, 6, "[3] EXIT GAME", curses.A_DIM)

        stdscr.addstr(15, 2, "Press 1, 2, or 3 to make a selection.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [ord('3'), ord('q'), ord('Q'), 27]: 
            break
        elif key == ord('1'):
            start_new_player_game(stdscr, levels)
        elif key == ord('2'):
            show_player_scoreboard(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
