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
import os
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


# Where a packaged Ariadne puts its launcher. A wrapper in ~/bin beside one of
# these is the thing this looks for.
PACKAGED = (
    "/usr/bin/ariadne",
    "/usr/local/bin/ariadne",
    os.path.expanduser("~/.local/share/flatpak/exports/bin/com.kingletas.Ariadne"),
    "/var/lib/flatpak/exports/bin/com.kingletas.Ariadne",
    "/snap/bin/ariadne",
)


def installs() -> list[str]:
    """Every Ariadne on this machine, in the order a launch would find them.

    They all answer to one application id, so a running copy of any of them
    takes the launch of any other: the window that opens is whichever was
    already there, and nothing says so. Found the hard way -- a screenshot run
    photographed an installed copy for an entire session and reported success.
    """
    found = []
    # The entry point of the interpreter running this is not an install, it is
    # this. Listing it made the check fire on a machine with nothing wrong.
    #
    # `sys.prefix` and not the realpath of `sys.executable`: a virtualenv built
    # with --system-site-packages symlinks its python, so the realpath resolves
    # to /usr/bin and the venv's own entry point looks like a system install.
    mine = {os.path.join(sys.prefix, "bin"), os.path.dirname(sys.executable)}
    for directory in (os.environ.get("PATH") or "").split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, "ariadne")
        if not (os.path.isfile(candidate) and os.access(candidate, os.X_OK)):
            continue
        if directory in mine or os.path.dirname(candidate) in mine:
            continue
        real = os.path.realpath(candidate)
        if real not in [os.path.realpath(f) for f in found]:
            found.append(candidate)
    for packaged in PACKAGED:
        if os.path.exists(packaged) and os.path.realpath(packaged) not in [
            os.path.realpath(f) for f in found
        ]:
            found.append(packaged)
    return found


def one_install(stream) -> None:
    """Say so when there is more than one, and stay silent when there is not.

    The rule is that an app which ships an installation does not also keep a
    wrapper in ~/bin. The wrapper is for building it; the package is the app.
    """
    every = installs()
    if len(every) < 2:
        return
    print("", file=stream)
    print("  ariadne is installed %d times, and they share one" % len(every), file=stream)
    print("  application id — a running copy of any of them takes the", file=stream)
    print("  launch of any other, and says nothing:", file=stream)
    print("", file=stream)
    for path in every:
        marker = "   ← reached first" if path == every[0] else ""
        print(("    %s%s" % (path, marker)).rstrip(), file=stream)
    print("", file=stream)
    print("  Keep the packaged one. A ~/bin wrapper is for building it.", file=stream)


def where_rulings_go() -> str:
    """The store, and whether it can be written. A store nobody can find is one
    people worry about, and this is the command they run when they are worried."""
    from ..decisions.sidecar import store_dir

    directory = store_dir()
    if not os.path.isdir(directory):
        return f"{directory}  (made on the first ruling)"
    kept = len([n for n in os.listdir(directory) if n.endswith(".json")])
    return f"{directory}  ({kept} book{'' if kept == 1 else 's'})"


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
        print("", file=out)
        print(f"  rulings  {where_rulings_go()}", file=out)
        one_install(out)
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
