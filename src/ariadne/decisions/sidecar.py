import contextlib
import json
import os
import tempfile
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Reader decisions -- the sidecar
# ---------------------------------------------------------------------------
#
# Everything the reader decides lives in one JSON file beside the book, in a
# shape a person can read and edit. Deleting ariadne leaves it intact, which is
# the whole of the portability requirement.
#
# WHY LINKS ARE SUGGESTED AND NEVER ASSERTED
# Two mechanical signals for "these two names are one person" were tested over
# six novels and both failed. Adjacency finds true aliases 8.9% of the time
# against 79.5% for the two halves of one name. Co-occurrence shape is worse
# than useless: an alias pair shares chapters BY CONSTRUCTION, so at chapter
# granularity aliases score HIGHER on co-occurrence than unrelated characters
# do. Nothing countable separates them.
#
# So ariadne proposes only what it can prove -- one name contained in another --
# and every other link comes from the reader. In some books the identity is the
# plot, which is the second reason never to assert one.


def sidecar_path(book_path):
    base = os.path.abspath(book_path).rstrip(os.sep)
    return base + ".ariadne.json"


def load_decisions(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("version", 1)
    d.setdefault("links", [])  # [{"keep": str, "also": str, "state": ...}]
    d.setdefault("hidden", [])
    d.setdefault("renamed", {})
    d.setdefault("position", 0)
    d.setdefault("glosses", {})  # name -> {"at": chapter index, "text": str}
    d.setdefault("relations", {})  # name -> [{"at": chapter index, "text": str}]
    d.setdefault("warnings", [])  # [{"at": chapter index, "text": str}]
    d.setdefault("settings", {})  # place name -> True kept, False struck
    return d


def save_decisions(path, d):
    """Written beside the target and renamed over it.

    A crash partway through a plain write leaves a truncated file, and this one
    holds every ruling the reader has made about the book. `os.replace` is
    atomic on the same filesystem, so the sidecar is either the old one or the
    new one and never half of each.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handle, temporary = tempfile.mkstemp(dir=directory, prefix=".ariadne-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    except BaseException:
        # A failed save must not also delete the reader's decisions.
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def containment_links(names):
    """The only link ariadne proposes on its own.

    One name wholly contains another as whole words -- `Prince Andrew` inside
    `Prince Andrew Bolkonski`, `Sancho` inside `Sancho Panza`. Measured at
    79.5% on the two halves of a single name, and it cannot fire on two
    unrelated people because it is a containment test rather than a guess.
    """
    out = []
    ordered = sorted(names, key=len, reverse=True)
    for long in ordered:
        toks = long.split()
        if len(toks) < 2:
            continue
        for short in names:
            if short == long or " " in short and short not in long:
                continue
            if short in toks or (" " in short and (" " + short + " ") in (" " + long + " ")):
                out.append((long, short))
    return out


def apply_decisions(entities, decisions):
    """Fold accepted links, drop hidden entities, apply renames.

    A rejected or merely proposed link changes nothing: an unaccepted
    suggestion must be invisible, so the reader is never shown a merge they
    did not make.
    """
    accepted = {}
    for link in decisions.get("links", []):
        if link.get("state") == "accepted":
            accepted[link["also"]] = link["keep"]
    hidden = set(decisions.get("hidden", []))
    renamed = decisions.get("renamed", {})

    merged = OrderedDict()
    for e in entities:
        name = accepted.get(e["name"], e["name"])
        if name in hidden or e["name"] in hidden:
            continue
        name = renamed.get(name, name)
        if name not in merged:
            merged[name] = {
                "name": name,
                "first": e["first"],
                "chapters": list(e["chapters"]),
                "counts": list(e["counts"]),
                "total": e["total"],
                "kind": e.get("kind", "unknown"),
                "longest_gap": e.get("longest_gap", 0),
            }
            continue
        m = merged[name]
        m["first"] = min(m["first"], e["first"])
        m["total"] += e["total"]
        per = dict(zip(m["chapters"], m["counts"], strict=True))
        for c, n in zip(e["chapters"], e["counts"], strict=True):
            per[c] = per.get(c, 0) + n
        m["chapters"] = sorted(per)
        m["counts"] = [per[c] for c in m["chapters"]]
        if e.get("kind", "unknown") != "unknown" and m.get("kind") == "unknown":
            m["kind"] = e["kind"]
        chs = m["chapters"]
        gaps = [b - a - 1 for a, b in zip(chs, chs[1:], strict=False)] if len(chs) > 1 else []
        m["longest_gap"] = max(gaps) if gaps else 0
    return sorted(merged.values(), key=lambda e: (e["first"], e["name"]))
