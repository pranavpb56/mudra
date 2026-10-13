"""Pure-python gesture classifier. Input: 21 MediaPipe hand landmarks as (x, y) in 0..1."""
import math

FINGERS = {"index": (6, 8), "middle": (10, 12), "ring": (14, 16), "pinky": (18, 20)}


def _d(lm, a, b):
    return math.hypot(lm[a][0] - lm[b][0], lm[a][1] - lm[b][1])


def hand_size(lm):
    return _d(lm, 0, 9) or 1e-6


def fingers_up(lm):
    up = {n: _d(lm, 0, tip) > _d(lm, 0, pip) * 1.15 for n, (pip, tip) in FINGERS.items()}
    up["thumb"] = _d(lm, 4, 17) > _d(lm, 3, 17) * 1.05
    return up


def classify(lm, was_pinched=False, pinch_on=0.30, pinch_off=0.45):
    """Returns: pinch | palm | fist | point | peace | shaka | other"""
    up = fingers_up(lm)
    ratio = _d(lm, 4, 8) / hand_size(lm)
    close = ratio < (pinch_off if was_pinched else pinch_on)
    # "OK sign": thumb+index touch while at least one other finger is open (a fist is not a pinch)
    if close and (up["middle"] or up["ring"] or up["pinky"]):
        return "pinch"
    pattern = (up["index"], up["middle"], up["ring"], up["pinky"])
    if pattern == (True, True, True, True):
        return "palm"
    if pattern == (False, False, False, False):
        return "fist"
    if pattern == (True, False, False, False):
        return "point"
    if pattern == (True, True, False, False):
        return "peace"
    if pattern == (False, False, False, True) and up["thumb"]:
        return "shaka"
    return "other"
