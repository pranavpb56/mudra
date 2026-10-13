"""Tiny plugin API. Drop a .py file in ~/.mudra/plugins/ that defines register(api)."""
import importlib.util
import subprocess
from pathlib import Path


class API:
    def __init__(self):
        self.gesture_handlers = {}  # gesture name -> [callables]
        self.voice_handlers = {}    # spoken phrase -> callable

    def on_gesture(self, name):
        def deco(fn):
            self.gesture_handlers.setdefault(name, []).append(fn)
            return fn
        return deco

    def on_voice(self, phrase):
        def deco(fn):
            self.voice_handlers[phrase] = fn
            return fn
        return deco

    def say(self, text):
        subprocess.Popen(["say", text])

    def fire_gesture(self, name):
        for fn in self.gesture_handlers.get(name, []):
            try:
                fn()
            except Exception as e:  # a bad plugin must never crash the loop
                print(f"[mudra] plugin error on gesture '{name}': {e}")


def load_plugins(api, dirs):
    for d in dirs:
        d = Path(d)
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f"mudra_plugin_{f.stem}", f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.register(api)
                print(f"[mudra] loaded plugin {f.name}")
            except Exception as e:
                print(f"[mudra] failed to load plugin {f.name}: {e}")
