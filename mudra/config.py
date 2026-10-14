import sys
import tomllib
from pathlib import Path

HOME = Path.home() / ".mudra"
DEFAULT = Path(__file__).with_name("default_win.toml" if sys.platform.startswith("win") else "default.toml")


def _merge(base: dict, extra: dict) -> dict:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load() -> dict:
    cfg = tomllib.loads(DEFAULT.read_text())
    user = HOME / "mudra.toml"
    if user.exists():
        _merge(cfg, tomllib.loads(user.read_text()))
    return cfg


def init_user_config() -> Path:
    HOME.mkdir(exist_ok=True)
    (HOME / "plugins").mkdir(exist_ok=True)
    dst = HOME / "mudra.toml"
    if not dst.exists():
        dst.write_text(DEFAULT.read_text())
    return dst
