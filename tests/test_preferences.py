"""What the reader chose about the application, rather than about a book.

A theme belongs to the person and not to what they are reading, so it does not
go in a sidecar that follows one book around. Everything here fails quietly: a
preference that cannot be read costs somebody their choice of theme, and
refusing to open the window over it would cost them the book.
"""

import json

import pytest

from ariadne.app import preferences


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    return tmp_path / "store"


def test_the_default_is_what_every_other_application_does():
    assert preferences.theme() == "system"


def test_a_choice_is_remembered():
    preferences.set_theme("dark")
    assert preferences.theme() == "dark"


def test_it_lives_beside_the_books_and_not_inside_one(store):
    preferences.set_theme("light")
    assert preferences.settings_path() == str(store / "settings.json")
    assert (store / "settings.json").is_file()
    assert "books" not in preferences.settings_path().rsplit("/", 1)[-1]


def test_a_theme_nobody_offers_is_refused():
    preferences.set_theme("dark")
    preferences.set_theme("neon")
    assert preferences.theme() == "dark", "an unknown theme was written"


def test_a_value_nobody_offers_is_not_read_back(store):
    store.mkdir(parents=True, exist_ok=True)
    (store / "settings.json").write_text(json.dumps({"theme": "neon"}), encoding="utf-8")
    assert preferences.theme() == "system", "a theme it cannot honour was returned"


def test_saving_one_setting_keeps_the_others(store):
    store.mkdir(parents=True, exist_ok=True)
    (store / "settings.json").write_text(
        json.dumps({"theme": "dark", "something-else": 41}), encoding="utf-8"
    )
    preferences.set_theme("light")
    kept = json.loads((store / "settings.json").read_text(encoding="utf-8"))
    assert kept["theme"] == "light"
    assert kept["something-else"] == 41, "an unrelated setting was lost"


def test_a_file_that_cannot_be_read_costs_the_choice_and_nothing_more(store):
    store.mkdir(parents=True, exist_ok=True)
    (store / "settings.json").write_text("{ this is not json", encoding="utf-8")
    assert preferences.theme() == "system"
    # And it can still be written over rather than being stuck forever.
    preferences.set_theme("dark")
    assert preferences.theme() == "dark"


def test_a_store_that_cannot_be_written_does_not_raise(tmp_path, monkeypatch):
    """Somewhere a directory cannot be made. The window still has to open."""
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("", encoding="utf-8")
    monkeypatch.setenv("ARIADNE_HOME", str(blocked))
    preferences.set_theme("dark")
    assert preferences.theme() == "system"
