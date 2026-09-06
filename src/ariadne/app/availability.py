"""Whether this machine can open the desktop reader, and what to do if not.

The toolkit is not a wheel. GTK, libadwaita and the GObject bindings come from
the distribution, so a fresh clone can pass every test, install cleanly, and
still fail to open a window -- with a bare `ModuleNotFoundError: gi` and no
indication that the answer is two apt packages.

Nothing here imports the toolkit. It asks whether it *could*, which is a
different question and the only one that can be answered on a machine where it
cannot.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys

# name, what it is, and where it comes from on the distributions people use
REQUIREMENTS = (
    (
        "gi",
        "the GObject bindings",
        {
            "apt": "python3-gi python3-gi-cairo",
            "dnf": "python3-gobject",
            "pacman": "python-gobject",
        },
    ),
    (
        "gi.repository.Gtk",
        "GTK 4",
        {
            "apt": "gir1.2-gtk-4.0",
            "dnf": "gtk4",
            "pacman": "gtk4",
        },
    ),
    (
        "gi.repository.Adw",
        "libadwaita",
        {
            "apt": "gir1.2-adw-1",
            "dnf": "libadwaita",
            "pacman": "libadwaita",
        },
    ),
)


def package_manager() -> str:
    for tool in ("apt", "dnf", "pacman"):
        if shutil.which(tool):
            return tool
    return "apt"


def missing() -> list[tuple[str, str, dict]]:
    """What is not here. An empty list means the window will open."""
    if importlib.util.find_spec("gi") is None:
        return list(REQUIREMENTS)

    import gi

    absent = []
    for name, what, packages in REQUIREMENTS:
        if name == "gi":
            continue
        namespace, version = ("Gtk", "4.0") if name.endswith("Gtk") else ("Adw", "1")
        try:
            gi.require_version(namespace, version)
            __import__(f"gi.repository.{namespace}")
        except (ImportError, ValueError):
            absent.append((name, what, packages))
    return absent


def report(stream=None) -> int:
    """Say plainly what is here and what is not. Zero when the window will open."""
    out = stream or sys.stdout
    absent = missing()
    if not absent:
        import gi
        from gi.repository import Adw, Gtk

        print("ariadne: the desktop reader can open here.", file=out)
        print(
            f"  GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}"
            f"  ·  libadwaita {Adw.MAJOR_VERSION}.{Adw.MINOR_VERSION}"
            f"  ·  PyGObject {gi.__version__}",
            file=out,
        )
        return 0

    manager = package_manager()
    print("ariadne: the desktop reader cannot open here yet.", file=out)
    print("", file=out)
    for _name, what, _packages in absent:
        print(f"  missing  {what}", file=out)
    print("", file=out)
    wanted = " ".join(
        dict.fromkeys(
            package for _n, _w, packages in absent for package in packages.get(manager, "").split()
        )
    )
    install = {"apt": "sudo apt install", "dnf": "sudo dnf install", "pacman": "sudo pacman -S"}[
        manager
    ]
    print(f"  {install} {wanted}", file=out)
    print("", file=out)
    print("  Everything else works without them: the page, --inspect, --about,", file=out)
    print("  --refusals and the whole command line are unaffected.", file=out)
    return 1
