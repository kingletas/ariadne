from ..analysis.corpus import introduction_curve
from ..analysis.prose import summarise_words

# ---------------------------------------------------------------------------
# Before you start
# ---------------------------------------------------------------------------
#
# THIS ONE IS ABOUT THE WHOLE BOOK, AND SAYS SO EVERYWHERE IT APPEARS.
#
# Everything else here is bounded by where the reader is. This is not, because
# the question it answers is asked before there is a position to bound it with:
# what am I in for. It reports structure and never plot -- how many people, how
# fast they arrive, whether one of them holds the book -- so it can be read
# without learning anything that happens.
#
# It exists because a synopsis does not say any of it. Measured over 113 fiction
# nominees from the 2025 Goodreads Choice Awards: a synopsis names a median of
# two people. Over 53 novels measured whole, a book has introduced nineteen by a
# tenth of the way in and finishes with sixty. Nine of the 153 synopses mention
# narrative structure in any wording; none name a viewpoint count.


def crowding(m, corpus):
    """Where this book sits against the corpus on cast size and arrival."""
    n = len(m["entities"])
    curve, last_new = introduction_curve(m)
    ref = ((corpus or {}).get("curve") or {}).get("all") or {}
    out = {"names": n, "curve": curve, "last_new": last_new, "band": {}}
    for q in ("0.1", "0.25", "0.5", "0.75"):
        b = ref.get(q)
        if b and curve:
            out["band"][q] = (b["p25"], b["p75"])
    return out


def about_report(title, chapters, m, person, foc, series, corpus, bounds=None):
    """What a reader is in for, stated before they start."""
    words = summarise_words(chapters)
    print("%s" % title)
    print(
        "%d chapters, %s words, about %d hours at 250 words a minute"
        % (len(chapters), format(words, ","), round(words / 250 / 60))
    )
    if series:
        where = (" \u2014 book %s" % series["position"]) if series["position"] else ""
        print("\nPART OF A SERIES: %s%s" % (series["name"], where))
        print("  The file says so. Most do not, and most synopses do not either.")

    print("\nHOW MANY PEOPLE YOU WILL BE HOLDING")
    c = crowding(m, corpus)
    print("  %d names in the whole book" % c["names"])
    if c["curve"]:
        for q, label in (
            ("0.1", "a tenth in"),
            ("0.25", "a quarter in"),
            ("0.5", "halfway"),
            ("0.75", "three quarters in"),
        ):
            band = c["band"].get(q)
            met = round(c["names"] * c["curve"][q] / 100)
            note = ""
            if band:
                lo, hi = band
                v = c["curve"][q]
                note = "  (middle half of the corpus is %.0f-%.0f%%, this is %s)" % (
                    lo,
                    hi,
                    "inside" if lo <= v <= hi else "below" if v < lo else "above",
                )
            print(
                "  by %-18s %3.0f%% of them \u2014 about %d people%s"
                % (label, c["curve"][q], met, note)
            )

    if bounds and len(bounds) > 1:
        print("\nHOW THE CAST GROWS ACROSS THE SERIES")
        for btitle, bstart, bcount in bounds:
            end = bstart + bcount - 1
            new_here = sum(1 for e in m["entities"] if bstart <= e["first"] <= end)
            carried = sum(1 for e in m["entities"] if e["first"] < bstart)
            print(
                "  %+5d  %-46s %s"
                % (
                    new_here,
                    btitle[:46],
                    ("%d already known" % carried) if carried else "the start",
                )
            )
        print("  Every name new to a volume is somebody to learn while still")
        print("  holding everyone from before it.")

    if person:
        word = {
            "first": "the first person",
            "mixed": "a mix of first and third",
            "third": "the third person",
        }[person["kind"]]
        print("\nTOLD IN %s" % word.upper())
        print("  %.0f%% of the pronouns outside dialogue are I or me." % (100 * person["share"]))
        if person["kind"] != "third":
            print("  So the narrator is rarely called by name, and every count of who")
            print("  appears most understates them. Nothing below tries to name a lead.")

    if foc and foc.get("refused"):
        print("\nDOES ONE PERSON HOLD IT -- NOT REPORTED")
        print(
            "  This book names its people %.0f times less often than it says he or" % foc["ratio"]
        )
        print("  she, so whoever a chapter belongs to is mostly a pronoun and counting")
        print("  names measures who is talked about instead. Above about 15 that")
        print("  answer is wrong more often than right, so there is no answer here.")
    elif foc:
        print("\nDOES ONE PERSON HOLD IT")
        print(
            "  %s is named most in %.0f%% of chapters; %d different people lead one."
            % (foc["lead"], 100 * foc["share"], foc["owners"])
        )
        print("  A book with a single protagonist reaches 50-60%; one that hands you")
        print("  round a cast sits nearer 12%.")
        print("  Treat the share as a floor: two names for one person that you have")
        print("  not linked yet split their chapters and make the book look wider.")

    print("\nThis page is about the whole book and holds nothing that happens in it.")
    print("Cast size, pace and narration are structure. Everything else ariadne")
    print("shows you stops at the chapter you are on.")
