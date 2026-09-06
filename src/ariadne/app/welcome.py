"""What opens when nobody named a book.

Launching from an applications menu passes no argument, so this is the first
thing most people will ever see. Printing usage to a terminal that is not there
and exiting — which is what it used to do — reads as the application being
broken.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GObject, Gtk  # noqa: E402

READABLE = (
    ("Books", ["*.epub", "*.docx", "*.txt", "*.md"]),
    ("EPUB", ["*.epub"]),
    ("Word documents", ["*.docx"]),
    ("Plain text", ["*.txt", "*.md"]),
)


class Welcome(Adw.ApplicationWindow):
    """Emits `chosen` with a path, or `failed` with a reason to show."""

    __gsignals__ = {
        "chosen": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, application):
        super().__init__(application=application, title="Ariadne")
        self.set_default_size(720, 520)

        root = Adw.ToolbarView()
        root.add_css_class("reader-root")
        root.add_top_bar(Adw.HeaderBar())

        page = Adw.StatusPage()
        page.set_icon_name("document-open-symbolic")
        page.set_title("Open a book you own")
        page.set_description(
            "Ariadne reads the file, works out who appears in which chapter, and "
            "shows you nothing past the bookmark you set.\n\n"
            "An EPUB, a Word document, a folder of Markdown, or plain text. "
            "It never downloads a book and keeps no library of its own."
        )

        buttons = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER
        )
        open_file = Gtk.Button(label="Open a book…")
        open_file.add_css_class("suggested-action")
        open_file.add_css_class("pill")
        open_file.connect("clicked", lambda _b: self._pick_file())
        buttons.append(open_file)

        open_folder = Gtk.Button(label="Open a folder of Markdown…")
        open_folder.add_css_class("pill")
        open_folder.connect("clicked", lambda _b: self._pick_folder())
        buttons.append(open_folder)

        page.set_child(buttons)
        root.set_content(page)
        self.set_content(root)

        self._banner = None

    # --- choosing ---

    def _filters(self) -> Gio.ListStore:
        filters = Gio.ListStore.new(Gtk.FileFilter)
        for name, patterns in READABLE:
            f = Gtk.FileFilter()
            f.set_name(name)
            for pattern in patterns:
                f.add_pattern(pattern)
            filters.append(f)
        return filters

    def _pick_file(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Open a book")
        dialog.set_filters(self._filters())
        dialog.open(self, None, self._picked)

    def _pick_folder(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Open a folder of Markdown")
        dialog.select_folder(self, None, self._picked_folder)

    def _picked(self, dialog, result) -> None:
        try:
            chosen = dialog.open_finish(result)
        except Exception:
            return  # dismissed, which is not an error
        if chosen is not None:
            self.emit("chosen", chosen.get_path())

    def _picked_folder(self, dialog, result) -> None:
        try:
            chosen = dialog.select_folder_finish(result)
        except Exception:
            return
        if chosen is not None:
            self.emit("chosen", chosen.get_path())

    # --- when the book cannot be read ---

    def explain(self, reason: str) -> None:
        """A refusal is a sentence, not a stack trace.

        Ariadne refuses by name — no chapter convention, too few chapters, no
        quotation convention — and the reason is the useful part. Reaching it
        should not require a terminal.
        """
        dialog = Adw.AlertDialog()
        dialog.set_heading("That book cannot be read")
        dialog.set_body(reason)
        dialog.add_response("close", "Choose another")
        dialog.present(self)
