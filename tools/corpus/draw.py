#!/usr/bin/env python3
"""Draw a stratified sample from the frame, and record exactly what was drawn.

Allocation is proportional to the square root of each cell's size, floored at 2 and
capped at 40. Straight proportional allocation would give Slavic 19 books of 1000 and
leave most of its cells empty; sqrt allocation lifts the small strata enough to report
a band for them without pretending they are as well covered as English.

The seed and the frame definition are written out with the sample, because a draw
nobody can repeat is the reason this corpus had to be rebuilt from nothing.
"""

import collections
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import ERAS, GENRES, build

SEED = int(os.environ.get("CORPUS_SEED", "20260905"))
TARGET = 1000
FLOOR, CAP = 2, 40


def allocate(cells, target):
    """Cell size -> how many to draw from it. sqrt-proportional, floored and capped."""
    weight = {k: math.sqrt(len(v)) for k, v in cells.items()}
    total = sum(weight.values())
    alloc = {}
    for k, v in cells.items():
        n = round(target * weight[k] / total)
        # the cell's own size is the last word: the floor may not promise books
        # that are not there, which silently under-delivers the sample.
        alloc[k] = min(len(v), max(FLOOR, min(n, CAP)))
    # settle the rounding against the target, largest cells first, never past cell size
    order = sorted(cells, key=lambda k: -len(cells[k]))
    while sum(alloc.values()) != target:
        short = target - sum(alloc.values())
        moved = False
        for k in order if short > 0 else reversed(order):
            if short > 0 and alloc[k] < min(CAP, len(cells[k])):
                alloc[k] += 1
                moved = True
            elif short < 0 and alloc[k] > FLOOR:
                alloc[k] -= 1
                moved = True
            if sum(alloc.values()) == target:
                break
        if not moved:
            break
    return alloc


def main():
    global TARGET
    if len(sys.argv) > 2:
        TARGET = int(sys.argv[2])
    frame, dropped = build()
    cells = collections.defaultdict(list)
    for b in frame:
        cells[(b["group"], b["era"], b["genre"])].append(b)

    alloc = allocate(cells, TARGET)
    rng = random.Random(SEED)
    sample, reserve = [], collections.defaultdict(list)
    for key in sorted(cells):
        pool = sorted(cells[key], key=lambda b: b["id"])
        rng.shuffle(pool)
        n = alloc[key]
        for b in pool[:n]:
            b = dict(b, cell="%s/%s/%s" % key)
            sample.append(b)
        # keep the rest of the cell as replacements for books that will not download
        reserve["%s/%s/%s" % key] = [dict(b, cell="%s/%s/%s" % key) for b in pool[n:]]

    out = {
        "seed": SEED,
        "target": TARGET,
        "frame": {
            "source": "Project Gutenberg catalogue CSV, pg_catalog.csv",
            "size": len(frame),
            "definition": (
                "Type=Text; Library of Congress class in PR/PS/PQ/PT/PG, which fixes "
                "language of composition and survives translation; Subjects or "
                "Bookshelves naming fiction or a novel; first author datable."
            ),
            "excluded": dict(dropped),
            "strata": "english/romance/germanic/slavic x 5 eras x 6 genres",
            "cells_occupied": len(cells),
            "allocation": "sqrt-proportional, floor %d, cap %d" % (FLOOR, CAP),
        },
        "sample": sample,
        "reserve": {k: v for k, v in reserve.items()},
    }
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.json"
    json.dump(out, open(path, "w"), indent=1)

    print("frame %d -> sample %d across %d cells" % (len(frame), len(sample), len(cells)))
    print("\nby language group:")
    for k, v in collections.Counter(b["group"] for b in sample).most_common():
        print("   %-10s %4d  (frame %5d)" % (k, v, sum(1 for f in frame if f["group"] == k)))
    print("\nby era:")
    for name, _, _ in ERAS:
        print("   %-10s %4d" % (name, sum(1 for b in sample if b["era"] == name)))
    print("\nby genre:")
    for g in GENRES:
        print("   %-12s %4d" % (g, sum(1 for b in sample if b["genre"] == g)))
    per = collections.Counter(b["cell"] for b in sample)
    print(
        "\nbooks per cell: min %d, median %d, max %d"
        % (min(per.values()), sorted(per.values())[len(per) // 2], max(per.values()))
    )
    print("replacements held in reserve: %d" % sum(len(v) for v in reserve.values()))
    print("written to " + path)


if __name__ == "__main__":
    main()
