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
