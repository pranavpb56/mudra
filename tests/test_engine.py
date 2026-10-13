import tomllib
from pathlib import Path

from mudra.engine import Engine
from mudra.plugins import API
from tests.helpers import make_hand

CFG = tomllib.loads((Path(__file__).parents[1] / "mudra" / "default.toml").read_text())


class FakeCtl:
    def __init__(self):
        self.log = []

    def move(self, x, y): self.log.append(("move",))
    def press(self): self.log.append(("press",))
    def release(self): self.log.append(("release",))
    def scroll(self, n): self.log.append(("scroll", n))
    def key(self, c): self.log.append(("key", c))


def feed(engine, hand, frames, t0=0.0, dt=0.04):
    for i in range(frames):
        engine.step(hand(i) if callable(hand) else hand, t0 + i * dt)


def test_pinch_press_and_release():
    ctl = FakeCtl()
    e = Engine(CFG, ctl, API())
    feed(e, make_hand(middle=True, ring=True, pinky=True, pinch=True), 5)
    assert ("press",) in ctl.log
    feed(e, make_hand(index=True), 5, t0=1.0)
    assert ("release",) in ctl.log


def test_point_moves_cursor():
    ctl = FakeCtl()
    e = Engine(CFG, ctl, API())
    feed(e, make_hand(index=True), 6)
    assert ("move",) in ctl.log


def test_swipe_right_switches_desktop():
    ctl = FakeCtl()
    e = Engine(CFG, ctl, API())
    feed(e, lambda i: make_hand(True, True, True, True, dx=0.06 * i), 14, t0=10.0)
    assert ("key", "ctrl+right") in ctl.log


def test_plugin_gesture_hook():
    api, hits = API(), []
    api.on_gesture("fist")(lambda: hits.append(1))
    e = Engine(CFG, FakeCtl(), api)
    feed(e, make_hand(), 5)
    assert hits
