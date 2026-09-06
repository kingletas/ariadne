"""One book, turned into the model every front end is drawn from.

This exists so there is one assembly rather than one per front end. The command
line built it inline, which was fine while the page was the only thing that
consumed it; the desktop reader opening a book on its own would have meant a
second copy of a nine-step pipeline, and the two would have parted.
"""

from __future__ import annotations

import copy

from .analysis.about import crowding
from .analysis.corpus import load_corpus
from .analysis.prose import (
    focus,
    narrative_person,
    pace,
    summarise_words,
    warning_map,
)
from .core.settings import MIN_USES
from .decisions.sidecar import apply_decisions, load_decisions, sidecar_path
from .ingest.book import load
from .ingest.epub import epub_series
from .ingest.quotes import quote_convention
from .ingest.series import load_series
from .model.build import build_model, model_json
from .model.classify import classify

WPM = 250


def open_book(paths, *, title=None, min_uses=None, spoil=False, decisions_path=None):
    """A book (or a series read as one) as `(model, undecided, sidecar)`.

    `undecided` is the index before the reader's rulings are folded in, kept
    because a merge cannot be inverted once the index is rewritten and the
    desktop reader lets one be taken back.
    """
    if isinstance(paths, str):
        paths = [paths]

    bounds = None
    if len(paths) > 1:
        title_read, convention, chapters, bounds = load_series(paths, title)
    else:
        title_read, convention, chapters = load(paths[0], title)

    quotes = (
        "speaker labels"
        if convention.startswith("play:")
        else quote_convention("\n".join(chapters))
    )

    sidecar = decisions_path or sidecar_path(paths[0])
    decisions = load_decisions(sidecar)

    presence, counts, first = build_model(chapters, min_uses or MIN_USES)

    person = narrative_person(chapters)
    kinds = classify("\n".join(chapters), set(first), (person or {}).get("kind"))

    model = model_json(title_read, convention, quotes, presence, counts, first, kinds)
    undecided = copy.deepcopy(model["entities"])
    model["entities"] = apply_decisions(model["entities"], decisions)

    if bounds:
        model["books"] = [{"title": b[0], "start": b[1], "chapters": b[2]} for b in bounds]
    model["glosses"] = decisions.get("glosses") or {}
    # Only what the reader has accepted. A proposed relationship is invisible,
    # exactly as an unaccepted alias link is.
    model["relations"] = {
        name: [r for r in rows if r.get("state") == "accepted"]
        for name, rows in (decisions.get("relations") or {}).items()
    }
    model["relations"] = {k: v for k, v in model["relations"].items() if v}
    model["spoil"] = bool(spoil)
    model["pace"] = pace(chapters, presence, first)

    words = summarise_words(chapters)
    measured = crowding(model, load_corpus())
    model["about"] = {
        "words": words,
        "hours": round(words / WPM / 60),
        "names": measured["names"],
        "curve": measured["curve"],
        "band": measured["band"],
        "person": person,
        "focus": focus(counts, kinds, person, (person or {}).get("third_pronouns", 0)),
        # A series run loads every volume, so the first file's own metadata
        # would announce "book 1" over a page covering all of them.
        "series": None if bounds else epub_series(paths[0]),
    }
    if bounds:
        # A series reader's question is not how big the cast is, it is how much
        # of it arrived before the volume in their hand.
        model["about"]["volumes"] = [
            {
                "title": btitle,
                "new": sum(
                    1 for e in model["entities"] if bstart <= e["first"] <= bstart + bcount - 1
                ),
                "carried": sum(1 for e in model["entities"] if e["first"] < bstart),
                "chapters": bcount,
            }
            for btitle, bstart, bcount in bounds
        ]
    model["warn"] = warning_map(decisions.get("warnings") or [], len(chapters), spoil=bool(spoil))

    return model, undecided, sidecar
