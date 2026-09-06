"""Grouped navigation, which replaced a row of seven flat tabs.

The seven were not peers. `people` and `places` are filters of `everyone` and
`cast list` is a third cut of the same list, while `map` and `pace` are
different objects and `away a while` is an attention view. Presenting them as
one row said they were all the same kind of thing.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa: E402

WIDTH = 220

GROUPS = (
    ("CAST", (("everyone", "Everyone"), ("people", "People"), ("places", "Places"))),
    ("EXPLORE", (("ground", "Where you've been"), ("map", "Map"), ("pace", "Pace"))),
    ("ATTENTION", (("away", "Away a while"), ("warnings", "Warnings"))),
)


class Rail(Gtk.Box):
    """Emits `chose` with the view key."""

    __gsignals__ = {"chose": (GObject.SignalFlags.RUN_FIRST, None, (str,))}

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("rail")
        self.set_size_request(WIDTH, -1)
        self._rows: dict[str, Gtk.ListBoxRow] = {}
        self._boxes: list[Gtk.ListBox] = []
        self._quiet = False

        for heading, entries in GROUPS:
            label = Gtk.Label(label=heading, xalign=0)
            label.add_css_class("rail-group")
            self.append(label)

            box = Gtk.ListBox()
            box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            box.add_css_class("navigation-sidebar")
            box.connect("row-selected", self._selected)
            for key, text in entries:
                row = Gtk.ListBoxRow()
                row.add_css_class("rail-item")
                row.set_child(Gtk.Label(label=text, xalign=0))
                row.key = key
                box.append(row)
                self._rows[key] = row
            self._boxes.append(box)
            self.append(box)

        self.choose("everyone")

    def choose(self, key: str) -> None:
        row = self._rows.get(key)
        if row is None:
            return
        self._quiet = True
        for box in self._boxes:
            box.unselect_all()
        row.get_parent().select_row(row)
        self._quiet = False
        self.emit("chose", key)

    def set_badge(self, key: str, count: int) -> None:
        """A count, never a severity. A red badge on `warnings` would tell the
        reader how bad the thing is, which is the one thing warnings must not
        do until they deliberately open them."""
        row = self._rows.get(key)
        if row is None:
            return
        label = row.get_child()
        base = dict((k, t) for _, entries in GROUPS for k, t in entries)[key]
        label.set_text(f"{base} · {count}" if count else base)

    def _selected(self, box, row):
        if self._quiet or row is None:
            return
        for other in self._boxes:
            if other is not box:
                other.unselect_all()
        self.emit("chose", row.key)
