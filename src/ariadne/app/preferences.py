"""What the reader chose about the application, rather than about a book.

One small file beside the book store. A theme is not a ruling: it belongs to
the person and not to what they are reading, so it does not go in a sidecar
that follows one book around.

Everything here fails quietly. A preference that cannot be read costs somebody
their choice of theme; refusing to open the window over it would cost them the
book.
"""

from __future__ import annotations

import json
import os

from ..decisions.sidecar import store_dir

# What the reader can pick, and what each means to libadwaita. `system` is the
# default and the one that needs no explaining: it is what every other
# application on the machine does.
THEMES = ("system", "light", "dark")
DEFAULT = "system"


def settings_path() -> str:
    """Beside the books rather than inside them."""
    return os.path.join(os.path.dirname(store_dir()), "settings.json")


def read(name: str, fallback):
    """One setting, or the fallback. Never raises and never guesses."""
    try:
        with open(settings_path(), encoding="utf-8") as fh:
            return json.load(fh).get(name, fallback)
    except (OSError, ValueError):
        return fallback


def write(name: str, value) -> None:
    """Keep the rest of the file. Losing an unrelated setting to save one is
    the kind of small theft nobody notices until it matters."""
    path = settings_path()
    try:
        with open(path, encoding="utf-8") as fh:
            settings = json.load(fh)
        if not isinstance(settings, dict):
            settings = {}
    except (OSError, ValueError):
        settings = {}
    settings[name] = value
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
    except OSError:
        return


def theme() -> str:
    """The reader's choice, or `system` when they have not made one."""
    chosen = read("theme", DEFAULT)
    return chosen if chosen in THEMES else DEFAULT


def set_theme(name: str) -> None:
    if name in THEMES:
        write("theme", name)
