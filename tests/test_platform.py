import tomllib
from pathlib import Path

from mudra.commands import run_action

PKG = Path(__file__).parents[1] / "mudra"


def test_both_default_configs_parse_and_match_shape():
    mac = tomllib.loads((PKG / "default.toml").read_text())
    win = tomllib.loads((PKG / "default_win.toml").read_text())
    for cfg in (mac, win):
        assert {"camera", "tracking", "voice", "gestures", "voice_commands"} <= set(cfg)
    assert set(mac["tracking"]) == set(win["tracking"])


def test_key_repeat_syntax():
    calls = []

    class Ctl:
        def key(self, c): calls.append(c)

    run_action("key:volumeup*3", Ctl())
    assert calls == ["volumeup"] * 3
