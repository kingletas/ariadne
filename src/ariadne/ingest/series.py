from ..core.refusal import Refusal
from .book import load

# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------
#
# A series is read in order, so the reader's position is a book and a chapter
# within it, and everything from earlier books is already known. Chapters are
# laid end to end and the position becomes a single index across the whole
# run -- which means the spoiler rule needs no new logic at all, and that is
# the reason for doing it this way rather than tracking a position per book.


def load_series(paths, title_override=None):
    """Several books as one continuous run of chapters."""
    all_chapters, bounds, titles, conventions = [], [], [], []
    for path in paths:
        title, convention, chapters = load(path)
        bounds.append((title, len(all_chapters), len(chapters)))
        all_chapters.extend(chapters)
        titles.append(title)
        conventions.append(convention)
    if len(all_chapters) < 3:
        raise Refusal("the whole series yielded only %d chapters" % len(all_chapters))
    name = title_override or " · ".join(titles)
    conv = "%d books, %d chapters" % (len(paths), len(all_chapters))
    if len(set(conventions)) == 1:
        conv += " (%s)" % conventions[0]
    return name, conv, all_chapters, bounds
