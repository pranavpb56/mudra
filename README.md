# Mudra 🤌

**Control your Mac with your hands and your voice. Offline. Open source. Extensible.**

<!-- PUT YOUR DEMO GIF HERE. This is the most important line in the repo. -->
![demo](docs/demo.gif)

Move the cursor by pointing. Click and drag with an OK-sign pinch. Scroll with two fingers. Swipe your palm to switch desktops. Hold a shaka 🤙 and just say what you want: *"open notes"*, *"screenshot"*, *"search Hyderabad weather"*.

No cloud. No account. Your webcam frames and your voice never leave your laptop.

## Install (Apple Silicon Mac)

```bash
git clone https://github.com/pranavpb56/mudra && cd mudra
./setup.sh
source .venv/bin/activate && mudra
```

Give your terminal **Camera**, **Microphone** and **Accessibility** access when macOS asks.
For desktop swiping, enable *Mission Control → Move left/right a space* in Keyboard Shortcuts.

## Gestures

| Gesture | Does |
|---|---|
| ☝️ Point (index only) | Move cursor |
| 👌 OK-sign (thumb+index touch, other fingers open) | Click · hold to drag · quick double pinch = double-click |
| ✌️ Peace sign, move hand up/down | Scroll |
| 🖐️ Open palm, swipe left/right | Switch desktop (configurable) |
| 🤙 Shaka, hold 0.6s | Listen for a voice command |
| ✊ Fist | Pause (safe resting pose) |

## Voice

Runs fully offline with Whisper. Built-ins: `open <any app>`, `search <anything>`, `screenshot`, `scroll down`, `volume up`, `mute`, `new tab`, `lock screen` … and you add your own in config.

## Configure

```bash
mudra init        # creates ~/.mudra/mudra.toml
```

Map any gesture or phrase to an action: `key:cmd+shift+4`, `app:Spotify`, `url:https://…`, `shell:…`, `say:…`, `scroll:-10`.

## Plugins (the fun part)

Drop a file in `~/.mudra/plugins/`:

```python
def register(api):
    @api.on_voice("what time is it")
    def _():
        api.say("Time to ship")

    @api.on_gesture("swipe_right")
    def _():
        print("next slide!")
```

See [`examples/plugins/`](examples/plugins). Built a cool one? Open a PR.

## Troubleshooting

- **Cursor jittery** → lower `smoothing`, light your room from the front, raise `stable_frames`.
- **Gestures misfire** → hold your hand 40–70 cm from the camera, palm facing it.
- **Nothing moves** → check Accessibility permission for your terminal app.
- **Voice slow** → set `model = "tiny.en"` in config.

## Roadmap / good first issues

- [ ] Two-hand gestures (zoom, rotate)
- [ ] Right-click and middle-click gestures
- [ ] Windows and Linux backends (`commands.Controller` is the only OS-specific file)
- [ ] Native menu-bar app
- [ ] Faster voice with `mlx-whisper`
- [ ] Gesture recorder: teach Mudra your own gestures
- [ ] Multilingual voice (Telugu, Hindi, Tamil…)
- [ ] Presentation mode, gaming profiles, accessibility profiles

## Develop

```bash
pip install -e ".[dev]" && pytest
```

`gestures.py` (classifier) and `engine.py` (gesture → action logic) have no OS dependencies, so most contributions are testable without a webcam.

## License

MIT

## Always-on voice

Mudra can listen all the time. Say the wake word, then your command:

> **"Jarvis, open notes"** · **"Jarvis, search hyderabad weather"** · **"Jarvis, volume down"**

Change `wake_word`, `always_on` and `mic_threshold` in `~/.mudra/mudra.toml`. Everything runs offline on your Mac, and audio never leaves your machine. The shaka 🤙 gesture still works as push-to-talk.
