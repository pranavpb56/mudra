# Mudra 

**Control your System with your hands and your voice. Offline. Open source. Extensible.**

<!-- PUT YOUR DEMO GIF HERE. This is the most important line in the repo. -->
<!-- add a demo GIF later: ![demo](docs/demo.gif) -->

Move the cursor by pointing. Click and drag with an OK-sign pinch. Scroll with two fingers. Swipe your palm to switch desktops. Hold a shaka 🤙 and just say what you want: *"open notes"*, *"screenshot"*, *"search Hyderabad weather"*.

No cloud. No account. Your webcam frames and your voice never leave your laptop.

## Install (macOS, Apple Silicon)

```bash
git clone https://github.com/pranavpb56/mudra && cd mudra
./setup.sh
source .venv/bin/activate && mudra
```

Give your terminal **Camera**, **Microphone** and **Accessibility** access when macOS asks.
For desktop swiping, enable *Mission Control → Move left/right a space* in Keyboard Shortcuts.

## Install (Windows, experimental)

> Windows support is new and has had less testing than macOS. If something misbehaves, please open an issue.

1. Install **Python 3.12** from https://www.python.org/downloads/ (tick **Add python.exe to PATH**).
2. In PowerShell:

```powershell
git clone https://github.com/pranavpb56/mudra
cd mudra
powershell -ExecutionPolicy Bypass -File setup.ps1
.\.venv\Scripts\mudra.exe
```

3. Allow camera and microphone: *Settings > Privacy & security > Camera / Microphone > Let desktop apps access = On*.

Desktop swipe uses `Win+Ctrl+Left/Right`. Edit your config with `notepad %USERPROFILE%\.mudra\mudra.toml`.

## Gestures

| Gesture | Does |
|---|---|
| ☝️ Point (index only) | Move cursor |
| 👌 OK-sign (thumb+index touch, other fingers open) | Click · hold to drag · quick double pinch = double-click |
| ✌️ Peace sign, move hand up/down | Scroll |
| 🖐️ Open palm, swipe left/right | Switch desktop (configurable) |
| 🤙 Shaka, hold 0.6s | Listen for a voice command |
| 🤟 Three fingers (index, middle, ring), move up/down | Volume knob |
| ✊ Fist | Pause (safe resting pose) |

## Voice

Runs fully offline with Whisper. Built-ins: `open <any app>`, `search <anything>`, `screenshot`, `scroll down`, `volume up`, `mute`, `new tab`, `lock screen` … and you add your own in config.

## More than gestures

**Voice typing.** Say `Computer, type hello world` to type into any app. Or say `Computer, start dictation` and just talk: everything you say is typed where your cursor is, until you say `stop dictation`.

**Modes.** Gestures can change meaning per situation:

- `Computer, presentation mode`: palm swipe sends the left/right arrow keys, so you can run slides from across the room
- `Computer, media mode`: palm swipe changes to the previous/next track
- `Computer, normal mode`: back to the defaults

Define your own under `[modes.<name>.gestures]` in the config, then add a voice command like `"movie mode" = "mode:movie"`.

**Volume knob.** Hold three fingers up (index, middle, ring) and move your hand up or down.

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
- [x] Windows backend (experimental, needs testers)
- [ ] Linux backend (`commands.py` is the only OS-specific file)
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

> **"Computer, open notes"** · **"Computer, search hyderabad weather"** · **"Computer, volume down"**

Change `wake_word`, `always_on` and `mic_threshold` in `~/.mudra/mudra.toml`. Everything runs offline on your Mac, and audio never leaves your machine. The shaka 🤙 gesture still works as push-to-talk.
