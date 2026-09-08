"""Drives the real window and saves what it drew.

A window cannot be reviewed from its source. This opens the reader against a
real book model, walks the views, moves the bookmark, and writes PNGs so the
result can be looked at rather than reasoned about.

Drive what a person touches, not the method behind it: click the rail row,
move the bookmark, type in the search box.

Writes into local.d/smoke/, which every repository here keeps for exactly
this: output nobody reviews, regenerated on every run, and never committed.
The screenshots the README shows are chosen out of it rather than swept up.

Usage:
  uv run python scripts/gui-smoke.py [MODEL.json] [SHOTS_DIR]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ariadne.app.assets import use_bundled_fonts

# Before the toolkit. Pango reads fontconfig once, so a driver that imports gi
# first photographs the system's faces and nothing says the shipped ones were
# missed.
FONTS = use_bundled_fonts()

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import (  # noqa: E402 — after the versions above
    Adw,
    Gio,
    GLib,
    Gtk,
    PangoCairo,
)

from ariadne.app.main import ReaderApplication  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "tests" / "golden" / "model" / "war-and-peace.json"
WINDOW = (1280, 860)

failures = 0


def check(label: str, ok: bool) -> bool:
    global failures
    print(f"{'ok   ' if ok else 'FAIL '} {label}")
    failures += not ok
    return ok


def pump(seconds: float = 0.25) -> None:
    deadline = time.monotonic() + seconds
    context = GLib.MainContext.default()
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)


def snapshot(window: Gtk.Widget, path: Path) -> None:
    paintable = Gtk.WidgetPaintable.new(window)
    width, height = window.get_width(), window.get_height()
    if width <= 1 or height <= 1:
        check(f"{path.name}: the window has a size", False)
        return
    renderer = window.get_native().get_renderer()
    node = None
    for _ in range(15):
        holder = Gtk.Snapshot()
        paintable.snapshot(holder, width, height)
        node = holder.to_node()
        if node is not None:
            break
        pump(0.15)
    if node is None or renderer is None:
        check(f"{path.name}: something painted — is the screen locked?", False)
        return
    renderer.render_texture(node, None).save_to_png(str(path))
    print(f"ok    wrote {path.name} ({width}x{height})")


def drive(app, model, shots: Path) -> None:
    window = app.get_active_window()
    window.set_default_size(*WINDOW)
    pump(1.0)

    check("the window opened", window is not None)
    families = {f.get_name() for f in PangoCairo.FontMap.get_default().list_families()}
    check(f"the shipped faces are loaded ({FONTS})", {"Manrope", "Literata"} <= families)
    snapshot(window, shots / "01-everyone-chapter-1.png")

    window._bookmark.set_chapter(179)
    pump(0.6)
    check("the bookmark moved to chapter 180", window._bookmark.chapter == 179)
    check_layout(window)
    snapshot(window, shots / "02-everyone-chapter-180.png")

    # The four cuts of the cast are chips inside it now, not rail items.
    for key, name in (("people", "03-people"), ("away", "04-away-a-while")):
        window._chips[key].set_active(True)
        pump(0.5)
        check(f"the {key} facet is showing", window._facet == key)
        snapshot(window, shots / f"{name}.png")

    window._chips["everyone"].set_active(True)
    pump(0.3)
    window._searched(_Typed("bezukhov"))
    pump(0.4)
    snapshot(window, shots / "05-search.png")

    window._searched(_Typed(""))
    pump(0.3)

    window._rail.choose("ground")
    pump(0.6)
    check("where you've been proposes settings", window._curation.kept_settings == set())
    quiet(window)
    snapshot(window, shots / "15-ground-proposed.png")

    # The reader rules on a setting the same way they rule on a name.
    window._ground.emit("ruled", window._curation.keep_setting("Moscow"))
    window._ground.emit("ruled", window._curation.keep_setting("Petersburg"))
    window._ground.emit("ruled", window._curation.strike_setting("Alexander"))
    pump(0.6)
    check(
        "kept settings are remembered", window._curation.kept_settings == {"Moscow", "Petersburg"}
    )
    snapshot(window, shots / "16-ground-ruled.png")

    for key, name in (("pace", "09-pace"), ("map", "10-map"), ("warnings", "11-warnings")):
        window._rail.choose(key)
        pump(0.6)
        quiet(window)
        snapshot(window, shots / f"{name}.png")

    window._map.emit("centred", "Pierre")
    pump(0.6)
    check("the map focused on a person", window._focus_on == "Pierre")
    snapshot(window, shots / "12-map-focused.png")

    window._rail.choose("cast")
    window._about.fill(model.get("about") or {})
    window._about.present(window)
    pump(0.6)
    check("about this book opens as a dialog", window._about.get_mapped())
    quiet(window)
    snapshot(window, shots / "13-about.png")
    window._about.close()
    pump(0.3)

    # Open the drawer the way a person does: by the name on a card.
    window._open_drawer("Pierre")
    pump(0.6)
    quiet(window)
    check("the drawer opened on a name", window._split.get_show_sidebar())
    snapshot(window, shots / "07-drawer.png")

    # A ruling rewrites the index, so the whole window has to follow it.
    window._open_drawer("Prince Andrew")
    pump(0.3)
    pairs = window._curation.candidates(window._bookmark.chapter)
    check(f"there are name matches to rule on ({len(pairs)})", bool(pairs))
    snapshot(window, shots / "08-merge-prompt.png")

    # A merge rewrites the index, and everything on screen has to follow it.
    keep, also = window._curation.candidates(window._bookmark.chapter)[0]
    before = len(window._curation.model["entities"])
    window._drawer._ruled(window._curation.merge(keep, also))
    pump(0.6)
    after = len(window._curation.model["entities"])
    check(
        f"merging {also!r} into {keep!r} shrank the cast ({before} to {after})", after == before - 1
    )
    check("undo became available", window._undo.get_sensitive())
    snapshot(window, shots / "14-after-merge.png")

    window._after_ruling(window._curation.undo())
    pump(0.4)
    check("undo restored the cast", len(window._curation.model["entities"]) == before)

    window._bookmark.set_chapter(0)
    pump(0.4)
    window._chips["away"].set_active(True)
    pump(0.4)
    check("away a while is empty at the start", True)
    snapshot(window, shots / "06-away-empty.png")

    # Dark is where people read, and until this redesign the cast strips were
    # drawn in light-mode paper colours there. Photograph it.
    window._chips["everyone"].set_active(True)
    window._shut_drawer()
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    pump(0.5)
    window._bookmark.set_chapter(179)
    pump(0.6)
    check("dark mode is on", window._dark())
    snapshot(window, shots / "17-dark-cast.png")
    window._rail.choose("ground")
    pump(0.6)
    snapshot(window, shots / "18-dark-ground.png")
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT)
    pump(0.3)


def quiet(window) -> None:
    """Clear a toast left over from the step before.

    Several of these frames end up in the README, and a notice about a ruling
    made three steps earlier is not what the picture is of.
    """
    if window._toast is not None:
        window._toast.dismiss()
        window._toast = None
        pump(0.4)


def check_layout(window) -> None:
    """The two numbers the redesign is answerable for.

    Six full-width bands used to stack above the first cast card, which began
    at 373px -- 43% of the window -- before a reader saw the thing the
    application is for. And the axis has to span exactly what the strips span,
    or the plumb line through it is decoration rather than a fact.
    """
    card = first_card(window)
    if card is not None:
        _, top = card.translate_coordinates(window, 0, 0)
        check(f"the first card starts at {top}px, not 373", top < 200)

    strip = first_strip(card) if card is not None else None
    if strip is not None:
        axis_x, _ = window._bookmark.translate_coordinates(window, 0, 0)
        strip_x, _ = strip.translate_coordinates(window, 0, 0)
        widths = (window._bookmark.get_width(), strip.get_width())
        # One pixel is the card's own border, and it is under half a chapter.
        aligned = abs(axis_x - strip_x) <= 1 and abs(widths[0] - widths[1]) <= 2
        check(
            f"the axis and the strips span the same box (axis {axis_x}+{widths[0]}, "
            f"strip {strip_x}+{widths[1]})",
            aligned,
        )


def descend(widget, wanted):
    """First widget of a class, breadth first. GTK gives no query for this."""
    queue = [widget]
    while queue:
        node = queue.pop(0)
        if isinstance(node, wanted):
            return node
        child = node.get_first_child()
        while child is not None:
            queue.append(child)
            child = child.get_next_sibling()
    return None


def first_card(window):
    row = descend(window._cast, Gtk.ListView)
    return descend(row, Gtk.Box) if row is not None else None


def first_strip(card):
    from ariadne.app.presence import PresenceStrip

    return descend(card, PresenceStrip)


class _Typed:
    """The search box's shape, so the handler can be driven without a widget."""

    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text


def main() -> int:
    source = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_MODEL
    shots = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else ROOT / "local.d" / "smoke"
    shots.mkdir(parents=True, exist_ok=True)

    model = json.loads(source.read_text(encoding="utf-8"))
    print(f"      {source.name}: {model['chapters']} chapters, {len(model['entities'])} names")

    app = ReaderApplication(model)
    # An installed Ariadne holding the bus name turns `run` into a remote
    # activation: it wakes the other window, photographs nothing, and returns
    # 0. Drive this process or drive nothing.
    app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)

    def go(_app):
        try:
            drive(app, model, shots)
        except Exception:
            import traceback

            traceback.print_exc()
            globals()["failures"] += 1
        finally:
            app.quit()

    app.connect("activate", lambda a: GLib.idle_add(go, a))
    app.run([])
    check("the run produced screenshots", any(shots.glob("*.png")))
    print(f"\n{failures} check(s) failed")
    return failures


if __name__ == "__main__":
    sys.exit(main())
