#!/usr/bin/env python3
"""Rebuild the Ariadne sampling frame from the Project Gutenberg catalogue.

The frame is fiction with a datable author, in one of four language groups, so that
every book can be placed in exactly one language x era x genre cell. A title that
cannot be placed is out of the frame rather than dropped into a default cell —
a wrong stratum is worse than a smaller frame.
"""

import collections
import csv
import os
import re

CSV = os.environ.get(
    "CORPUS_CSV", os.path.expanduser("~/.local/share/ariadne-corpus/pg_catalog.csv")
)

# Language of composition comes from the Library of Congress class, not from the
# language of the file. A Constance Garnett translation of Dostoevsky is an English
# file classed PG, and it is Slavic-composed — which is the distinction the corpus
# was built to test. Grouping on the file's language would put it in "english".
LOCC_GROUP = {"PR": "english", "PS": "english", "PQ": "romance", "PT": "germanic", "PG": "slavic"}

# Genre is decided by Library of Congress class first, because it is assigned by a
# cataloguer; subject strings are a fallback and are far noisier.
GENRE_RULES = [
    ("adventure", r"Adventure stories|Sea stories|Western stories|Pirates|Voyages"),
    ("mystery", r"Detective and mystery|Crime|Spy stories|Thriller"),
    (
        "speculative",
        r"Science fiction|Fantasy fiction|Fantasy literature|Utopias|Horror|Ghost stories|Gothic",
    ),
    ("romance", r"Love stories|Courtship|Romance fiction|Domestic fiction|Marriage -- Fiction"),
    ("historical", r"Historical fiction|War stories|Historical drama"),
]
GENRE_FALLBACK = "general"
GENRES = [g for g, _ in GENRE_RULES] + [GENRE_FALLBACK]

ERAS = [
    ("pre-1800", None, 1799),
    ("1800-1849", 1800, 1849),
    ("1850-1879", 1850, 1879),
    ("1880-1909", 1880, 1909),
    ("1910-", 1910, None),
]

YEARS = re.compile(r"(\d{4})\s*-\s*(\d{4})")
FICTION = re.compile(r"\bfiction\b|\bnovel", re.I)


def author_years(field):
    """First author's birth and death, from 'Surname, Name, 1812-1870'."""
    m = YEARS.search(field or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def era_of(birth, death):
    """Place a book by the author's mid-career, taken as birth + 40.

    Using the author rather than the Issued date is deliberate: Issued is when
    Gutenberg posted the file, which says nothing about when the book was written.
    """
    if birth is None:
        return None
    mid = birth + 40
    if death and death < mid:
        mid = (birth + death) // 2
    for name, lo, hi in ERAS:
        if (lo is None or mid >= lo) and (hi is None or mid <= hi):
            return name
    return None


def genre_of(subjects, locc):
    for name, pat in GENRE_RULES:
        if re.search(pat, subjects, re.I):
            return name
    return GENRE_FALLBACK


def group_of(locc):
    """The first literature class on the record decides the language group."""
    for code in re.findall(r"\bP[RSQTG]\b", locc or ""):
        return LOCC_GROUP[code]
    return None


def build():
    frame, dropped = [], collections.Counter()
    for row in csv.DictReader(open(CSV, encoding="utf-8")):
        if row["Type"] != "Text":
            dropped["not text"] += 1
            continue
        lang = (row["Language"] or "").split(";")[0].strip()
        # English-language files only. The group above is the language of
        # composition; this is the language of the text actually measured, and
        # the prose measures are not comparable across languages -- MATTR on an
        # agglutinative language is structurally higher for reasons that are
        # nothing to do with the writing.
        if lang != "en":
            dropped["not an English-language file"] += 1
            continue
        subj, locc, shelves = row["Subjects"] or "", row["LoCC"] or "", row["Bookshelves"] or ""
        group = group_of(locc)
        if not group:
            dropped["not a literature class"] += 1
            continue
        if not FICTION.search(subj) and not FICTION.search(shelves):
            dropped["literature but not fiction"] += 1
            continue
        birth, death = author_years(row["Authors"])
        era = era_of(birth, death)
        if era is None:
            dropped["author not datable"] += 1
            continue
        frame.append(
            {
                "id": int(row["Text#"]),
                "title": row["Title"],
                "authors": row["Authors"],
                "language": lang,
                "group": group,
                "era": era,
                "genre": genre_of(subj, locc),
            }
        )
    return frame, dropped


if __name__ == "__main__":
    frame, dropped = build()
    print("FRAME: %d titles\n" % len(frame))
    print("excluded:")
    for k, v in dropped.most_common():
        print("   %-24s %6d" % (k, v))
    print("\nby language group:")
    for k, v in collections.Counter(b["group"] for b in frame).most_common():
        print("   %-10s %6d" % (k, v))
    print("\nby era:")
    for name, _, _ in ERAS:
        print("   %-10s %6d" % (name, sum(1 for b in frame if b["era"] == name)))
    print("\nby genre:")
    for g in GENRES:
        print("   %-12s %6d" % (g, sum(1 for b in frame if b["genre"] == g)))
    cells = collections.Counter((b["group"], b["era"], b["genre"]) for b in frame)
    print(
        "\ncells: %d of %d possible occupied; empty %d"
        % (len(cells), 4 * 5 * 6, 4 * 5 * 6 - len(cells))
    )
    print("smallest occupied cells:", cells.most_common()[-5:])
