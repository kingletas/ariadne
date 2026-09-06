"""Four measures of a chapter, on one axis, under one crosshair.

The page draws these as four separate sparklines, so a reader cannot see that
chapter 140 was quiet *and* crowded without counting along each one by eye.
Here they share an axis and a cursor: move over any of them and all four say
what they hold at that chapter.

It carries no verdict and never will. These are counts, not a score -- a quiet
chapter is a choice somebody made, and no number here can say whether it worked.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

from . import tokens  # noqa: E402

# key, the heading above the chart, the short word in the readout, and how the
# number is said. The short word is written rather than derived: taking the
# first word of the heading produced "how 16.7%".
MEASURES = (
    ("d", "How much of the chapter is dialogue", "dialogue", "{:.0f}%"),
    ("o", "People on stage", "on stage", "{:.0f}"),
    ("f", "Names you meet for the first time", "new names", "{:.0f}"),
    ("w", "Chapter length in words", "words", "{:,.0f}"),
)

ROW = 74
PAD_LEFT = 8
PAD_RIGHT = 8


class PaceView(Gtk.Box):
    """Emits `go` when the reader clicks a chapter."""

    __gsignals__ = {"go": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._rows: list[dict] = []
        self._upto = 0
        self._cursor: int | None = None
        self._dark = False

        self._caption = Gtk.Label(xalign=0, wrap=True)
        self._caption.add_css_class("summary-line")
        self.append(self._caption)

        self._readout = Gtk.Label(xalign=0)
        self._readout.add_css_class("pace-readout")
        self.append(self._readout)

        self._area = Gtk.DrawingArea(vexpand=True, hexpand=True)
        self._area.set_draw_func(self._draw)
        self._area.set_content_height(ROW * len(MEASURES) + 16)
        self._area.set_valign(Gtk.Align.FILL)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._moved)
        motion.connect("leave", lambda _c: self._park())
        self._area.add_controller(motion)
        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self._area.add_controller(click)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._area)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroller)

    def show_pace(self, rows, upto, dark=False):
        self._rows, self._upto, self._dark = rows, upto, dark
        self._caption.set_text(
            f"Chapters 1 to {upto + 1}. Nothing past where you are is drawn. "
            "These are counts, not a score — a quiet chapter is a choice somebody "
            "made, and no number here can tell you whether it worked."
        )
        self._park()
        self._area.queue_draw()

    # --- the cursor ---

    def _chapter_at(self, x, width):
        span = self._upto + 1
        usable = max(1, width - PAD_LEFT - PAD_RIGHT)
        return min(span - 1, max(0, int((x - PAD_LEFT) / usable * span)))

    def _moved(self, _controller, x, _y):
        self._cursor = self._chapter_at(x, self._area.get_width())
        self._say(self._cursor)
        self._area.queue_draw()

    def _clicked(self, _gesture, n_press, x, _y):
        if n_press == 1:
            self.emit("go", self._chapter_at(x, self._area.get_width()))

    def _park(self):
        self._cursor = None
        self._say(self._upto)

    def _say(self, chapter):
        if not self._rows or chapter is None or chapter >= len(self._rows):
            self._readout.set_text("")
            return
        row = self._rows[chapter]
        parts = "   ".join(
            f"{word} {shape.format(row.get(key, 0))}" for key, _heading, word, shape in MEASURES
        )
        where = " · at your bookmark" if chapter == self._upto else ""
        self._readout.set_text(f"Chapter {chapter + 1}{where}   ·   {parts}")

    # --- drawing ---

    def _draw(self, _area, cr, width, height, *_):
        rows = self._rows[: self._upto + 1]
        if not rows:
            return
        palette = tokens.DARK if self._dark else tokens.LIGHT
        ink = tokens.rgb(palette["ink"])
        faint = tokens.rgb(palette["ink_faint"])
        line = tokens.rgb(palette["line"])
        accent = tokens.rgb(palette["accent"])

        usable = max(1, width - PAD_LEFT - PAD_RIGHT)
        step = usable / len(rows)
        band = max(ROW, (height - 16) / len(MEASURES))
        cr.select_font_face("sans")

        for index, (key, heading, _word, shape) in enumerate(MEASURES):
            top = index * band + 8
            plot_top, plot_bottom = top + 20, top + band - 14
            values = [r.get(key, 0) for r in rows]
            peak = max(values) or 1

            cr.set_source_rgb(*faint)
            cr.set_font_size(11)
            cr.move_to(PAD_LEFT, top + 12)
            cr.show_text(heading)
            label = f"0 to {shape.format(peak)}"
            cr.move_to(width - PAD_RIGHT - cr.text_extents(label).width, top + 12)
            cr.show_text(label)

            cr.set_source_rgb(*line)
            cr.set_line_width(1)
            cr.move_to(PAD_LEFT, plot_bottom + 0.5)
            cr.line_to(width - PAD_RIGHT, plot_bottom + 0.5)
            cr.stroke()

            cr.set_source_rgb(*ink)
            cr.set_line_width(1.2)
            for i, value in enumerate(values):
                x = PAD_LEFT + i * step + step / 2
                y = plot_bottom - (value / peak) * (plot_bottom - plot_top)
                cr.line_to(x, y) if i else cr.move_to(x, y)
            cr.stroke()

        # One crosshair down all four, which is the whole point of sharing an
        # axis: a chapter is quiet and crowded at the same time or it is not.
        cursor = self._cursor if self._cursor is not None else self._upto
        if 0 <= cursor < len(rows):
            x = PAD_LEFT + cursor * step + step / 2
            cr.set_source_rgba(*accent, 0.9)
            cr.set_line_width(1.5)
            cr.move_to(x, 4)
            cr.line_to(x, len(MEASURES) * band)
            cr.stroke()
            for index, (key, _heading, _word, _shape) in enumerate(MEASURES):
                top = index * band + 8
                plot_top, plot_bottom = top + 20, top + band - 14
                peak = max(r.get(key, 0) for r in rows) or 1
                y = plot_bottom - (rows[cursor].get(key, 0) / peak) * (plot_bottom - plot_top)
                cr.arc(x, y, 3.5, 0, 6.2832)
                cr.fill()
