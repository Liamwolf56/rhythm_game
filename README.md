# 🎵 Python Terminal Rhythm Game Engine

A feature-packed, low-latency terminal rhythm game built using Python, `curses`, and `pygame.mixer`. Jump, slice, dodge, and hit notes across 8 dynamic minigame levels synced to custom audio tracks!

## 🚀 Features

* **8 Unique Level Modes**:
  * **Piano / Note Lanes**: Hit falling notes on the `D`, `F`, `J`, and `K` keys.
  * **Frog Jump**: Jump over obstacles on beat using the spacebar.
  * **Memory Echo**: Memorize and repeat arrow key sequences.
  * **Noodle Slurp**: Press and hold the spacebar while noodles pass through the target zone.
  * **Space Shooter**: Fire beat lasers across 3 sectors using keys `1`, `2`, and `3`.
  * **Drum Kit**: Strike `SPACE` or `ENTER` on the beat marker.
  * **Chef Slice**: Time your chops with `C` or `SPACE` to slice passing veggies.
  * **Matrix Dodge**: Dodge incoming matrix attacks using `D`, `F`, `J`, and `K`.
* **Low-Latency Audio Engine**: Built with a custom `pygame.mixer` channel controller that eliminates buffer bleeding and dynamically handles hit sounds and music transitions.
* **Persistent Player Profiles & Scoreboards**: Save individual run histories, view high scores, and track match logs locally in JSON format.
* **Custom Audio Fallbacks**: Includes support for default audio tracks (`Blip.mp3`) alongside dynamically synthesized point sound fallbacks.

## 🛠️ Requirements

* Python 3.8+
* `pygame`
* `numpy`
* `windows-curses` (if running natively on Windows; standard `curses` is built into WSL/Linux/macOS)

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/Liamwolf56/rhythm_game.git](https://github.com/Liamwolf56/rhythm_game.git)
   cd rhythm_game
Install dependencies:

Bash
pip install pygame numpy
Run the game:

Bash
python rhythm_json.py
🎮 How to Play
Launch the game and select [1] NEW GAME from the main menu.

Enter your player profile name.

Complete 8 randomized level challenges.

Check your overall performance and match history on the [2] OLD GAMES / BOARD scoreboard!


---

### Push the README to GitHub

Once you've updated your local `README.md` file, save it and run these commands in your WSL terminal:

```bash
git add README.md
git commit -m "Update README with 8-level modes, audio engine details, and player scoreboards"
git push origin main
