"""The reader's rulings, and the promise that none of them is lost.

Curation is the one thing here that writes. Every test below is really about
the first pillar: never lose somebody's work.
"""

import json
import os
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


# The shelving conventions one book turns up under. Same bytes every time.
SPELLINGS = (
    "Divergent.epub",
    "01 - Divergent - Veronica Roth (2011).epub",
    "[1] divergent_RETAIL.epub",
    "DIVERGENT (2011).epub",
    "divergent.v2.epub",
)


def test_one_book_spelled_five_ways_is_one_file(tmp_path, monkeypatch):
    """The defect this closes: the slug decided the filename, so a book renamed
    on disk opened a second store file and the rulings in the first vanished."""
    from ariadne.decisions.sidecar import decisions_for, save_decisions, store_dir

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    books = []
    for name in SPELLINGS:
        book = tmp_path / name
        book.write_bytes(b"the same bytes")
        books.append(book)

    where, found = decisions_for(str(books[0]), "Divergent")
    found["position"] = 12
    save_decisions(where, found)

    for book in books:
        again, rulings = decisions_for(str(book), "Divergent")
        assert again == where, f"{book.name} opened a different file"
        assert rulings["position"] == 12, f"{book.name} lost the rulings"

    kept = os.listdir(store_dir())
    assert kept == [os.path.basename(where)], f"the store grew a duplicate: {kept}"


def test_the_name_it_is_given_first_is_the_name_it_keeps(tmp_path, monkeypatch):
    """Renaming to match today's filename was tried and churned the store."""
    from ariadne.decisions.sidecar import decisions_for, save_decisions

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    for name in SPELLINGS:
        (tmp_path / name).write_bytes(b"the same bytes")

    where, found = decisions_for(str(tmp_path / SPELLINGS[0]), "Divergent")
    save_decisions(where, found)
    for name in SPELLINGS[1:]:
        again, _ = decisions_for(str(tmp_path / name), "Divergent")
        assert again == where, f"{name} renamed the stored file"


def test_a_filename_is_cleaned_up_when_there_is_no_title(tmp_path, monkeypatch):
    """A shelving convention is not a title, and it is all there is sometimes."""
    from ariadne.decisions.sidecar import store_slug

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = tmp_path / "01 - Divergent (2011).epub"
    book.write_bytes(b"x")
    assert store_slug(str(book)) == "divergent"
    assert store_slug(str(book), "Divergent") == "divergent"
    # A title wins over the filename, because a filename is somebody's shelf.
    assert store_slug(str(tmp_path / "09 - whatever.epub"), "The Atherion") == "the-atherion"


def test_a_name_survives_the_alphabet_it_is_written_in(tmp_path, monkeypatch):
    """This reads Russian books. A title collapsing to "book" is unusable."""
    import unicodedata

    from ariadne.decisions.sidecar import store_slug

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    assert store_slug("/x/y.epub", "Война и мир") == "война-и-мир"
    assert store_slug("/x/y.epub", "三体") == "三体"
    # Composed and decomposed forms of one title are one name.
    same = "Café Society"
    assert store_slug("/x/y.epub", unicodedata.normalize("NFD", same)) == store_slug(
        "/x/y.epub", unicodedata.normalize("NFC", same)
    )
    # And a title with nothing in it a filesystem can use still gets a name.
    assert store_slug("/x/y.epub", "!!! ???") == "book"


def markdown_book(folder, chapters=4, body="Vela walked to Harrowgate."):
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(1, chapters + 1):
        (folder / f"ch{i}.md").write_text(f"# Chapter {i}\n\n{body}\n", encoding="utf-8")
    return folder


def test_a_folder_of_markdown_is_a_book_and_can_be_keyed(tmp_path, monkeypatch):
    """It could not be. `book_key` opened the book to hash it, and a folder is
    not a file -- so choosing one on the welcome screen raised
    IsADirectoryError at the file chooser, on a manuscript."""
    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = markdown_book(tmp_path / "Manuscript")
    where = sidecar_path(str(book))
    assert where.endswith(".json")
    assert "manuscript-" in os.path.basename(where)


def test_a_folder_is_keyed_on_its_chapters_and_not_its_path(tmp_path, monkeypatch):
    import shutil

    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    first = markdown_book(tmp_path / "here" / "Manuscript")
    moved = tmp_path / "elsewhere" / "Manuscript"
    moved.parent.mkdir(parents=True)
    shutil.copytree(first, moved)
    assert sidecar_path(str(first)) == sidecar_path(str(moved))

    changed = markdown_book(tmp_path / "third" / "Manuscript", body="Corin waited instead.")
    assert sidecar_path(str(changed)) != sidecar_path(str(first))


def test_a_folder_key_ignores_what_is_not_a_chapter(tmp_path, monkeypatch):
    """A note beside a manuscript is not part of it, and must not change which
    file the rulings are in."""
    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = markdown_book(tmp_path / "Manuscript")
    before = sidecar_path(str(book))
    (book / "notes.txt").write_text("a thought", encoding="utf-8")
    (book / "cover.png").write_bytes(b"\x89PNG")
    assert sidecar_path(str(book)) == before


def test_a_book_that_was_edited_is_a_different_book(tmp_path, monkeypatch):
    """Stated rather than assumed: the chapters may have moved under every
    decision already made, so the old rulings stay under the old file."""
    from ariadne.decisions.sidecar import sidecar_path

    monkeypatch.setenv("ARIADNE_HOME", str(tmp_path / "store"))
    book = tmp_path / "book.epub"
    book.write_bytes(b"first edition")
    before = sidecar_path(str(book))
    book.write_bytes(b"second edition, re-downloaded")
    assert sidecar_path(str(book)) != before


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
