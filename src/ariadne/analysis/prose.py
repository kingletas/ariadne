import re
from collections import Counter

from ..core.text import QUOTED

# ---------------------------------------------------------------------------
# Comparing two versions of the same book
# ---------------------------------------------------------------------------
#
# A revision track needs a different question answered than a reader does:
# not who is in this book, but what did the pass actually change. Word counts
# alone cannot say -- a consolidation that merges two chapters and rewrites a
# third looks the same as a rewrite that touched everything.
#
# So the map is built from content hashes rather than filenames. A chapter
# that moved keeps its hash, which is what distinguishes a renumbering from a
# rewrite, and it is the distinction that matters: The Atherion's R0001 merged
# eight corridor chapters into six, and every chapter after the merge shifted
# number while its text stayed byte-identical. Read by filename that looks
# like fifteen chapters silently holding the wrong text. Read by hash it is
# one deliberate consolidation.


def prose_shape(text):
    """Lexical diversity and sentence rhythm, the two measures a revision is
    usually trying not to disturb.

    MATTR over a moving window rather than a raw type-token ratio, because a
    long book always looks less diverse under TTR purely for being long.
    """
    words = [w.lower() for w in re.findall(r"[A-Za-z\u00c0-\u00ff'\u2019-]+", text)]
    if len(words) < 2000:
        return None
    win, step = 500, 250
    ratios = [len(set(words[i : i + win])) / win for i in range(0, len(words) - win, step)]
    sents = [
        len(re.findall(r"[A-Za-z\u00c0-\u00ff'\u2019-]+", s))
        for s in re.split(r"[.!?]+[\s\"\u201d']", text)
    ]
    sents = [s for s in sents if 1 <= s <= 200]
    if not ratios or len(sents) < 50:
        return None
    mean = sum(sents) / len(sents)
    var = sum((s - mean) ** 2 for s in sents) / len(sents)
    return {
        "mattr": sum(ratios) / len(ratios),
        "sent_mean": mean,
        "sent_cv": (var**0.5) / mean if mean else 0.0,
    }


def pace(chapters, presence, first):
    """Three counts per chapter, and deliberately no verdict on them.

    How much of the chapter is dialogue, how many people are on stage, and how
    many of them the reader is meeting for the first time. Readers abandon a
    book in the middle far more than at the start, and the usual reason is not
    knowing whether a slow patch ends -- a curve answers that and a label does
    not.

    Nothing here is scored. "Slow" is a reading judgement about a book somebody
    wrote on purpose, and three counts cannot make it.
    """
    rows = []
    for i, body in enumerate(chapters):
        words = len(body.split())
        spoken = sum(len(m.group(1).split()) for m in QUOTED.finditer(body))
        here = presence[i] if i < len(presence) else set()
        fresh = sum(1 for n in here if first.get(n) == i)
        rows.append(
            {
                "w": words,
                "d": round(100.0 * spoken / words, 1) if words else 0.0,
                "o": len(here),
                "f": fresh,
            }
        )
    return rows


def warning_map(rows, n_chapters, spoil=False):
    """Warnings keyed by the position at which each becomes visible.

    A warning for chapter N appears one chapter early -- that is the entire
    point, since a warning that arrives with the chapter is not a warning. It
    is keyed here rather than filtered in the page so that the page performs
    the same `key <= position` test every other view performs, and so this
    mapping can be tested directly.
    """
    out = {}
    for r in rows:
        at = int(r.get("at", 0))
        if not 0 <= at < n_chapters:
            continue
        reveal = 0 if spoil else max(0, at - 1)
        out.setdefault(str(reveal), []).append({"at": at, "text": r.get("text", "")})
    for key in out:
        out[key].sort(key=lambda x: x["at"])
    return out


NARRATION_I = ("I", "me", "my", "myself", "mine")


NARRATION_3 = ("he", "she", "him", "her", "his", "hers", "himself", "herself")


def narrative_person(chapters):
    """Whether the book is narrated in the first person, and how strongly.

    Dialogue is stripped first: "I" is normal inside speech in any novel, so
    counting it there measures nothing. What is left is narration, and there
    the split is wide -- measured over eighteen novels whose person is not in
    doubt, first-person books run 30-74% and third-person 1-16%, with nothing
    between 16% and 30%. Bleak House, half of which is Esther's first-person
    account, lands at 36% and is reported as mixed, which is right.

    It matters beyond being a nice fact: a first-person narrator is called "I"
    rather than by name, so every count of who dominates a chapter understates
    them. Jane Eyre's most-named person is Bessie. Naming this case is what
    lets the focus measure refuse it rather than answer confidently.
    """
    text = QUOTED.sub(" ", "\n".join(chapters))
    words = re.findall(r"[A-Za-z']+", text)
    if len(words) < 2000:
        return None
    first = sum(1 for w in words if w in NARRATION_I)
    third = sum(1 for w in words if w in NARRATION_3)
    if first + third < 200:
        return None
    share = first / (first + third)
    kind = "first" if share >= 0.45 else "mixed" if share >= 0.25 else "third"
    return {"share": share, "kind": kind, "third_pronouns": third}


def focus(counts, kinds, person, pronouns):
    """How much of the book one person holds, and how many hold the rest.

    Per chapter, whoever is named most; then the share of chapters belonging to
    the book's overall lead. Emma reaches 60% and Vanity Fair 12%, which is the
    difference between a book about somebody and a book about a set of people.

    Refused outright for first-person narration, where the counts cannot see
    the narrator at all, and refused again where the book carries its people by
    pronoun rather than by name.

    That second test is the same failure one degree milder, and it needed
    measuring rather than assuming. Take the pronouns in narration against the
    mentions of the most-named person: over twelve novels whose lead is not in
    doubt, every book below 14 named its lead correctly and every book above 15
    named the wrong one -- Bleak House answered Richard where the lead is
    Esther, Vanity Fair answered Amelia where it is Becky Sharp, and A Tale of
    Two Cities answered Miss Pross. Middlemarch sits at 14.3 and is wrong, so
    the gate lets one through rather than catching all three by also refusing
    two books it gets right.

    An unmerged alias blunts it further even when it answers, splitting one
    person across several names, and every split makes a book look wider than
    it is. So the share is reported as a floor.
    """
    if not person or person["kind"] != "third":
        return None
    people = {n for n, k in kinds.items() if k == "person"}
    if len(people) < 4 or len(counts) < 8:
        return None
    tally = Counter()
    owners = []
    for c in counts:
        here = {n: v for n, v in c.items() if n in people}
        tally.update(here)
        owners.append(max(here, key=here.get) if here else None)
    if not tally:
        return None
    lead, mentions = tally.most_common(1)[0]
    if pronouns and mentions and pronouns / mentions > 15:
        return {"refused": "carried by pronoun", "ratio": pronouns / mentions, "lead": None}
    owned = sum(1 for o in owners if o == lead)
    return {
        "lead": lead,
        "share": owned / len(owners),
        "ratio": (pronouns / mentions) if mentions else None,
        "owners": len({o for o in owners if o}),
    }


def chapter_spread(chapters, key):
    """How much this measure varies between chapters of one book.

    The noise floor. A revision delta smaller than the gap between two
    consecutive chapters of the same book has not moved anything.
    """
    vals = []
    for c in chapters:
        shape = prose_shape(c)
        if shape:
            vals.append(shape[key])
    if len(vals) < 4:
        return None
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    return var**0.5


def chapter_hashes(chapters):
    """One hash per chapter, over normalised text.

    Whitespace is collapsed so a reflow is not mistaken for a rewrite.
    """
    import hashlib

    out = []
    for body in chapters:
        norm = re.sub(r"\s+", " ", body).strip()
        out.append(hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12])
    return out


def compare_versions(a_chapters, b_chapters):
    """How the second version relates to the first, chapter by chapter."""
    ah, bh = chapter_hashes(a_chapters), chapter_hashes(b_chapters)
    where = {}
    for i, h in enumerate(ah):
        where.setdefault(h, i)
    rows, offsets = [], []
    for j, h in enumerate(bh):
        src = where.get(h)
        if src is None:
            rows.append((j, None, "rewritten"))
        elif src == j:
            rows.append((j, src, "unchanged"))
        else:
            rows.append((j, src, "moved"))
            offsets.append(src - j)
    # How many chapters the second version is short by. NOT the set of
    # originals whose hash is unaccounted for: a rewritten chapter matches
    # nothing by hash, so on a pass that rewrites every chapter that set is
    # the whole book, and reporting it as "absorbed" is false. The arithmetic
    # is the honest measure -- if the count did not shrink, nothing was merged.
    absorbed = max(0, len(ah) - len(bh))
    return rows, absorbed


def summarise_words(chapters):
    return sum(len(c.split()) for c in chapters)
