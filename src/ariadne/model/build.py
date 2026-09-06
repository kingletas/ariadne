import re
from collections import Counter

from ..model.names import RUN, candidates, normalise

CHAPTER_HEAD = re.compile(
    r"^(?:\s*(?:chapter|book|part|canto|stave|volume)\b[^\n]{0,120}\n+)+", re.I
)


def strip_headings(chapters):
    """Chapter text with its own heading lines taken off the front.

    A heading is not prose and its words are not names, but split_text keeps it
    inside the chapter it opens, so every capitalised word in a chapter title
    reached the name detector. On a web-serial scrape that repeats the title
    inside the body, that put whole title phrases in the cast list as if they
    were characters -- 18 of 110 entries on one book, 9 of them multi-word.

    The loop matters: a scrape prints the title, then the title again, then the
    prose, so taking only the first heading off leaves the second.

    Measured over eight normal novels this costs nothing -- seven unchanged,
    Moby-Dick down two, and no real name lost from a hand-checked list.
    """
    out = []
    for c in chapters:
        head = 0
        while True:
            m = CHAPTER_HEAD.match(c[head:])
            if not m or not m.group(0).strip():
                break
            head += m.end()
        out.append(c[head:] if head < len(c) else c)
    return out


def build_model(chapters, min_uses):
    """Per-chapter presence and first appearance. Everything downstream is a
    function of these two, which is what makes the spoiler rule structural."""
    bodies = strip_headings(chapters)
    whole = "\n".join(bodies)
    names = candidates(whole, min_uses)
    # Longest first, so "Prince Andrew" claims the span before "Andrew" does.
    ordered = sorted(names, key=len, reverse=True)
    presence, counts = [], []
    for body in bodies:
        here, cnt = set(), Counter()
        for m in RUN.finditer(body):
            g = normalise(m.group(1))
            if g in names:
                here.add(g)
                cnt[g] += 1
                continue
            for cand in ordered:  # a longer name inside the run
                if g.startswith(cand + " ") or g == cand:
                    here.add(cand)
                    cnt[cand] += 1
                    break
            else:
                head = g.split(" ")[0]
                if head in names:
                    here.add(head)
                    cnt[head] += 1
        presence.append(here)
        counts.append(cnt)
    first = {}
    for i, here in enumerate(presence):
        for n in here:
            first.setdefault(n, i)
    return presence, counts, first


def cooccurrence(presence, upto):
    """Who shares a chapter with whom, over chapters 0..upto only."""
    pair = Counter()
    solo = Counter()
    for here in presence[: upto + 1]:
        hs = sorted(here)
        for n in hs:
            solo[n] += 1
        for i, a in enumerate(hs):
            for b in hs[i + 1 :]:
                pair[(a, b)] += 1
    return pair, solo


def model_json(title, convention, quotes, presence, counts, first, kinds=None):
    n = len(presence)
    kinds = kinds or {}
    entities = []
    # Sorted by name as well as by first chapter. Ties are the normal case --
    # 71 of Crime and Punishment's 80 names share a first chapter -- and with
    # only `first` to sort on they broke on set iteration order, which Python
    # randomises per process. Three identical runs produced three different
    # files, so every rebuild churned the whole page and no diff could tell a
    # real change from the shuffle.
    for name, f in sorted(first.items(), key=lambda kv: (kv[1], kv[0])):
        chs = [i for i, here in enumerate(presence) if name in here]
        gaps = [b - a - 1 for a, b in zip(chs, chs[1:], strict=False)] if len(chs) > 1 else []
        entities.append(
            {
                "name": name,
                "first": f,
                "chapters": chs,
                "counts": [counts[i].get(name, 0) for i in chs],
                "total": sum(counts[i].get(name, 0) for i in chs),
                "kind": kinds.get(name, "unknown"),
                "longest_gap": max(gaps) if gaps else 0,
            }
        )
    assoc = {}
    for upto in range(n):
        pair, solo = cooccurrence(presence, upto)
        top = []
        for (a, b), c in pair.most_common(400):
            j = c / (solo[a] + solo[b] - c)
            top.append((a, b, round(j, 3)))
        assoc[upto] = sorted(top, key=lambda r: -r[2])[:60]
    return {
        "title": title,
        "chapters": n,
        "convention": convention,
        "quotes": quotes,
        "entities": entities,
        "assoc": assoc,
    }
