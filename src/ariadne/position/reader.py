import os
import re

from ..core.refusal import Refusal

# ---------------------------------------------------------------------------
# Finding a word
# ---------------------------------------------------------------------------
#
# Full-text search stays in the tool and never reaches the page. An index of
# every word against the chapters it appears in is a far richer derived work
# than a cast list -- it is the book's whole vocabulary, located -- and the
# pages are meant to be shareable precisely because they carry names, counts
# and chapter numbers and nothing else. So the page searches the names it
# already holds, and this searches the file, which the reader already owns.


def koreader_position(path, n_chapters):
    """A chapter index from a KOReader sidecar.

    KOReader keeps reading state in `<book>.sdr/metadata.<ext>.lua`, and the
    field worth having is `percent_finished` -- a fraction of the whole book.
    That is coarser than a chapter, so it is rounded down: being told you are
    one chapter behind where you actually are is safe, and being told you are
    one ahead is a spoiler.
    """
    if os.path.isdir(path):
        found = [os.path.join(path, f) for f in sorted(os.listdir(path)) if f.endswith(".lua")]
        if not found:
            raise Refusal("no .lua metadata in %s" % path)
        path = found[0]
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except OSError as exc:
        raise Refusal("cannot read %s: %s" % (path, exc)) from exc
    m = re.search(r'\["percent_finished"\]\s*=\s*([0-9.]+)', text)
    if not m:
        raise Refusal(
            "no percent_finished in %s. That file is written by KOReader when "
            "it closes a book; a book never opened there has none." % path
        )
    frac = float(m.group(1))
    return max(0, min(n_chapters - 1, int(frac * n_chapters)))


def find_word(chapters, needle, upto):
    """Chapters at or before `upto` that contain `needle`, with a count.

    The position bound is the same one the page uses, so a search cannot
    report a hit the reader has not reached.
    """
    pat = re.compile(r"\b%s\b" % re.escape(needle), re.I)
    out = []
    for i, body in enumerate(chapters):
        if i > upto:
            break
        n = len(pat.findall(body))
        if n:
            out.append((i, n))
    return out
