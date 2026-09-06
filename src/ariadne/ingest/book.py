import os
import re

from ..core.refusal import Refusal
from ..ingest.chapters import drop_toc, split_text
from ..ingest.docx import read_docx
from ..ingest.epub import read_epub, strip_html
from ..ingest.gutenberg import GUT_END, GUT_START
from ..ingest.markdown import read_markdown_dir
from ..ingest.plays import ACT_SCENE, looks_like_a_play


def load(path, title_override=None):
    """A book as (title, convention, [chapter text]). Refuses rather than guesses."""
    if os.path.isdir(path):
        title, chapters = read_markdown_dir(path)
        convention = "one Markdown file per chapter"
        if len(chapters) < 3:
            raise Refusal("only %d chapter file(s) with content in %s" % (len(chapters), path))
    elif path.lower().endswith(".docx"):
        chapters, convention = read_docx(path)
        title = None
        if len(chapters) < 3:
            raise Refusal(
                "found %d section(s). A .docx is split on Heading styles; this "
                "one has fewer than three, so there is nothing to segment on." % len(chapters)
            )
    elif path.lower().endswith(".epub"):
        title, docs = read_epub(path)
        chapters = [t for t in (strip_html(d) for d in docs) if len(t.split()) >= 600]
        convention = "epub spine (>= 600 words)"
        if len(chapters) < 3:
            raise Refusal(
                "only %d spine document(s) hold 600+ words. This may be a short "
                "work, a picture book, or an epub whose chapters are one file." % len(chapters)
            )
    else:
        raw = open(path, encoding="utf-8", errors="ignore").read()
        m = GUT_START.search(raw)
        if m:
            raw = raw[m.end() :]
        m = GUT_END.search(raw)
        if m:
            raw = raw[: m.start()]
        # Gutenberg puts Title:/Author: in the header, above the START marker
        # that has already been cut. Look in what preceded it.
        title = None
        head = open(path, encoding="utf-8", errors="ignore").read(4000)
        mt = re.search(r"^Title:\s*(.+)$", head, re.M)
        ma = re.search(r"^Author:\s*(.+)$", head, re.M)
        if mt:
            title = mt.group(1).strip()
            if ma:
                title += " — " + ma.group(1).strip()
        if looks_like_a_play(raw):
            # Same table-of-contents problem as prose: a play lists its scenes
            # in the front matter using the same words it divides them with.
            marks = drop_toc(raw, list(ACT_SCENE.finditer(raw)))
            chapters = [
                raw[m.start() : (marks[i + 1].start() if i + 1 < len(marks) else len(raw))].strip()
                for i, m in enumerate(marks)
            ]
            convention = "play: act and scene divisions"
        else:
            convention, chapters = split_text(raw)
        if len(chapters) < 3:
            raise Refusal("only %d chapter(s) found with %s." % (len(chapters), convention))
    return (
        title_override or title or os.path.splitext(os.path.basename(path))[0],
        convention,
        chapters,
    )
