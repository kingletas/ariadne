"""The bookmark, which is the only control that decides what exists.

Every view is built from it, so it is one panel directly under the header
rather than a setting somewhere. The slider is coarse and the spin button is
exact, and both drive the same value: a second progress state would be two
answers to the one question the whole application is about.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, GObject, Gtk  # noqa: E402

# Long enough to read, short enough not to become furniture.
ANNOUNCEMENT_SECONDS = 6


class Bookmark(Gtk.Box):
    """Emits `moved` with a zero-based chapter index."""

    __gsignals__ = {"moved": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self, chapters: int):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class("bookmark")
        self._chapters = max(1, chapters)
        self._quiet = False

        label = Gtk.Label(label="BOOKMARK", xalign=0)
        label.add_css_class("bookmark-label")
        self.append(label)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._back = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self._back.set_tooltip_text("Previous chapter")
        self._back.add_css_class("flat")
        self._back.connect("clicked", lambda _b: self.set_chapter(self.chapter - 1))
        row.append(self._back)

        # The spin button carries its own steppers, so the chevrons beside it
        # were a second pair of buttons doing the same job. It shows the number
        # and takes one typed straight in; the chevrons are the ones a reader
        # reaches for without looking.
        self._spin = Gtk.SpinButton.new_with_range(1, self._chapters, 1)
        self._spin.set_numeric(True)
        self._spin.set_width_chars(4)
        self._spin.set_tooltip_text("Chapter you are on")
        self._spin.connect("value-changed", self._spun)
        row.append(self._spin)

        self._forward = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self._forward.set_tooltip_text("Next chapter")
        self._forward.add_css_class("flat")
        self._forward.connect("clicked", lambda _b: self.set_chapter(self.chapter + 1))
        row.append(self._forward)

        self._of = Gtk.Label(xalign=0)
        self._of.add_css_class("reading-position")
        self._of.set_margin_start(4)
        row.append(self._of)

        self._title = Gtk.Label(xalign=1, hexpand=True, ellipsize=3)
        self._title.add_css_class("chapter-title")
        row.append(self._title)
        self.append(row)

        # Snapped to whole chapters: a bookmark between two of them is not a
        # place in a book, and every view below is indexed by chapter anyway.
        self._scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, self._chapters, 1)
        self._scale.add_css_class("bookmark-scale")
        self._scale.set_round_digits(0)
        self._scale.set_draw_value(False)
        self._scale.set_hexpand(True)
        self._scale.connect("value-changed", self._slid)
        self.append(self._scale)

        # A ruling is an ordinary act, not an alarm. Adw.Banner's own styling
        # reads as a warning, and the estate rule is that colour never carries
        # a meaning of its own -- so this is a quiet line that takes itself away.
        self._banner = Gtk.Label(xalign=0)
        self._banner.add_css_class("announcement")
        self._banner.set_visible(False)
        self.append(self._banner)
        self._announcement = 0

        self.set_chapter(0)

    @property
    def chapter(self) -> int:
        return int(self._spin.get_value()) - 1

    def set_chapter(self, index: int) -> None:
        index = max(0, min(self._chapters - 1, index))
        if index == self.chapter:
            return
        self._quiet = True
        self._spin.set_value(index + 1)
        self._scale.set_value(index + 1)
        self._quiet = False
        self._changed(index)

    def show_chapter_title(self, title: str | None) -> None:
        """Only ever the chapter the reader is on. A later title is the book."""
        self._title.set_text(title or "")

    def _spun(self, _spin):
        if not self._quiet:
            self._scale.set_value(self._spin.get_value())
            self._changed(self.chapter)

    def _slid(self, _scale):
        if not self._quiet:
            self._spin.set_value(round(self._scale.get_value()))

    def _changed(self, index: int) -> None:
        self._of.set_text(f"of {self._chapters}")
        self._back.set_sensitive(index > 0)
        self._forward.set_sensitive(index < self._chapters - 1)
        self.emit("moved", index)

    def announce(self, message: str) -> None:
        """A status line the screen reader reads and the eye can ignore."""
        if self._announcement:
            GLib.source_remove(self._announcement)
            self._announcement = 0
        self._banner.set_text(message or "")
        self._banner.set_visible(bool(message))
        if message:
            self._banner.update_property([Gtk.AccessibleProperty.LABEL], [message])
            self._announcement = GLib.timeout_add_seconds(ANNOUNCEMENT_SECONDS, self._quieten)

    def _quieten(self) -> bool:
        self._banner.set_visible(False)
        self._announcement = 0
        return False
