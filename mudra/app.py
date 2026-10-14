import json
import subprocess
import sys
import threading
import time

from . import config
from .commands import Controller, beep, build_phrases, match_voice, run_action
from .engine import Engine
from .plugins import API, load_plugins

HELP = "point=move  OK-sign=click/drag  peace=scroll  palm swipe=desktop  three=volume  shaka=voice  fist=pause"


class VoiceProcess:
    """Runs speech recognition in a separate process so a native-library crash can't take gestures down."""

    def __init__(self, on_command, status):
        self.status = status
        self.on_command = on_command
        self.proc = subprocess.Popen([sys.executable, "-m", "mudra.voice_worker"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg["k"] == "status":
                self.status["text"] = msg["t"]
            elif msg["k"] == "command":
                try:
                    self.on_command(msg["t"])
                except Exception as e:
                    self.status["text"] = f"error: {e}"
        self.status["text"] = "voice process stopped (gestures still work)"

    def listen(self):
        try:
            self.proc.stdin.write("listen\n")
            self.proc.stdin.flush()
        except Exception:
            pass

    def close(self):
        self.proc.terminate()


def run(cfg, preview=True, voice=True, camera=None):
    import cv2
    import mediapipe as mp

    api = API()
    load_plugins(api, [config.HOME / "plugins"])
    ctl = Controller()
    phrases = build_phrases(cfg["voice_commands"], api.voice_handlers)
    status = {"text": "ready"}

    def on_command(text):
        action = match_voice(text, phrases)
        if action is None:
            beep("Basso")
            status["text"] = f'no match: "{text}"'
        else:
            beep("Glass")
            status["text"] = f'heard: "{text}"'
            if callable(action):
                action()
            elif action.startswith("mode:"):
                ok = engine.set_mode(action[5:].strip())
                status["text"] = f"mode: {engine.mode}" if ok else f'unknown mode "{action[5:]}"'
            else:
                run_action(action, ctl)

    vp = VoiceProcess(on_command, status) if voice and cfg["voice"]["enabled"] else None

    def listen():
        if vp:
            beep("Pop")
            vp.listen()

    cam = cfg["camera"]
    idx = cam["index"] if camera is None else camera
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if sys.platform.startswith("win") else cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    if not cap.isOpened():
        raise SystemExit("Could not open the camera. Check camera permissions (macOS: System Settings > "
                         "Privacy & Security > Camera; Windows: Settings > Privacy & security > Camera).")

    hands = mp.solutions.hands.Hands(max_num_hands=1, model_complexity=0,
                                     min_detection_confidence=0.7, min_tracking_confidence=0.6)
    draw, conns = mp.solutions.drawing_utils, mp.solutions.hands.HAND_CONNECTIONS
    engine = Engine(cfg, ctl, api, on_listen=listen, screen=ctl.screen_size())
    m = cfg["tracking"]["frame_margin"]
    print("[mudra] running. Press q in the preview window (or Ctrl+C) to quit.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            lm, hl = None, None
            if res.multi_hand_landmarks:
                hl = res.multi_hand_landmarks[0]
                lm = [(p.x, p.y) for p in hl.landmark]
            gesture = engine.step(lm, time.time())
            if preview:
                h, w = frame.shape[:2]
                if hl:
                    draw.draw_landmarks(frame, hl, conns)
                cv2.rectangle(frame, (int(m * w), int(m * h)), (int((1 - m) * w), int((1 - m) * h)), (80, 80, 80), 1)
                cv2.putText(frame, f"[{engine.mode}] {gesture}  |  {status['text']}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, HELP, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.imshow("Mudra", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        ctl.release()
        if vp:
            vp.close()
        cap.release()
        cv2.destroyAllWindows()
