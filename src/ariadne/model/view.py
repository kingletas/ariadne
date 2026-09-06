"""The book as it stands at a chapter, and nothing past it.

Every view in every front end is built from this. The page carries its own copy
in JavaScript because it has to run in a browser with no Python behind it; this
is the one the invariant asserts, and the one a native front end uses, so there
are two implementations rather than five.

`upto` is a zero-based chapter index and is inclusive: `clip(m, 0)` is the book
after chapter one.
"""

# A name seen in fewer than four chapters, or used fewer than ten times, was
# never established enough to be forgotten. Twenty thousand words is roughly
# eighty minutes of reading -- a gap somebody actually returns from having lost
# the thread.
MIN_APPEARANCES = 4
MIN_USES = 10
LOST_WORDS = 20000


def clip(model, upto):
    """Every entity met by `upto`, with its later appearances removed.

    An entity first met after the position is absent rather than empty: a name
    the reader has not reached is not a person they know nothing about, it is a
    person who does not exist yet.
    """
    seen = []
    for entity in model["entities"]:
        if entity["first"] > upto:
            continue
        chapters, counts = [], []
        for chapter, count in zip(entity["chapters"], entity["counts"], strict=False):
            if chapter > upto:
                break
            chapters.append(chapter)
            counts.append(count)
        if not chapters:
            continue
        seen.append(
            {
                **entity,
                "chapters": chapters,
                "counts": counts,
                "total": sum(counts),
                "last": chapters[-1],
            }
        )
    return seen


def ranked(entities):
    """Most present first, which is what `everyone` shows."""
    return sorted(entities, key=lambda e: (-len(e["chapters"]), -e["total"], e["name"]))


def of_kind(entities, kind):
    return [e for e in entities if e.get("kind") == kind]


def matching(entities, needle):
    """Accent- and case-insensitive, because most of the corpus is translated.

    A reader typing `natasha` is looking for Natásha, and a search that says no
    name matches is worse than no search at all.
    """
    import unicodedata

    def fold(s):
        return "".join(
            c for c in unicodedata.normalize("NFD", s.casefold()) if unicodedata.category(c) != "Mn"
        )

    if not needle.strip():
        return entities
    want = fold(needle.strip())
    return [e for e in entities if want in fold(e["name"])]


def cumulative_words(pace):
    """Running total, so words between two chapters is one subtraction."""
    running = [0]
    for row in pace or []:
        running.append(running[-1] + row["w"])
    return running


def away_a_while(entities, upto, pace, min_words=LOST_WORDS, factor=3):
    """Who has been gone unusually long *for them*, and long in reading time.

    Four conditions, and the first is the one that does most of the work. A
    name seen in fewer than four chapters, or used fewer than ten times, was
    never established -- it has not been forgotten, it is finished. Without
    that floor this flags 146 of the 378 names met by chapter 180 of War and
    Peace, which is the noise the whole view was rebuilt to remove.

    It cannot claim to predict forgetting. It measures an absence unusual for
    that person that is also long in reading time, and no reader has tested it.
    """
    running = cumulative_words(pace)
    out = []
    for entity in entities:
        seen, uses = entity["chapters"], entity["total"]
        if len(seen) < MIN_APPEARANCES or uses < MIN_USES:
            continue
        gaps = sorted(b - a for a, b in zip(seen, seen[1:], strict=False))
        typical = gaps[len(gaps) // 2]
        if not typical:
            continue
        last = seen[-1]
        gone = upto - last
        if gone < factor * typical:
            continue
        # No word counts means no floor to apply, and the relative test stands
        # on its own rather than the whole view silently going empty.
        if len(running) < 2:
            if gone < max(3, factor * typical):
                continue
            since = 0
        else:
            since = running[upto + 1] - running[last + 1]
            if since < min_words:
                continue
        out.append({**entity, "gone": gone, "since_words": since, "usual_gap": typical})
    return sorted(out, key=lambda e: -e["total"])


def alongside(model, name, chapter, limit=4):
    """Who else was in the room the last time the reader met somebody.

    The aggregate `often_with` answers a different question. When you have lost
    track of a person, the hook you need is the particular chapter, not the
    company they usually keep.
    """
    return [
        e["name"]
        for e in model["entities"]
        if e["name"] != name and e["first"] <= chapter and chapter in e["chapters"]
    ][:limit]


def often_with(model, name, upto, limit=3):
    """Who shares chapters with this one, strongest first.

    Read out of the co-occurrence already computed for the position rather than
    recounted here, so the cards and the map can never disagree about who is
    in the room with whom.
    """
    pairs = (model.get("assoc") or {}).get(str(upto)) or []
    beside = [(strength, b if a == name else a) for a, b, strength in pairs if name in (a, b)]
    beside.sort(reverse=True)
    return [other for _, other in beside[:limit]]


def neighbours(entities, name, limit=8):
    """Who actually shares chapters with one person, counted from the index.

    `often_with` reads the co-occurrence table the page ships, which is capped
    at the strongest forty pairs in the whole book so the file stays small
    enough to email. That is right for a summary line and far too thin for a
    focus: at chapter 180 of War and Peace it finds Pierre exactly two
    companions. This counts the shared chapters directly, so it is complete for
    the person asked about and costs one pass over the cast.
    """
    mine = next((e for e in entities if e["name"] == name), None)
    if mine is None:
        return []
    theirs = set(mine["chapters"])
    shared = []
    for entity in entities:
        if entity["name"] == name:
            continue
        together = len(theirs.intersection(entity["chapters"]))
        if together:
            shared.append((together, entity["name"]))
    shared.sort(reverse=True)
    return [(name, count) for count, name in shared[:limit]]
