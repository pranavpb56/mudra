"""Turns a stream of hand landmarks into actions. No camera or OS imports, so it is unit-testable."""
from collections import deque

from .commands import run_action
from .gestures import classify


class Engine:
    def __init__(self, cfg, ctl, api, on_listen=None, screen=(1440, 900)):
        self.cfg = cfg
        self.t = cfg["tracking"]
        self.base_gest = cfg["gestures"]
        self.gest = dict(self.base_gest)
        self.mode = "normal"
        self.ctl, self.api, self.on_listen, self.screen = ctl, api, on_listen, screen
        self.cur = "none"
        self.cand, self.n = "none", 0
        self.pos = None
        self.prev_y = None
        self.acc = 0.0
        self.hist = deque()
        self.last_swipe = 0.0
        self.last_voice = 0.0
        self.last_vol = 0.0
        self.shaka_t = None

    def set_mode(self, name):
        """Switch gesture profile: 'normal' or any [modes.<name>] section in the config."""
        modes = self.cfg.get("modes", {})
        if name == "normal":
            self.gest = dict(self.base_gest)
        elif name in modes:
            self.gest = {**self.base_gest, **modes[name].get("gestures", {})}
        else:
            return False
        self.mode = name
        return True

    def _run(self, spec):
        if spec:
            run_action(spec, self.ctl)

    def _change(self, new):
        if self.cur == "pinch":
            self.ctl.release()
        if new == "pinch":
            self.ctl.press()
        self.cur = new
        self.prev_y, self.acc, self.shaka_t = None, 0.0, None
        self.hist.clear()
        if new == "none":
            self.pos = None
        self.api.fire_gesture(new)

    def step(self, lm, now):
        raw = "none"
        if lm:
            raw = classify(lm, self.cur == "pinch", self.t["pinch_on"], self.t["pinch_off"])
        if raw == self.cand:
            self.n += 1
        else:
            self.cand, self.n = raw, 1
        if self.n >= self.t["stable_frames"] and self.cand != self.cur:
            self._change(self.cand)
        if lm and self.cur != "none":
            self._act(lm, now)
        return self.cur

    def _act(self, lm, now):
        t, cur = self.t, self.cur
        if cur in ("point", "pinch"):
            ax, ay = lm[t["anchor"]]
            m = t["frame_margin"]
            nx = min(max((ax - m) / (1 - 2 * m), 0.0), 1.0)
            ny = min(max((ay - m) / (1 - 2 * m), 0.0), 1.0)
            tx, ty = nx * (self.screen[0] - 1), ny * (self.screen[1] - 1)
            a = t["smoothing"]
            if self.pos is None:
                self.pos = (tx, ty)
            else:
                self.pos = (self.pos[0] + (tx - self.pos[0]) * a, self.pos[1] + (ty - self.pos[1]) * a)
            self.ctl.move(*self.pos)
        elif cur == "peace":
            y = lm[9][1]
            if self.prev_y is not None:
                self.acc += (self.prev_y - y) * t["scroll_speed"]
                n = int(self.acc)
                if n:
                    self.ctl.scroll(n)
                    self.acc -= n
            self.prev_y = y
        elif cur == "three":  # volume knob: three fingers up, move hand up/down
            y = lm[9][1]
            if self.prev_y is not None:
                self.acc += (self.prev_y - y) * t.get("volume_speed", 120)
                if abs(self.acc) >= 1 and now - self.last_vol > 0.12:
                    n = int(self.acc)
                    self.ctl.volume_step(n)
                    self.acc -= n
                    self.last_vol = now
            self.prev_y = y
        elif cur == "palm":
            self.hist.append((now, lm[0][0]))
            while self.hist and now - self.hist[0][0] > t["swipe_window"]:
                self.hist.popleft()
            if now - self.last_swipe > t["swipe_cooldown"] and len(self.hist) >= 3:
                dx = self.hist[-1][1] - self.hist[0][1]
                if abs(dx) > t["swipe_distance"]:
                    name = "swipe_right" if dx > 0 else "swipe_left"
                    self.last_swipe = now
                    self.hist.clear()
                    self._run(self.gest.get(name))
                    self.api.fire_gesture(name)
        elif cur == "shaka":
            if self.shaka_t is None:
                self.shaka_t = now
            elif now - self.shaka_t > t["shaka_hold"] and now - self.last_voice > 3.0:
                self.last_voice, self.shaka_t = now, None
                if self.on_listen:
                    self.on_listen()
