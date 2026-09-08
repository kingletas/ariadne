"""One axis, and the acceptance test for the whole redesign.

The defect this closes: four surfaces each drew their own chapter axis and
three of them sized it from the bookmark, so at chapter 180 of 365 the midpoint
of a card strip was chapter 90 while the midpoint of the scale above it was
chapter 182.

These tests import `axis` and nothing else in `app`. Every drawing surface
routes its geometry through it, so proving the module proves the alignment
without needing a display -- and `test_layering` proves the surfaces have no
other way to compute a position.
"""

import ast
import re
from pathlib import Path

from ariadne.app import axis

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "ariadne" / "app"

# The surfaces that share the axis. Map draws associations rather than a
# timeline, so it is deliberately not one of them.
REGISTERED = ("presence.py", "ground.py", "pace.py", "bookmark.py")


def test_a_position_is_a_function_of_the_book_not_the_bookmark():
    """The substitution that is the whole redesign."""
    width, chapters = 1000.0, 365
    assert axis.x_for(0, width, chapters) < axis.x_for(180, width, chapters)
    # Halfway through the book is halfway across the surface, whatever has been
    # read. Nothing in the signature can express the bookmark.
    middle = axis.x_for(182, width, chapters)
    assert abs(middle - width / 2) < axis.slot(width, chapters)


def test_the_plumb_line_crosses_the_same_chapter_on_every_surface():
    """The acceptance test.

    Every registered surface spans the same box, so a vertical line through the
    axis knob has to land on the same chapter on all of them. Checked at every
    chapter of a long book rather than at a convenient one.
    """
    width, chapters = 1212.0, 365
    for chapter in range(chapters):
        x = axis.x_for(chapter, width, chapters)
        assert axis.chapter_at(x, width, chapters) == chapter, (
            f"chapter {chapter} draws at {x:.2f}, which reads back as "
            f"{axis.chapter_at(x, width, chapters)}"
        )


def test_a_click_anywhere_lands_inside_the_book():
    """Including the edges, which is where an off-by-one lives."""
    for chapters in (1, 2, 37, 365, 1000):
        for width in (10.0, 240.0, 1212.0):
            for x in (-50.0, 0.0, width / 3, width - 0.01, width, width + 50.0):
                assert 0 <= axis.chapter_at(x, width, chapters) <= chapters - 1


def test_a_book_of_one_chapter_does_not_divide_by_zero():
    assert axis.chapter_at(0.0, 100.0, 0) == 0
    assert axis.x_for(0, 100.0, 0) == 50.0
    assert axis.chapter_at(10.0, 0.0, 10) == 0


# Where a span turns into pixels.
GEOMETRY = ("_draw", "_clicked", "_chapter_at", "_to_x")


def _geometry(name):
    """Every method in a registered surface that turns a chapter into an x."""
    body = (APP / name).read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in GEOMETRY:
            yield node, ast.get_source_segment(body, node) or ""


def _reads_upto(tree):
    """`self._upto` nodes, and the ones that only compare or slice with it."""
    every, allowed = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "_upto":
            every.add(id(node))
        # Comparing against the bookmark, or clipping a list at it, is how a
        # view refuses to show the future. Neither one measures anything.
        if isinstance(node, ast.Compare | ast.Slice):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Attribute) and inner.attr == "_upto":
                    allowed.add(id(inner))
    return every, allowed


def test_no_surface_measures_from_the_bookmark():
    """The bookmark may say what to hide. It may never say how wide a chapter is.

    A surface that sizes itself from `upto` draws a scale that gets shorter as
    the reader advances, which is what put four axes on one screen. Clipping a
    list at the bookmark is the opposite thing and stays.
    """
    for name in REGISTERED:
        for node, _source in _geometry(name):
            every, allowed = _reads_upto(node)
            assert every <= allowed, (
                f"{name}:{node.name} measures something from the bookmark; ask axis"
            )


def test_every_registered_surface_asks_the_axis():
    """The positive half: geometry goes through one module or it is not shared."""
    for name in REGISTERED:
        methods = list(_geometry(name))
        assert methods, f"{name} declares none of {GEOMETRY}"
        for node, source in methods:
            # Directly, or by handing the question to the method beside it that
            # does -- `pace._clicked` asks its own `_chapter_at`.
            delegates = any(m in source for m in GEOMETRY if m != node.name)
            assert "axis." in source or delegates, (
                f"{name}:{node.name} computes an x without the axis"
            )


def test_no_drawn_colour_is_a_literal():
    """Every drawn colour comes from the palette, or dark mode misses it.

    `presence.py` hard-coded its track and its ticks and was never told which
    mode it was in, so the default view drew light-mode paper colours at night.
    """
    literal = re.compile(r"set_source_rgba?\(\s*[\d.]")
    for path in sorted(APP.glob("*.py")):
        body = path.read_text(encoding="utf-8")
        assert not literal.search(body), (
            f"{path.name} draws a literal colour; it cannot follow the theme"
        )


def test_no_retired_colour_survives():
    """The old palette, by value. A stray hex is a token that stopped being one."""
    retired = re.compile(r"#(F7F3EA|2F6F68|B8832F|282621|EFE9DC|DDD6C8)", re.IGNORECASE)
    for path in sorted((ROOT / "src" / "ariadne" / "app").rglob("*.py")):
        found = retired.findall(path.read_text(encoding="utf-8"))
        assert not found, f"{path.name} still carries {found}"
