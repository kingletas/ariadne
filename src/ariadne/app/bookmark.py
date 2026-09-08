"""The bookmark, which is the only control that decides what exists.

It is not a panel any more. It is the chapter axis at the top of the content
column, and every chapter-indexed surface below it is drawn to the same scale
through `axis` -- so a vertical line through the knob crosses the same chapter
on every strip on screen.

Drawn rather than built from `Gtk.Scale`, because a scale's knob travels inset
by half its own width: its chapter 1 sits nine pixels in from its own left
edge, and nothing below it could ever line up with that.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

from . import axis, tokens  # noqa: E402

HEIGHT = 36
TRACK = 6
KNOB = 8
LABEL_BASELINE = 11


class Bookmark(Gtk.DrawingArea):
    """The axis. Emits `moved` with a zero-based chapter index."""

    __gsignals__ = {"moved": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self, chapters: int):
        super().__init__()
        self.add_css_class("bookmark")
        self._chapters = max(1, chapters)
        self._chapter = 0
        self._dark = False

        self.set_content_height(HEIGHT)
        self.set_hexpand(True)
        self.set_margin_start(axis.INSET)
        self.set_margin_end(axis.INSET)
        self.set_draw_func(self._draw)
        self.set_focusable(True)
        self.set_tooltip_text("Where you are. Click or drag to move; [ and ] step a chapter")
        self.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Bookmark - the chapter you have read to"]
        )

        click = Gtk.GestureClick()
        click.connect("pressed", self._pressed)
        self.add_controller(click)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", lambda _g, x, _y: self._to_x(x))
        drag.connect("drag-update", self._dragged)
        self.add_controller(drag)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._typed)
        self.add_controller(keys)

        self._changed(0)

    @property
    def chapter(self) -> int:
        return self._chapter

    def set_chapter(self, index: int) -> None:
        index = max(0, min(self._chapters - 1, index))
        if index == self._chapter:
            return
        self._chapter = index
        self._changed(index)

    def set_dark(self, dark: bool) -> None:
        if dark != self._dark:
            self._dark = dark
            self.queue_draw()

    def _changed(self, index: int) -> None:
        self.queue_draw()
        self.emit("moved", index)

    # --- what moves it ---

    def _to_x(self, x: float) -> None:
        self.set_chapter(axis.chapter_at(x, self.get_width(), self._chapters))

    def _pressed(self, gesture, n_press, x, _y):
        if n_press == 1:
            self.grab_focus()
            self._to_x(x)
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    def _dragged(self, gesture, dx, _dy):
        ok, start, _ = gesture.get_start_point()
        if ok:
            self._to_x(start + dx)

    def _typed(self, _controller, keyval, _code, _state) -> bool:
        from gi.repository import Gdk

        steps = {
            Gdk.KEY_Left: -1,
            Gdk.KEY_Right: 1,
            Gdk.KEY_Page_Up: -10,
            Gdk.KEY_Page_Down: 10,
        }
        if keyval in steps:
            self.set_chapter(self._chapter + steps[keyval])
            return True
        if keyval == Gdk.KEY_Home:
            self.set_chapter(0)
            return True
        if keyval == Gdk.KEY_End:
            self.set_chapter(self._chapters - 1)
            return True
        return False

    # --- drawing ---

    def _draw(self, _area, cr, width, height, *_):
        palette = tokens.DARK if self._dark else tokens.LIGHT
        middle = height - KNOB - 4

        cr.select_font_face("sans")
        cr.set_font_size(11)
        cr.set_source_rgb(*tokens.rgb(palette["ink_faint"]))
        cr.move_to(0, LABEL_BASELINE)
        cr.show_text("1")
        last = str(self._chapters)
        cr.move_to(width - cr.text_extents(last).width, LABEL_BASELINE)
        cr.show_text(last)

        cr.set_source_rgb(*tokens.rgb(palette["line_strong"]))
        cr.rectangle(0, middle - TRACK / 2, width, TRACK)
        cr.fill()

        here = axis.x_for(self._chapter, width, self._chapters)
        cr.set_source_rgb(*tokens.rgb(palette["accent"]))
        cr.rectangle(0, middle - TRACK / 2, here, TRACK)
        cr.fill()

        # The knob wears a ring in the canvas colour so it stays a knob where it
        # sits on top of its own filled track.
        cr.set_source_rgb(*tokens.rgb(palette["paper"]))
        cr.arc(here, middle, KNOB + 2, 0, 6.2832)
        cr.fill()
        cr.set_source_rgb(*tokens.rgb(palette["accent"]))
        cr.arc(here, middle, KNOB, 0, 6.2832)
        cr.fill()
