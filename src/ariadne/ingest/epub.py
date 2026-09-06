import html
import os
import re
import zipfile
from xml.etree import ElementTree as ET

from ..ingest.chapters import BREAK_CLASS

OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "cnt": "urn:oasis:names:tc:opendocument:xmlns:container",
}


def strip_html(doc):
    """Text of one xhtml document, with scene breaks preserved as ---."""
    doc = re.sub(r"(?is)<(script|style).*?</\1>", " ", doc)
    doc = re.sub(r"(?i)<hr[^>]*>", "\n\n---\n\n", doc)
    doc = re.sub(
        r'(?is)<p[^>]*class="([^"]+)"[^>]*>\s*</p>',
        lambda m: "\n\n---\n\n" if any(BREAK_CLASS.match(c) for c in m.group(1).split()) else " ",
        doc,
    )
    doc = re.sub(r"(?i)</(p|div|h[1-6]|blockquote)>", "\n\n", doc)
    doc = re.sub(r"(?s)<[^>]+>", " ", doc)
    doc = html.unescape(doc)
    doc = re.sub(r"[ \t]+", " ", doc)
    return re.sub(r"\n{3,}", "\n\n", doc).strip()


def read_epub(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("META-INF/container.xml"))
    opf_path = root.find(".//cnt:rootfile", OPF_NS).get("full-path")
    base = os.path.dirname(opf_path)
    opf = ET.fromstring(z.read(opf_path))
    title_el = opf.find(".//dc:title", OPF_NS)
    title = title_el.text if title_el is not None else None
    ids = {i.get("id"): i.get("href") for i in opf.findall(".//opf:manifest/opf:item", OPF_NS)}
    names = set(z.namelist())
    docs = []
    for ref in opf.findall(".//opf:spine/opf:itemref", OPF_NS):
        href = ids.get(ref.get("idref"))
        if not href:
            continue
        p = os.path.normpath(os.path.join(base, href)) if base else href
        if p in names:
            docs.append(z.read(p).decode("utf-8", "ignore"))
    return title, docs


def epub_series(path):
    """Which series a book belongs to, and where in it, if the file says.

    Two conventions and neither is guaranteed: EPUB 3 records a collection with
    `belongs-to-collection` and a `group-position` refining it, and Calibre
    writes `calibre:series` with `calibre:series_index`. Most files carry
    neither -- 2 of 17 real epubs here have it.

    Worth reading anyway, because it is the thing a reader is least often told.
    Of nineteen series entries among the 2025 Goodreads Choice Award nominees,
    seven mention the series in their own synopsis; the other twelve leave a
    reader to work out from the cover that they have started in the middle.
    """
    if not path.lower().endswith(".epub"):
        return None
    try:
        z = zipfile.ZipFile(path)
        root = ET.fromstring(z.read("META-INF/container.xml"))
        opf = ET.fromstring(z.read(root.find(".//cnt:rootfile", OPF_NS).get("full-path")))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError, AttributeError):
        return None
    name = position = None
    refines = {}
    for m in opf.iter():
        if not m.tag.endswith("meta"):
            continue
        prop = (m.get("property") or "").strip()
        if prop == "belongs-to-collection" and (m.text or "").strip():
            name = m.text.strip()
            if m.get("id"):
                refines[m.get("id")] = True
        elif prop == "group-position" and (m.text or "").strip():
            position = m.text.strip()
        elif m.get("name") == "calibre:series" and m.get("content"):
            name = name or m.get("content").strip()
        elif m.get("name") == "calibre:series_index" and m.get("content"):
            position = position or m.get("content").strip()
    if not name:
        return None
    # Calibre writes 1.0 where a person would write 1.
    if position and position.endswith(".0"):
        position = position[:-2]
    return {"name": name, "position": position}
