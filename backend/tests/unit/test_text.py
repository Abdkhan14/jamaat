from scraping.text import clean_text


def test_collapses_whitespace_and_adds_space_after_punctuation():
    raw = "Fajr:\t6:00\n\nZuhr:1:30"
    result = clean_text(raw)
    assert "\t" not in result
    assert "\n" not in result
    assert "Fajr: " in result
    assert "Zuhr: " in result


def test_repairs_broken_times():
    assert "6:30 pm" in clean_text("6 : 30pm")
    assert "6:30 pm" in clean_text("6:30 p m")
