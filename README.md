# Python Rhythm & Arcade Engine

A terminal-based, multi-minigame rhythm engine built with **Python**, **Curses**, and **Pygame**. Features 8 distinct rhythm/arcade game modes, custom audio synthesized via **NumPy**, custom player profile history, and continuous scoring across randomized 8-level runs.

---

## Key Features

* **Multi-Player Profiles & History:** Input player names before each run to track total scores across matches in `player_scores.json`.
* **8-Level Randomized Campaign:** Automatically shuffles and plays through all 8 distinct mini-game levels, accumulating a total score across the entire run.
* **Global & Player Scoreboards:** View top player run totals or search match logs for specific player names.
* **8 Arcade Mini-Game Types:**
  1. **Piano Roll:** 4-lane falling notes (`D`, `F`, `J`, `K`).
  2. **Frog Jump:** Obstacle jumper timing (`SPACE`).
  3. **Echo Pattern:** Memory-sequence rhythm repetition (Arrow Keys).
  4. **Noodle Slurp:** Hold-down sustain note timing (`SPACE`).
  5. **Space Shooter:** Multi-sector target clearing (`1`, `2`, `3`).
  6. **Drum Kit:** On-beat ring timing (`SPACE` / `ENTER`).
  7. **Chef Slice:** Precision chopping rhythm (`C` / `SPACE`).
  8. **Matrix Dodge:** Fast-reaction bullet dodging (`D`, `F`, `J`, `K`).
* **Dynamic Audio Engine:** Real-time pulse sound effects synthesized using `pygame.mixer` and `numpy`.

---

## Quick Start

### 1. Prerequisites & Dependencies

Ensure you have Python 3 and the required libraries installed:

```bash
pip install pygame numpy
2. Run the GameExecute the main application script:Bashpython3 rhythm_json.py
ControlsGame ModeKey BindingsMain Menu Navigation1 (New Game), 2 (Old Games/Board), 3 or Q (Exit)Piano Roll / Matrix DodgeD, F, J, KFrog Jump / Drum KitSPACE or ENTEREcho PatternUp, Down, Left, Right Arrow KeysNoodle SlurpHold SPACESpace Shooter1, 2, 3Chef SliceC or SPACEData Structure & Configurationsong.json: Controls level layouts, speed, notes, and individual game-mode parameters.player_scores.json: Automatically manages player profile names, personal high scores, and individual match history logs.high_scores.json: Tracks historical single-level scores.Project StructurePlaintextrhythm_game/
├── rhythm_json.py        # Main curses application & menu logic
├── song.json             # Level definitions and note configurations
├── player_scores.json    # Saved player runs and score history
└── README.md             # Project documentation

---

### Push Changes to GitHub

Once you've pasted this into `README.md`, commit and push with:

```bash
git add README.md
git commit -m "Update README with player profile features and main menu controls"
git push origin main
