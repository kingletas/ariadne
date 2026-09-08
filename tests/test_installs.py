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

import io
import os

from ariadne.app.availability import installs, one_install


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
