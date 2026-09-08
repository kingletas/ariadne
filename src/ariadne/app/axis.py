"""Where a chapter falls, in pixels. One answer, used by everything.

Four surfaces drew their own chapter axis and three of them sized it from the
bookmark rather than from the book, so the midpoint of a card strip was a
different chapter from the midpoint of the scale above it. The substitution
that fixes it is this whole module: a position is a function of the book's
length, and nothing here is told where the reader is.

It draws nothing and knows no widgets. A surface that registers with the axis
sets its own horizontal margins to `INSET` and then asks these functions,
which is what makes one plumb line true rather than merely intended.
"""

from __future__ import annotations

# The inset every axis-registered surface shares, matching the content
# column's own margins. A registered surface inside a 1px card border sits one
# pixel in from the axis; that is well under a chapter's width in any book long
# enough for the strips to matter.
INSET = 24


def slot(width: float, chapters: int) -> float:
    """How wide one chapter is on a surface `width` px across."""
    return width / max(1, chapters)


def x_for(chapter: int, width: float, chapters: int) -> float:
    """The centre of a chapter's slot, in px, on a surface `width` px across.

    `chapters` is the book's length and never the bookmark: a scale that
    shortens as the reader advances is a different scale every chapter.
    """
    chapters = max(1, chapters)
    step = slot(width, chapters)
    return min(max(0, chapter), chapters - 1) * step + step / 2


def chapter_at(x: float, width: float, chapters: int) -> int:
    """The chapter under `x`, for clicks and hovers. The inverse of `x_for`."""
    chapters = max(1, chapters)
    if width <= 0:
        return 0
    return min(chapters - 1, max(0, int(x / width * chapters)))
