"""Pictures are read, never invented, and a manifest that is wrong says so.

The folder is the only content Ariadne takes from beside the book other than
the reader's own rulings, and it is the most spoiling thing it can show. So
every way the manifest can be wrong is a named refusal rather than a skipped
line: a plate quietly dropped is a picture the author meant a reader to see.
"""

import pytest

from ariadne.core.refusal import Refusal
from ariadne.ingest.illustrations import illustrations_dir, load_plates

CHAPTERS = 40


def book_with(tmp_path, manifest, files=("plate01.png",)):
    """A book, its illustrations folder, and whatever pictures were asked for."""
    book = tmp_path / "book.txt"
    book.write_text("a book", encoding="utf-8")
    folder = tmp_path / "book.txt.illustrations"
    folder.mkdir()
    for name in files:
        (folder / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    if manifest is not None:
        (folder / "plates.tsv").write_text(manifest, encoding="utf-8")
    return book


def test_the_folder_sits_beside_the_book_like_the_rulings_do(tmp_path):
    assert illustrations_dir(tmp_path / "a.epub").endswith("a.epub.illustrations")


def test_a_book_with_no_folder_has_no_plates_and_says_nothing(tmp_path):
    book = tmp_path / "book.txt"
    book.write_text("a book", encoding="utf-8")
    assert load_plates(book, CHAPTERS) == []


def test_a_folder_with_no_manifest_is_not_an_error(tmp_path):
    """Somebody dropping images in is not a claim about which chapter they are."""
    book = book_with(tmp_path, None)
    assert load_plates(book, CHAPTERS) == []


def test_a_plate_carries_the_chapter_it_may_be_seen_from(tmp_path):
    book = book_with(tmp_path, "plate01.png\t7\tPierre\tPierre at the duel\n")
    (plate,) = load_plates(book, CHAPTERS)
    # Stated from 1 the way a reader counts, held from 0 the way the axis does.
    assert plate["from"] == 6
    assert plate["subject"] == "Pierre"
    assert plate["caption"] == "Pierre at the duel"


def test_plates_come_back_in_the_order_they_are_reached(tmp_path):
    book = book_with(
        tmp_path,
        "plate03.png\t30\t\t\nplate01.png\t2\t\t\nplate02.png\t11\t\t\n",
        files=("plate01.png", "plate02.png", "plate03.png"),
    )
    assert [p["from"] for p in load_plates(book, CHAPTERS)] == [1, 10, 29]


def test_comments_and_blank_lines_are_not_rows(tmp_path):
    book = book_with(tmp_path, "# file\tfrom\n\nplate01.png\t3\t\t\n\n")
    assert len(load_plates(book, CHAPTERS)) == 1


@pytest.mark.parametrize(
    ("manifest", "says"),
    [
        ("plate01.png\n", "tab separated"),
        ("plate01.png\tlater\t\t\n", "not a chapter number"),
        ("plate01.png\t0\t\t\n", "outside this book"),
        ("plate01.png\t41\t\t\n", "outside this book"),
        ("missing.png\t3\t\t\n", "no such picture"),
        ("plate01.txt\t3\t\t\n", "not a picture"),
        ("plate01.png\t3\t\t\nplate01.png\t9\t\t\n", "listed twice"),
    ],
)
def test_every_way_the_manifest_can_be_wrong_is_a_named_refusal(tmp_path, manifest, says):
    book = book_with(tmp_path, manifest, files=("plate01.png", "plate01.txt"))
    with pytest.raises(Refusal) as why:
        load_plates(book, CHAPTERS)
    assert says in str(why.value)


def test_a_manifest_cannot_reach_outside_the_folder(tmp_path):
    """The manifest is data from beside the book, so it is not trusted with a path."""
    book = book_with(tmp_path, "../../secret.png\t3\t\t\n")
    with pytest.raises(Refusal) as why:
        load_plates(book, CHAPTERS)
    assert "plain filename" in str(why.value)


def test_the_shareable_page_never_carries_them():
    """The page holds names, counts and chapter numbers and no book content.

    Embedding somebody's artwork in a file made to be sent to a friend is a
    redistribution of it, so the page does not read this key. Asserted rather
    than trusted, because the model carries it and nothing else stops `render`.
    """
    from pathlib import Path

    page = Path(__file__).resolve().parents[1] / "src" / "ariadne" / "render" / "page.py"
    assert "plates" not in page.read_text(encoding="utf-8")
