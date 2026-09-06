"""What the reader is allowed to see, and what the attention view is worth.

`clip` is the spoiler rule for every native front end; `away_a_while` is the
measure that was rebuilt once already for firing on almost everything it saw.
Both are asserted against a real book rather than a fixture, because the
failure in each case only appears at scale.
"""

import json
from pathlib import Path

import pytest

from ariadne.model.view import away_a_while, clip, matching, often_with, ranked

GOLDEN = Path(__file__).resolve().parent / "golden" / "model"


@pytest.fixture(scope="module")
def war():
    return json.loads((GOLDEN / "war-and-peace.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("book", sorted(p.stem for p in GOLDEN.glob("*.json")))
def test_clip_never_reaches_past_the_bookmark(book):
    """The one property. Checked at every tenth chapter of every book."""
    model = json.loads((GOLDEN / f"{book}.json").read_text(encoding="utf-8"))
    for upto in range(0, model["chapters"], max(1, model["chapters"] // 10)):
        for entity in clip(model, upto):
            assert entity["first"] <= upto, f"{book}: {entity['name']} met later than {upto}"
            assert max(entity["chapters"]) <= upto, (
                f"{book}: {entity['name']} appears past chapter {upto}"
            )
            assert entity["total"] == sum(entity["counts"])


def test_clip_grows_but_never_shrinks(war):
    counts = [len(clip(war, upto)) for upto in range(0, 200, 20)]
    assert counts == sorted(counts)
    assert counts[0] < counts[-1]


def test_away_a_while_surfaces_the_few_not_the_many(war):
    """It flagged 146 of 378 without the establishment floor, and 528 of 533
    before the rule was rebuilt at all. A view that fires on a third of its
    input trains the reader to ignore the tab rather than the entry."""
    met = clip(war, 179)
    away = away_a_while(met, 179, war["pace"])
    assert len(away) < len(met) * 0.20, (
        f"{len(away)} of {len(met)} flagged — the floor is not holding"
    )
    assert [e["name"] for e in away[:3]] == ["Dólokhov", "Anatole", "Prince Vasíli"]


def test_away_a_while_is_empty_at_the_start(war):
    assert away_a_while(clip(war, 2), 2, war["pace"]) == []


def test_a_walk_on_is_finished_rather_than_forgotten(war):
    """Somebody seen twice in chapter three has not been lost track of."""
    met = clip(war, 179)
    away = {e["name"] for e in away_a_while(met, 179, war["pace"])}
    walk_ons = [e["name"] for e in met if len(e["chapters"]) < 4 or e["total"] < 10]
    assert away.isdisjoint(walk_ons)


def test_search_ignores_accents_and_case(war):
    met = ranked(clip(war, 179))
    assert [e["name"] for e in matching(met, "natasha")] == ["Natásha"]
    assert matching(met, "BEZUKHOV")
    assert matching(met, "  ") == met


def test_often_with_comes_from_the_recorded_co_occurrence(war):
    beside = often_with(war, "Natásha", 179)
    assert beside and "Sónya" in beside
    assert "Natásha" not in beside
