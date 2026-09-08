"""The pictures, and where in the book they sit.

Two things, and the second is the one that makes it feel like reliving rather
than browsing. `PlateBand` draws a mark per picture on the shared axis, so the
illustrations are a chapter-indexed thing like everything else and a reader can
see at a glance where the book is illustrated and where it is bare. `PlatesView`
shows the ones they have reached, newest last, in the order the book gets to
them.

Nothing past the bookmark exists here, the same way it does not exist anywhere
else: the list is clipped before it arrives and the band draws no mark beyond
it. A picture is the most spoiling thing this application could show, so it is
the one most strictly bound.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

from . import axis, tokens  # noqa: E402

BAND_HEIGHT = 18
MARK = 3.0
# `Gtk.Picture` with nothing asked of it collapses to a strip inside a vertical
# box, so the height is stated and the width follows the picture's own shape.
PLATE = 400


class PlateBand(Gtk.DrawingArea):
    """One mark per picture, on the axis above it. Emits `go` with a chapter."""

    __gsignals__ = {"go": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self):
        super().__init__()
        self.set_content_height(BAND_HEIGHT)
        self.set_hexpand(True)
        self.set_margin_start(axis.INSET)
        self.set_margin_end(axis.INSET)
        self._at: list[int] = []
        self._upto = 0
        self._length = 1
        self._dark = False
        self.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self.add_controller(click)

    def show_plates(self, plates, upto, length, dark=False):
        self._at = sorted({p["from"] for p in plates})
        self._upto = max(0, upto)
        self._length = max(1, length)
        self._dark = dark
        reached = sum(1 for c in self._at if c <= self._upto)
        self.set_tooltip_text(
            f"{reached} of the {len(self._at)} illustrated chapters you have reached"
        )
        self.queue_draw()

    def _clicked(self, _gesture, n_press, x, _y):
        if n_press != 1 or not self._at:
            return
        want = axis.chapter_at(x, self.get_width(), self._length)
        reached = [c for c in self._at if c <= self._upto]
        if reached:
            self.emit("go", min(reached, key=lambda c: abs(c - want)))

    def _draw(self, _area, cr, width, height, *_):
        palette = tokens.DARK if self._dark else tokens.LIGHT
        # Gold is the magnitude role and a plate is a thing the book has, so it
        # carries the same weight as a setting the reader kept.
        cr.set_source_rgb(*tokens.rgb(palette["magnitude"]))
        for chapter in self._at:
            if chapter > self._upto:
                break
            x = axis.x_for(chapter, width, self._length)
            cr.rectangle(x - MARK / 2, 2, MARK, height - 4)
            cr.fill()


class PlatesView(Gtk.Box):
    """The pictures reached so far. Emits `go` with a chapter."""

    __gsignals__ = {"go": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._caption = Gtk.Label(xalign=0, wrap=True)
        self._caption.add_css_class("summary-line")
        self.append(self._caption)

        self._rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self._rows.set_margin_start(axis.INSET)
        self._rows.set_margin_end(axis.INSET)
        self._rows.set_margin_top(8)
        self._rows.set_margin_bottom(24)
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._rows)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroller)

    def show_plates(self, plates, upto, length):
        reached = [p for p in plates if p["from"] <= upto]
        ahead = len(plates) - len(reached)
        self._caption.set_text(
            f"{len(reached)} of {len(plates)} pictures, through chapter {upto + 1} of {length}."
            + (f" {ahead} further on." if ahead else " You have seen all of them.")
            if plates
            else "This book has no illustrations folder beside it."
        )

        child = self._rows.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self._rows.remove(child)
            child = nxt

        for plate in reached:
            self._rows.append(self._plate(plate))
        if not reached and plates:
            empty = Gtk.Label(
                label="Nothing illustrated yet. The first picture is in chapter "
                f"{plates[0]['from'] + 1}.",
                xalign=0,
                wrap=True,
            )
            empty.add_css_class("empty-state")
            self._rows.append(empty)

    def _plate(self, plate):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("plate")

        picture = Gtk.Picture.new_for_filename(plate["path"])
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_can_shrink(True)
        picture.set_size_request(-1, PLATE)
        # Centred rather than filling: the frame is drawn on the widget, and a
        # widget the width of the column puts a border where the picture is not.
        picture.set_halign(Gtk.Align.CENTER)
        box.append(picture)

        said = plate["caption"] or plate["subject"] or plate["file"]
        line = Gtk.Label(xalign=0.5, wrap=True)
        line.add_css_class("plate-caption")
        line.set_text(said)
        box.append(line)

        where = Gtk.Button(label=f"Chapter {plate['from'] + 1}")
        where.add_css_class("flat")
        where.add_css_class("plate-where")
        where.set_halign(Gtk.Align.CENTER)
        where.connect("clicked", lambda _b, c=plate["from"]: self.emit("go", c))
        box.append(where)
        return box
