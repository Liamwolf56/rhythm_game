# 🎵 Python Terminal Rhythm Game Engine

A feature-packed, low-latency terminal rhythm game built using Python, `curses`, and `pygame.mixer`. Jump, slice, dodge, and hit notes across 8 dynamic minigame levels synced to custom audio tracks!

## 🚀 Features

* **8 Unique Level Modes**:
  * **Piano / Note Lanes**: Hit falling notes on `D`, `F`, `J`, and `K`.
  * **Frog Jump**: Jump over obstacles on beat using `SPACE`.
  * **Memory Echo**: Memorize and repeat arrow key sequences.
  * **Noodle Slurp**: Press and hold `SPACE` while noodles pass through the target zone.
  * **Space Shooter**: Fire beat lasers across 3 sectors using `1`, `2`, and `3`.
  * **Drum Kit**: Strike `SPACE` or `ENTER` on the beat marker.
  * **Chef Slice**: Time your chops with `C` or `SPACE` to slice passing veggies.
  * **Matrix Dodge**: Dodge incoming matrix attacks using `D`, `F`, `J`, and `K`.
* **Low-Latency Audio Engine**: Custom `pygame.mixer` channel controller eliminating buffer bleeding, dynamically managing `Blip.mp3` hit triggers and track transitions.
* **Persistent Scoreboards**: Save profile run histories, view high scores, and review match logs stored locally in JSON format.
* **1-Click Desktop App Launcher**: Integrated Windows batch (`.bat`) and VBScript launch triggers to run the game directly from your desktop without touching the terminal.

## 🛠️ Requirements

* Python 3.8+
* `pygame`
* `numpy`
* WSL / Linux or `windows-curses` for native Windows environments

## 📦 Quick Start & Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/Liamwolf56/rhythm_game.git](https://github.com/Liamwolf56/rhythm_game.git)
   cd rhythm_game
Install dependencies:

Bash
pip install pygame numpy
Launch from Terminal:

Bash
python3 rhythm_json.py
🖥️ Running as a Desktop App (Windows / WSL)
Double-click Play_Rhythm_Game.bat generated in your repository root (or Desktop shortcut) to launch the game instantly in a dedicated window without manually entering terminal commands.

🎮 How to Play
Launch the game and select [1] NEW GAME from the main menu.

Enter your player profile name.

Play through 8 randomized level challenges.

Review your match records on the [2] OLD GAMES / BOARD scoreboard!


---

### Save and Push to GitHub

To commit this final `README.md` update directly to your repository:

```bash
git add README.md
git commit -m "Docs: update README with desktop launcher instructions"
git pull --rebase origin main
git push origin main
