"""The cast, which is the primary object and the default view.

A card per person or place, built from the index clipped to the bookmark. The
list is virtualised because the largest book in the corpus carries 526 names
and the reader can drag the bookmark across all of them in one gesture.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GObject, Gtk  # noqa: E402

from .presence import PresenceStrip  # noqa: E402


class Entity(GObject.Object):
    """One row's data. GTK needs a GObject; the dict stays the truth."""

    def __init__(self, data: dict):
        super().__init__()
        self.data = data


class CastView(Gtk.Box):
    """Emits `opened` with an entity name, and `chapter` with an index."""

    __gsignals__ = {
        "opened": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "chapter": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._upto = 0

        self._summary = Gtk.Label(xalign=0)
        self._summary.add_css_class("summary-line")
        self.append(self._summary)

        self._items = Gio.ListStore.new(Entity)
        selection = Gtk.NoSelection.new(self._items)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup)
        factory.connect("bind", self._bind)

        self._list = Gtk.ListView.new(selection, factory)
        self._list.add_css_class("background")
        self._list.set_vexpand(True)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self._list)
        scroller.set_vexpand(True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroller)

        self._empty = Gtk.Label(xalign=0)
        self._empty.add_css_class("empty-state")
        self._empty.set_visible(False)
        self.append(self._empty)

    def show_entities(self, entities, upto, summary, empty_message=None):
        self._upto = upto
        self._items.remove_all()
        for entity in entities:
            self._items.append(Entity(entity))
        self._summary.set_text(summary)
        showing = bool(entities)
        self._list.get_parent().set_visible(showing)
        self._empty.set_visible(not showing)
        if not showing:
            self._empty.set_text(empty_message or "Nothing here yet.")

    # --- the card ---

    def _setup(self, _factory, item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("cast-card")

        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name = Gtk.Button()
        name.set_has_frame(False)
        name.add_css_class("name-button")
        inner = Gtk.Label(xalign=0)
        inner.add_css_class("cast-name")
        name.set_child(inner)
        heading.append(name)
        kind = Gtk.Label()
        kind.add_css_class("cast-kind")
        heading.append(kind)
        fresh = Gtk.Label(label="NEW")
        fresh.add_css_class("cast-new")
        heading.append(fresh)
        card.append(heading)

        facts = Gtk.Label(xalign=0)
        facts.add_css_class("cast-facts")
        card.append(facts)

        note = Gtk.Label(xalign=0)
        note.add_css_class("cast-note")
        card.append(note)

        with_whom = Gtk.Label(xalign=0, wrap=True)
        with_whom.add_css_class("cast-with")
        card.append(with_whom)

        strip = PresenceStrip(on_chapter=lambda c, _hit: self.emit("chapter", c))
        card.append(strip)

        item.set_child(card)
        item.widgets = (inner, kind, fresh, facts, note, with_whom, strip, name)

    def _bind(self, _factory, item):
        inner, kind, fresh, facts, note, with_whom, strip, button = item.widgets
        entity = item.get_item().data

        inner.set_text(entity["name"])
        known = entity.get("kind") in ("person", "place")
        kind.set_text(entity["kind"] if known else "")
        kind.set_visible(known)
        fresh.set_visible(entity["first"] == self._upto)

        seen = len(entity["chapters"])
        facts.set_text(
            f"First met in chapter {entity['first'] + 1}  ·  "
            f"seen in {seen} chapter{'s' if seen != 1 else ''}  ·  "
            f"last in chapter {entity['chapters'][-1] + 1}  ·  "
            f"{entity['total']} mentions"
        )

        note.set_text(entity.get("note") or "")
        note.set_visible(bool(entity.get("note")))

        often = entity.get("with") or []
        lead = "Last seen with " if entity.get("note") else "Often with "
        with_whom.set_text(lead + ", ".join(often) if often else "")
        with_whom.set_visible(bool(often))

        strip.show_entity(entity["chapters"], self._upto)

        if getattr(button, "wired", None) != entity["name"]:
            if getattr(button, "handler", None):
                button.disconnect(button.handler)
            button.handler = button.connect(
                "clicked", lambda _b, n=entity["name"]: self.emit("opened", n)
            )
            button.wired = entity["name"]
