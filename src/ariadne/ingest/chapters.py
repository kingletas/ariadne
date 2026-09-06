import re

from ..core.refusal import Refusal

# Scene-break markers differ per publisher; there is no standard. These class
# names were read off real books. `sp` is a break, `split_noi` is not, so the
# match is anchored.
BREAK_CLASS = re.compile(
    r"^(sp|orn|separator|sbreak|SB\d*|para-sp|.*[Ss]pace-?[Bb]reak.*|.*[_-]asep)$"
)


# Chapter heading conventions, most specific first. The table of contents uses
# the same convention as the headings it lists, which is why drop_toc exists.
# `CHAP.` is the 18th-century spelling and it is not a rarity: across twenty
# refused pre-1800 books it appears 188 times, and requiring the word in full
# is why five of fifteen were usable before 1800 against thirteen of fifteen
# after 1860. `LETTER n` is the other half -- the epistolary novel divides on
# letters, and a segmenter with no word for one refuses the whole form.
CHAP = r"CHAP(?:TER|S?\.|\b)"


FORMS = [
    (
        "chapter_titled",
        re.compile(r"^[ \t]*%s\s*(?:[IVXLC]+|\d+)[.:]?\s+\S.*$" % CHAP, re.M | re.I),
    ),
    (
        "chapter_plain",
        re.compile(r"^[ \t]*%s\s*(?:[IVXLC]+|\d+|[A-Z][a-z]+)[.:]?[ \t]*$" % CHAP, re.M | re.I),
    ),
    (
        "letter_n",
        re.compile(r"^[ \t]*LETTER\s+(?:[IVXLC]+|\d+|[A-Z][a-z]+)[.:]?[ \t]*.*$", re.M | re.I),
    ),
    # A verse epic divides on cantos and a tale collection on nights or tales.
    # These are what the reader actually stops at, so they are the right unit
    # even though none of them is called a chapter.
    (
        "division",
        re.compile(
            r"^[ \t]*(?:CANTO|STAVE|FYTTE|NIGHT|TALE|EPISODE|IDYLL)\s+"
            r"(?:[IVXLC]+|\d+|[A-Z][a-z]+)[.:]?[ \t]*.*$",
            re.M | re.I,
        ),
    ),
    (
        "book_n",
        re.compile(r"^[ \t]*BOOK\s+(?:[IVXLC]+|\d+|[A-Z][A-Za-z]+)[.:]?[ \t]*.*$", re.M | re.I),
    ),
    ("bare_roman", re.compile(r"^[ \t]*([IVXLC]{1,6})[.:]?[ \t]*$", re.M)),
    ("bare_arabic", re.compile(r"^[ \t]*(\d{1,3})[.:]?[ \t]*$", re.M)),
]


def drop_toc(text, marks):
    """Keep only headings with real prose after them. A contents entry has
    almost nothing between it and the next entry."""
    if len(marks) < 4:
        return marks
    keep = []
    for i, m in enumerate(marks):
        nxt = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        if len(text[m.end() : nxt].split()) >= 120:
            keep.append(m)
    return keep or marks


def split_text(text):
    best = None
    for name, pat in FORMS:
        marks = drop_toc(text, list(pat.finditer(text)))
        if len(marks) < 2:
            continue
        if best is None or len(marks) > len(best[1]):
            best = (name, marks)
    if best is None:
        raise Refusal(
            "no chapter convention found. Looked for: CHAPTER n, CHAPTER n. Title, "
            "BOOK n, a bare roman numeral, a bare number -- each alone on its line."
        )
    name, marks = best
    out = []
    for i, m in enumerate(marks):
        nxt = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append(text[m.start() : nxt].strip())
    return name, out
