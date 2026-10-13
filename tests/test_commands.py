from mudra.commands import build_phrases, match_voice

P = build_phrases({"screenshot": "key:cmd+shift+3", "new tab": "key:cmd+t"}, {})


def test_exact():
    assert match_voice("Screenshot.", P) == "key:cmd+shift+3"


def test_fuzzy():
    assert match_voice("new tap", P) == "key:cmd+t"


def test_open_app():
    assert match_voice("open notes", P) == "app:Notes"


def test_search():
    assert match_voice("search hyderabad weather", P).startswith("url:https://www.google.com/search?q=")


def test_no_match():
    assert match_voice("blah blah", P) is None
