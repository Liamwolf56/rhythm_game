# 8-Level Terminal Rhythm Engine

A lightweight, multi-mode terminal rhythm game engine built in Python using `curses`, `pygame.mixer`, and `numpy`. Designed to run seamlessly in Linux environments, including **WSL (Windows Subsystem for Linux)**.

Featuring 8 unique rhythm mini-game mechanics, procedural audio synthesis with zero external MP3 dependencies required for hit feedback, high score tracking, and flexible JSON level configuration.

---

## Features

- **8 Distinct Rhythm Modes:**
  1. **Piano Lane Dash:** Classic 4-lane scrolling note drop (`D`, `F`, `J`, `K`).
  2. **Frog Beat Jump:** Obstacle dodge timing game using `SPACE`.
  3. **Echo Sequence:** Memory-based pattern repeating using Arrow Keys.
  4. **Noodle Slurp Tempo:** Hold-note duration gauge mechanic using `SPACE`.
  5. **Space Beat Blast:** 3-sector targeting defense using `1`, `2`, `3`.
  6. **Drum Roll Beat Maker:** BPM-synced metronome hit timing using `SPACE`/`ENTER`.
  7. **Rhythm Chef Veggie Chop:** Rapid-fire cooking slash precision using `C` or `SPACE`.
  8. **Matrix Bullet Dodge:** Dynamic lane bullet weaving using `D`, `F`, `J`, `K`.
- **Procedural Sound Engine:** Low-latency hit feedback generated dynamically in memory using `numpy` sine wave and noise burst audio synthesis.
- **Persistent High Scores:** Local score persistence per level stored in `high_scores.json`.
- **JSON Level Customization:** Easy level creation, speed adjustment, and note mapping via `song.json`.

---

## Prerequisites & Installation

### 1. System Dependencies (WSL / Ubuntu)

Ensure system Python and audio drivers are available:

```bash
sudo apt update
sudo apt install -y python3 python3-pip libsdl2-mixer-2.0-0
2. Python PackagesInstall required dependencies:Bashpip install pygame numpy
Quick StartClone the Repository:Bashgit clone [https://github.com/Liamwolf56/rhythm_game.git](https://github.com/Liamwolf56/rhythm_game.git)
cd rhythm_game
Run the Game Engine:Bashpython3 rhythm_json.py
ControlsMode / ScreenActionKey BindsMain MenuSelect Level1 - 8Main MenuQuit GameQ or ESCLanes (Piano / Matrix)Hit / Dodge LanesD, F, J, KSpace BlastFire Sector Lasers1, 2, 3Echo BeatFollow SequenceUp, Down, Left, RightChef / Drum / FrogAction / Chop / JumpSPACE, ENTER, CLevel Configuration (song.json)Levels are defined dynamically inside song.json. You can extend level durations, adjust hit windows, or add new levels by altering the structure:JSON{
  "level_id": 1,
  "type": "piano",
  "title": "Piano Lane Dash",
  "speed": 6.0,
  "hit_window": 0.35,
  "notes": [
    {"lane": 0, "time": 1.0},
    {"lane": 1, "time": 1.4}
  ]
}
Project StructurePlaintextrhythm_game/
├── rhythm_json.py     # Main engine, game loops & audio synthesizer
├── song.json          # Level data configurations & timings
├── high_scores.json   # Persistent score tracking (generated)
└── README.md          # Project documentation

---

### Step 2: Push to GitHub

Run this command in your WSL terminal to write and commit the README directly:

```bash
git add README.md
git commit -m "Add documentation for 8-level rhythm engine"
git push origin main
