import os

MIN_USES = int(os.environ.get("ARIADNE_MIN_USES", "5"))


# ---------------------------------------------------------------------------
# The other reader
# ---------------------------------------------------------------------------
#
# A novelist wants the opposite of what a reader wants. The reader must not be
# shown what is coming; the writer needs exactly the parts nobody reaches --
# the name used once and dropped, the character who leaves before the ending
# and is never accounted for. Same index, opposite question, so it is a report
# rather than a page: there is no position to respect.


def _corpus_path():
    """Where the measured bands live, in the order they are looked for.

    The default used to be `~/bin/ariadne.d/corpus.json`, which is a fact about
    one machine written into the source. A package installed anywhere has to
    carry its own copy, or `--corpus` and the bands in `--about` are silently
    empty and nothing says why.
    """
    override = os.environ.get("ARIADNE_CORPUS")
    if override:
        return override
    beside = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "corpus.json"
    )
    if os.path.exists(beside):
        return beside
    return os.path.expanduser("~/bin/ariadne.d/corpus.json")


CORPUS = _corpus_path()
