"""Where the book has been, which is a map of the book and not of the world.

There are no coordinates here and there will not be. Ariadne has no gazetteer,
makes no network request, and half the places that matter in a novel are not on
any map -- Bald Hills, Otrádnoe, Thrushcross Grange, Boguchárovo. Placing those
would mean inventing them, and placing Ithaca or Troy would mean choosing which
Ithaca. So what is drawn is the shape of the book's movement through its own
settings: which ones, when, and how long it stays.

WHY A SETTING IS PROPOSED AND NEVER ASSERTED
The place classifier is not accurate enough to map. It calls Death, Man and
Right places in Moby-Dick, Apollo and Agamemnon places in the Odyssey, and
Hareton Earnshaw a place in Wuthering Heights. Ranking instead by how many
chapters a place is the most-named place *in* -- a setting is one the chapter
keeps returning to, not one mentioned in passing -- and cutting at three
chapters held, a hand-check over six books put 21 of 26 right. Four in five is
a good proposal and a bad map.

So the reader rules, exactly as they do on whether two names are one person.
`Moby Dick` holding nine chapters is obvious to anybody who has read forty of
them, and one click removes it forever.
"""

# A place named once in a chapter is a mention; twice is the chapter being
# about somewhere.
MENTIONS_IN_CHAPTER = 2

# Below this the ranking is mostly people and objects the classifier misread.
CHAPTERS_HELD = 3


def settings(model, upto, floor=MENTIONS_IN_CHAPTER):
    """Candidate settings, most chapters held first.

    Returns `(name, [chapters it holds])`. A chapter is held by whichever place
    is named most inside it, so a chapter has one setting or none.
    """
    per_chapter = {}
    for entity in model["entities"]:
        if entity.get("kind") != "place" or entity["first"] > upto:
            continue
        for chapter, count in zip(entity["chapters"], entity["counts"], strict=False):
            if chapter <= upto and count >= floor:
                per_chapter.setdefault(chapter, []).append((count, entity["name"]))

    held = {}
    for chapter, rows in per_chapter.items():
        held.setdefault(max(rows)[1], []).append(chapter)
    return sorted(
        ((name, sorted(chapters)) for name, chapters in held.items()),
        key=lambda row: (-len(row[1]), row[1][0]),
    )


def proposed(model, upto, minimum=CHAPTERS_HELD):
    """The ones worth putting to the reader, rather than every candidate."""
    return [
        (name, chapters) for name, chapters in settings(model, upto) if len(chapters) >= minimum
    ]


def scope(model, upto, confirmed=None):
    """How much ground the book has covered, and how concentrated it is.

    `settled` is the share of chapters read that have a setting at all. A low
    one is not a defect: a book can happen in a room, and Moby-Dick spends long
    stretches on cetology rather than anywhere.
    """
    rows = [
        (name, chapters)
        for name, chapters in settings(model, upto)
        if confirmed is None or name in confirmed
    ]
    with_setting = sum(len(chapters) for _, chapters in rows)
    read = upto + 1
    biggest = len(rows[0][1]) if rows else 0
    return {
        "places": len(rows),
        "chapters_placed": with_setting,
        "settled": with_setting / read if read else 0.0,
        "concentration": biggest / with_setting if with_setting else 0.0,
        "widest": rows[0][0] if rows else None,
    }


def moves(model, upto, confirmed=None):
    """The order the book visits its settings, with each stay's length.

    Consecutive chapters in one place are one stay. Returning later is a second
    stay, because a reader who goes back to Moscow has gone back to Moscow.
    """
    rows = settings(model, upto)
    where = {}
    for name, chapters in rows:
        if confirmed is not None and name not in confirmed:
            continue
        for chapter in chapters:
            where[chapter] = name

    journey, current, start = [], None, 0
    for chapter in range(upto + 1):
        here = where.get(chapter)
        if here == current:
            continue
        if current is not None:
            journey.append({"place": current, "from": start, "to": chapter - 1})
        current, start = here, chapter
    if current is not None:
        journey.append({"place": current, "from": start, "to": upto})
    return journey
