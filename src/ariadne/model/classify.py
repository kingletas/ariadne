import bisect
import re
from collections import Counter

from ..core.text import QUOTED
from ..model.names import RUN, TITLES, normalise

# Person, place, or neither. Two countable signals, and they separate cleanly:
# a place follows a preposition and is never the subject of a speech verb, so
# across seventeen names whose kind is not in doubt every place scored a speech
# ratio of 0.001 or less and a preposition ratio above 0.2, while every person
# scored the reverse. The Pequod -- a ship -- scores zero on both and is
# therefore left unclassified, which is the right answer rather than a miss.
PREP_BEFORE = re.compile(
    r"\b(?:in|at|to|from|near|toward|towards|into|through|across|beyond"
    r"|outside|inside|around|past|via|for|of)\s+$",
    re.I,
)


SPEECH_AFTER = re.compile(
    r"^\s*(?:said|says|asked|replied|answered|cried|whispered|shouted"
    r"|murmured|thought|told|continued|added|muttered|exclaimed)\b",
    re.I,
)


SPEECH_BEFORE = re.compile(
    # `to` is deliberately absent. "said to X" would be caught by it, and so
    # would every "to Moscow" in the book -- which classified a city as a
    # person on the first run.
    r"\b(?:said|says|asked|replied|answered|cried|whispered|shouted"
    r"|murmured|told)\s+$",
    re.I,
)


def classify(text, names, narration=None):
    """A kind per name, abstaining wherever the signals do not agree.

    One pass over the text rather than one pass per name: scanning the whole
    book once for each of 562 names took the better part of a minute on War
    and Peace, against a third of a second for everything else the tool does.

    THE NARRATOR OF A FIRST-PERSON BOOK IS THE CASE THE SPEECH TEST CANNOT SEE.
    Nobody writes "Pip said" when Pip is telling the story, so Pip, Jane and
    Huck all score exactly zero on speech and near zero on prepositions, and
    fall through to unknown -- the protagonist, unclassified, at the top of the
    opening screen.

    What they do have is being spoken TO. 94% of the uses of Pip's name are
    inside quotation marks, 93% of Jane's, 90% of Huck's, because the only time
    a first-person narrator is named is when somebody addresses them.

    That signal alone is not a person test and was measured failing as one: at
    0.85 across 45 books it also promotes England, France and Spain, and every
    Highness, Majesty and Grace in a costume drama. It works only inside a book
    already known to be narrated in the first person, which `narrative_person`
    decides and gets right 18 times out of 18.

    Scored over eighteen novels the narrow rule finds Pip, Jane, Huck, Esther
    Summerson and one of Dracula's journal-keepers, misses Ishmael -- named
    nineteen times in all, and only 16% of those in dialogue -- and fires on
    none of eleven third-person books. It can only ever turn unknown into
    person; nothing it does takes a classification away.
    """
    quoted = [(m.start(), m.end()) for m in QUOTED.finditer(text)]
    q_starts = [a for a, _ in quoted]
    q_ends = [b for _, b in quoted]

    def spoken_at(pos):
        i = bisect.bisect_right(q_starts, pos) - 1
        return i >= 0 and pos < q_ends[i]

    prep = Counter()
    speech = Counter()
    total = Counter()
    vocative = Counter()
    for m in RUN.finditer(text):
        run = normalise(m.group(1))
        name = run if run in names else run.split(" ")[0]
        if name not in names:
            continue
        total[name] += 1
        before = text[max(0, m.start() - 30) : m.start()]
        after = text[m.end() : m.end() + 30]
        if PREP_BEFORE.search(before):
            prep[name] += 1
        # Both orders count. Russian and French translation puts the verb
        # first far more often than English does, and checking only
        # "Natasha said" leaves "said Natasha" invisible -- which left
        # Napoleon, Kutuzov and Natasha unclassified on the first run.
        if SPEECH_AFTER.match(after) or SPEECH_BEFORE.search(before):
            speech[name] += 1
        if spoken_at(m.start()):
            vocative[name] += 1
    out = {}
    for name in names:
        # An honorific settles it outright. "Count Bezukhov" is addressed and
        # travelled to, so the preposition test called him a place on the
        # first run; no title in the list has ever introduced one.
        parts = name.split()
        if len(parts) > 1 and parts[0] in TITLES:
            out[name] = "person"
            continue
        n = total[name]
        if not n:
            out[name] = "unknown"
            continue
        if speech[name] / n >= 0.02:
            out[name] = "person"
        elif prep[name] / n >= 0.20:
            out[name] = "place"
        else:
            out[name] = "unknown"

    if narration in ("first", "mixed"):
        narrator, uses = None, 0
        for name, n in total.items():
            if n < 15 or out.get(name) != "unknown":
                continue
            if name.split()[0] in TITLES:
                continue
            if (
                vocative[name] / n >= 0.85
                and speech[name] / n <= 0.01
                and prep[name] / n <= 0.10
                and n > uses
            ):
                narrator, uses = name, n
        if narrator:
            out[narrator] = "person"
    return out
