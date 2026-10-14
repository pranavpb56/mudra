"""Action execution + voice phrase matching. Heavy deps (pynput, Quartz) are imported lazily."""
import difflib
import re
import subprocess
import sys
import time
import webbrowser
from urllib.parse import quote_plus

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")
_NO_WINDOW = 0x08000000  # Windows: don't flash a console window


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def build_phrases(cfg_commands: dict, plugin_handlers: dict) -> dict:
    phrases = {normalize(k): v for k, v in cfg_commands.items()}
    phrases.update({normalize(k): v for k, v in plugin_handlers.items()})
    return phrases


def match_voice(text: str, phrases: dict, cutoff: float = 0.78):
    """Returns an action string / callable, or None."""
    t = normalize(text)
    if not t:
        return None
    if t in phrases:
        return phrases[t]
    close = difflib.get_close_matches(t, list(phrases), n=1, cutoff=cutoff)
    if close:
        return phrases[close[0]]
    m = re.match(r"(?:open|launch|start) (.+)", t)
    if m:
        return f"app:{m.group(1).title()}"
    m = re.match(r"(?:search|google|look up) (.+)", t)
    if m:
        return "url:https://www.google.com/search?q=" + quote_plus(m.group(1))
    return None


def beep(name: str) -> None:
    """Short feedback sounds: Pop (listening), Glass (understood), Basso (no match)."""
    try:
        if IS_MAC:
            subprocess.Popen(["afplay", f"/System/Library/Sounds/{name}.aiff"])
        elif IS_WIN:
            import winsound
            kinds = {"Pop": winsound.MB_OK, "Glass": winsound.MB_ICONASTERISK, "Basso": winsound.MB_ICONHAND}
            winsound.MessageBeep(kinds.get(name, winsound.MB_OK))
    except Exception:
        pass


def say(text: str) -> None:
    if IS_MAC:
        subprocess.Popen(["say", text])
    elif IS_WIN:
        ps = ("Add-Type -AssemblyName System.Speech; "
              "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('%s')" % text.replace("'", "''"))
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], creationflags=_NO_WINDOW)


def open_app(name: str) -> None:
    if IS_MAC:
        subprocess.Popen(["open", "-a", name])
    elif IS_WIN:
        subprocess.Popen(["cmd", "/c", "start", "", name], creationflags=_NO_WINDOW)


def run_action(spec: str, ctl) -> None:
    kind, _, arg = spec.partition(":")
    arg = arg.strip()
    if kind == "key":
        combo, _, times = arg.partition("*")  # "key:volumeup*5" presses 5 times
        for _ in range(int(times) if times.strip().isdigit() else 1):
            ctl.key(combo.strip())
    elif kind == "app":
        open_app(arg)
    elif kind == "url":
        webbrowser.open(arg)
    elif kind == "shell":
        subprocess.Popen(arg, shell=True)  # config is the user's own file
    elif kind == "say":
        say(arg)
    elif kind == "scroll":
        ctl.scroll(int(arg))
    else:
        print(f"[mudra] unknown action: {spec!r}")


class _Keys:
    """Keyboard shortcuts via pynput, shared by the macOS and Windows controllers."""

    def _init_keys(self):
        from pynput.keyboard import Controller as K, Key

        self.kb, self.Key = K(), Key
        self.mods = {"cmd": Key.cmd, "command": Key.cmd, "win": Key.cmd, "super": Key.cmd,
                     "ctrl": Key.ctrl, "control": Key.ctrl, "alt": Key.alt, "option": Key.alt,
                     "shift": Key.shift}
        self.named = {"left": Key.left, "right": Key.right, "up": Key.up, "down": Key.down,
                      "tab": Key.tab, "space": Key.space, "enter": Key.enter, "return": Key.enter,
                      "esc": Key.esc, "escape": Key.esc, "delete": Key.backspace,
                      "backspace": Key.backspace}
        media = {"volumeup": "media_volume_up", "volumedown": "media_volume_down",
                 "mute": "media_volume_mute", "playpause": "media_play_pause",
                 "nexttrack": "media_next", "prevtrack": "media_previous"}
        for alias, attr in media.items():
            if hasattr(Key, attr):
                self.named[alias] = getattr(Key, attr)

    def key(self, combo):
        parts = [p.strip().lower() for p in combo.split("+")]
        mods = [self.mods[p] for p in parts[:-1]]
        last = parts[-1]
        k = self.named.get(last)
        if k is None and len(last) > 1:
            k = getattr(self.Key, last, None)  # f1..f12, home, end, page_up ...
        if k is None:
            k = last
        for m in mods:
            self.kb.press(m)
        self.kb.press(k)
        self.kb.release(k)
        for m in reversed(mods):
            self.kb.release(m)


class _Mac(_Keys):
    """macOS mouse via Quartz (so drags work) + pynput keyboard."""

    def __init__(self):
        import Quartz as Q

        self.Q = Q
        self._init_keys()
        self.x = self.y = 0.0
        self.down = False
        self.clicks = 1
        self.last_up = 0.0

    def screen_size(self):
        b = self.Q.CGDisplayBounds(self.Q.CGMainDisplayID())
        return b.size.width, b.size.height

    def _post(self, etype):
        Q = self.Q
        e = Q.CGEventCreateMouseEvent(None, etype, (self.x, self.y), Q.kCGMouseButtonLeft)
        Q.CGEventSetIntegerValueField(e, Q.kCGMouseEventClickState, self.clicks)
        Q.CGEventPost(Q.kCGHIDEventTap, e)

    def move(self, x, y):
        self.x, self.y = x, y
        self._post(self.Q.kCGEventLeftMouseDragged if self.down else self.Q.kCGEventMouseMoved)

    def press(self):
        now = time.time()
        self.clicks = self.clicks + 1 if now - self.last_up < 0.4 else 1  # gives double-click for free
        self.down = True
        self._post(self.Q.kCGEventLeftMouseDown)

    def release(self):
        if self.down:
            self._post(self.Q.kCGEventLeftMouseUp)
            self.down = False
            self.last_up = time.time()

    def scroll(self, n):
        Q = self.Q
        e = Q.CGEventCreateScrollWheelEvent(None, Q.kCGScrollEventUnitLine, 1, int(n))
        Q.CGEventPost(Q.kCGHIDEventTap, e)


class _Win(_Keys):
    """Windows mouse + keyboard via pynput (SendInput). Experimental."""

    def __init__(self):
        import ctypes
        from pynput.mouse import Button, Controller as M

        self.user32 = ctypes.windll.user32
        try:
            self.user32.SetProcessDPIAware()  # work in real pixels on scaled displays
        except Exception:
            pass
        self.m, self.Button = M(), Button
        self._init_keys()
        self.down = False

    def screen_size(self):
        return float(self.user32.GetSystemMetrics(0)), float(self.user32.GetSystemMetrics(1))

    def move(self, x, y):
        self.m.position = (int(x), int(y))

    def press(self):
        self.m.press(self.Button.left)
        self.down = True

    def release(self):
        if self.down:
            self.m.release(self.Button.left)
            self.down = False

    def scroll(self, n):
        self.m.scroll(0, int(n))


def Controller():
    if IS_MAC:
        return _Mac()
    if IS_WIN:
        return _Win()
    raise SystemExit("Mudra currently supports macOS and Windows. Linux contributions welcome!")
