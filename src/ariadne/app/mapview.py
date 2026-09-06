"""Who shares chapters with whom, in three shapes rather than one ring.

A ring with every name on it stops working long before the books that need it
most: at chapter 180 of War and Peace it is 378 labels with lines crossing
everywhere, which is a texture rather than a diagram. So the ring is the
small-cast case, and a large cast gets a focus instead -- one person in the
middle and the people actually beside them.

Nothing past the bookmark is drawn. The whole-cast ring reads the co-occurrence
table the page ships; a focus counts shared chapters directly, because that
table is capped at the strongest forty pairs in the book and finds Pierre two
companions at chapter 180.
"""

from __future__ import annotations

import math

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

from ..model.view import clip, neighbours  # noqa: E402
from . import tokens  # noqa: E402

# Past this many names a ring is a texture rather than a diagram.
RING_LIMIT = 28
NEIGHBOURS = 8


class MapView(Gtk.Box):
    """Emits `centred` when the reader picks somebody to centre on."""

    # Not `focus`: Gtk.Widget already has a signal by that name, and
    # overriding it replaces the widget's own focus handling.
    __gsignals__ = {"centred": (GObject.SignalFlags.RUN_FIRST, None, (str,))}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._pairs: list[tuple[str, str, float]] = []
        self._beside: list[tuple[str, int]] = []
        self._focus: str | None = None
        self._dark = False
        self._nodes: list[tuple[str, float, float]] = []

        self._caption = Gtk.Label(xalign=0, wrap=True)
        self._caption.add_css_class("summary-line")
        self.append(self._caption)

        self._area = Gtk.DrawingArea(vexpand=True, hexpand=True)
        self._area.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect("released", self._clicked)
        self._area.add_controller(click)
        self.append(self._area)

    def show_map(self, model, upto, focus=None, dark=False):
        self._pairs = (model.get("assoc") or {}).get(str(upto)) or []
        self._beside = neighbours(clip(model, upto), focus, NEIGHBOURS) if focus else []
        self._focus, self._dark = focus, dark
        names = {n for a, b, _ in self._pairs for n in (a, b)}

        if focus:
            self._caption.set_text(
                f"Who shares chapters with {focus}, up to chapter {upto + 1}. "
                "A thicker line means more chapters together. Click a name to move "
                "the focus; nothing past your position is drawn."
            )
        elif len(names) > RING_LIMIT:
            self._caption.set_text(
                f"{len(names)} names share chapters by chapter {upto + 1} — too many "
                "for a useful full map. Click anybody on a card to focus the map on "
                "them, or read the chapter bands on their card instead."
            )
        else:
            self._caption.set_text(
                f"Who shares chapters with whom, up to chapter {upto + 1}. "
                "A thicker line means more chapters together."
            )
        self._area.queue_draw()

    # --- geometry ---

    def _visible(self):
        """The focused neighbourhood, or the whole ring when it is small enough."""
        if self._focus:
            return (
                [self._focus] + [n for n, _ in self._beside],
                [(self._focus, n, count) for n, count in self._beside],
            )
        names = sorted({n for a, b, _ in self._pairs for n in (a, b)})
        if len(names) > RING_LIMIT:
            return [], []
        return names, self._pairs

    def _clicked(self, _gesture, n_press, x, y):
        if n_press != 1:
            return
        for name, nx, ny in self._nodes:
            if (x - nx) ** 2 + (y - ny) ** 2 <= 18**2:
                self.emit("centred", name)
                return

    def _draw(self, _area, cr, width, height, *_):
        names, edges = self._visible()
        palette = tokens.DARK if self._dark else tokens.LIGHT
        ink = tokens.rgb(palette["ink"])
        faint = tokens.rgb(palette["ink_faint"])
        accent = tokens.rgb(palette["accent"])
        self._nodes = []

        if not names:
            cr.set_source_rgb(*faint)
            cr.set_font_size(13)
            cr.move_to(24, height / 2)
            cr.show_text("Choose a person on a card to focus the map.")
            return

        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 90
        at = {}
        if self._focus:
            at[self._focus] = (cx, cy)
            ring = names[1:]
            for i, name in enumerate(ring):
                angle = (i / max(1, len(ring))) * 2 * math.pi
                at[name] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        else:
            for i, name in enumerate(names):
                angle = (i / len(names)) * 2 * math.pi - math.pi / 2
                at[name] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

        strongest = max((s for _, _, s in edges), default=1) or 1
        for a, b, strength in edges:
            if a not in at or b not in at:
                continue
            cr.set_source_rgba(*ink, 0.18 + 0.5 * (strength / strongest))
            cr.set_line_width(0.6 + 3.4 * (strength / strongest))
            cr.move_to(*at[a])
            cr.line_to(*at[b])
            cr.stroke()

        if self._focus and self._beside:
            cr.set_font_size(10)
            for name, count in self._beside:
                if name not in at:
                    continue
                mx = (at[self._focus][0] + at[name][0]) / 2
                my = (at[self._focus][1] + at[name][1]) / 2
                cr.set_source_rgb(*faint)
                cr.move_to(mx + 4, my - 3)
                cr.show_text(f"{count} ch")

        cr.select_font_face("sans")
        for name, (x, y) in at.items():
            middle = name == self._focus
            cr.set_source_rgb(*(accent if middle else ink))
            cr.arc(x, y, 7 if middle else 4.5, 0, 2 * math.pi)
            cr.fill()
            cr.set_font_size(12 if middle else 11)
            extents = cr.text_extents(name)
            cr.move_to(x - extents.width / 2, y - 12)
            cr.show_text(name)
            self._nodes.append((name, x, y))
