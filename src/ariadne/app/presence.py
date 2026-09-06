"""The presence strip: where somebody has been, drawn as a ticker tape.

One tick per chapter the reader has reached, filled where the person appears.
It is the densest thing on a card and the only one that answers "when" rather
than "how much", so it is drawn rather than written -- and it is clickable,
because a mark you cannot ask about is decoration.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

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
        self._on_chapter = on_chapter
        self.set_draw_func(self._draw)

        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self.add_controller(click)
        self.set_cursor(Gtk.Widget.get_cursor(self))

    def show_entity(self, chapters, upto):
        self._chapters = set(chapters)
        self._upto = max(0, upto)
        self.set_tooltip_text(
            f"{len(self._chapters)} of the {self._upto + 1} chapters you have read"
        )
        self.queue_draw()

    def _chapter_at(self, x, width):
        span = self._upto + 1
        if span <= 0 or width <= 0:
            return None
        chapter = int(x / width * span)
        return min(span - 1, max(0, chapter))

    def _clicked(self, _gesture, n_press, x, _y):
        if n_press != 1 or self._on_chapter is None:
            return
        chapter = self._chapter_at(x, self.get_width())
        if chapter is not None:
            self._on_chapter(chapter, chapter in self._chapters)

    def _draw(self, _area, cr, width, height, *_):
        span = self._upto + 1
        if span <= 0:
            return
        step = width / span
        # Below one pixel per chapter the marks merge into a smear, so a long
        # book draws a coarser strip rather than a solid bar that says nothing.
        tick = max(MIN_TICK, step - GAP)

        cr.set_source_rgba(0.85, 0.84, 0.78, 1.0)
        cr.rectangle(0, height / 2 - 3, width, 6)
        cr.fill()

        cr.set_source_rgba(0.28, 0.26, 0.21, 0.85)
        for chapter in sorted(self._chapters):
            if chapter > self._upto:
                break
            cr.rectangle(chapter * step, height / 2 - 7, tick, 14)
            cr.fill()
