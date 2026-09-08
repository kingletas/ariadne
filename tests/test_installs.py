"""One app, one install. The check that says when that is not true.

Three copies of Ariadne answered to one application id on this machine, and
they all reach the same session bus name -- so a running copy of any of them
takes the launch of any other and the window that opens is whichever was
already there. Nothing says so.

It cost a screenshot run an entire session: `make smoke` woke an installed
Flatpak, photographed nothing, and exited 0.

The rule is that an app which ships an installation does not also keep a
wrapper in `~/bin`. The wrapper is for building it; the package is the app.
"""

import ast
import io
import os
from pathlib import Path

from ariadne.app.availability import installs, one_install

ROOT = Path(__file__).resolve().parents[1]


def only(monkeypatch, tmp_path, *names):
    """A PATH holding exactly the executables named, and nothing packaged."""
    directories = []
    for i, name in enumerate(names):
        directory = tmp_path / f"d{i}"
        directory.mkdir(exist_ok=True)
        target = directory / name
        target.write_text("#!/bin/sh\n", encoding="utf-8")
        target.chmod(0o755)
        directories.append(str(directory))
    monkeypatch.setenv("PATH", os.pathsep.join(directories))
    monkeypatch.setattr("ariadne.app.availability.PACKAGED", ())
    return directories


def said(monkeypatch, tmp_path, *names):
    only(monkeypatch, tmp_path, *names)
    out = io.StringIO()
    one_install(out)
    return out.getvalue()


def test_a_single_install_is_silent(monkeypatch, tmp_path):
    assert said(monkeypatch, tmp_path, "ariadne") == ""


def test_no_install_at_all_is_silent(monkeypatch, tmp_path):
    """Running from a checkout, which is every developer every day."""
    assert said(monkeypatch, tmp_path) == ""


def test_two_installs_are_named(monkeypatch, tmp_path):
    spoken = said(monkeypatch, tmp_path, "ariadne", "ariadne")
    assert "installed 2 times" in spoken
    assert "reached first" in spoken
    assert spoken.count("/ariadne") >= 2


def test_the_first_on_path_is_the_one_marked(monkeypatch, tmp_path):
    directories = only(monkeypatch, tmp_path, "ariadne", "ariadne")
    every = installs()
    assert every[0].startswith(directories[0]), "the marked one is not the one PATH finds"


def test_the_interpreter_running_this_is_not_an_install(monkeypatch, tmp_path):
    """A virtualenv's own entry point is not a second Ariadne, it is this one.

    `sys.prefix`, not the realpath of `sys.executable`: a venv built with
    --system-site-packages symlinks its python, so the realpath lands in
    /usr/bin and the venv's own entry point reads as a system install. That
    made the check fire on a machine with nothing wrong.
    """
    import sys

    venv = tmp_path / "venv"
    (venv / "bin").mkdir(parents=True)
    entry = venv / "bin" / "ariadne"
    entry.write_text("#!/bin/sh\n", encoding="utf-8")
    entry.chmod(0o755)

    elsewhere = tmp_path / "real"
    elsewhere.mkdir()
    packaged = elsewhere / "ariadne"
    packaged.write_text("#!/bin/sh\n", encoding="utf-8")
    packaged.chmod(0o755)

    monkeypatch.setenv("PATH", os.pathsep.join([str(venv / "bin"), str(elsewhere)]))
    monkeypatch.setattr("ariadne.app.availability.PACKAGED", ())
    monkeypatch.setattr(sys, "prefix", str(venv))

    every = installs()
    assert every == [str(packaged)], f"the running interpreter was counted: {every}"


# --- the window has to say whose it is ---------------------------------------


def test_the_program_name_is_set_to_the_application_id():
    """Wayland takes a window's app id from the program name, and GNOME finds
    a window's icon by matching that id to a .desktop file.

    The launcher runs `python3 -c ...`, so the name was `python3`: the shell
    looked for python3.desktop, found nothing, and drew a generic icon on a
    window that was otherwise working. Read from the source rather than run,
    because this has to be true before any window exists.
    """
    body = (ROOT / "src" / "ariadne" / "app" / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(body)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "set_prgname":
            continue
        assert node.args and getattr(node.args[0], "id", None) == "APP_ID", (
            "the program name is set to something other than the application id"
        )
        return
    raise AssertionError("nothing sets the program name, so the window has no icon")


def test_the_desktop_entry_names_the_window_class():
    """X11 matches on WM_CLASS rather than the Wayland app id, and an entry
    that does not say so has the same missing icon there."""
    entry = (ROOT / "data" / "com.kingletas.Ariadne.desktop").read_text(encoding="utf-8")
    assert "StartupWMClass=com.kingletas.Ariadne" in entry


def test_the_icon_carries_the_palette_the_application_uses():
    """The icon is the one drawing that lives outside `app/`, so the check that
    swept the retired colours out of the code never looked at it."""
    from ariadne.app import tokens

    icon = (ROOT / "data" / "com.kingletas.Ariadne.svg").read_text(encoding="utf-8")
    retired = ("#F7F3EA", "#2F6F68", "#B8832F")
    found = [colour for colour in retired if colour.lower() in icon.lower()]
    assert not found, f"the icon still uses the retired palette: {found}"
    assert tokens.LIGHT["accent"].lower() in icon.lower(), "the icon does not use the accent"
