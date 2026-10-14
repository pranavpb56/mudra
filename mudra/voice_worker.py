"""Voice worker process. Talks to the parent with JSON lines: run via `python -m mudra.voice_worker`.

Speech recognition runs in its own process so its native libraries (PortAudio, CTranslate2,
ONNX) can never crash or conflict with the camera/hand-tracking process.
"""
import json
import sys
import threading

_out = sys.stdout
sys.stdout = sys.stderr  # stray library prints go to stderr; stdout is reserved for JSON lines


def emit(kind, text):
    _out.write(json.dumps({"k": kind, "t": text}) + "\n")
    _out.flush()


class Status(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key == "text":
            emit("status", value)


def _once(listener, handle):
    try:
        emit("status", "listening...")
        handle(listener.listen_once())
    except Exception as e:
        emit("status", f"voice error: {e}")


def main():
    from . import config
    from .voice import Listener

    cfg = config.load()["voice"]
    listener = Listener(cfg)

    def handle(cmd):
        c = " ".join(cmd.lower().replace(".", "").replace(",", "").split())
        if c in ("start dictation", "dictation on", "start typing", "start dictating"):
            listener.dictating = True
            emit("status", "dictation ON - say 'stop dictation' to end")
            return
        if listener.dictating:
            if c in ("stop dictation", "dictation off", "stop typing", "stop dictating"):
                listener.dictating = False
                emit("status", "dictation OFF")
                return
            emit("command", "type " + cmd)
            return
        emit("command", cmd)

    if cfg.get("always_on", False):
        threading.Thread(target=listener.wake_loop, args=(handle, Status()), daemon=True).start()
    for line in sys.stdin:  # parent asks for push-to-talk by writing "listen"
        if line.strip() == "listen":
            threading.Thread(target=_once, args=(listener, handle), daemon=True).start()


if __name__ == "__main__":
    main()
