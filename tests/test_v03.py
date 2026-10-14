import tomllib
from pathlib import Path

from mudra.commands import build_phrases, match_voice, run_action
from mudra.engine import Engine
from mudra.gestures import classify
from mudra.plugins import API
from mudra.voice import strip_wake
from tests.helpers import make_hand
from tests.test_engine import FakeCtl, feed

CFG = tomllib.loads((Path(__file__).parents[1] / "mudra" / "default.toml").read_text())
P = build_phrases(CFG["voice_commands"], {})


class Ctl(FakeCtl):
    def volume_step(self, n): self.log.append(("vol", n))
    def type_text(self, s): self.log.append(("type", s))


def test_three_fingers_gesture():
    assert classify(make_hand(index=True, middle=True, ring=True)) == "three"


def test_volume_knob_up():
    ctl = Ctl()
    e = Engine(CFG, ctl, API())
    feed(e, lambda i: make_hand(True, True, True, dy=-0.02 * i), 14, t0=10.0, dt=0.2)
    assert any(c[0] == "vol" and c[1] > 0 for c in ctl.log)


def test_presentation_mode_remaps_swipe():
    ctl = Ctl()
    e = Engine(CFG, ctl, API())
    assert e.set_mode("presentation") and e.mode == "presentation"
    feed(e, lambda i: make_hand(True, True, True, True, dx=0.06 * i), 14, t0=10.0)
    assert ("key", "right") in ctl.log
    assert e.set_mode("normal") and not e.set_mode("nonsense")


def test_mode_voice_commands_exist():
    assert match_voice("presentation mode", P) == "mode:presentation"
    assert match_voice("normal mode", P) == "mode:normal"


def test_type_command_keeps_original_text():
    assert match_voice("Type hello world.", P) == "type:hello world."
    ctl = Ctl()
    run_action("type:hello world.", ctl)
    assert ctl.log == [("type", "hello world. ")]


def test_wake_word_fuzzy():
    assert strip_wake("Hey Jarvis, open notes.", "jarvis") == "open notes"
    assert strip_wake("Travis open safari", "jarvis") == "open safari"
    assert strip_wake("open notes", "jarvis") is None
    assert strip_wake("Jarvis.", "jarvis") == ""
