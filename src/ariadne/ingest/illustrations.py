"""Pictures somebody drew, filed against the chapter they may be seen from.

Nothing here is generated and nothing is inferred. Ariadne does not decide what
a place looks like -- `model/ground.py` refuses to invent a position for Bald
Hills and this is the same refusal wearing a picture. What it decides is *when*
a picture already drawn may be shown, which is the one question it is built to
answer.

The folder sits beside the book, named like the rulings sidecar:

    the-book.epub
    the-book.epub.illustrations/
        plates.tsv
        plate01.png

`plates.tsv` is the whole contract, and it is a manifest rather than a filename
convention on purpose. `ch12-vael.png` is a guess dressed as a fact: it breaks
silently the day a chapter is inserted, and nothing would say so.

    file <TAB> from <TAB> subject <TAB> caption

`from` is the chapter the picture may first be seen from, counting from 1 the
way a reader does. **It is not the chapter the picture illustrates.** A drawing
of somebody at a place they have not reached yet is a spoiler filed under the
wrong number, and only the person who drew it knows the difference.

`subject` is a name from the cast, or empty. `caption` is what to say under it.

A book with no folder has no plates and that is silent -- most books have none.
A folder that is there and wrong is a refusal by name, because a manifest
nobody checks is a manifest that has already drifted.
"""

import os

from ..core.refusal import Refusal

MANIFEST = "plates.tsv"
SUFFIX = ".illustrations"

# What a viewer can be trusted to draw. A manifest naming anything else is a
# mistake worth reporting rather than a file to skip quietly.
KINDS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def illustrations_dir(book_path):
    """Where the pictures for this book would be, whether or not any are."""
    return os.path.abspath(book_path).rstrip(os.sep) + SUFFIX


def load_plates(book_path, chapters):
    """Every plate for this book, in the order they may be reached.

    `chapters` is the book's length, so a manifest pointing past the end is
    caught here rather than by a view drawing off the edge of its own axis.
    Returns [] when there is no folder; raises `Refusal` when there is one and
    it cannot be trusted.
    """
    folder = illustrations_dir(book_path)
    manifest = os.path.join(folder, MANIFEST)
    if not os.path.isfile(manifest):
        return []

    plates = []
    seen = set()
    with open(manifest, encoding="utf-8") as fh:
        for number, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            plates.append(_row(line, number, folder, chapters, seen))
    plates.sort(key=lambda p: (p["from"], p["file"]))
    return plates


def _row(line, number, folder, chapters, seen):
    """One manifest row, or a refusal naming the line that is wrong."""
    parts = line.split("\t")
    if len(parts) < 2:
        raise Refusal(
            "%s line %d: needs at least a file and a chapter, tab separated -- "
            "got %r. The columns are file, from, subject, caption." % (MANIFEST, number, line[:60])
        )
    name = parts[0].strip()
    where = parts[1].strip()
    subject = parts[2].strip() if len(parts) > 2 else ""
    caption = parts[3].strip() if len(parts) > 3 else ""

    if os.path.splitext(name)[1].lower() not in KINDS:
        raise Refusal(
            "%s line %d: %r is not a picture this can draw. Expected one of %s."
            % (MANIFEST, number, name, ", ".join(KINDS))
        )
    # A separator in the name would reach outside the folder the book owns.
    if os.sep in name or (os.altsep and os.altsep in name) or name.startswith("."):
        raise Refusal(
            "%s line %d: %r must be a plain filename inside the folder." % (MANIFEST, number, name)
        )
    path = os.path.join(folder, name)
    if not os.path.isfile(path):
        raise Refusal("%s line %d: no such picture -- %s" % (MANIFEST, number, name))
    if name in seen:
        raise Refusal(
            "%s line %d: %r is listed twice. A plate shown at two chapters is "
            "two decisions, and only one of them can be right." % (MANIFEST, number, name)
        )
    seen.add(name)

    try:
        chapter = int(where)
    except ValueError:
        raise Refusal(
            "%s line %d: %r is not a chapter number. Count from 1, the way a "
            "reader does." % (MANIFEST, number, where)
        ) from None
    if chapter < 1 or chapter > max(1, chapters):
        raise Refusal(
            "%s line %d: chapter %d is outside this book, which has %d."
            % (MANIFEST, number, chapter, chapters)
        )

    return {
        "file": name,
        "path": path,
        "from": chapter - 1,
        "subject": subject,
        "caption": caption,
    }
