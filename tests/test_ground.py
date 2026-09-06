"""Where the book has been, and the honesty around it.

The measure that ranks settings is good enough to propose and not good enough
to assert, which is the whole reason the reader rules on each one. These tests
hold both halves: that the proposal is worth making, and that nothing lands on
the map without being asked for.
"""

import json
from pathlib import Path

import pytest

from ariadne.app.curation import Curation
from ariadne.model.ground import moves, proposed, scope, settings

GOLDEN = Path(__file__).resolve().parent / "golden" / "model"


def model(name):
    return json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))


# What a person says these books are actually set in, written down so the
# measure is graded against a reading rather than against itself.
REAL = {
    "war-and-peace": {
        "Moscow",
        "Petersburg",
        "Russia",
        "Boguchárovo",
        "Borodinó",
        "Otrádnoe",
        "Smolénsk",
        "Bald Hills",
        "Mozháysk",
        "Prussia",
        "Pratzen",
        "Vílna",
        "Tarútino",
        "Krásnoe",
        "France",
        "Europe",
    },
    "wuthering-heights": {
        "Wuthering Heights",
        "Gimmerton",
        "Thrushcross Grange",
        "Penistone Crags",
    },
    "great-expectations": {
        "London",
        "Walworth",
        "Richmond",
        "England",
        "Newgate",
        "Mill Pond Bank",
        "Barnard’s Inn",
        "New South Wales",
    },
}


@pytest.mark.parametrize("book", sorted(REAL))
def test_the_proposal_is_worth_putting_to_a_reader(book):
    """Four in five is the bar. Below that it is a guess wearing a map."""
    m = model(book)
    names = [name for name, _ in proposed(m, m["chapters"] - 1)]
    assert names, f"{book}: nothing proposed at all"
    right = sum(1 for name in names if name in REAL[book])
    assert right / len(names) >= 0.66, (
        f"{book}: only {right} of {len(names)} proposals are places — "
        f"{[n for n in names if n not in REAL[book]]}"
    )


def test_a_setting_holds_a_chapter_rather_than_being_mentioned_in_it():
    """Ranking on raw mentions calls Death a place in Moby-Dick."""
    m = model("moby-dick")
    held = dict(settings(m, m["chapters"] - 1))
    assert "Nantucket" in held
    assert len(held["Nantucket"]) > len(held.get("Death", []))


@pytest.mark.parametrize("book", sorted(REAL))
def test_no_chapter_has_two_settings(book):
    m = model(book)
    seen = {}
    for name, chapters in settings(m, m["chapters"] - 1):
        for chapter in chapters:
            assert chapter not in seen, f"chapter {chapter} claimed by {seen[chapter]} and {name}"
            seen[chapter] = name


def test_nothing_past_the_bookmark_is_placed():
    m = model("war-and-peace")
    for upto in (10, 90, 200):
        for _name, chapters in settings(m, upto):
            assert max(chapters) <= upto
        assert all(stay["to"] <= upto for stay in moves(m, upto))


def test_the_journey_reads_in_order():
    m = model("wuthering-heights")
    journey = moves(m, m["chapters"] - 1)
    assert journey == sorted(journey, key=lambda stay: stay["from"])
    assert all(stay["from"] <= stay["to"] for stay in journey)


def test_scope_counts_only_what_has_been_read():
    m = model("war-and-peace")
    early, late = scope(m, 20), scope(m, 200)
    assert early["chapters_placed"] <= late["chapters_placed"]
    assert 0 <= early["settled"] <= 1


def test_a_struck_setting_stays_off_the_map(tmp_path):
    """Moby Dick is a whale, and one click has to be enough, forever."""
    m = model("moby-dick")
    sidecar = str(tmp_path / "moby.epub.ariadne.json")
    curation = Curation(m, sidecar)
    curation.strike_setting("Moby Dick")
    assert "Moby Dick" in Curation(m, sidecar).struck_settings


def test_the_map_is_empty_until_somebody_makes_it(tmp_path):
    m = model("war-and-peace")
    curation = Curation(m, str(tmp_path / "w.ariadne.json"))
    assert curation.kept_settings == set()
    assert proposed(m, 179), "there should be something to propose"
    assert scope(m, 179, curation.kept_settings)["places"] == 0
