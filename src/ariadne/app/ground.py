"""Where the book has been — a map of the book, not of the world.

One band per setting, chapters left to right, filled where the book is there.
Ordered by first arrival, so reading down it is reading the journey. There are
no coordinates and there will not be: half the places that matter in a novel
are on no map, and inventing a position for Bald Hills would be the confident
wrong answer this tool exists not to give.

Every row starts as a proposal. The measure behind it -- which place a chapter
names most -- put 21 of 26 right over six books, which is a good proposal and a
bad map. One click each makes it the reader's.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

from ..model.ground import proposed, scope  # noqa: E402
from . import tokens  # noqa: E402

BAND_HEIGHT = 22


class Band(Gtk.DrawingArea):
    """The chapters one setting holds, across everything read so far."""

    def __init__(self, on_chapter=None):
        super().__init__()
        self.set_content_height(BAND_HEIGHT)
        self.set_hexpand(True)
        self._chapters: set[int] = set()
        self._upto = 0
        self._kept = False
        self._dark = False
        self._on_chapter = on_chapter
        self.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self.add_controller(click)

    def show_band(self, chapters, upto, kept, dark):
        self._chapters = set(chapters)
        self._upto = max(0, upto)
        self._kept, self._dark = kept, dark
        first, last = min(self._chapters) + 1, max(self._chapters) + 1
        self.set_tooltip_text(f"{len(self._chapters)} chapters, {first} to {last}")
        self.queue_draw()

    def _clicked(self, _gesture, n_press, x, _y):
        if n_press != 1 or self._on_chapter is None:
            return
        span = self._upto + 1
        width = self.get_width()
        if width > 0 and span > 0:
            self._on_chapter(min(span - 1, max(0, int(x / width * span))))

    def _draw(self, _area, cr, width, height, *_):
        span = self._upto + 1
        if span <= 0:
            return
        palette = tokens.DARK if self._dark else tokens.LIGHT
        step = width / span

        cr.set_source_rgb(*tokens.rgb(palette["surface_muted"]))
        cr.rectangle(0, height / 2 - 5, width, 10)
        cr.fill()

        # Gold is the magnitude role; a proposal has not earned it yet.
        fill = palette["magnitude"] if self._kept else palette["ink_faint"]
        cr.set_source_rgb(*tokens.rgb(fill))
        for chapter in sorted(self._chapters):
            if chapter > self._upto:
                break
            cr.rectangle(chapter * step, height / 2 - 8, max(2.0, step), 16)
            cr.fill()


class GroundView(Gtk.Box):
    """Emits `go` with a chapter and `ruled` with a message to announce."""

    __gsignals__ = {
        "go": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "ruled": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, curation):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._curation = curation

        self._scope = Gtk.Label(xalign=0, wrap=True)
        self._scope.add_css_class("summary-line")
        self.append(self._scope)

        self._caption = Gtk.Label(xalign=0, wrap=True)
        self._caption.add_css_class("ground-caption")
        self.append(self._caption)

        self._rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._rows.set_margin_start(24)
        self._rows.set_margin_end(24)
        self._rows.set_margin_top(8)
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._rows)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroller)

    def show_ground(self, model, upto, dark=False):
        kept, struck = self._curation.kept_settings, self._curation.struck_settings
        candidates = [
            (name, chapters) for name, chapters in proposed(model, upto) if name not in struck
        ]
        # Anything the reader has kept stays on the map even if it drops below
        # the proposal threshold at this bookmark.
        known = {name for name, _ in candidates}
        for name, chapters in proposed(model, upto, minimum=1):
            if name in kept and name not in known:
                candidates.append((name, chapters))

        ruled = bool(kept or struck)
        rows = [(n, c) for n, c in candidates if n in kept] if ruled else candidates
        unruled = [(n, c) for n, c in candidates if n not in kept] if ruled else []

        measure = scope(model, upto, kept if kept else None)
        placed = measure["settled"] * 100
        self._scope.set_text(
            f"{len(rows)} {'setting' if len(rows) == 1 else 'settings'} through chapter "
            f"{upto + 1}  ·  {placed:.0f}% of what you have read happens somewhere named"
            + (f"  ·  most of it in {measure['widest']}" if measure["widest"] else "")
        )
        self._caption.set_text(
            "No coordinates, and there will not be any — half the places that matter in a "
            "novel are on no map. This is where the book has been, in the order it went. "
            + (
                "Keep or strike a row and the map becomes yours."
                if not ruled
                else "Struck rows are gone; the ones below are still proposals."
            )
        )

        child = self._rows.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self._rows.remove(child)
            child = nxt

        order = sorted(rows, key=lambda row: row[1][0])
        for name, chapters in order:
            self._rows.append(self._row(name, chapters, upto, True, dark, ruled))
        if unruled:
            heading = Gtk.Label(label="STILL PROPOSED", xalign=0)
            heading.add_css_class("rail-group")
            self._rows.append(heading)
            for name, chapters in sorted(unruled, key=lambda row: row[1][0]):
                self._rows.append(self._row(name, chapters, upto, False, dark, ruled))
        if not order and not unruled:
            empty = Gtk.Label(
                label="Nowhere named often enough yet. A setting is a place a chapter "
                "keeps returning to, not one mentioned in passing.",
                xalign=0,
                wrap=True,
            )
            empty.add_css_class("empty-state")
            self._rows.append(empty)

    def _row(self, name, chapters, upto, kept, dark, ruled):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("ground-row")

        label = Gtk.Label(label=name, xalign=0, ellipsize=3)
        label.add_css_class("ground-name")
        label.set_size_request(160, -1)
        row.append(label)

        count = Gtk.Label(label=f"{len(chapters)} ch", xalign=1)
        count.add_css_class("cast-facts")
        count.set_size_request(44, -1)
        row.append(count)

        band = Band(on_chapter=lambda c: self.emit("go", c))
        band.show_band(chapters, upto, kept and ruled, dark)
        row.append(band)

        if not (kept and ruled):
            yes = Gtk.Button.new_from_icon_name("object-select-symbolic")
            yes.add_css_class("flat")
            yes.set_tooltip_text(f"Keep {name} as a setting")
            yes.connect(
                "clicked", lambda _b, n=name: self.emit("ruled", self._curation.keep_setting(n))
            )
            row.append(yes)
        no = Gtk.Button.new_from_icon_name("window-close-symbolic")
        no.add_css_class("flat")
        no.set_tooltip_text(f"{name} is not a setting")
        no.connect(
            "clicked", lambda _b, n=name: self.emit("ruled", self._curation.strike_setting(n))
        )
        row.append(no)
        return row
