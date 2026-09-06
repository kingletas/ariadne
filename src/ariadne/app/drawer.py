"""The detail drawer: everything known about one name, and what can be done to it.

It slides in beside the list rather than over it, so the reader never loses
their place. Nothing in it reaches past the bookmark -- the appearances it
lists are the ones already read, and a later one does not exist to it.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import GObject, Gtk  # noqa: E402

WIDTH = 400

# A lead appears in eighty-odd chapters. Showing every chip by default turns
# the drawer into a wall of numbers with the controls somewhere past it.
CHAPTER_CHIPS = 24


class Drawer(Gtk.Box):
    """Emits `acted` with a message to announce, and `go` with a chapter."""

    __gsignals__ = {
        "acted": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "go": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "closed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "opened": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, curation):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("drawer")
        self.set_size_request(WIDTH, -1)
        self._curation = curation
        self._name = ""
        self._upto = 0

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        head.add_css_class("drawer-head")
        self._heading = Gtk.Label(xalign=0, hexpand=True, wrap=True)
        self._heading.add_css_class("drawer-title")
        head.append(self._heading)
        shut = Gtk.Button.new_from_icon_name("window-close-symbolic")
        shut.add_css_class("flat")
        shut.set_tooltip_text("Close (Escape)")
        shut.connect("clicked", lambda _b: self.emit("closed"))
        head.append(shut)
        self.append(head)

        self._body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self._body.add_css_class("drawer-body")
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._body)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroller)

    @property
    def name(self) -> str:
        """Whose card is showing, so the window can follow the bookmark."""
        return self._name

    # --- filling it ---

    def show_name(self, model, name: str, upto: int) -> None:
        self._name, self._upto = name, upto
        entity = next((e for e in model["entities"] if e["name"] == name), None)
        self._heading.set_text(name)
        child = self._body.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self._body.remove(child)
            child = nxt

        if entity is None or entity["first"] > upto:
            self._body.append(
                self._field("Not met yet", "You have not reached this name at your bookmark.")
            )
            return

        chapters = [c for c in entity["chapters"] if c <= upto]
        uses = sum(
            n for c, n in zip(entity["chapters"], entity["counts"], strict=False) if c <= upto
        )

        if entity.get("kind") in ("person", "place"):
            self._body.append(self._field("What it is", entity["kind"]))
        self._body.append(self._field("First met", f"Chapter {entity['first'] + 1}"))
        self._body.append(self._field("Last seen", f"Chapter {chapters[-1] + 1}"))
        self._body.append(
            self._field(
                "Seen in",
                f"{len(chapters)} chapter{'s' if len(chapters) != 1 else ''}  ·  {uses} mentions",
            )
        )

        also = [
            link["also"]
            for link in self._curation.decisions.get("links", [])
            if link.get("keep") == name and link.get("state") == "accepted"
        ]
        if also:
            self._body.append(self._field("Also called", " · ".join(also)))

        # What can be acted on comes first. A lead appears in eighty chapters,
        # and putting that list above the note buries every control below it.
        self._body.append(self._note_field(name))
        self._body.append(self._merge_field(model, name, upto))
        self._body.append(self._chapter_links("Appears in", chapters))

    # --- pieces ---

    def _field(self, label: str, value: str) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        heading = Gtk.Label(label=label, xalign=0)
        heading.add_css_class("drawer-label")
        box.append(heading)
        body = Gtk.Label(label=value, xalign=0, wrap=True)
        body.add_css_class("drawer-value")
        box.append(body)
        return box

    def _chapter_links(self, label: str, chapters: list[int]) -> Gtk.Box:
        """Every chapter is a button. A list you cannot act on is a paragraph."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        heading = Gtk.Label(label=f"{label} ({len(chapters)})", xalign=0)
        heading.add_css_class("drawer-label")
        box.append(heading)
        flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=8)
        flow.set_column_spacing(4)
        flow.set_row_spacing(4)

        def fill(limit):
            child = flow.get_first_child()
            while child is not None:
                nxt = child.get_next_sibling()
                flow.remove(child)
                child = nxt
            for chapter in chapters[:limit]:
                button = Gtk.Button(label=str(chapter + 1))
                button.add_css_class("chapter-chip")
                button.set_tooltip_text(f"Go to chapter {chapter + 1}")
                button.connect("clicked", lambda _b, c=chapter: self.emit("go", c))
                flow.append(button)

        fill(CHAPTER_CHIPS)
        box.append(flow)
        if len(chapters) > CHAPTER_CHIPS:
            more = Gtk.Button(label=f"Show all {len(chapters)}")
            more.add_css_class("flat")
            more.set_halign(Gtk.Align.START)

            def expand(button):
                fill(len(chapters))
                button.set_visible(False)

            more.connect("clicked", expand)
            box.append(more)
        return box

    def _note_field(self, name: str) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        heading = Gtk.Label(label="Your note", xalign=0)
        heading.add_css_class("drawer-label")
        box.append(heading)
        entry = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD)
        entry.add_css_class("note-entry")
        entry.set_size_request(-1, 72)
        entry.get_buffer().set_text(self._curation.note_for(name))
        box.append(entry)
        save = Gtk.Button(label="Save note")
        save.set_halign(Gtk.Align.START)
        save.connect("clicked", lambda _b: self._save_note(name, entry))
        box.append(save)
        return box

    def _save_note(self, name: str, entry: Gtk.TextView) -> None:
        buffer = entry.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.emit("acted", self._curation.note(name, text, self._upto))

    def _merge_field(self, model, name: str, upto: int) -> Gtk.Widget:
        """Only pairs ariadne can prove, and never applied without an answer."""
        pairs = [p for p in self._curation.candidates(upto) if name in p]
        if not pairs:
            return Gtk.Box()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("merge-box")
        heading = Gtk.Label(label="POSSIBLE NAME MATCH", xalign=0)
        heading.add_css_class("drawer-label")
        box.append(heading)
        keep, also = pairs[0]
        box.append(
            Gtk.Label(
                label=f"“{also}” may be the same person as “{keep}”, judged on what you "
                f"have read through chapter {upto + 1}.",
                xalign=0,
                wrap=True,
            )
        )
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        yes = Gtk.Button(label="Merge names")
        yes.add_css_class("suggested-action")
        yes.connect("clicked", lambda _b: self._ruled(self._curation.merge(keep, also)))
        row.append(yes)
        no = Gtk.Button(label="Keep separate")
        no.connect("clicked", lambda _b: self._ruled(self._curation.separate(keep, also)))
        row.append(no)
        box.append(row)
        return box

    def _ruled(self, message: str) -> None:
        self.emit("acted", message)
        self.emit("opened", self._name)
