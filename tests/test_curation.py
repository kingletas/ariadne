"""The reader's rulings, and the promise that none of them is lost.

Curation is the one thing here that writes. Every test below is really about
the first pillar: never lose somebody's work.
"""

import json
from pathlib import Path

import pytest

from ariadne.app.curation import Curation
from ariadne.decisions.sidecar import load_decisions, save_decisions

GOLDEN = Path(__file__).resolve().parent / "golden" / "model"


@pytest.fixture
def book():
    return json.loads((GOLDEN / "war-and-peace.json").read_text(encoding="utf-8"))


@pytest.fixture
def sidecar(tmp_path):
    return str(tmp_path / "war-and-peace.epub.ariadne.json")


def test_a_merge_folds_one_name_into_another(book, sidecar):
    curation = Curation(book, sidecar)
    before = len(curation.model["entities"])
    keep, also = curation.candidates(179)[0]
    curation.merge(keep, also)
    names = {e["name"] for e in curation.model["entities"]}
    assert len(curation.model["entities"]) == before - 1
    assert also not in names
    assert keep in names


def test_a_merge_survives_the_process(book, sidecar):
    keep, also = Curation(book, sidecar).candidates(179)[0]
    Curation(book, sidecar).merge(keep, also)
    again = Curation(book, sidecar)
    assert {e["name"] for e in again.model["entities"]}.isdisjoint({also})


def test_undo_restores_the_index_rather_than_inverting_it(book, sidecar):
    curation = Curation(book, sidecar)
    before = [e["name"] for e in curation.model["entities"]]
    keep, also = curation.candidates(179)[0]
    curation.merge(keep, also)
    assert curation.can_undo
    curation.undo()
    assert [e["name"] for e in curation.model["entities"]] == before
    assert not curation.can_undo


def test_undo_reaches_back_through_several_rulings(book, sidecar):
    curation = Curation(book, sidecar)
    before = len(curation.model["entities"])
    for keep, also in curation.candidates(179)[:3]:
        curation.merge(keep, also)
    while curation.can_undo:
        curation.undo()
    assert len(curation.model["entities"]) == before


def test_keeping_two_names_separate_stops_them_being_offered_again(book, sidecar):
    curation = Curation(book, sidecar)
    keep, also = curation.candidates(179)[0]
    curation.separate(keep, also)
    assert (keep, also) not in curation.candidates(179)
    assert len(curation.model["entities"]) == len(Curation(book, None).model["entities"])


def test_nothing_merges_without_being_asked(book, sidecar):
    """Two mechanical signals for this were tested over six novels and both
    failed. Ariadne proposes; the reader rules."""
    curation = Curation(book, sidecar)
    assert curation.candidates(179), "there should be pairs to ask about"
    assert len(curation.model["entities"]) == len(book["entities"])


def test_a_note_is_kept_against_the_name(book, sidecar):
    curation = Curation(book, sidecar)
    curation.note("Pierre", "the one who inherits", 179)
    assert Curation(book, sidecar).note_for("Pierre") == "the one who inherits"
    curation.note("Pierre", "", 179)
    assert Curation(book, sidecar).note_for("Pierre") == ""


def test_a_warning_lands_a_chapter_early_and_never_sooner(book, sidecar):
    curation = Curation(book, sidecar)
    curation.warn(40, "somebody does not make it through this one")
    warn = curation.model["warn"]
    visible = sorted(int(at) for at in warn)
    assert visible == [39], "a warning is announced exactly one chapter early"
    assert "does not make it" not in json.dumps(
        {at: rows for at, rows in warn.items() if int(at) < 39}
    )


def test_the_position_is_remembered(book, sidecar):
    curation = Curation(book, sidecar)
    assert curation.position == 0
    curation.remember_position(41)
    assert Curation(book, sidecar).position == 41


def test_a_failed_write_does_not_destroy_what_was_there(tmp_path):
    """The sidecar holds every ruling the reader has made. A crash partway
    through a write must leave the old file, not half of a new one."""
    path = tmp_path / "book.ariadne.json"
    save_decisions(str(path), {"links": [{"keep": "A", "also": "B", "state": "accepted"}]})
    original = path.read_text(encoding="utf-8")

    class Unserialisable:
        pass

    with pytest.raises(TypeError):
        save_decisions(str(path), {"links": Unserialisable()})
    assert path.read_text(encoding="utf-8") == original
    assert load_decisions(str(path))["links"][0]["also"] == "B"
    assert not list(tmp_path.glob(".ariadne-*")), "a failed write left a temporary file"


# --- a book somewhere that cannot be written -------------------------------
#
# Found on a real book: Divergent, opened from a removable drive through the
# Flatpak file portal, which grants the one file that was picked and not the
# directory around it. Every bookmark move wrote a temporary file whose rename
# failed, the exception went into a GTK signal handler that prints and carries
# on, and the header said "Saved locally" throughout. An hour of reading and
# every ruling in it was lost, and the only trace was an orphaned temp file.


def test_it_says_up_front_when_it_cannot_save(tmp_path):
    """Before the reader spends an hour relying on it, not after."""
    from ariadne.app.curation import Curation

    # A path whose directory is not one. The portal case is the same shape from
    # the process's side: a place a file cannot be created and renamed.
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("", encoding="utf-8")

    curation = Curation({"entities": [], "chapters": 3}, str(blocked / "book.ariadne.json"))
    assert curation.trouble, "a place it cannot write reported no trouble"
    assert curation.saves_to, "the path is still where it would save"


def test_a_place_that_stops_being_writable_is_reported_rather_than_raised(tmp_path):
    """It used to raise into a signal handler, which prints and carries on.

    A store directory that has simply gone is remade -- that is a first run,
    not a failure. This is the other case: somewhere a directory cannot be
    made at all, which is what the file portal looked like from inside the
    process.
    """
    import shutil

    from ariadne.app.curation import Curation

    home = tmp_path / "store"
    home.mkdir()
    book = home / "book.ariadne.json"
    curation = Curation({"entities": [], "chapters": 9}, str(book))
    assert not curation.trouble, "a writable directory reported trouble"

    curation.remember_position(2)
    assert book.is_file(), "a writable directory did not save"

    shutil.rmtree(home)
    home.write_text("", encoding="utf-8")  # a file where the directory was
    curation.remember_position(5)  # must not raise
    assert curation.trouble, "a save that failed reported nothing"


def test_a_store_that_does_not_exist_yet_is_made(tmp_path):
    """The first run ever. Failing on a missing store would be the same loss."""
    from ariadne.app.curation import Curation

    book = tmp_path / "never" / "been" / "here" / "book.ariadne.json"
    curation = Curation({"entities": [], "chapters": 9}, str(book))
    assert not curation.trouble, curation.trouble
    curation.remember_position(3)
    assert book.is_file(), "a first run did not create its own store"


def test_a_saveable_book_says_nothing_at_all(tmp_path):
    """The quiet path, which is the one that has to stay quiet."""
    from ariadne.app.curation import Curation

    curation = Curation({"entities": [], "chapters": 4}, str(tmp_path / "b.ariadne.json"))
    curation.remember_position(1)
    assert curation.trouble == ""


# --- where the rulings live ------------------------------------------------
#
# They were beside the book until 2026-09-08, when a book on a removable drive
# opened through the Flatpak file portal lost an hour of them: the portal
# grants the one file that was picked and not the directory around it, so every
# save failed and the only trace was an orphaned temporary file.


def test_the_store_is_not_beside_the_book(tmp_path, monkeypatch):
    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = tmp_path / "somewhere" / "read-only" / "book.epub"
    book.parent.mkdir(parents=True)
    book.write_bytes(b"a book")

    where = sidecar_path(str(book))
    assert str(book.parent) not in where, "the rulings are still beside the book"
    assert where.startswith(str(tmp_path / "store"))


def test_a_book_is_found_by_what_is_in_it_not_where_it_sits(tmp_path, monkeypatch):
    """So a library that gets reorganised does not lose every ruling in it."""
    import shutil

    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    first = tmp_path / "here" / "book.epub"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"the same bytes")
    moved = tmp_path / "elsewhere" / "book.epub"
    moved.parent.mkdir(parents=True)
    shutil.copy(first, moved)

    assert sidecar_path(str(first)) == sidecar_path(str(moved))

    different = tmp_path / "other.epub"
    different.write_bytes(b"different bytes entirely")
    assert sidecar_path(str(different)) != sidecar_path(str(first))


def test_a_renamed_book_keeps_its_rulings(tmp_path, monkeypatch):
    """The slug in the filename is for a human; the hash is what identifies it."""
    from ariadne.decisions.sidecar import book_key

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = tmp_path / "Divergent.epub"
    book.write_bytes(b"the same bytes")
    before = book_key(str(book))
    renamed = tmp_path / "01 - Divergent (2011).epub"
    book.rename(renamed)
    assert book_key(str(renamed)) == before


def test_rulings_already_beside_a_book_are_read_once_and_never_written_again(tmp_path, monkeypatch):
    """Upgrading must lose nothing somebody has already ruled on."""
    import json

    from ariadne.app.curation import Curation
    from ariadne.decisions.sidecar import beside_book, decisions_for

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = tmp_path / "book.epub"
    book.write_bytes(b"a book")
    older = tmp_path / "book.epub.ariadne.json"
    older.write_text(json.dumps({"position": 17, "hidden": ["Someone"]}), encoding="utf-8")

    where, found = decisions_for(str(book))
    assert found["position"] == 17, "an existing sidecar was not read"
    assert found["hidden"] == ["Someone"], "existing rulings were not read"
    assert where != beside_book(str(book)), "it would write beside the book again"

    # And writing goes to the store, leaving the old file exactly as it was.
    before = older.read_text(encoding="utf-8")
    curation = Curation({"entities": [], "chapters": 40, "title": "A Book"}, where)
    curation.remember_position(20)
    assert older.read_text(encoding="utf-8") == before, "it wrote to the old sidecar"
    assert json.loads(open(where, encoding="utf-8").read())["position"] == 20
