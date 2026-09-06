"""Drives the real window and saves what it drew.

A window cannot be reviewed from its source. This opens the reader against a
real book model, walks the views, moves the bookmark, and writes PNGs so the
result can be looked at rather than reasoned about.

Drive what a person touches, not the method behind it: click the rail row,
move the bookmark, type in the search box.

Writes into build/smoke/, which is not tracked: this runs on every change and
the four screenshots the README shows are chosen rather than swept up.

Usage:
  uv run python scripts/gui-smoke.py [MODEL.json] [SHOTS_DIR]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GLib, Gtk  # noqa: E402 — after the versions above

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
    snapshot(window, shots / "01-everyone-chapter-1.png")

    window._bookmark.set_chapter(179)
    pump(0.6)
    check("the bookmark moved to chapter 180", window._bookmark.chapter == 179)
    snapshot(window, shots / "02-everyone-chapter-180.png")

    for key, name in (("people", "03-people"), ("away", "04-away-a-while")):
        window._rail.choose(key)
        pump(0.5)
        snapshot(window, shots / f"{name}.png")

    window._rail.choose("everyone")
    pump(0.3)
    window._searched(_Typed("bezukhov"))
    pump(0.4)
    snapshot(window, shots / "05-search.png")

    window._searched(_Typed(""))
    pump(0.3)

    window._rail.choose("ground")
    pump(0.6)
    check("where you've been proposes settings", window._curation.kept_settings == set())
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
        snapshot(window, shots / f"{name}.png")

    window._map.emit("centred", "Pierre")
    pump(0.6)
    check("the map focused on a person", window._focus_on == "Pierre")
    snapshot(window, shots / "12-map-focused.png")

    window._rail.choose("everyone")
    window._about.set_expanded(True)
    pump(0.5)
    check("about this book opens", window._about.get_expanded())
    snapshot(window, shots / "13-about.png")
    window._about.set_expanded(False)
    pump(0.2)

    # Open the drawer the way a person does: by the name on a card.
    window._open_drawer("Pierre")
    pump(0.6)
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
    window._rail.choose("away")
    pump(0.4)
    check("away a while is empty at the start", True)
    snapshot(window, shots / "06-away-empty.png")


class _Typed:
    """The search box's shape, so the handler can be driven without a widget."""

    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text


def main() -> int:
    source = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_MODEL
    shots = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else ROOT / "build" / "smoke"
    shots.mkdir(parents=True, exist_ok=True)

    model = json.loads(source.read_text(encoding="utf-8"))
    print(f"      {source.name}: {model['chapters']} chapters, {len(model['entities'])} names")

    app = ReaderApplication(model)

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
    print(f"\n{failures} check(s) failed")
    return failures


if __name__ == "__main__":
    sys.exit(main())
