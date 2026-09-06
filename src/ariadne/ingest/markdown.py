import os
import re

from ..core.refusal import Refusal


def read_markdown_dir(path):
    """A folder of Markdown chapter files, one file per chapter.

    This is the shape a manuscript takes here: `Chapters/` inside a project,
    each file carrying YAML frontmatter and sometimes its own `# Title`
    heading. Both are stripped -- a heading is structure, not prose, and
    leaving it in makes every chapter title a candidate proper noun.
    """
    root = path
    if os.path.isdir(os.path.join(path, "Chapters")):
        root = os.path.join(path, "Chapters")
    files = sorted(f for f in os.listdir(root) if f.endswith(".md"))
    if not files:
        raise Refusal("no .md files in %s" % root)
    out = []
    for f in files:
        body = open(os.path.join(root, f), encoding="utf-8").read()
        body = re.sub(r"\A---.*?^---\s*$", "", body, flags=re.S | re.M)
        body = re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
        if body.strip():
            out.append(body.strip())
    title = os.path.basename(os.path.abspath(path).rstrip("/"))
    if title == "Chapters":
        title = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return title, out
