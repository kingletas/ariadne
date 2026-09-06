import json

from ..core.settings import CORPUS


def load_corpus():
    """The measured band, or nothing. Missing is not an error.

    A band is what 45 books happened to do, not a target: the same corpus
    showed adverb density spreading 13.6x and dialogue share 90x among books
    that all succeeded, so a number outside a band is a difference and never a
    fault. The file is data rather than a constant so re-measuring is an edit.
    """
    try:
        with open(CORPUS, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def introduction_curve(m):
    """What share of the cast the reader has met, at four points in the book.

    The strongest structural regularity in the corpus: half the cast inside
    the first tenth, nine in ten by halfway, and the 19th-century canon and
    the 2021 bestseller list draw nearly the same line.
    """
    n = m["chapters"]
    firsts = sorted(e["first"] for e in m["entities"])
    if not firsts or n < 4:
        return None, None
    out = {}
    for q in ("0.1", "0.25", "0.5", "0.75"):
        cut = int(n * float(q))
        out[q] = 100.0 * sum(1 for f in firsts if f <= cut) / len(firsts)
    last_new = 100.0 * max(firsts) / (n - 1)
    return out, last_new


def band_note(value, band):
    """Where one number falls against a measured band, in words.

    Quoted against the middle half rather than the extremes. Resampling the
    31 books 400 times moves the minimum of the adverb band between 1.8 and
    9.2 and the minimum of the dialogue band between 0.6 and 19.4 -- so a
    report that printed min and max would be quoting the two numbers the
    sample knows worst. The quartiles barely move.
    """
    if not band:
        return ""
    if value < band["p25"]:
        return "below the middle half"
    if value > band["p75"]:
        return "above the middle half"
    return "in the middle half"


def term_coverage(m):
    """The invented vocabulary, and how evenly the book carries it.

    Everything the classifier could not call a person or a place. That bucket
    is where a book's terms of art live -- and also where its noise lives, and
    the two do not separate by frequency: across one manuscript the real terms
    ran a median of 12 uses over 7 chapters against 7 over 5 for the noise,
    which is no gap at all. So this reports the bucket and does not claim to
    know which is which. The author does.
    """
    n = m["chapters"]
    rows = []
    for e in m["entities"]:
        if e.get("kind") != "unknown" or not e["chapters"]:
            continue
        chs = e["chapters"]
        span = (chs[-1] - chs[0] + 1) / n if n else 0
        rows.append(
            {
                "name": e["name"],
                "total": e["total"],
                "chapters": len(chs),
                "first": chs[0],
                "last": chs[-1],
                "span": span,
                "once": len(chs) == 1,
                "front": chs[-1] < n * 0.34 and len(chs) > 1,
                "late": chs[0] > n * 0.66 and len(chs) > 1,
            }
        )
    rows.sort(key=lambda r: -r["total"])
    return rows


def writer_report(m, tail=0.2):
    """Names used once, names that stop early, and names that arrive late."""
    n = m["chapters"]
    last_act = int(n * (1 - tail))
    once, vanished, late = [], [], []
    for e in m["entities"]:
        chs = e["chapters"]
        if not chs:
            continue
        if len(chs) == 1:
            once.append((e["name"], chs[0], e["total"]))
        elif chs[-1] < last_act and e["total"] >= 5:
            vanished.append((e["name"], chs[-1], e["total"]))
        if chs[0] >= last_act and e["total"] >= 5:
            late.append((e["name"], chs[0], e["total"]))
    once.sort(key=lambda r: -r[2])
    vanished.sort(key=lambda r: -r[2])
    late.sort(key=lambda r: -r[2])
    return once, vanished, late, last_act
