#!/usr/bin/env python3
"""Measure every fetched book with Ariadne's own code, and save after each one.

The engine is imported rather than reimplemented, so the new bands are
produced by exactly the code that reads them back. Reimplementing prose_shape or
introduction_curve here would let the corpus and the tool drift apart silently,
which is a failure the stored band has already had once.

A book that will not segment is recorded as a refusal rather than skipped, because
the refusal count is one of the numbers the corpus publishes. Only counts and
ratios are kept — never any of the text, which is the line Ariadne itself draws.

Usage:  measure.py TEXTDIR OUT.json
"""

import json
import os
import sys
from pathlib import Path

# The engine is imported from this checkout rather than from wherever a copy
# happens to be installed, so the bands are produced by exactly the code that
# will read them back. It used to load ~/bin/ariadne by path; that file stopped
# existing the day the tool became a package, and nothing said so until this
# was run.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ariadne.analysis.corpus import introduction_curve  # noqa: E402
from ariadne.analysis.prose import prose_shape  # noqa: E402
from ariadne.core.refusal import Refusal  # noqa: E402
from ariadne.ingest.book import load  # noqa: E402
from ariadne.model.build import build_model, model_json  # noqa: E402


def measure_one(path):
    """One book -> a record of counts and ratios. Raises on refusal."""
    title, convention, chapters = load(path)
    text = "\n".join(chapters)
    rec = {"chapters": len(chapters), "words": len(text.split()), "convention": convention}

    shape = prose_shape(text)
    if shape:
        rec["mattr"] = round(shape["mattr"], 4)
        rec["sentence_cv"] = round(shape["sent_cv"], 4)

    if len(chapters) >= 4:
        presence, counts, first = build_model(chapters, 5)
        model = model_json(title, convention, "double", presence, counts, first)
        curve, last_new = introduction_curve(model)
        if curve:
            rec["curve"] = {k: round(v, 3) for k, v in curve.items()}
            rec["last_new"] = round(last_new, 3)
            rec["names"] = len(model["entities"])
            rec["segmented"] = True
    rec.setdefault("segmented", False)
    return rec


def main():
    textdir, outpath = sys.argv[1], sys.argv[2]
    results = json.load(open(outpath)) if os.path.exists(outpath) else {}
    state = json.load(open(os.path.join(textdir, "_fetch-state.json")))["done"]
    files = sorted(f for f in os.listdir(textdir) if f.endswith(".txt"))

    refused = errored = 0
    for f in files:
        key = f[2:-4]
        if key in results:
            continue
        rec = {"id": int(key)}
        meta = state.get(key, {})
        rec.update({k: meta.get(k) for k in ("title", "authors", "cell", "group", "era", "genre")})
        try:
            rec.update(measure_one(os.path.join(textdir, f)))
        except Refusal as e:
            rec.update({"segmented": False, "refusal": str(e)[:140]})
            refused += 1
        except Exception as e:
            rec.update({"segmented": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
            errored += 1
        results[key] = rec
        json.dump(results, open(outpath, "w"))
        if len(results) % 100 == 0:
            print(
                "  %4d measured, %4d segmented"
                % (len(results), sum(1 for r in results.values() if r.get("segmented"))),
                flush=True,
            )

    seg = sum(1 for r in results.values() if r.get("segmented"))
    pro = sum(1 for r in results.values() if r.get("mattr"))
    print(
        "DONE: %d measured, %d segmented, %d with prose, %d refused, %d errored"
        % (len(results), seg, pro, refused, errored)
    )


if __name__ == "__main__":
    main()
