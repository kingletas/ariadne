import zipfile
from xml.etree import ElementTree as ET

from ..core.refusal import Refusal


def read_docx(path):
    """Text of a .docx, one paragraph per line, headings kept as their own line.

    A docx is a zip with the document in word/document.xml. Paragraphs are
    <w:p> and runs of text are <w:t>; a paragraph styled as a heading carries
    <w:pStyle w:val="Heading1"> or similar, which is a far better chapter
    signal than any typographic guess and is used when it is present.
    """
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    lines, headings = [], []
    for para in root.iter(W + "p"):
        text = "".join(node.text or "" for node in para.iter(W + "t")).strip()
        if not text:
            continue
        style = para.find("%spPr/%spStyle" % (W, W))
        val = style.get(W + "val", "") if style is not None else ""
        if val.lower().startswith("heading"):
            headings.append(len(lines))
        lines.append(text)
    if not lines:
        raise Refusal("word/document.xml holds no paragraph text")
    if len(headings) >= 3:
        chapters = []
        for i, start in enumerate(headings):
            end = headings[i + 1] if i + 1 < len(headings) else len(lines)
            chapters.append("\n\n".join(lines[start:end]))
        return chapters, "docx heading styles"
    return ["\n\n".join(lines)], "docx, no heading styles"
