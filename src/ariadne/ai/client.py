# ---------------------------------------------------------------------------
# Who is who to whom
# ---------------------------------------------------------------------------
#
# The one thing readers ask for that co-occurrence cannot answer. A map of who
# shares chapters says whether two names are connected and never how; the
# request is always for the how -- who is married to whom, which king rules
# where -- and that is a family tree, which is the artefact a reader of
# Taliesin went looking for and abandoned because the one they found spoiled a
# marriage.
#
# So it needs a model, and it is the most spoiler-dense thing here. Three
# rules keep it usable:
#
#   Bounded by position unless the reader says otherwise. A relation is stored
#   with the chapter it was established in, and hidden until the reader gets
#   there -- so the tree grows as the book does, which is exactly what was
#   asked for and what no wiki can do.
#
#   Facts, not prose. Each relation is a short clause. Nothing from the book
#   is copied into the page, which is what keeps a page shareable.
#
#   The reader's own account, and their say-so. Same as an explanation: their
#   key, their book, their choice to run it.

# Haiku by default: both jobs here are narrow and structured -- answer from an
# excerpt, or list stated relationships -- and the cheapest capable model is
# the right one to spend somebody else's money on. --model overrides it.
#
# Adaptive thinking is only sent to models that accept it. Haiku 4.5 predates
# it and returns a 400 for the parameter, so passing it unconditionally would
# make the default model the one that cannot run.
DEFAULT_MODEL = "claude-haiku-4-5"


ADAPTIVE_THINKING = (
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-fable-5",
    "claude-fable-5-1",
)


def _thinking_for(model):
    """Adaptive thinking where the model takes it, nothing where it does not."""
    return {"thinking": {"type": "adaptive"}} if model in ADAPTIVE_THINKING else {}
