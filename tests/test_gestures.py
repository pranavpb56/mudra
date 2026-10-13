from mudra.gestures import classify
from tests.helpers import make_hand


def test_palm():
    assert classify(make_hand(True, True, True, True)) == "palm"


def test_fist_is_not_pinch():
    assert classify(make_hand()) == "fist"


def test_point():
    assert classify(make_hand(index=True)) == "point"


def test_peace():
    assert classify(make_hand(index=True, middle=True)) == "peace"


def test_shaka():
    assert classify(make_hand(pinky=True, thumb=True)) == "shaka"


def test_pinch_ok_sign():
    assert classify(make_hand(middle=True, ring=True, pinky=True, pinch=True)) == "pinch"
