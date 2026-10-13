"""Action execution + voice phrase matching. Heavy deps (pynput, Quartz) are imported lazily."""
import difflib
import re
import subprocess
import time
from urllib.parse import quote_plus


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


def run_action(spec: str, ctl) -> None:
    kind, _, arg = spec.partition(":")
    arg = arg.strip()
    if kind == "key":
        ctl.key(arg)
    elif kind == "app":
        subprocess.Popen(["open", "-a", arg])
    elif kind == "url":
        subprocess.Popen(["open", arg])
    elif kind == "shell":
        subprocess.Popen(arg, shell=True)  # config is the user's own file
    elif kind == "say":
        subprocess.Popen(["say", arg])
    elif kind == "scroll":
        ctl.scroll(int(arg))
    else:
        print(f"[mudra] unknown action: {spec!r}")


class Controller:
    """macOS mouse (Quartz, so drags work) + keyboard (pynput)."""

    def __init__(self):
        import Quartz as Q
        from pynput.keyboard import Controller as K, Key

        self.Q = Q
        self.kb = K()
        self.x = self.y = 0.0
        self.down = False
        self.clicks = 1
        self.last_up = 0.0
        self.mods = {"cmd": Key.cmd, "command": Key.cmd, "ctrl": Key.ctrl, "control": Key.ctrl,
                     "alt": Key.alt, "option": Key.alt, "shift": Key.shift}
        self.named = {"left": Key.left, "right": Key.right, "up": Key.up, "down": Key.down,
                      "tab": Key.tab, "space": Key.space, "enter": Key.enter, "return": Key.enter,
                      "esc": Key.esc, "escape": Key.esc, "delete": Key.backspace,
                      "backspace": Key.backspace}

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

    def key(self, combo):
        parts = [p.strip().lower() for p in combo.split("+")]
        mods = [self.mods[p] for p in parts[:-1]]
        last = parts[-1]
        k = self.named.get(last, last)
        for m in mods:
            self.kb.press(m)
        self.kb.press(k)
        self.kb.release(k)
        for m in reversed(mods):
            self.kb.release(m)
