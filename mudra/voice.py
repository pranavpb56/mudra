"""Offline speech-to-text via faster-whisper: push-to-talk (shaka) or always-on wake word."""
import difflib
import re
import subprocess
import threading
import time


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def strip_wake(text, wake_word):
    """If text starts with the wake word (fuzzy, within the first 3 words) return the rest, else None."""
    words, w = _norm(text).split(), _norm(wake_word)
    for i in range(min(3, len(words))):
        if difflib.SequenceMatcher(None, words[i], w).ratio() >= 0.75:
            return " ".join(words[i + 1:])
    return None


class Listener:
    def __init__(self, cfg):
        self.cfg = cfg
        self.model = None
        self.error = None
        self._ready = threading.Event()
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            from faster_whisper import WhisperModel
            print("[mudra] loading voice model (first run downloads it)...", flush=True)
            self.model = WhisperModel(self.cfg["model"], device="cpu", compute_type="int8")
            print("[mudra] voice model ready", flush=True)
        except Exception as e:
            self.error = e
            print(f"[mudra] voice model failed to load: {e}", flush=True)
        finally:
            self._ready.set()

    def _transcribe(self, audio, prompt=None):
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1,
                                            vad_filter=True, initial_prompt=prompt)
        return " ".join(s.text for s in segments).strip()

    def listen_once(self) -> str:
        import sounddevice as sd

        if not self._ready.is_set():
            raise RuntimeError("voice model still loading, try again in a minute")
        if self.error:
            raise RuntimeError(f"voice model failed: {self.error}")
        sr = 16000
        audio = sd.rec(int(self.cfg["record_seconds"] * sr), samplerate=sr, channels=1, dtype="float32")
        sd.wait()
        audio = audio.flatten()
        if float(abs(audio).max()) < 0.005:
            raise RuntimeError("mic is silent: allow Microphone for your terminal app")
        return self._transcribe(audio)

    def wake_loop(self, on_command, status):
        """Always listening. Say '<wake_word> <command>', e.g. 'jarvis open notes'."""
        import numpy as np
        import sounddevice as sd

        self._ready.wait()
        if self.error:
            return
        wake = self.cfg.get("wake_word", "jarvis")
        thresh = float(self.cfg.get("mic_threshold", 0.015))
        sr, block = 16000, 1600  # 100 ms blocks
        buf, quiet = [], 0
        awaiting_until = ignore_until = 0.0
        status["text"] = f'say "{wake} <command>"'
        with sd.InputStream(samplerate=sr, channels=1, dtype="float32", blocksize=block) as stream:
            while True:
                data, _ = stream.read(block)
                if time.time() < ignore_until:
                    buf, quiet = [], 0
                    continue
                if float(np.sqrt(np.mean(data ** 2))) > thresh:
                    buf.append(data.copy())
                    quiet = 0
                elif buf:
                    buf.append(data.copy())
                    quiet += 1
                if not buf or (quiet < 8 and len(buf) < 80):
                    continue
                audio = np.concatenate(buf).flatten()
                buf, quiet = [], 0
                if len(audio) < sr * 0.4:
                    continue  # a click or cough, not speech
                try:
                    text = self._transcribe(audio, prompt=wake)
                except Exception as e:
                    status["text"] = f"voice error: {e}"
                    continue
                if not text:
                    continue
                cmd = strip_wake(text, wake)
                if time.time() < awaiting_until:  # last utterance was just the wake word
                    cmd = text if cmd is None else cmd
                    awaiting_until = 0.0
                elif cmd is None:
                    continue
                elif not cmd.strip():
                    awaiting_until = time.time() + 6
                    status["text"] = "yes? say a command"
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Pop.aiff"])
                    ignore_until = time.time() + 0.8
                    continue
                try:
                    on_command(cmd)
                except Exception as e:
                    status["text"] = f"error: {e}"
                ignore_until = time.time() + 1.2
