"""The shell: a compact header, the rail, the axis, and one content area.

Nothing here reaches into the model directly. Every view is handed the result
of `clip`, which is the only thing that knows where the reader is -- so a view
added later cannot reach past the bookmark by forgetting to.

The axis is the bookmark. It sits at the top of the content column, spans
exactly what the views span, and is pinned: every view owns its own scroller
inside the stack, so the axis stays put while the list under it moves.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk  # noqa: E402

from ..model.view import (  # noqa: E402
    alongside,
    away_a_while,
    clip,
    matching,
    of_kind,
    often_with,
    ranked,
)
from . import axis, preferences, tokens  # noqa: E402
from .bookmark import Bookmark  # noqa: E402
from .cast import CastView  # noqa: E402
from .drawer import WIDTH as DRAWER_WIDTH  # noqa: E402
from .drawer import Drawer  # noqa: E402
from .ground import GroundView  # noqa: E402
from .mapview import MapView  # noqa: E402
from .pace import PaceView  # noqa: E402
from .panels import AboutBook, Warnings, since_bookmark  # noqa: E402
from .plates import PlateBand, PlatesView  # noqa: E402
from .rail import FACETS, Rail  # noqa: E402

WPM = 250
AWAY_CAP = 25

# Long enough to read, short enough not to become furniture.
ANNOUNCEMENT_SECONDS = 6
# The one that carries an action gets longer, because reaching for a button is
# slower than reading a line. It still goes: a notice that waits to be
# dismissed is furniture, and it sat over three different views for an hour.
SINCE_SECONDS = 12
# The bookmark has to be still this long before "since your bookmark" is said,
# so dragging across two hundred chapters is one sentence rather than two
# hundred of them.
SETTLED_MS = 1200
# What makes the shared axis legible rather than merely true -- and it crosses
# everything on the way down, which is a permanent cost for an occasional
# benefit. So it is drawn while the bookmark is moving, which is when the
# alignment is the thing being looked at, and it goes when the reader stops.
#
# It was a 2px rule at 38%, always on, and read as a divider through the cards
# rather than a guide behind them.
PLUMB_ALPHA = 0.28
PLUMB_WIDTH = 1
# Long enough to see where everything lined up, short enough not to linger.
PLUMB_LINGER_MS = 1400


class ReaderWindow(Adw.ApplicationWindow):
    def __init__(self, application, curation):
        model = curation.model
        super().__init__(application=application, title=model.get("title", "Ariadne"))
        self.set_default_size(1280, 860)
        self._curation = curation
        self._model = model
        self._chapters = model.get("chapters", 1)
        self._view = "cast"
        self._facet = "everyone"
        self._query = ""
        self._focus_on = None
        self._mark = 0
        self._settling = 0
        self._said = ""
        self._toast = None
        self._warned = False
        self._moving = 0

        root = Adw.ToolbarView()
        root.add_css_class("reader-root")
        root.add_top_bar(self._header())

        split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._rail = Rail()
        self._rail.connect("chose", self._chose)
        split.append(self._rail)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)

        self._bookmark = Bookmark(self._chapters)
        self._bookmark.connect("moved", self._moved)
        content.append(self._bookmark)

        # Registered with the axis like everything else, so the pictures sit
        # under the chapters they belong to rather than in a list of their own.
        self._plates = self._model.get("plates") or []
        self._band = PlateBand()
        self._band.connect("go", lambda _b, c: self._bookmark.set_chapter(c))
        self._band.set_visible(bool(self._plates))
        content.append(self._band)

        self._about = AboutBook()
        self._facets = self._facet_row()
        content.append(self._facets)

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
        self._gallery = PlatesView()
        self._gallery.connect("go", lambda _g, c: self._bookmark.set_chapter(c))

        self._stack.add_named(self._gallery, "plates")
        self._stack.add_named(self._cast, "cast")
        self._stack.add_named(self._pace, "pace")
        self._stack.add_named(self._map, "map")
        self._stack.add_named(self._ground, "ground")
        self._stack.add_named(self._warnings, "warnings")
        content.append(self._plumbed(self._stack))

        self._toasts = Adw.ToastOverlay()
        self._toasts.set_child(content)

        self._drawer = Drawer(self._curation)
        self._drawer.connect("closed", lambda _d: self._shut_drawer())
        self._drawer.connect("go", lambda _d, c: self._bookmark.set_chapter(c))
        self._drawer.connect("acted", lambda _d, m: self._after_ruling(m))
        self._drawer.connect("opened", lambda _d, n: self._open_drawer(n))

        self._split = Adw.OverlaySplitView()
        self._split.set_sidebar_position(Gtk.PackType.END)
        self._split.set_sidebar(self._drawer)
        self._split.set_content(self._toasts)
        self._split.set_max_sidebar_width(DRAWER_WIDTH)
        self._split.set_min_sidebar_width(DRAWER_WIDTH)
        self._split.set_collapsed(False)
        self._split.set_show_sidebar(False)
        split.append(self._split)

        root.set_content(split)
        self.set_content(root)

        self._shortcuts()
        # Where they left off, so "since your bookmark" is a real span rather
        # than the whole book measured from chapter one.
        self._mark = self._curation.position
        self._bookmark.set_chapter(self._mark)
        self._refresh(self._mark)

    # --- the plumb line ---

    def _plumbed(self, child: Gtk.Widget) -> Gtk.Overlay:
        """One line from under the axis to the foot of the content column."""
        overlay = Gtk.Overlay()
        overlay.set_child(child)
        self._plumb = Gtk.DrawingArea()
        self._plumb.set_draw_func(self._draw_plumb)
        # It is decoration, and decoration that eats clicks is a defect.
        self._plumb.set_can_target(False)
        overlay.add_overlay(self._plumb)
        return overlay

    def _draw_plumb(self, _area, cr, width, height, *_):
        # Only over views whose x means a chapter. The map draws associations
        # and the gallery draws pictures; a line down either is decoration
        # pretending to line up with something.
        if self._view in ("map", "plates"):
            return
        if not (self._moving or preferences.plumb()):
            return
        palette = tokens.DARK if self._dark() else tokens.LIGHT
        span = max(1, width - 2 * axis.INSET)
        x = axis.INSET + axis.x_for(self._bookmark.chapter, span, self._chapters)
        cr.set_source_rgba(*tokens.rgb(palette["accent"]), PLUMB_ALPHA)
        cr.rectangle(x - PLUMB_WIDTH / 2, 0, PLUMB_WIDTH, height)
        cr.fill()

    # --- shortcuts ---

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
            self._search.grab_focus()
            return True
        if control and keyval == Gdk.KEY_g:
            self._ask_chapter()
            return True
        if keyval in (Gdk.KEY_bracketleft,):
            self._bookmark.set_chapter(self._bookmark.chapter - 1)
            return True
        if keyval in (Gdk.KEY_bracketright,):
            self._bookmark.set_chapter(self._bookmark.chapter + 1)
            return True
        return False

    def _ask_chapter(self) -> None:
        """Type a chapter. The axis drags, and dragging cannot cross 200 of them.

        This is what the spin button was for; it left the strip with the rest of
        the panel, and losing the exact jump with it would have been a trade
        rather than a simplification.
        """
        spin = Gtk.SpinButton.new_with_range(1, self._chapters, 1)
        spin.set_value(self._bookmark.chapter + 1)
        spin.set_numeric(True)
        spin.set_activates_default(True)

        ask = Adw.AlertDialog(heading="Go to chapter", body=f"1 to {self._chapters}")
        ask.set_extra_child(spin)
        ask.add_response("cancel", "Cancel")
        ask.add_response("go", "Go")
        ask.set_default_response("go")
        ask.set_close_response("cancel")
        ask.connect(
            "response",
            lambda _d, answer: (
                self._bookmark.set_chapter(int(spin.get_value()) - 1) if answer == "go" else None
            ),
        )
        ask.present(self)

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
        self._announce(message)
        self._undo.set_sensitive(self._curation.can_undo)
        self._undo.set_tooltip_text(
            f"Undo: {self._curation.last_action}" if self._curation.can_undo else "Nothing to undo"
        )
        self._say_saved()

    # --- what the window says ---

    def _announce(self, message: str) -> None:
        """A ruling is an ordinary act, not an alarm."""
        if message:
            self._say(Adw.Toast(title=message, timeout=ANNOUNCEMENT_SECONDS))

    def _say(self, toast) -> None:
        """One at a time, and said out loud as well as shown.

        The overlay queues, and a queue of rulings means the third one is read
        six seconds after the reader stopped caring -- so a new toast replaces
        the one before it.

        The announcement is explicit because `Adw.Toast` carries no accessible
        property and nothing here can prove the platform makes one. This is the
        behaviour the bookmark's own status line had, kept rather than assumed.
        """
        if self._toast is not None:
            self._toast.dismiss()
        self._toast = toast
        self._toasts.add_toast(toast)
        self._toasts.announce(toast.get_title(), Gtk.AccessibleAnnouncementPriority.MEDIUM)

    def _tell_since(self, message: str) -> None:
        """Once, when the reader has settled, and never as a running commentary.

        It is a greeting about the session -- what happened while they were
        away -- so it is said when they first move on from where they left off
        and not again. Repeating it every chapter would train them past it.
        """
        if not message or message == self._said:
            return
        self._said = message
        toast = Adw.Toast(title=message, timeout=SINCE_SECONDS)
        pairs = self._curation.candidates(self._bookmark.chapter)
        if pairs:
            toast.set_button_label("Rule on them")
            toast.connect("button-clicked", lambda _t: self._rule_on(pairs[0][0]))
        self._say(toast)

    def _rule_on(self, name: str) -> None:
        """A notice about work to do that does not take you to the work is a
        notification. This takes them to it."""
        self._rail.choose("cast")
        self._open_drawer(name)

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

        # The position is also the way to type a chapter, which is the one
        # thing the spin button did that the axis cannot.
        self._progress = Gtk.Button()
        self._progress.add_css_class("flat")
        self._progress.add_css_class("position-button")
        self._progress.set_tooltip_text("Go to a chapter (Ctrl+G)")
        self._position = Gtk.Label()
        self._position.add_css_class("reading-position")
        self._progress.set_child(self._position)
        self._progress.connect("clicked", lambda _b: self._ask_chapter())

        self._undo = Gtk.Button.new_from_icon_name("edit-undo-symbolic")
        self._undo.add_css_class("flat")
        self._undo.set_sensitive(False)
        self._undo.connect("clicked", lambda _b: self._after_ruling(self._curation.undo()))

        self._saved = Gtk.Label()
        self._saved.add_css_class("saved-locally")
        self._say_saved()

        bar.pack_end(self._menu())
        bar.pack_end(self._undo)
        bar.pack_end(self._progress)
        bar.pack_start(self._saved)
        return bar

    def _menu(self) -> Gtk.MenuButton:
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu.set_tooltip_text("Menu")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("menu-popover")
        box.append(self._appearance())

        about = Gtk.Button(label="About this book…")
        about.add_css_class("flat")
        about.set_child(Gtk.Label(label="About this book…", xalign=0))
        about.connect("clicked", lambda _b: self._show_about(menu))
        box.append(about)
        popover = Gtk.Popover()
        popover.set_child(box)
        menu.set_popover(popover)
        return menu

    def _appearance(self) -> Gtk.Box:
        """Follow the system, or override it. Night is when people read.

        The system is the default and stays first: it is what every other
        application on the machine does, and most people never touch this.
        """
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        label = Gtk.Label(label="Appearance", xalign=0)
        label.add_css_class("menu-heading")
        wrap.append(label)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add_css_class("linked")
        row.add_css_class("appearance")
        self._themes: dict[str, Gtk.ToggleButton] = {}
        first = None
        for key, text in (("system", "System"), ("light", "Light"), ("dark", "Dark")):
            button = Gtk.ToggleButton(label=text, hexpand=True)
            if first is None:
                first = button
            else:
                button.set_group(first)
            button.connect("toggled", self._themed, key)
            row.append(button)
            self._themes[key] = button
        self._themes[preferences.theme()].set_active(True)
        wrap.append(row)

        guide = Gtk.CheckButton(label="Always show the bookmark line")
        guide.add_css_class("menu-check")
        guide.set_active(preferences.plumb())
        guide.set_tooltip_text(
            "The line shows while you move the bookmark, so you can see that "
            "every strip is on the same scale. Tick this to keep it there."
        )
        guide.connect("toggled", self._plumbed_toggle)
        wrap.append(guide)

        line = Gtk.Separator()
        line.set_margin_top(4)
        wrap.append(line)
        return wrap

    def _plumbed_toggle(self, button: Gtk.CheckButton) -> None:
        preferences.set_plumb(button.get_active())
        self._plumb.queue_draw()

    def _themed(self, button: Gtk.ToggleButton, key: str) -> None:
        if not button.get_active() or preferences.theme() == key:
            return
        # Imported here and not at the top: `main` builds this window, so a
        # module-level import would close the circle.
        from .main import apply_theme

        preferences.set_theme(key)
        apply_theme(key)
        # The strips and bands are drawn rather than styled, so the stylesheet
        # reloading underneath them is not enough -- they hold the palette they
        # were last painted with until something asks them to paint again.
        self._refresh(self._bookmark.chapter)

    def _show_about(self, menu: Gtk.MenuButton) -> None:
        menu.popdown()
        self._about.fill(self._model.get("about") or {})
        self._about.present(self)

    def _say_saved(self) -> None:
        """What the file actually did, never what was intended.

        This label said "Saved locally" on the strength of a path existing. A
        book opened from a removable drive through the Flatpak portal could not
        be written to at all, and the label said it had been for an hour.
        """
        trouble = self._curation.trouble
        if not self._curation.saves_to:
            self._saved.set_text("Not saved")
            self._saved.set_tooltip_text("Opened without a book file, so there is nowhere to save")
        elif trouble:
            self._saved.set_text("Cannot save")
            self._saved.set_tooltip_text(
                f"Nothing is being written to {self._curation.saves_to}\n\n{trouble}"
            )
        else:
            self._saved.set_text("Saved locally")
            self._saved.set_tooltip_text(self._curation.saves_to)
        self._saved.remove_css_class("cannot-save")
        if trouble and self._curation.saves_to:
            self._saved.add_css_class("cannot-save")
            self._warn_once(trouble)

    def _warn_once(self, trouble: str) -> None:
        """Said the first time and not again. A reader who has been told once
        and gone on reading has decided; repeating it every chapter is noise."""
        if self._warned:
            return
        self._warned = True
        toast = Adw.Toast(
            title="Your rulings are not being saved — this book is somewhere Ariadne cannot write",
            timeout=0,
        )
        self._say(toast)

    def _title_and_author(self):
        raw = self._model.get("title", "")
        for sep in (" — ", " -- "):
            if sep in raw:
                name, author = raw.split(sep, 1)
                return name.strip(), author.strip()
        return raw, ""

    def _facet_row(self) -> Gtk.Box:
        """The four cuts of the cast, and the search that filters whichever is on."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.add_css_class("facets")
        row.set_margin_top(8)
        row.set_margin_start(axis.INSET)
        row.set_margin_end(axis.INSET)

        self._chips: dict[str, Gtk.ToggleButton] = {}
        first = None
        for key, text in FACETS:
            chip = Gtk.ToggleButton(label=text)
            chip.add_css_class("chip")
            if first is None:
                first = chip
            else:
                chip.set_group(first)
            chip.connect("toggled", self._faceted, key)
            row.append(chip)
            self._chips[key] = chip
        self._chips["everyone"].set_active(True)

        self._search = Gtk.SearchEntry(hexpand=True, halign=Gtk.Align.END)
        self._search.set_placeholder_text("Search names or places")
        self._search.set_max_width_chars(28)
        self._search.connect("search-changed", self._searched)
        row.append(self._search)
        return row

    def _faceted(self, chip: Gtk.ToggleButton, key: str) -> None:
        if not chip.get_active() or key == self._facet:
            return
        self._facet = key
        self._refresh(self._bookmark.chapter)

    # --- what the bookmark decides ---

    def _moved(self, _bookmark, index: int) -> None:
        self._show_plumb()
        self._refresh(index)
        self._curation.remember_position(index)

    def _show_plumb(self) -> None:
        """Draw the line while the bookmark is moving, and stop when it stops."""
        if self._moving:
            GLib.source_remove(self._moving)
        self._moving = GLib.timeout_add(PLUMB_LINGER_MS, self._hide_plumb)
        self._plumb.queue_draw()

    def _hide_plumb(self) -> bool:
        self._moving = 0
        self._plumb.queue_draw()
        return False

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
        dark = self._dark()
        met = clip(self._model, upto)
        self._position.set_text(self._read_so_far(upto))
        self._bookmark.set_dark(dark)
        self._plumb.queue_draw()
        if self._split.get_show_sidebar() and self._drawer.name:
            self._drawer.show_name(self._model, self._drawer.name, upto)

        self._settle(upto)
        self._rail.set_badge("warnings", self._visible_warnings(upto))
        self._rail.offer("plates", bool(self._plates))
        self._facets.set_visible(self._view == "cast")
        if self._plates:
            self._band.show_plates(self._plates, upto, self._chapters, dark)

        if self._view == "plates":
            self._stack.set_visible_child_name("plates")
            self._gallery.show_plates(self._plates, upto, self._chapters)
            return

        if self._view == "pace":
            self._stack.set_visible_child_name("pace")
            self._pace.show_pace(self._model.get("pace") or [], upto, self._chapters, dark)
            return
        if self._view == "ground":
            self._stack.set_visible_child_name("ground")
            self._ground.show_ground(self._model, upto, self._chapters, dark)
            return
        if self._view == "map":
            self._stack.set_visible_child_name("map")
            self._map.show_map(self._model, upto, self._focus_on, dark)
            return
        if self._view == "warnings":
            self._stack.set_visible_child_name("warnings")
            self._warnings.show_warnings(self._model.get("warn") or {}, upto)
            return

        self._stack.set_visible_child_name("cast")
        rows, summary, empty = self._cast_rows(met, upto)
        if self._query:
            rows = matching(rows, self._query)
            if not rows:
                empty = "No name here matches that."
        for entity in rows:
            self._describe(entity, upto)
        self._cast.show_entities(rows, upto, self._chapters, summary, empty, dark)

    def _cast_rows(self, met, upto):
        if self._facet == "away":
            rows = away_a_while(met, upto, self._model.get("pace") or [])
            # Capped, and the cap is stated. A list of everybody who qualifies
            # is the noise this view exists to remove.
            hidden = max(0, len(rows) - AWAY_CAP)
            rows = rows[:AWAY_CAP]
            summary = f"{len(rows)} you have not seen for a while"
            if hidden:
                summary += f" · {hidden} more below the fold"
            return rows, summary, "Nobody you have lost track of yet."
        if self._facet in ("people", "places"):
            kind = "person" if self._facet == "people" else "place"
            rows = ranked(of_kind(met, kind))
            return (
                rows,
                f"{len(rows)} of the {len(met)} you have met",
                f"No {self._facet} identified yet.",
            )
        rows = ranked(met)
        fresh = sum(1 for e in met if e["first"] == upto)
        summary = f"{len(met)} of {len(self._model['entities'])} met · {fresh} new in this chapter"
        return rows, summary, "Nobody yet — you are at the start."

    def _describe(self, entity, upto: int) -> None:
        if self._facet == "away":
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

    def _settle(self, upto: int) -> None:
        """Wait for the bookmark to stop before saying what changed."""
        if self._settling:
            GLib.source_remove(self._settling)
            self._settling = 0
        if upto <= self._mark:
            return
        self._settling = GLib.timeout_add(SETTLED_MS, self._settled, upto)

    def _settled(self, upto: int) -> bool:
        self._settling = 0
        candidates = len(self._curation.candidates(upto))
        self._tell_since(since_bookmark(self._model, self._mark, upto, candidates))
        return False

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
