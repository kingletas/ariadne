"""What the split must not have changed.

The books these pages were built from are not on disk any more, so the pages
are the baseline: each one carries the model it was rendered from, and the
renderer must still turn that model back into that exact file. Ingest gets
purpose-built fixtures instead, recorded by `tests/golden/snapshot_ingest.py`.
"""

import hashlib
import json
from pathlib import Path

import pytest

from ariadne.core.refusal import Refusal
from ariadne.ingest.book import load
from ariadne.ingest.quotes import quote_convention
from ariadne.model.build import build_model
from ariadne.render.page import render_page

GOLDEN = Path(__file__).resolve().parent / "golden"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"


def pages():
    for line in (GOLDEN / "pages.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        book, digest, size = line.split("\t")
        yield book, digest, int(size)


def ingest_rows():
    for line in (GOLDEN / "ingest.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        yield tuple(line.split("\t"))


@pytest.mark.parametrize("book,digest,size", list(pages()), ids=lambda v: str(v)[:24])
def test_the_renderer_reproduces_the_page(book, digest, size):
    model = json.loads((GOLDEN / "model" / f"{book}.json").read_text(encoding="utf-8"))
    page = render_page(model)
    assert len(page) == size, f"{book}: page is {len(page)} bytes, was {size}"
    assert hashlib.sha256(page.encode()).hexdigest() == digest, (
        f"{book}: the renderer no longer produces the recorded page"
    )


@pytest.mark.parametrize("row", list(ingest_rows()), ids=lambda r: r[0])
def test_ingest_still_reads_the_fixture_the_same_way(row):
    name, segmentation, chapters, quotes, digest = row
    path = FIXTURES / name
    path = path if path.is_dir() else next(FIXTURES.glob(f"{name}.*"))

    if segmentation == "REFUSAL":
        with pytest.raises(Refusal) as why:
            load(str(path))
        assert str(why.value).startswith(quotes[:40])
        return

    _, convention, read = load(str(path))
    assert convention == segmentation
    assert len(read) == int(chapters)
    try:
        assert quote_convention("\n".join(read)) == quotes
    except Refusal:
        assert quotes == "refused"
    assert hashlib.sha256("\x00".join(read).encode()).hexdigest() == digest
    build_model(read, min_uses=3)
