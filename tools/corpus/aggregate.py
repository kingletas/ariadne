#!/usr/bin/env python3
"""Turn the per-book measurements into the bands Ariadne reports.

Keeps corpus.json's existing shape so the tool reads it unchanged, and adds two
things it did not carry: the frame definition, and the list of books measured.
Their absence is why the 259-book corpus could not be extended and had to be
rebuilt from nothing.

Groups follow the Library of Congress class. "english" is PR/PS — composed in
English; "translated" is PQ/PT/PG — composed in a Romance, Germanic or Slavic
language and read here in translation.

Usage:  aggregate.py MEASURED.json SAMPLE.json OUT.json
"""

import json
import os
import statistics as st
import sys
from datetime import date

POINTS = ["0.1", "0.25", "0.5", "0.75"]


def summary(values):
    v = sorted(values)
    if not v:
        return None
    return {
        "n": len(v),
        "min": round(v[0], 3),
        "max": round(v[-1], 3),
        "median": round(st.median(v), 3),
        "p25": round(percentile(v, 25), 3),
        "p75": round(percentile(v, 75), 3),
        "mean": round(st.fmean(v), 3),
        "sd": round(st.stdev(v), 3) if len(v) > 1 else 0.0,
    }


def percentile(sorted_v, p):
    """Linear interpolation, matching the quartiles the corpus already reports."""
    if len(sorted_v) == 1:
        return sorted_v[0]
    k = (len(sorted_v) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_v) - 1)
    return sorted_v[lo] + (sorted_v[hi] - sorted_v[lo]) * (k - lo)


def measured_on(path):
    """When the books were measured, which is not when this was run.

    The field is called `measured` and used to carry `date.today()`, so
    re-aggregating an old measurement relabelled it as measured today. The
    measurement artefact's own timestamp is the honest answer, and it makes
    `build` reproducible: the same measurements give the same file.
    """
    return date.fromtimestamp(os.path.getmtime(path)).isoformat()


def main():
    measured = json.load(open(sys.argv[1]))
    sample = json.load(open(sys.argv[2]))
    out_path = sys.argv[3]

    # Only the drawn sample counts. The text directory can hold books from an
    # earlier draw, and a corpus that quietly includes them is no longer the
    # stratified sample it claims to be.
    drawn = {str(b["id"]) for b in sample["sample"]}
    books = [v for k, v in measured.items() if k in drawn]
    missing = len(drawn) - len(books)
    if missing:
        print("WARNING: %d drawn books have no measurement" % missing)
    groups = {
        "all": books,
        "english": [b for b in books if b.get("group") == "english"],
        "translated": [b for b in books if b.get("group") in ("romance", "germanic", "slavic")],
    }

    curve, prose = {}, {}
    for name, rows in groups.items():
        seg = [b for b in rows if b.get("segmented")]
        curve[name] = {p: summary([b["curve"][p] for b in seg if "curve" in b]) for p in POINTS}
        curve[name]["last_new"] = summary([b["last_new"] for b in seg if "last_new" in b])
        lex = [b for b in rows if b.get("mattr") and b.get("segmented")]
        prose[name] = {
            "mattr": summary([b["mattr"] for b in lex]),
            "sentence_cv": summary([b["sentence_cv"] for b in lex]),
        }

    segmented = sum(1 for b in books if b.get("segmented"))
    lexical = sum(1 for b in books if b.get("mattr") and b.get("segmented"))

    # per-stratum bands: the reason for going to 1000 in the first place
    strata = {}
    for axis in ("group", "era", "genre"):
        strata[axis] = {}
        for value in sorted({b.get(axis) for b in books if b.get(axis)}):
            seg = [b for b in books if b.get(axis) == value and b.get("segmented")]
            if len(seg) < 12:  # too thin to quote a quartile from
                continue
            strata[axis][value] = {
                "n": len(seg),
                "curve_0.25": summary([b["curve"]["0.25"] for b in seg if "curve" in b]),
                "mattr": summary([b["mattr"] for b in seg if b.get("mattr")]),
            }

    out = {
        "note": (
            "Measured, not chosen. %d books drawn by metadata from a frame of %d, "
            "stratified by language of composition, era and genre. A number outside "
            "a band is a difference and never a fault." % (len(books), sample["frame"]["size"])
        ),
        "measured": measured_on(sys.argv[1]),
        "sources": {
            "selection": "%d Gutenberg texts, stratified" % len(books),
            "segmented": segmented,
            "lexical": lexical,
            "strata": "english/romance/germanic/slavic x 5 eras x 6 genres",
            "lexical_note": (
                "prose measured on the %d files that segment; %d of %d refuse "
                "and cannot be chaptered" % (lexical, len(books) - segmented, len(books))
            ),
        },
        "frame": sample["frame"],
        "draw": {
            "seed": sample["seed"],
            "supersedes": (
                "the 259-book corpus of 2026-09-05, whose frame and book list "
                "were not kept; the two are not comparable"
            ),
        },
        "curve": curve,
        "prose": prose,
        "by_stratum": strata,
        "books": sorted(
            [
                {"id": b["id"], "cell": b.get("cell"), "segmented": bool(b.get("segmented"))}
                for b in books
            ],
            key=lambda b: b["id"],
        ),
    }
    json.dump(out, open(out_path, "w"), indent=1)

    print("corpus: %d books, %d segmented, %d with prose" % (len(books), segmented, lexical))
    print("\nintroduction curve, all books")
    print("  %-12s %8s %8s %8s" % ("point", "p25", "median", "p75"))
    for p in POINTS + ["last_new"]:
        s = curve["all"][p]
        if s:
            print("  %-12s %8.1f %8.1f %8.1f" % (p, s["p25"], s["median"], s["p75"]))
    m = prose["all"]["mattr"]
    print(
        "\nmattr  p25 %.3f  median %.3f  p75 %.3f  (n=%d)"
        % (m["p25"], m["median"], m["p75"], m["n"])
    )
    print("\nper-stratum bands quotable (n>=12):")
    for axis, d in strata.items():
        print("  %-6s %s" % (axis, ", ".join("%s(%d)" % (k, v["n"]) for k, v in d.items())))
    print("\nwritten to " + out_path)


if __name__ == "__main__":
    main()
