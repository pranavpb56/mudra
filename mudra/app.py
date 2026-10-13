import subprocess
import threading
import time

from . import config
from .commands import Controller, build_phrases, match_voice, run_action
from .engine import Engine
from .plugins import API, load_plugins

HELP = "point=move  OK-sign=click/drag  peace=scroll  palm swipe=desktop  shaka=voice  fist=pause"


def beep(name):
    subprocess.Popen(["afplay", f"/System/Library/Sounds/{name}.aiff"])


def run(cfg, preview=True, voice=True, camera=None):
    import cv2
    import mediapipe as mp

    api = API()
    load_plugins(api, [config.HOME / "plugins"])
    ctl = Controller()
    phrases = build_phrases(cfg["voice_commands"], api.voice_handlers)
    status = {"text": "ready"}
    busy = threading.Lock()
    listener = None
    if voice and cfg["voice"]["enabled"]:
        from .voice import Listener
        listener = Listener(cfg["voice"])

    def listen():
        if listener is None or not busy.acquire(blocking=False):
            return

        def work():
            try:
                beep("Pop")
                status["text"] = "listening..."
                text = listener.listen_once()
                action = match_voice(text, phrases)
                if action is None:
                    beep("Basso")
                    status["text"] = f'no match: "{text}"'
                else:
                    beep("Glass")
                    status["text"] = f'heard: "{text}"'
                    action() if callable(action) else run_action(action, ctl)
            except Exception as e:
                status["text"] = f"voice error: {e}"
            finally:
                busy.release()

        threading.Thread(target=work, daemon=True).start()

    if listener is not None and cfg["voice"].get("always_on", False):
        def on_wake(text):
            action = match_voice(text, phrases)
            if action is None:
                beep("Basso")
                status["text"] = f'no match: "{text}"'
            else:
                beep("Glass")
                status["text"] = f'heard: "{text}"'
                action() if callable(action) else run_action(action, ctl)

        threading.Thread(target=listener.wake_loop, args=(on_wake, status), daemon=True).start()

    cam = cfg["camera"]
    cap = cv2.VideoCapture(cam["index"] if camera is None else camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    if not cap.isOpened():
        raise SystemExit("Could not open the camera. Grant Camera access to your terminal in "
                         "System Settings > Privacy & Security > Camera.")

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
                cv2.putText(frame, f"{gesture}  |  {status['text']}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, HELP, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.imshow("Mudra", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        ctl.release()
        cap.release()
        cv2.destroyAllWindows()
