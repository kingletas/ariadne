"""Where a reader is, when the book is several books."""

from ..core.refusal import Refusal


def resolve_series_position(spec, bounds, n_chapters):
    """A position given as BOOK:CHAPTER, resolved to one index across the run.

    A reader of a series says "book three, chapter five", not "chapter 214".
    Chapters are laid end to end so the spoiler rule needs no new logic, which
    leaves only this translation to do.
    """
    if ":" not in spec:
        return max(0, min(n_chapters - 1, int(spec) - 1))
    book_s, chap_s = spec.split(":", 1)
    try:
        book, chap = int(book_s), int(chap_s)
    except ValueError as exc:
        raise Refusal("position %r is not BOOK:CHAPTER or a chapter number" % spec) from exc
    if not bounds:
        raise Refusal("a BOOK:CHAPTER position needs more than one book")
    if not 1 <= book <= len(bounds):
        raise Refusal("book %d, but this run has %d" % (book, len(bounds)))
    title, start, count = bounds[book - 1]
    if not 1 <= chap <= count:
        raise Refusal("chapter %d, but %s has %d" % (chap, title, count))
    return start + chap - 1
