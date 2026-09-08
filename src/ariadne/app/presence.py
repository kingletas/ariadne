"""The presence strip: where somebody has been, drawn as a ticker tape.

It spans the whole book, not the part that has been read. The ticks stop at the
bookmark and the rest draws as empty track, so a strip says how much book is
left as well as where somebody has been -- and it shares the axis above it, so
a mark sits under the chapter it belongs to.

It is clickable, because a mark you cannot ask about is decoration.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from . import axis, tokens  # noqa: E402

HEIGHT = 26
MIN_TICK = 2.0
GAP = 1.0


class PresenceStrip(Gtk.DrawingArea):
    """Chapters 0..upto, filled where this entity appears."""

    def __init__(self, on_chapter=None):
        super().__init__()
        self.set_content_height(HEIGHT)
        self.set_hexpand(True)
        self._chapters: set[int] = set()
        self._upto = 0
        self._length = 1
        self._dark = False
        self._on_chapter = on_chapter
        self.set_draw_func(self._draw)

        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self.add_controller(click)
        self.set_cursor(Gtk.Widget.get_cursor(self))

    def show_entity(self, chapters, upto, length, dark=False):
        self._chapters = set(chapters)
        self._upto = max(0, upto)
        self._length = max(1, length)
        self._dark = dark
        self.set_tooltip_text(
            f"{len(self._chapters)} of the {self._upto + 1} chapters you have read"
        )
        self.queue_draw()

    def _clicked(self, _gesture, n_press, x, _y):
        if n_press != 1 or self._on_chapter is None:
            return
        chapter = axis.chapter_at(x, self.get_width(), self._length)
        self._on_chapter(chapter, chapter in self._chapters)

    def _draw(self, _area, cr, width, height, *_):
        step = axis.slot(width, self._length)
        # Below one pixel per chapter the marks merge into a smear, so a long
        # book draws a coarser strip rather than a solid bar that says nothing.
        tick = max(MIN_TICK, step - GAP)

        palette = tokens.DARK if self._dark else tokens.LIGHT

        cr.set_source_rgb(*tokens.rgb(palette["line_strong"]))
        cr.rectangle(0, height / 2 - 3, width, 6)
        cr.fill()

        cr.set_source_rgba(*tokens.rgb(palette["ink"]), 0.85)
        for chapter in sorted(self._chapters):
            if chapter > self._upto:
                break
            x = axis.x_for(chapter, width, self._length)
            cr.rectangle(x - tick / 2, height / 2 - 7, tick, 14)
            cr.fill()
