"""Five views, which is how many there are.

Eight items in three groups presented `everyone`, `people`, `places` and
`away a while` as peers of `map` and `pace`. They are not: all four render the
same cast list with a different filter, and the window branched on exactly
that. They are a facet of one view, so they are chips inside it, and what is
left needs no group headings -- five peers do not.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

WIDTH = 220

VIEWS = (
    ("cast", "Cast"),
    ("ground", "Where you've been"),
    ("map", "Map"),
    ("pace", "Pace"),
    ("plates", "Pictures"),
    ("warnings", "Warnings"),
)

# A book with no illustrations folder beside it has no pictures view. An empty
# view that explains its own emptiness is a row every reader learns to skip.
OPTIONAL = ("plates",)

# The four cuts of the cast list. Order is the reader's likely reach, not
# alphabetical: everyone first, and the attention view last.
FACETS = (
    ("everyone", "Everyone"),
    ("people", "People"),
    ("places", "Places"),
    ("away", "Away a while"),
)


class Rail(Gtk.Box):
    """Emits `chose` with the view key."""

    __gsignals__ = {"chose": (GObject.SignalFlags.RUN_FIRST, None, (str,))}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("rail")
        self.set_size_request(WIDTH, -1)
        self._rows: dict[str, Gtk.ListBoxRow] = {}
        self._quiet = False

        self._box = Gtk.ListBox()
        self._box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._box.add_css_class("navigation-sidebar")
        self._box.set_margin_top(8)
        self._box.connect("row-selected", self._selected)
        for key, text in VIEWS:
            row = Gtk.ListBoxRow()
            row.add_css_class("rail-item")
            row.set_child(Gtk.Label(label=text, xalign=0))
            row.key = key
            self._box.append(row)
            self._rows[key] = row
        self.append(self._box)

        self.choose("cast")

    def offer(self, key: str, present: bool) -> None:
        """Show an optional view, or take it away. Only the optional ones move."""
        row = self._rows.get(key)
        if row is not None and key in OPTIONAL:
            row.set_visible(present)

    def choose(self, key: str) -> None:
        row = self._rows.get(key)
        if row is None:
            return
        self._quiet = True
        self._box.select_row(row)
        self._quiet = False
        self.emit("chose", key)

    def set_badge(self, key: str, count: int) -> None:
        """A count, never a severity. A red badge on `warnings` would tell the
        reader how bad the thing is, which is the one thing warnings must not
        do until they deliberately open them."""
        row = self._rows.get(key)
        if row is None:
            return
        base = dict(VIEWS)[key]
        row.get_child().set_text(f"{base} · {count}" if count else base)

    def _selected(self, _box, row):
        if self._quiet or row is None:
            return
        self.emit("chose", row.key)
