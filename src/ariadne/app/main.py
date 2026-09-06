"""The application object: one window over one book."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gtk  # noqa: E402

from . import tokens  # noqa: E402
from .curation import Curation  # noqa: E402
from .welcome import Welcome  # noqa: E402
from .window import ReaderWindow  # noqa: E402

_PROVIDER = None

APP_ID = "com.kingletas.Ariadne"


class ReaderApplication(Adw.Application):
    """One window. A book if it was named, and a way to pick one if not."""

    def __init__(self, model: dict | None = None, undecided=None, sidecar: str | None = None):
        super().__init__(application_id=APP_ID)
        self._curation = None
        if model is not None:
            pristine = dict(model)
            if undecided is not None:
                pristine["entities"] = undecided
            self._curation = Curation(pristine, sidecar)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)
        manager = Adw.StyleManager.get_default()
        load_styles(manager)
        manager.connect("notify::dark", lambda m, _p: load_styles(m))

    def do_activate(self) -> None:
        window = self.get_active_window()
        if window is not None:
            window.present()
            return
        if self._curation is None:
            self._welcome().present()
            return
        ReaderWindow(self, self._curation).present()

    def _welcome(self):
        window = Welcome(self)
        window.connect("chosen", self._open)
        return window

    def _open(self, welcome, path: str) -> None:
        """Read the book the person picked, or say why it cannot be read.

        A refusal here is the useful answer rather than a failure -- Ariadne
        refuses by name, and the name is what tells somebody their book has no
        chapter convention it can find.
        """
        from ..assemble import open_book
        from ..core.refusal import Refusal

        try:
            model, undecided, sidecar = open_book(path)
        except Refusal as why:
            welcome.explain(str(why))
            return
        except Exception as why:  # noqa: BLE001 — reported, never swallowed
            welcome.explain(f"{type(why).__name__}: {why}")
            return

        pristine = dict(model)
        pristine["entities"] = undecided
        self._curation = Curation(pristine, sidecar)
        reader = ReaderWindow(self, self._curation)
        reader.present()
        welcome.close()


def load_styles(manager=None) -> None:
    """The reading profile, over whatever the system theme is.

    GTK 4.14 has no CSS `var()`, so the whole palette is resolved into
    `@define-color` and the sheet is rebuilt when the system flips between
    light and dark rather than switched with a selector.

    A display is absent when the app is driven headless, and that is not an
    error -- every widget still has to build.
    """
    display = Gdk.Display.get_default()
    if display is None:
        return
    manager = manager or Adw.StyleManager.get_default()
    palette = tokens.DARK if manager.get_dark() else tokens.LIGHT

    global _PROVIDER
    if _PROVIDER is not None:
        Gtk.StyleContext.remove_provider_for_display(display, _PROVIDER)
    _PROVIDER = Gtk.CssProvider()
    _PROVIDER.load_from_string(tokens.stylesheet(palette))
    Gtk.StyleContext.add_provider_for_display(
        display, _PROVIDER, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def run(
    model: dict | None = None,
    undecided=None,
    sidecar: str | None = None,
    argv: list[str] | None = None,
) -> int:
    return ReaderApplication(model, undecided, sidecar).run(argv or [])
