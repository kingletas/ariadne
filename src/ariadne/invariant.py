"""The one property that must never regress, and the place it is asserted.

This is not a test helper. `ariadne --self-test` is a documented command and
the developer guide calls it the gate, so it lives in the package and the suite
calls it too rather than owning it. A fixture is generated rather than read:
the property is about the index, not about any particular book.
"""

from .analysis.prose import pace, warning_map
from .decisions.sidecar import apply_decisions
from .model.build import build_model, model_json


def self_test():
    """Build every view of a synthetic book and assert nothing leaks.

    The fixture is generated rather than read: the property under test is about
    the index, not about any particular book, and a fixture with no text in it
    cannot drift when a corpus moves.
    """
    chapters = []
    for i in range(12):
        who = ["Alda", "Bertrand", "Cosima", "Dmitri", "Evrémonde", "Fyodor"][: i // 2 + 1]
        body = " ".join(
            "%s walked in and %s answered him plainly here." % (w, w) for w in who for _ in range(4)
        )
        chapters.append("Chapter %d\n\n%s" % (i + 1, body))
    presence, counts, first = build_model(chapters, min_uses=3)
    if len(first) < 4:
        return 1, "fixture produced only %d entities; the test proves nothing" % len(first)
    leaks = 0
    for i in range(len(chapters)):
        seen = set()
        for j in range(i + 1):
            seen |= presence[j]
        for name in seen:
            if first[name] > i:
                leaks += 1
    # The invariant must survive a merge, because folding two names into one
    # rewrites `first` to the earlier of them. A reader who accepted a link
    # supplied that knowledge themselves, so the merged entity is legitimately
    # first met where its earliest half was -- but it must never move LATER,
    # and no merged entity may appear before its own first chapter.
    ents = [
        {
            "name": n,
            "first": f,
            "chapters": [i for i, h in enumerate(presence) if n in h],
            "counts": [counts[i].get(n, 0) for i, h in enumerate(presence) if n in h],
            "total": sum(c.get(n, 0) for c in counts),
        }
        for n, f in sorted(first.items(), key=lambda kv: kv[1])
    ]
    names = [e["name"] for e in ents]
    merged_leaks = 0
    if len(names) >= 2:
        keep, also = names[0], names[-1]
        d = {
            "links": [{"keep": keep, "also": also, "state": "accepted"}],
            "hidden": [],
            "renamed": {},
        }
        folded = apply_decisions(ents, d)
        by_name = {e["name"]: e for e in folded}
        if also in by_name:
            merged_leaks += 1  # the folded name must be gone
        m = by_name.get(keep)
        if m and m["chapters"] and m["first"] > min(m["chapters"]):
            merged_leaks += 1  # first must not trail its own use

    # A warning must never be visible more than one chapter before the chapter
    # it is about, and never at all before that. The page indexes D.warn by the
    # position at which each becomes visible, so testing the map IS testing the
    # rule -- there is no second copy of the threshold in the page to drift.
    warn_rows = [{"at": i, "text": "w%d" % i} for i in range(len(chapters))]
    wmap = warning_map(warn_rows, len(chapters))
    warn_leaks = 0
    for upto in range(len(chapters)):
        visible = [w for key, rows in wmap.items() if int(key) <= upto for w in rows]
        for w in visible:
            if w["at"] > upto + 1:
                warn_leaks += 1  # more than one chapter early
        for w in warn_rows:
            if w["at"] - 1 <= upto and w not in visible and w["at"] > 0:
                warn_leaks += 1  # due, and did not appear
    if len(wmap) != len(chapters) - 1:
        # Chapters 1 and 2 share a reveal position, since a warning on the
        # first chapter has nowhere earlier to go.
        warn_leaks += 1
    spoiled = warning_map(warn_rows, len(chapters), spoil=True)
    if set(spoiled) != {"0"}:
        warn_leaks += 1  # --spoil must reveal all at once

    pace_rows = pace(chapters, presence, first)
    pace_bad = (
        len(pace_rows) != len(chapters)
        or any(r["d"] < 0 or r["d"] > 100 for r in pace_rows)
        or any(r["o"] < 0 or r["f"] < 0 for r in pace_rows)
    )

    # The same book must produce the same file every time. Ties on `first` are
    # the normal case, and with nothing to break them they broke on set
    # iteration order, which Python randomises per process. Asserting the sort
    # key is what stops that returning.
    ordered = model_json("t", "c", "double", presence, counts, first)["entities"]
    keys = [(e["first"], e["name"]) for e in ordered]
    unordered = keys != sorted(keys)

    accents = [n for n in first if any(c in n for c in "éèêàóúí")]
    problems = []
    if warn_leaks:
        problems.append("%d warning visibility fault(s)" % warn_leaks)
    if pace_bad:
        problems.append(
            "pace produced %d row(s) for %d chapters, or a value out of range"
            % (len(pace_rows), len(chapters))
        )
    if unordered:
        problems.append(
            "entities are not ordered by (first chapter, name), so the "
            "same book will not produce the same file twice"
        )
    if leaks:
        problems.append("%d leak(s) across %d views" % (leaks, len(chapters)))
    if merged_leaks:
        problems.append("%d fault(s) after folding an accepted link" % merged_leaks)
    if not accents:
        problems.append("accented name was not indexed -- Unicode handling regressed")
    if problems:
        return 1, "; ".join(problems)
    return 0, (
        "%d views, %d entities, 0 leaks before and after a merge; "
        "%d warnings visible exactly one chapter early and never sooner; "
        "pace clean over %d chapters; %d entities in a stable order; "
        "accented name indexed as %s"
        % (len(chapters), len(first), len(warn_rows), len(pace_rows), len(ordered), accents[0])
    )
