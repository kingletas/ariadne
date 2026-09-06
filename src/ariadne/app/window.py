"""The shell: a compact header, the rail, the bookmark, and one content area.

Nothing here reaches into the model directly. Every view is handed the result
of `clip`, which is the only thing that knows where the reader is -- so a view
added later cannot reach past the bookmark by forgetting to.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from ..model.view import (  # noqa: E402
    alongside,
    away_a_while,
    clip,
    matching,
    of_kind,
    often_with,
    ranked,
)
from .bookmark import Bookmark  # noqa: E402
from .cast import CastView  # noqa: E402
from .drawer import WIDTH as DRAWER_WIDTH  # noqa: E402
from .drawer import Drawer  # noqa: E402
from .ground import GroundView  # noqa: E402
from .mapview import MapView  # noqa: E402
from .pace import PaceView  # noqa: E402
from .panels import AboutBook, SinceBookmark, Warnings  # noqa: E402
from .rail import Rail  # noqa: E402

WPM = 250
AWAY_CAP = 25


class ReaderWindow(Adw.ApplicationWindow):
    def __init__(self, application, curation):
        model = curation.model
        super().__init__(application=application, title=model.get("title", "Ariadne"))
        self.set_default_size(1280, 860)
        self._curation = curation
        self._model = model
        self._chapters = model.get("chapters", 1)
        self._view = "everyone"
        self._query = ""
        self._focus_on = None
        self._mark = 0

        root = Adw.ToolbarView()
        root.add_css_class("reader-root")
        root.add_top_bar(self._header())

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._bookmark = Bookmark(self._chapters)
        self._bookmark.connect("moved", self._moved)
        body.append(self._bookmark)

        split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._rail = Rail()
        self._rail.connect("chose", self._chose)
        split.append(self._rail)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)

        self._about = AboutBook()
        about_holder = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        about_holder.add_css_class("boxed-list")
        about_holder.set_margin_start(24)
        about_holder.set_margin_end(24)
        about_holder.set_margin_top(10)
        about_holder.append(self._about)
        content.append(about_holder)

        self._since = SinceBookmark()
        content.append(self._since)

        self._search = self._search_row()
        content.append(self._search)

        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._cast = CastView()
        self._cast.connect("chapter", lambda _c, i: self._bookmark.set_chapter(i))
        self._cast.connect("opened", lambda _c, n: self._open_drawer(n))
        self._pace = PaceView()
        self._pace.connect("go", lambda _p, c: self._bookmark.set_chapter(c))
        self._map = MapView()
        self._map.connect("centred", lambda _m, n: self._focus_map(n))
        self._ground = GroundView(self._curation)
        self._ground.connect("go", lambda _g, c: self._bookmark.set_chapter(c))
        self._ground.connect("ruled", lambda _g, m: self._after_ruling(m))
        self._warnings = Warnings()

        self._stack.add_named(self._cast, "cast")
        self._stack.add_named(self._pace, "pace")
        self._stack.add_named(self._map, "map")
        self._stack.add_named(self._ground, "ground")
        self._stack.add_named(self._warnings, "warnings")
        content.append(self._stack)
        self._drawer = Drawer(self._curation)
        self._drawer.connect("closed", lambda _d: self._shut_drawer())
        self._drawer.connect("go", lambda _d, c: self._bookmark.set_chapter(c))
        self._drawer.connect("acted", lambda _d, m: self._after_ruling(m))
        self._drawer.connect("opened", lambda _d, n: self._open_drawer(n))

        self._split = Adw.OverlaySplitView()
        self._split.set_sidebar_position(Gtk.PackType.END)
        self._split.set_sidebar(self._drawer)
        self._split.set_content(content)
        self._split.set_max_sidebar_width(DRAWER_WIDTH)
        self._split.set_min_sidebar_width(DRAWER_WIDTH)
        self._split.set_collapsed(False)
        self._split.set_show_sidebar(False)
        split.append(self._split)

        body.append(split)
        root.set_content(body)
        self.set_content(root)

        self._shortcuts()
        # Where they left off, so "since your bookmark" is a real span rather
        # than the whole book measured from chapter one.
        self._mark = self._curation.position
        self._bookmark.set_chapter(self._mark)
        self._refresh(self._mark)

    def _shortcuts(self) -> None:
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._pressed)
        self.add_controller(keys)

    def _pressed(self, _controller, keyval, _code, state) -> bool:
        from gi.repository import Gdk

        control = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if keyval == Gdk.KEY_Escape and self._split.get_show_sidebar():
            self._shut_drawer()
            return True
        if control and keyval == Gdk.KEY_z:
            self._after_ruling(self._curation.undo())
            return True
        if control and keyval == Gdk.KEY_f:
            self._search.get_first_child().grab_focus()
            return True
        if keyval in (Gdk.KEY_bracketleft,):
            self._bookmark.set_chapter(self._bookmark.chapter - 1)
            return True
        if keyval in (Gdk.KEY_bracketright,):
            self._bookmark.set_chapter(self._bookmark.chapter + 1)
            return True
        return False

    # --- the drawer ---

    def _open_drawer(self, name: str) -> None:
        self._drawer.show_name(self._model, name, self._bookmark.chapter)
        self._split.set_show_sidebar(True)

    def _shut_drawer(self) -> None:
        self._split.set_show_sidebar(False)

    def _after_ruling(self, message: str) -> None:
        """A ruling rewrites the index, so everything on screen is rebuilt."""
        self._model = self._curation.model
        self._refresh(self._bookmark.chapter)
        self._bookmark.announce(message)
        self._undo.set_sensitive(self._curation.can_undo)
        self._undo.set_tooltip_text(
            f"Undo: {self._curation.last_action}" if self._curation.can_undo else "Nothing to undo"
        )
        self._saved.set_text("Saved locally" if self._curation.saves_to else "Not saved")

    # --- chrome ---

    def _header(self) -> Adw.HeaderBar:
        bar = Adw.HeaderBar()
        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name, author = self._title_and_author()
        heading = Gtk.Label(label=name, xalign=0.5)
        heading.add_css_class("book-title")
        title.append(heading)
        if author:
            by = Gtk.Label(label=author, xalign=0.5)
            by.add_css_class("book-author")
            title.append(by)
        bar.set_title_widget(title)

        self._progress = Gtk.Label()
        self._progress.add_css_class("reading-position")

        self._undo = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        self._undo.add_css_class("flat")
        self._undo.set_sensitive(False)
        self._undo.connect("clicked", lambda _b: self._after_ruling(self._curation.undo()))

        self._saved = Gtk.Label(label="Saved locally")
        self._saved.add_css_class("saved-locally")
        self._saved.set_tooltip_text(
            self._curation.saves_to or "Nothing to save to — opened without a book file"
        )

        bar.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic"))
        bar.pack_end(self._undo)
        bar.pack_end(self._progress)
        bar.pack_start(self._saved)
        return bar

    def _title_and_author(self):
        raw = self._model.get("title", "")
        for sep in (" — ", " -- "):
            if sep in raw:
                name, author = raw.split(sep, 1)
                return name.strip(), author.strip()
        return raw, ""

    def _search_row(self) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_top(12)
        row.set_margin_start(24)
        row.set_margin_end(24)
        entry = Gtk.SearchEntry(hexpand=True)
        entry.set_placeholder_text("Search names or places")
        entry.connect("search-changed", self._searched)
        row.append(entry)
        return row

    # --- what the bookmark decides ---

    def _moved(self, _bookmark, index: int) -> None:
        self._refresh(index)
        self._curation.remember_position(index)

    def _chose(self, _rail, key: str) -> None:
        self._view = key
        self._refresh(self._bookmark.chapter)

    def _searched(self, entry) -> None:
        self._query = entry.get_text()
        self._refresh(self._bookmark.chapter)

    def _focus_map(self, name: str) -> None:
        self._focus_on = name
        self._rail.choose("map")

    def _dark(self) -> bool:
        return Adw.StyleManager.get_default().get_dark()

    def _refresh(self, upto: int) -> None:
        met = clip(self._model, upto)
        self._progress.set_text(self._read_so_far(upto))
        self._about.fill(self._model.get("about") or {})
        if self._split.get_show_sidebar() and self._drawer.name:
            self._drawer.show_name(self._model, self._drawer.name, upto)

        candidates = len(self._curation.candidates(upto))
        self._since.show_change(self._model, self._mark, upto, candidates)
        self._rail.set_badge("warnings", self._visible_warnings(upto))

        showing_cast = self._view in ("everyone", "people", "places", "away")
        self._search.set_visible(showing_cast)

        if self._view == "pace":
            self._stack.set_visible_child_name("pace")
            self._pace.show_pace(self._model.get("pace") or [], upto, self._dark())
            return
        if self._view == "ground":
            self._stack.set_visible_child_name("ground")
            self._ground.show_ground(self._model, upto, self._dark())
            return
        if self._view == "map":
            self._stack.set_visible_child_name("map")
            self._map.show_map(self._model, upto, self._focus_on, self._dark())
            return
        if self._view == "warnings":
            self._stack.set_visible_child_name("warnings")
            self._warnings.show_warnings(self._model.get("warn") or {}, upto)
            return

        self._stack.set_visible_child_name("cast")
        if self._view == "away":
            rows = away_a_while(met, upto, self._model.get("pace") or [])
            # Capped, and the cap is stated. A list of everybody who qualifies
            # is the noise this view exists to remove.
            shown, hidden = rows[:AWAY_CAP], max(0, len(rows) - AWAY_CAP)
            rows = shown
            summary = f"{len(rows)} you have not seen for a while"
            if hidden:
                summary += f" · {hidden} more below the fold"
            empty = "Nobody you have lost track of yet."
        elif self._view in ("people", "places"):
            rows = ranked(of_kind(met, "person" if self._view == "people" else "place"))
            summary = f"{len(rows)} of the {len(met)} you have met"
            empty = f"No {self._view} identified yet."
        else:
            rows = ranked(met)
            fresh = sum(1 for e in met if e["first"] == upto)
            summary = (
                f"{len(met)} of {len(self._model['entities'])} met · {fresh} new in this chapter"
            )
            empty = "Nobody yet — you are at the start."

        if self._query:
            rows = matching(rows, self._query)
            if not rows:
                empty = "No name here matches that."

        for entity in rows:
            if self._view == "away":
                # Who was there the last time, not who they usually keep company
                # with -- when you have lost somebody those are different questions.
                entity["with"] = alongside(self._model, entity["name"], entity["chapters"][-1])
                entity["note"] = (
                    f"Not seen for {entity['gone']} chapters · "
                    f"{entity['since_words'] // 1000}k words, longer than usual for them"
                )
            else:
                entity["with"] = often_with(self._model, entity["name"], upto)
                entity.pop("note", None)
        self._cast.show_entities(rows, upto, summary, empty)

    def _visible_warnings(self, upto: int) -> int:
        """Only ones whose trigger has been reached, and only ever a count.

        A badge that grew with severity would tell the reader how bad the thing
        is, which is the one thing a warning here must not do until they open it.
        """
        return sum(
            len(rows) for at, rows in (self._model.get("warn") or {}).items() if int(at) <= upto
        )

    def _read_so_far(self, upto: int) -> str:
        """Words behind the bookmark only. What is left is the book's business."""
        pace = self._model.get("pace") or []
        words = sum(row["w"] for row in pace[: upto + 1]) if pace else 0
        share = (upto + 1) / self._chapters * 100
        minutes = words // WPM
        spent = f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"
        return f"Chapter {upto + 1} of {self._chapters} · {share:.0f}% · {words:,} words · {spent}"
